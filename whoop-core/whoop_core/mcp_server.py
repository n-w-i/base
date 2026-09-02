import json
from datetime import datetime

from mcp.server.fastmcp import FastMCP

from whoop_core.db import init_db, query_recent

mcp = FastMCP("whoop")


def _ms_to_hours(ms: int | None) -> str:
    if ms is None:
        return "unknown"
    hours = ms / 3_600_000
    h = int(hours)
    m = int((hours - h) * 60)
    return f"{h}h {m}m"


def _format_today(cycle: dict | None, recovery: dict | None, sleep: dict | None, workouts: list) -> str:
    lines = []

    if recovery and recovery.get("score"):
        s = recovery["score"]
        score = s.get("recovery_score", "?")
        zone = "green" if score >= 67 else "yellow" if score >= 34 else "red"
        lines.append(f"Recovery: {score}% ({zone})")
        lines.append(f"  HRV: {s.get('hrv_rmssd_milli', '?'):.1f}ms")
        lines.append(f"  Resting HR: {s.get('resting_heart_rate', '?')} bpm")
        if s.get("spo2_percentage"):
            lines.append(f"  SpO2: {s['spo2_percentage']}%")
        if s.get("skin_temp_celsius"):
            lines.append(f"  Skin temp: {s['skin_temp_celsius']:.1f}°C")

    if sleep and sleep.get("score"):
        s = sleep["score"]
        stages = s.get("stage_summary", {})
        need = s.get("sleep_needed", {})
        lines.append(f"\nSleep: {s.get('sleep_performance_percentage', '?')}% performance")
        lines.append(f"  Time in bed: {_ms_to_hours(stages.get('total_in_bed_time_milli'))}")
        lines.append(f"  Deep sleep: {_ms_to_hours(stages.get('total_slow_wave_sleep_time_milli'))}")
        lines.append(f"  REM sleep: {_ms_to_hours(stages.get('total_rem_sleep_time_milli'))}")
        lines.append(f"  Light sleep: {_ms_to_hours(stages.get('total_light_sleep_time_milli'))}")
        lines.append(f"  Awake: {_ms_to_hours(stages.get('total_awake_time_milli'))}")
        lines.append(f"  Disturbances: {stages.get('disturbance_count', '?')}")
        lines.append(f"  Sleep cycles: {stages.get('sleep_cycle_count', '?')}")
        lines.append(f"  Efficiency: {s.get('sleep_efficiency_percentage', '?'):.1f}%")
        lines.append(f"  Respiratory rate: {s.get('respiratory_rate', '?'):.1f} breaths/min")
        total_need = (need.get("baseline_milli", 0) + need.get("need_from_sleep_debt_milli", 0)
                      + need.get("need_from_recent_strain_milli", 0) + need.get("need_from_recent_nap_milli", 0))
        lines.append(f"  Sleep needed: {_ms_to_hours(total_need)} (baseline {_ms_to_hours(need.get('baseline_milli'))})")
        if need.get("need_from_sleep_debt_milli", 0) > 0:
            lines.append(f"  Sleep debt: +{_ms_to_hours(need['need_from_sleep_debt_milli'])}")

    if cycle and cycle.get("score"):
        s = cycle["score"]
        lines.append(f"\nStrain: {s.get('strain', '?'):.1f}")
        lines.append(f"  Calories: {(s.get('kilojoule', 0) / 4.184):.0f} kcal")
        lines.append(f"  Avg HR: {s.get('average_heart_rate', '?')} bpm")
        lines.append(f"  Max HR: {s.get('max_heart_rate', '?')} bpm")

    if workouts:
        lines.append(f"\nWorkouts today: {len(workouts)}")
        for w in workouts:
            ws = w.get("score", {})
            lines.append(f"  - {w.get('sport_name', 'unknown')}: strain {ws.get('strain', '?'):.1f}, "
                        f"{ws.get('average_heart_rate', '?')} avg HR")

    return "\n".join(lines) if lines else "No data synced yet. Run 'whoop-core sync' first."


