import httpx

from recovery_forecast.config import WHOOP_CORE_URL, CALENDAR_INTEL_URL

# Fitness/fatigue time constants, in days. This is the classic Banister
# impulse-response model (aka TrainingPeaks' CTL/ATL/TSB): "fitness" is a
# slow-moving rolling average of daily strain, "fatigue" a fast-moving one,
# and "freshness" (fitness minus fatigue) is how primed-vs-worn-down you are.
# See recovery-forecast/README.md for the plain-language version.
FITNESS_DAYS = 42
FATIGUE_DAYS = 7

# How much one freshness point (roughly a strain point's worth of build-up)
# nudges predicted recovery. This is a hand-picked weight, not a fit
# coefficient — nobody's validated the "right" size of this effect for you.
FRESHNESS_WEIGHT = 2.0

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


def _fetch_whoop_data(days: int = 14, cycle_days: int = 45) -> dict:
    # Fitness (42-day) needs a longer history than the 14-day window used
    # for the recovery baseline, so cycles are fetched separately and wider.
    try:
        with httpx.Client(base_url=WHOOP_CORE_URL, timeout=10) as client:
            today = client.get("/today").json()
            recoveries = client.get(f"/recoveries?days={days}").json()
            sleeps = client.get(f"/sleeps?days={days}").json()
            cycles = client.get(f"/cycles?days={cycle_days}").json()
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


def _compute_training_load(cycles: list[dict]) -> dict:
    """Fitness (slow-decay) and fatigue (fast-decay) rolling averages of daily
    strain — see FITNESS_DAYS/FATIGUE_DAYS above. whoop-core returns cycles
    newest-first, so they're reversed to walk oldest-to-newest, the direction
    the rolling average actually decays in."""
    ordered = list(reversed(cycles))
    strains = [c["score"]["strain"] for c in ordered if c.get("score", {}).get("strain") is not None]

    if not strains:
        return {"fitness": 0.0, "fatigue": 0.0}

    fitness = fatigue = strains[0]
    for s in strains[1:]:
        fitness += (s - fitness) / FITNESS_DAYS
        fatigue += (s - fatigue) / FATIGUE_DAYS

    return {"fitness": fitness, "fatigue": fatigue}


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


def _summarize_day(
    recovery_delta: float,
    freshness_adjustment: float,
    sleep_bonus: float,
    events_affecting: list[dict],
    predicted_strain: float,
    strain_load: float,
    base_strain: float,
) -> str:
    """One plain-English sentence per side of the forecast (recovery, strain),
    naming whichever factor moved the number the most."""
    drivers = [("calendar", recovery_delta), ("freshness", freshness_adjustment), ("sleep", sleep_bonus)]
    name, value = max(drivers, key=lambda d: abs(d[1]))

    if abs(value) < 2:
        recovery_note = "Recovery looks like a normal day for you."
    elif name == "calendar":
        title = events_affecting[0]["title"] if events_affecting else "today's plans"
        direction = "down" if value < 0 else "up"
        recovery_note = f"{title} is the main thing pulling recovery {direction} today."
    elif name == "freshness":
        recovery_note = (
            "Lingering fatigue from recent training is dragging recovery down."
            if value < 0 else
            "You're fresh off recent training, giving recovery a boost."
        )
    else:
        recovery_note = (
            "Calendar suggests rougher sleep tonight, denting recovery."
            if value < 0 else
            "Nothing on the calendar should disrupt sleep tonight."
        )

    if strain_load >= 3:
        strain_note = "Plenty of planned activity will add real strain today."
    elif predicted_strain < base_strain - 1:
        strain_note = "Should be a lighter strain day than usual."
    else:
        strain_note = "Strain should land close to what's typical for you lately."

    return f"{recovery_note} {strain_note}"


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


