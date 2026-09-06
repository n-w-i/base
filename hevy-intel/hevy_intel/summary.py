from hevy_intel.db import query_recent_workouts


def most_recent_workout(days: int = 2) -> dict | None:
    """The latest logged workout, if any, within the window — the one
    base-menubar shows as "today's" strength session."""
    workouts = query_recent_workouts(days=days, limit=1)
    return workouts[0] if workouts else None


def format_workout(workout: dict) -> str:
    lines = [f"{workout.get('title', 'Workout')} ({workout['start_time']})"]
    for exercise in workout.get("exercises", []):
        sets = exercise.get("sets", [])
        working = [s for s in sets if s.get("type") != "warmup"]
        top = max(working, key=lambda s: (s.get("weight_kg") or 0), default=None)
        summary = f"{len(working)} sets"
        if top:
            bits = []
            if top.get("weight_kg"):
                bits.append(f"top {top['weight_kg']}kg")
            if top.get("reps"):
                bits.append(f"x{int(top['reps'])}")
            if top.get("rpe"):
                bits.append(f"@RPE {top['rpe']}")
            if bits:
                summary += f", {' '.join(bits)}"
        lines.append(f"  {exercise['title']} — {summary}")
    return "\n".join(lines)