@mcp.tool()
def how_am_i_feeling() -> str:
    """Get today's WHOOP snapshot — recovery score, sleep quality, strain, and HRV.
    Use this when the user asks how they're feeling, how their recovery is,
    how they slept, or anything about their current health status."""
    init_db()
    cycles = query_recent("cycles", days=1, limit=1)
    recoveries = query_recent("recoveries", days=1, limit=1)
    sleeps = query_recent("sleeps", days=1, limit=1)
    workouts = query_recent("workouts", days=1, limit=5)
    return _format_today(
        cycles[0] if cycles else None,
        recoveries[0] if recoveries else None,
        sleeps[0] if sleeps else None,
        workouts,
    )


@mcp.tool()
def get_recovery_trend(days: int = 7) -> str:
    """Get recovery scores and HRV over recent days to spot trends.
    Use this when the user asks about their recovery trend, how their
    week has been, or whether they're overtraining."""
    init_db()
    recoveries = query_recent("recoveries", days=days, limit=days)
    if not recoveries:
        return "No recovery data found. Run 'whoop-core sync' first."

    lines = [f"Recovery trend (last {days} days):\n"]
    for r in recoveries:
        s = r.get("score", {})
        date = r.get("created_at", "")[:10]
        score = s.get("recovery_score", "?")
        hrv = s.get("hrv_rmssd_milli", 0)
        rhr = s.get("resting_heart_rate", "?")
        zone = "green" if isinstance(score, (int, float)) and score >= 67 else "yellow" if isinstance(score, (int, float)) and score >= 34 else "red"
        lines.append(f"  {date}: {score}% ({zone}) — HRV {hrv:.1f}ms, RHR {rhr}bpm")

    scores = [r["score"]["recovery_score"] for r in recoveries if r.get("score", {}).get("recovery_score") is not None]
    if scores:
        avg = sum(scores) / len(scores)
        lines.append(f"\n  Average: {avg:.0f}%")
        if len(scores) >= 3 and scores[0] < scores[-1] - 10:
            lines.append("  Trend: declining — consider extra rest")
        elif len(scores) >= 3 and scores[0] > scores[-1] + 10:
            lines.append("  Trend: improving")

    return "\n".join(lines)


@mcp.tool()
def get_sleep_trend(days: int = 7) -> str:
    """Get sleep duration, performance, and efficiency over recent days.
    Use this when the user asks about their sleep patterns or quality."""
    init_db()
    sleeps = query_recent("sleeps", days=days, limit=days)
    if not sleeps:
        return "No sleep data found. Run 'whoop-core sync' first."

    lines = [f"Sleep trend (last {days} days):\n"]
    for s in sleeps:
        sc = s.get("score", {})
        stages = sc.get("stage_summary", {})
        date = s.get("start", "")[:10]
        perf = sc.get("sleep_performance_percentage", "?")
        total = _ms_to_hours(stages.get("total_in_bed_time_milli"))
        deep = _ms_to_hours(stages.get("total_slow_wave_sleep_time_milli"))
        lines.append(f"  {date}: {perf}% performance, {total} in bed, {deep} deep sleep")

    return "\n".join(lines)


@mcp.tool()
def get_strain_and_workouts(days: int = 7) -> str:
    """Get daily strain scores and workout details over recent days.
    Use this when the user asks about their training load, workouts,
    or exercise history."""
    init_db()
    cycles = query_recent("cycles", days=days, limit=days)
    workouts = query_recent("workouts", days=days, limit=50)

    lines = [f"Strain & workouts (last {days} days):\n"]

    if cycles:
        lines.append("Daily strain:")
        for c in cycles:
            s = c.get("score", {})
            date = c.get("start", "")[:10]
            strain = s.get("strain", 0)
            lines.append(f"  {date}: {strain:.1f} strain, {(s.get('kilojoule', 0) / 4.184):.0f} kcal")

    if workouts:
        lines.append("\nWorkouts:")
        for w in workouts:
            ws = w.get("score", {})
            date = w.get("start", "")[:10]
            lines.append(f"  {date}: {w.get('sport_name', 'unknown')} — strain {ws.get('strain', 0):.1f}, "
                        f"{ws.get('average_heart_rate', '?')} avg HR, {_ms_to_hours(ws.get('distance_meter'))}")

    return "\n".join(lines) if lines else "No strain data found."


def main():
    mcp.run()


if __name__ == "__main__":
    main()
