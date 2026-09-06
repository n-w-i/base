import httpx

from recovery_forecast.config import WHOOP_CORE_URL, CALENDAR_INTEL_URL

STRAIN_IMPACT = {
    "high": -18,
    "moderate": -8,
    "low": -3,
    "none": 0,
    "unknown": -5,
}

RECOVERY_IMPACT = {
    "high drain": -15,
    "moderate drain": -5,
    "stress — needs good sleep before": -10,
    "will hurt tomorrow's recovery": -20,
    "disrupts sleep routine": -12,
    "minimal": -2,
    "positive — aids recovery": 8,
    "unknown": -3,
}


def _fetch_whoop_data(days: int = 14) -> dict:
    try:
        with httpx.Client(base_url=WHOOP_CORE_URL, timeout=10) as client:
            today = client.get("/today").json()
            recoveries = client.get(f"/recoveries?days={days}").json()
            sleeps = client.get(f"/sleeps?days={days}").json()
            cycles = client.get(f"/cycles?days={days}").json()
        return {"today": today, "recoveries": recoveries, "sleeps": sleeps, "cycles": cycles}
    except httpx.ConnectError:
        return {}


def _fetch_calendar(days: int = 3) -> list[dict]:
    try:
        with httpx.Client(base_url=CALENDAR_INTEL_URL, timeout=10) as client:
            return client.get(f"/forecast?days={days}").json()
    except httpx.ConnectError:
        return []


def _compute_baseline(recoveries: list[dict], cycles: list[dict]) -> dict:
    scores = []
    hrvs = []
    rhrs = []

    for r in recoveries:
        s = r.get("score", {})
        if s.get("recovery_score") is not None:
            scores.append(s["recovery_score"])
        if s.get("hrv_rmssd_milli") is not None:
            hrvs.append(s["hrv_rmssd_milli"])
        if s.get("resting_heart_rate") is not None:
            rhrs.append(s["resting_heart_rate"])

    strains = [c["score"]["strain"] for c in cycles if c.get("score", {}).get("strain") is not None]

    def avg(lst):
        return sum(lst) / len(lst) if lst else 0

    return {
        "avg_recovery": avg(scores),
        "avg_hrv": avg(hrvs),
        "avg_rhr": avg(rhrs),
        "avg_strain": avg(strains),
        "recent_recovery": scores[0] if scores else None,
        "recent_hrv": hrvs[0] if hrvs else None,
        "recent_strain": strains[0] if strains else None,
        "recovery_trend": _trend(scores[:7]),
    }


def _trend(values: list) -> str:
    if len(values) < 3:
        return "insufficient data"
    recent = sum(values[:3]) / 3
    older = sum(values[3:min(7, len(values))]) / max(1, len(values[3:7]))
    diff = recent - older
    if diff > 5:
        return "improving"
    elif diff < -5:
        return "declining"
    return "stable"


def _estimate_sleep_quality(day_events: list[dict]) -> float:
    penalty = 0
    for e in day_events:
        cat = e.get("category", "other")
        if cat == "recovery_negative":
            penalty += 15
        elif cat == "travel":
            penalty += 10
        elif cat == "high_stress":
            penalty += 5
    return max(0, 100 - penalty)


def _predict_day(current_recovery: float, current_strain: float, day_calendar: dict | None, baseline: dict) -> dict:
    strain_delta = 0
    recovery_delta = 0
    events_affecting = []

    if day_calendar:
        for event in day_calendar.get("events", []):
            si = STRAIN_IMPACT.get(event.get("strain_impact", "unknown"), -5)
            ri = RECOVERY_IMPACT.get(event.get("recovery_impact", "unknown"), -3)
            # STRAIN_IMPACT's magnitude tracks physical intensity (e.g. "high" > "low");
            # its sign is only meaningful for RECOVERY_IMPACT's drain-on-recovery framing,
            # so strain load itself uses the absolute value.
            strain_delta += abs(si)
            recovery_delta += ri
            if event["category"] not in ("other", "cognitive"):
                events_affecting.append({
                    "title": event["title"],
                    "category": event["category"],
                    "impact": ri,
                })

    mean_reversion = (baseline["avg_recovery"] - current_recovery) * 0.3
    predicted = current_recovery + recovery_delta + mean_reversion

    sleep_quality = _estimate_sleep_quality(day_calendar.get("events", []) if day_calendar else [])
    sleep_bonus = (sleep_quality - 70) * 0.3
    predicted += sleep_bonus

    predicted = max(1, min(100, predicted))

    if predicted >= 67:
        zone = "green"
    elif predicted >= 34:
        zone = "yellow"
    else:
        zone = "red"

    # strain_delta's magnitude is on the same 0..18 scale as STRAIN_IMPACT, so it's
    # rescaled onto WHOOP's 0-21 strain range (roughly /5) before being applied.
    strain_mean_reversion = (baseline["avg_strain"] - current_strain) * 0.3
    predicted_strain = current_strain + (strain_delta / 5) + strain_mean_reversion
    predicted_strain = max(0, min(21, predicted_strain))

    return {
        "predicted_recovery": round(predicted, 1),
        "zone": zone,
        "recovery_delta": round(recovery_delta, 1),
        "mean_reversion": round(mean_reversion, 1),
        "sleep_quality_estimate": round(sleep_quality, 1),
        "predicted_strain": round(predicted_strain, 1),
        "strain_delta": round(strain_delta / 5, 1),
        "events_affecting": events_affecting,
    }


