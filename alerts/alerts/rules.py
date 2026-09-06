from datetime import date

import httpx

from alerts.config import WHOOP_CORE_URL, CALENDAR_INTEL_URL, RECOVERY_FORECAST_URL
from alerts.bedtime import calculate_bedtime

GENERIC_ADVICE = {
    "Light day — good opportunity to train if recovery allows.",
    "Rest day — great for recovery. Protect it.",
}


def _zone(score: float) -> str:
    if score >= 67:
        return "green"
    if score >= 34:
        return "yellow"
    return "red"


def check_recovery(state: dict) -> dict | None:
    """Notify once per day when today's recovery score first comes in."""
    try:
        with httpx.Client(base_url=WHOOP_CORE_URL, timeout=10) as client:
            today = client.get("/today").json()
    except httpx.ConnectError:
        return None

    recovery = today.get("recovery")
    if not recovery or not recovery.get("score"):
        return None

    score = recovery["score"].get("recovery_score")
    created_at = recovery.get("created_at", "")[:10]
    if score is None or not created_at:
        return None

    if state.get("last_recovery_alert_date") == created_at:
        return None

    zone = _zone(score)
    hrv = recovery["score"].get("hrv_rmssd_milli")
    sleep = today.get("sleep", {}).get("score", {})
    perf = sleep.get("sleep_performance_percentage")

    detail = f"HRV {hrv:.0f}ms" if hrv else ""
    if perf is not None:
        detail += f", slept {perf:.0f}% of need" if detail else f"Slept {perf:.0f}% of need"

    state["last_recovery_alert_date"] = created_at
    state["last_recovery_zone"] = zone

    icon = {"green": "🟢", "yellow": "🟡", "red": "🔴"}[zone]
    return {
        "title": "Base — Recovery",
        "message": f"{icon} Recovery: {int(score)}% ({zone}). {detail}".strip(),
    }


def check_calendar_advice(state: dict, lookahead_days: int = 2) -> list[dict]:
    """Surface non-generic calendar-intel advice for today/tomorrow, once each."""
    try:
        with httpx.Client(base_url=CALENDAR_INTEL_URL, timeout=10) as client:
            forecast = client.get(f"/forecast?days={lookahead_days}").json()
    except httpx.ConnectError:
        return []

    notified = set(state.get("notified_advice", []))
    new_notifications = []

    for day in forecast:
        for line in day.get("advice", []):
            if line in GENERIC_ADVICE:
                continue
            key = f"{day.get('date')}::{line}"
            if key in notified:
                continue
            notified.add(key)
            new_notifications.append({
                "title": f"Base — {day.get('day_name', 'Heads up')}",
                "message": line,
            })

    state["notified_advice"] = list(notified)
    return new_notifications


def check_forecast_risk(state: dict, lookahead_days: int = 3) -> dict | None:
    """Warn once per day about the worst predicted recovery day ahead."""
    try:
        with httpx.Client(base_url=RECOVERY_FORECAST_URL, timeout=10) as client:
            result = client.get(f"/predict?days={lookahead_days}").json()
    except httpx.ConnectError:
        return None

    predictions = result.get("predictions") or []
    if not predictions:
        return None

    today_str = date.today().isoformat()
    if state.get("last_forecast_alert_date") == today_str:
        return None

    worst = min(predictions, key=lambda p: p.get("predicted_recovery", 100))
    if worst.get("zone") not in ("red", "yellow"):
        return None

    state["last_forecast_alert_date"] = today_str

    events = worst.get("events_affecting") or []
    reason = f" — {events[0]['title']}" if events else ""
    return {
        "title": "Base — Forecast",
        "message": f"{worst['day']} looks like it could be rough ({int(worst['predicted_recovery'])}%, {worst['zone']}){reason}.",
    }


def check_bedtime(state: dict, minutes_before: int = 60) -> dict | None:
    """Remind once per day, shortly before the calculated bedtime."""
    bt = calculate_bedtime()

    today_str = date.today().isoformat()
    if state.get("last_bedtime_alert_date") == today_str:
        return None

    if not (0 <= bt["minutes_until_bedtime"] <= minutes_before):
        return None

    state["last_bedtime_alert_date"] = today_str

    wake_note = (
        f"tomorrow's {bt['wake_time']} meeting" if bt["wake_source"] == "calendar"
        else f"a {bt['wake_time']} wake-up"
    )
    return {
        "title": "Base — Bedtime",
        "message": f"You need to be asleep by {bt['bedtime_str']} to hit your sleep need before {wake_note}.",
    }
