from datetime import datetime, timedelta, timezone
import httpx

from lights_bridge.config import WHOOP_CORE_URL, CALENDAR_INTEL_URL


def _fetch_sleep_need() -> int | None:
    """Get total sleep need in milliseconds from whoop-core."""
    try:
        with httpx.Client(base_url=WHOOP_CORE_URL, timeout=10) as client:
            data = client.get("/today").json()
    except httpx.ConnectError:
        return None

    sleep = data.get("sleep")
    if not sleep or not sleep.get("score"):
        return None

    need = sleep["score"].get("sleep_needed", {})
    total = (
        (need.get("baseline_milli") or 0)
        + (need.get("need_from_sleep_debt_milli") or 0)
        + (need.get("need_from_recent_strain_milli") or 0)
        + (need.get("need_from_recent_nap_milli") or 0)
    )
    return total if total > 0 else None


def _fetch_tomorrow_first_event() -> str | None:
    """Get the start time of tomorrow's first calendar event."""
    try:
        with httpx.Client(base_url=CALENDAR_INTEL_URL, timeout=10) as client:
            forecast = client.get("/forecast?days=2").json()
    except httpx.ConnectError:
        return None

    if len(forecast) < 2:
        return None

    tomorrow = forecast[1]
    events = tomorrow.get("events", [])
    if not events:
        return None

    first = events[0]
    return first.get("start")


def calculate_bedtime(default_wake: str = "07:00", wind_down_minutes: int = 30) -> dict:
    sleep_need_ms = _fetch_sleep_need()
    tomorrow_first = _fetch_tomorrow_first_event()

    now = datetime.now()
    tomorrow = now + timedelta(days=1)

    if tomorrow_first and "T" in tomorrow_first:
        wake_time = datetime.fromisoformat(tomorrow_first.replace("Z", "+00:00"))
        wake_time = wake_time.astimezone().replace(tzinfo=None)
        wake_source = "calendar"
    else:
        h, m = default_wake.split(":")
        wake_time = tomorrow.replace(hour=int(h), minute=int(m), second=0, microsecond=0)
        wake_source = "default"

    if sleep_need_ms:
        sleep_need_hours = sleep_need_ms / 3_600_000
        sleep_source = "whoop"
    else:
        sleep_need_hours = 8.0
        sleep_source = "default (8h)"

    bedtime = wake_time - timedelta(hours=sleep_need_hours)
    wind_down_start = bedtime - timedelta(minutes=wind_down_minutes)

    return {
        "wake_time": wake_time.strftime("%H:%M"),
        "wake_source": wake_source,
        "sleep_need_hours": round(sleep_need_hours, 1),
        "sleep_source": sleep_source,
        "bedtime": bedtime.strftime("%H:%M"),
        "wind_down_start": wind_down_start.strftime("%H:%M"),
        "wind_down_minutes": wind_down_minutes,
        "should_dim_now": now >= wind_down_start,
        "minutes_until_wind_down": max(0, int((wind_down_start - now).total_seconds() / 60)),
    }