def build_prediction(forecast_days: int = 3) -> dict:
    whoop = _fetch_whoop_data()
    calendar = _fetch_calendar(forecast_days)

    if not whoop:
        return {"error": "Could not connect to whoop-core. Is it running on :9120?"}

    recoveries = whoop.get("recoveries", [])
    cycles = whoop.get("cycles", [])
    baseline = _compute_baseline(recoveries, cycles)

    today_recovery = baseline["recent_recovery"]
    if today_recovery is None:
        return {"error": "No recent recovery data. Run 'whoop-core sync' first."}

    today_strain = baseline["recent_strain"] if baseline["recent_strain"] is not None else baseline["avg_strain"]

    predictions = []
    running_recovery = today_recovery
    running_strain = today_strain

    for i in range(forecast_days):
        cal_day = calendar[i] if i < len(calendar) else None
        pred = _predict_day(running_recovery, running_strain, cal_day, baseline)
        pred["day"] = cal_day["day_name"] if cal_day else f"Day +{i+1}"
        pred["date"] = cal_day["date"] if cal_day else ""
        predictions.append(pred)
        running_recovery = pred["predicted_recovery"]
        running_strain = pred["predicted_strain"]

    return {
        "current": {
            "recovery": today_recovery,
            "hrv": baseline["recent_hrv"],
            "strain": today_strain,
            "avg_recovery_14d": round(baseline["avg_recovery"], 1),
            "avg_strain_14d": round(baseline["avg_strain"], 1),
            "trend": baseline["recovery_trend"],
        },
        "predictions": predictions,
        "calendar_connected": len(calendar) > 0,
    }


def format_prediction(result: dict) -> str:
    if "error" in result:
        return f"Error: {result['error']}"

    lines = []
    c = result["current"]
    lines.append(f"Current recovery: {c['recovery']}% (14-day avg: {c['avg_recovery_14d']}%, trend: {c['trend']})")
    if c.get("hrv"):
        lines.append(f"Current HRV: {c['hrv']:.1f}ms")
    if c.get("strain") is not None:
        lines.append(f"Current strain: {c['strain']:.1f} (14-day avg: {c['avg_strain_14d']})")

    lines.append(f"\nForecast ({'with' if result['calendar_connected'] else 'without'} calendar data):")
    lines.append("=" * 40)

    for p in result["predictions"]:
        zone_icon = {"green": "🟢", "yellow": "🟡", "red": "🔴"}[p["zone"]]
        lines.append(f"\n{p['day']} ({p['date']})")
        lines.append(f"  {zone_icon} Predicted recovery: {p['predicted_recovery']}% ({p['zone']})")
        lines.append(f"  🔥 Predicted strain: {p['predicted_strain']} / 21")

        if p["events_affecting"]:
            for e in p["events_affecting"]:
                sign = "+" if e["impact"] >= 0 else ""
                lines.append(f"    {e['title']} ({e['category'].replace('_', ' ')}) → {sign}{e['impact']} recovery")

        if p["recovery_delta"] != 0:
            lines.append(f"  Calendar impact: {p['recovery_delta']:+.0f}")
        lines.append(f"  Mean reversion: {p['mean_reversion']:+.1f}")
        lines.append(f"  Estimated sleep quality: {p['sleep_quality_estimate']:.0f}%")

    # Overall advice
    lines.append("\n" + "=" * 40)
    worst = min(result["predictions"], key=lambda p: p["predicted_recovery"])
    if worst["zone"] == "red":
        lines.append(f"⚠️  {worst['day']} looks rough — consider rescheduling intense activities or prioritizing sleep the night before.")
    elif worst["zone"] == "yellow":
        lines.append(f"📋 {worst['day']} may be tight — keep strain moderate and protect your sleep.")
    else:
        lines.append("✅ Looking good across the forecast — train as planned.")

    return "\n".join(lines)
