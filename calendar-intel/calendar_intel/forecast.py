from datetime import datetime, timedelta, timezone

from calendar_intel.auth import get_calendar_service
from calendar_intel.classifier import classify_event
from calendar_intel.config import FORECAST_DAYS


def get_upcoming_events(days: int = FORECAST_DAYS) -> list[dict]:
    service = get_calendar_service()
    now = datetime.now(timezone.utc)
    end = now + timedelta(days=days)

    events_result = service.events().list(
        calendarId="primary",
        timeMin=now.isoformat(),
        timeMax=end.isoformat(),
        singleEvents=True,
        orderBy="startTime",
        maxResults=100,
    ).execute()

    return events_result.get("items", [])


def build_forecast(days: int = FORECAST_DAYS) -> list[dict]:
    events = get_upcoming_events(days)
    now = datetime.now(timezone.utc)

    day_buckets = {}
    for d in range(days):
        date = (now + timedelta(days=d)).strftime("%Y-%m-%d")
        day_buckets[date] = {
            "date": date,
            "day_name": (now + timedelta(days=d)).strftime("%A"),
            "events": [],
            "high_strain_count": 0,
            "high_stress_count": 0,
            "recovery_negative_count": 0,
            "travel_count": 0,
            "has_rest": False,
        }

    for event in events:
        start = event.get("start", {})
        start_str = start.get("dateTime", start.get("date", ""))
        title = event.get("summary", "Untitled")

        if "T" in start_str:
            event_date = start_str[:10]
        else:
            event_date = start_str[:10]

        if event_date not in day_buckets:
            continue

        classification = classify_event(title)

        event_info = {
            "title": title,
            "start": start_str,
            "end": event.get("end", {}).get("dateTime", event.get("end", {}).get("date", "")),
            **classification,
        }

        bucket = day_buckets[event_date]
        bucket["events"].append(event_info)

        if classification["category"] == "high_strain":
            bucket["high_strain_count"] += 1
        elif classification["category"] == "high_stress":
            bucket["high_stress_count"] += 1
        elif classification["category"] == "recovery_negative":
            bucket["recovery_negative_count"] += 1
        elif classification["category"] == "travel":
            bucket["travel_count"] += 1
        elif classification["category"] == "rest":
            bucket["has_rest"] = True

    forecast = list(day_buckets.values())

    for i, day in enumerate(forecast):
        day["advice"] = _generate_advice(day, forecast[i - 1] if i > 0 else None, forecast[i + 1] if i + 1 < len(forecast) else None)

    return forecast


def _generate_advice(day: dict, prev_day: dict | None, next_day: dict | None) -> list[str]:
    advice = []

    if day["high_strain_count"] > 0 and day["high_stress_count"] > 0:
        advice.append("Heavy day — both intense exercise and high-pressure events. Prioritize sleep tonight.")

    if day["recovery_negative_count"] > 0 and next_day and next_day["high_strain_count"] > 0:
        advice.append(f"Drinks/late night today but {next_day['day_name']} has a workout — consider skipping or going easy tonight.")

    if day["recovery_negative_count"] > 0 and next_day and next_day["high_stress_count"] > 0:
        advice.append(f"Late night today but {next_day['day_name']} has a high-pressure event — early bed recommended.")

    if prev_day and prev_day["recovery_negative_count"] > 0 and day["high_strain_count"] > 0:
        advice.append("Yesterday had recovery-negative events — you might be yellow/red. Consider scaling back intensity.")

    if day["high_strain_count"] >= 2:
        advice.append("Multiple intense sessions planned — watch your strain budget and consider dropping one if recovery is low.")

    if day["travel_count"] > 0 and day["high_strain_count"] > 0:
        advice.append("Travel + training in one day — be flexible with the workout, fatigue may be higher than expected.")

    if day["has_rest"]:
        advice.append("Rest day — great for recovery. Protect it.")

    if not advice:
        if day["high_strain_count"] > 0:
            advice.append("Workout day — make sure recovery is green/yellow before going hard.")
        elif day["high_stress_count"] > 0:
            advice.append("Mentally demanding day — good sleep and low physical strain will help you perform.")
        else:
            advice.append("Light day — good opportunity to train if recovery allows.")

    return advice


def format_forecast(forecast: list[dict]) -> str:
    lines = []
    for day in forecast:
        lines.append(f"\n{day['day_name']} ({day['date']})")
        lines.append("-" * 30)

        if not day["events"]:
            lines.append("  No events scheduled")
        else:
            for e in day["events"]:
                cat_label = e["category"].replace("_", " ")
                lines.append(f"  {e['title']}")
                if e["category"] != "other":
                    lines.append(f"    → {cat_label}: {e['recovery_impact']}")

        for a in day["advice"]:
            lines.append(f"  💡 {a}")

    return "\n".join(lines)
