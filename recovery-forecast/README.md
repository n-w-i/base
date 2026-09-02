# recovery-forecast

Multi-day recovery prediction for [Base](../README.md). Combines your WHOOP history with upcoming calendar events to forecast where your recovery is heading.

## How it works

The predictor uses three signals:

1. **Your baseline** — 14-day average recovery, HRV, and resting HR from whoop-core
2. **Calendar impact** — classified events from calendar-intel (drinks → recovery drops, rest day → recovery improves)
3. **Mean reversion** — if you're far from your average, the model assumes you'll drift back

It chains predictions forward: today's predicted recovery becomes tomorrow's starting point, so the effects compound realistically.

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
Current recovery: 62% (14-day avg: 58%, trend: improving)
Current HRV: 67.5ms

Forecast (with calendar data):
========================================

Saturday (2026-07-19)
  🟡 Predicted recovery: 59.2% (yellow)
    Drinks with friends (recovery negative) → -20 recovery

Sunday (2026-07-20)
  🔴 Predicted recovery: 42.1% (red)
    Leg day (high strain) → -15 recovery

Monday (2026-07-21)
  🟡 Predicted recovery: 51.8% (yellow)

========================================
⚠️  Sunday looks rough — consider rescheduling intense activities.
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
