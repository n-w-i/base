# recovery-forecast

Multi-day recovery prediction for [Base](../README.md). Combines your WHOOP history with upcoming calendar events to forecast where your recovery is heading.

## Where the numbers actually come from

It's worth being upfront about this: **your current recovery, HRV, resting heart rate, and strain are real** — they come straight from WHOOP's own sensors and their own (proprietary, undocumented) scoring algorithm via whoop-core. We don't touch that math at all.

**Everything about future days is a guess we're making, not WHOOP's.** WHOOP doesn't forecast anything — it only ever tells you about today and the past. The multi-day forecast below is this module's own model, built from a few simple, hand-picked rules. It's a reasonable estimate, not a scientifically validated prediction, and it gets more useful the more days of real history whoop-core has synced.

## How the forecast is built

Three ingredients, recalculated for each day and chained forward (today's guess becomes tomorrow's starting point):

1. **Fitness, fatigue, and freshness** — this is the main driver. Think of two buckets that both fill up when you train:
   - **Fatigue** drains fast (roughly a week) — it's "how worn down you are from training recently"
   - **Fitness** drains slowly (roughly six weeks) — it's "how trained-up you are overall"
   - **Freshness** = fitness − fatigue. Positive means you're primed and recovered; negative means fatigue is outpacing your fitness. This is a well-established idea in sports science (sometimes called the Banister model, or CTL/ATL/TSB if you've used TrainingPeaks/Strava). We compute both buckets from your real WHOOP strain history, and freshness nudges the next day's predicted recovery up or down.
   - The size of that nudge (`FRESHNESS_WEIGHT` in the code) is a number we picked because it seemed reasonable — nobody's validated it against your actual outcomes.

2. **Calendar impact** — calendar-intel classifies your upcoming events by keyword (drinks → recovery drops, rest day → recovery improves, gym → adds to tomorrow's predicted strain). Each category has a fixed point value someone chose by feel, not something derived from your data. A "Gym" event always subtracts the same amount regardless of whether it's a 20-minute or 90-minute session.

3. **Estimated sleep quality** — a guess at how well you'll sleep, based only on what's on your calendar that day (travel and late nights lower it). It has no idea what you'll actually do or how you'll actually sleep.

**The honest caveats**: predictions compound — if day 1's guess is off, day 2 and 3 inherit that error, and nothing corrects it until you actually live through the day and WHOOP scores it for real. And because fitness/fatigue need real history to mean much, this forecast is more trustworthy the longer whoop-core has been syncing for you (a few days in, it's still finding its footing).

## Dependencies

- **whoop-core** (required) — must be running on `:9120` for WHOOP data
- **calendar-intel** (optional) — if running on `:9121`, predictions include calendar context. Without it, predictions are WHOOP-only.

## Setup

```bash
cd recovery-forecast
pip install -e .
```

## Use

```bash
# Make sure whoop-core is running first
whoop-core serve &

# Predict next 3 days
recovery-forecast predict

# With JSON output
recovery-forecast predict --json --days 5

# Start the API
recovery-forecast serve
```

## Example output

```
Current recovery: 89.0% (14-day avg: 82.5%, trend: stable)
Current HRV: 99.8ms
Current strain: 9.3 (14-day avg: 8.5)
Fitness: 6.9 | Fatigue: 8.0 | Freshness: -1.2 (fatigued)

Forecast (with calendar data):
========================================

Sunday (2026-09-06)
  🟢 Predicted recovery: 80.7% (green)
  🔥 Predicted strain: 12.5 / 21
    Gym (high strain) → -15 recovery
  Calendar impact: -15
  Freshness: -1.2 (fitness 6.9 − fatigue 8.0)
  Estimated sleep quality: 100%

Monday (2026-09-07)
  🟢 Predicted recovery: 86.4% (green)
  🔥 Predicted strain: 11.3 / 21
  Freshness: -1.7 (fitness 7.0 − fatigue 8.7)
  Estimated sleep quality: 100%

========================================
✅ Looking good across the forecast — train as planned.
```

## Local API

Runs on `http://localhost:9122` by default.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/predict?days=3` | GET | Multi-day recovery prediction |

## Claude MCP

```bash
claude mcp add recovery-forecast -- /path/to/recovery-forecast/.venv/bin/recovery-forecast-mcp
```

Then ask Claude: "predict my recovery for this week"