def _predict_day(
    current_recovery: float,
    current_strain: float,
    fitness: float,
    fatigue: float,
    day_calendar: dict | None,
    baseline: dict,
) -> dict:
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

    # Freshness = fitness minus fatigue, computed from the state going into
    # this day (i.e. before today's own training is added to the buckets
    # below) — this is how fresh/worn-down you wake up feeling.
    freshness = fitness - fatigue
    freshness_adjustment = freshness * FRESHNESS_WEIGHT

    predicted = current_recovery + recovery_delta + freshness_adjustment

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
    # The "reversion" target is now fatigue (a recency-weighted recent-strain
    # average) instead of a flat historical average, so quiet days settle back
    # toward what's actually typical for you lately, not a stale long-run mean.
    strain_load = strain_delta / 5
    strain_reversion = (fatigue - current_strain) * 0.3
    predicted_strain = current_strain + strain_load + strain_reversion
    predicted_strain = max(0, min(21, predicted_strain))

    # Roll fitness/fatigue forward by feeding in this day's predicted strain,
    # so the next day's freshness reflects today's planned training too.
    next_fitness = fitness + (predicted_strain - fitness) / FITNESS_DAYS
    next_fatigue = fatigue + (predicted_strain - fatigue) / FATIGUE_DAYS

    summary = _summarize_day(
        recovery_delta, freshness_adjustment, sleep_bonus,
        events_affecting, predicted_strain, strain_load, current_strain,
    )

    return {
        "predicted_recovery": round(predicted, 1),
        "zone": zone,
        "summary": summary,
        # The full recovery equation: base_recovery + recovery_delta +
        # freshness_adjustment + sleep_bonus (then clamped to 1-100) = predicted_recovery.
        "base_recovery": round(current_recovery, 1),
        "recovery_delta": round(recovery_delta, 1),
        "freshness_adjustment": round(freshness_adjustment, 1),
        "sleep_bonus": round(sleep_bonus, 1),
        # fitness/fatigue/freshness all describe the state going into this day
        # (before today's own training), so freshness == fitness - fatigue here.
        "fitness": round(fitness, 1),
        "fatigue": round(fatigue, 1),
        "freshness": round(freshness, 1),
        "sleep_quality_estimate": round(sleep_quality, 1),
        # The full strain equation: base_strain + strain_load + strain_reversion
        # (then clamped to 0-21) = predicted_strain.
        "predicted_strain": round(predicted_strain, 1),
        "base_strain": round(current_strain, 1),
        "strain_load": round(strain_load, 1),
        "strain_reversion": round(strain_reversion, 1),
        # Rolled-forward state for chaining into the next day's prediction —
        # not the same as fitness/fatigue above, which describe *this* day.
        "_next_fitness": next_fitness,
        "_next_fatigue": next_fatigue,
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
    load = _compute_training_load(cycles)

    today_recovery = baseline["recent_recovery"]
    if today_recovery is None:
        return {"error": "No recent recovery data. Run 'whoop-core sync' first."}

    today_strain = baseline["recent_strain"] if baseline["recent_strain"] is not None else baseline["avg_strain"]

    predictions = []
    running_recovery = today_recovery
    running_strain = today_strain
    running_fitness = load["fitness"]
    running_fatigue = load["fatigue"]

    for i in range(forecast_days):
        cal_day = calendar[i] if i < len(calendar) else None
        pred = _predict_day(running_recovery, running_strain, running_fitness, running_fatigue, cal_day, baseline)
        pred["day"] = cal_day["day_name"] if cal_day else f"Day +{i+1}"
        pred["date"] = cal_day["date"] if cal_day else ""
        running_recovery = pred["predicted_recovery"]
        running_strain = pred["predicted_strain"]
        running_fitness = pred.pop("_next_fitness")
        running_fatigue = pred.pop("_next_fatigue")
        predictions.append(pred)

    return {
        "current": {
            "recovery": today_recovery,
            "hrv": baseline["recent_hrv"],
            "strain": today_strain,
            "avg_recovery_14d": round(baseline["avg_recovery"], 1),
            "avg_strain_14d": round(baseline["avg_strain"], 1),
            "trend": baseline["recovery_trend"],
            "fitness": round(load["fitness"], 1),
            "fatigue": round(load["fatigue"], 1),
            "freshness": round(load["fitness"] - load["fatigue"], 1),
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
    if c.get("fitness") is not None:
        sign = "fresh" if c["freshness"] >= 0 else "fatigued"
        lines.append(f"Fitness: {c['fitness']} | Fatigue: {c['fatigue']} | Freshness: {c['freshness']:+.1f} ({sign})")

    lines.append(f"\nForecast ({'with' if result['calendar_connected'] else 'without'} calendar data):")
    lines.append("=" * 40)

    for p in result["predictions"]:
        zone_icon = {"green": "🟢", "yellow": "🟡", "red": "🔴"}[p["zone"]]
        lines.append(f"\n{p['day']} ({p['date']})")
        lines.append(f"  {zone_icon} Predicted recovery: {p['predicted_recovery']}% ({p['zone']})")
        lines.append(f"  🔥 Predicted strain: {p['predicted_strain']} / 21")
        lines.append(f"  {p['summary']}")

        if p["events_affecting"]:
            for e in p["events_affecting"]:
                sign = "+" if e["impact"] >= 0 else ""
                lines.append(f"    {e['title']} ({e['category'].replace('_', ' ')}) → {sign}{e['impact']} recovery")

        lines.append(f"  Freshness: {p['freshness']:+.1f} (fitness {p['fitness']} − fatigue {p['fatigue']})")
        lines.append(f"  Estimated sleep quality: {p['sleep_quality_estimate']:.0f}%")
        lines.append(
            f"  Recovery math: {p['base_recovery']} (base) "
            f"{p['recovery_delta']:+.0f} (calendar) "
            f"{p['freshness_adjustment']:+.1f} (freshness) "
            f"{p['sleep_bonus']:+.1f} (sleep) = {p['predicted_recovery']}%"
        )
        lines.append(
            f"  Strain math: {p['base_strain']} (base) "
            f"{p['strain_load']:+.1f} (planned activity) "
            f"{p['strain_reversion']:+.1f} (reverts toward fatigue) = {p['predicted_strain']}"
        )

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
