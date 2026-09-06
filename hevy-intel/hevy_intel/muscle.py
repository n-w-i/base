import json
from datetime import datetime, timezone

from hevy_intel.config import FATIGUE_HALF_LIFE_DAYS
from hevy_intel.db import query_sets_since

LOOKBACK_DAYS = 14
HARD_SET_MIN_RPE = 8.0
SECONDARY_WEIGHT = 0.5  # a secondary mover's set counts for half a primary set


def _days_ago(start_time: str) -> float:
    started = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
    return (datetime.now(timezone.utc) - started).total_seconds() / 86400


def _decay(days_ago: float) -> float:
    return 0.5 ** (days_ago / FATIGUE_HALF_LIFE_DAYS)


def compute_muscle_fatigue(lookback_days: int = LOOKBACK_DAYS) -> dict:
    """Per muscle group: a recency-decayed fatigue score from working sets,
    days since it was last trained as a primary mover, and whether it's
    likely still fatigued. Warmup sets are excluded; secondary movers count
    at half weight. This is a rough proxy for residual soreness/fatigue —
    not a validated model, just recency + volume + intensity."""
    sets = query_sets_since(lookback_days)

    fatigue_score: dict[str, float] = {}
    hard_sets: dict[str, int] = {}
    total_sets: dict[str, int] = {}
    days_since_trained: dict[str, float] = {}

    for row in sets:
        if row["set_type"] == "warmup":
            continue
        primary = row["primary_muscle_group"]
        secondary = json.loads(row["secondary_muscle_groups"] or "[]")
        if not primary:
            continue

        age = _days_ago(row["start_time"])
        decay = _decay(age)
        is_hard = (row["rpe"] or 0) >= HARD_SET_MIN_RPE or row["set_type"] in ("dropset", "failure")

        for muscle, weight in [(primary, 1.0)] + [(m, SECONDARY_WEIGHT) for m in secondary]:
            fatigue_score[muscle] = fatigue_score.get(muscle, 0.0) + decay * weight
            total_sets[muscle] = total_sets.get(muscle, 0) + 1
            if is_hard:
                hard_sets[muscle] = hard_sets.get(muscle, 0) + 1
            if muscle not in days_since_trained or age < days_since_trained[muscle]:
                days_since_trained[muscle] = age

    result = {}
    for muscle, score in fatigue_score.items():
        days = round(days_since_trained[muscle], 1)
        if score >= 3.0:
            state = "fatigued"
        elif score >= 1.0:
            state = "recovering"
        else:
            state = "fresh"
        result[muscle] = {
            "fatigue_score": round(score, 2),
            "state": state,
            "days_since_trained": days,
            "sets_last_14d": total_sets.get(muscle, 0),
            "hard_sets_last_14d": hard_sets.get(muscle, 0),
        }

    return result


def format_muscle_fatigue(fatigue: dict) -> str:
    if not fatigue:
        return "No recent training data."
    lines = []
    for muscle, info in sorted(fatigue.items(), key=lambda kv: -kv[1]["fatigue_score"]):
        lines.append(
            f"  {muscle.replace('_', ' ')}: {info['state']} "
            f"(last trained {info['days_since_trained']}d ago, "
            f"{info['sets_last_14d']} sets / {info['hard_sets_last_14d']} hard in last 14d)"
        )
    return "\n".join(lines)
