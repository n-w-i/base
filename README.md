# Base

A modular, calendar-aware performance coach powered by your WHOOP data. Runs locally on your machine — your health data never leaves your laptop.

## What it does

Base reads your WHOOP recovery/strain/sleep data alongside your Google Calendar to give you actionable, forward-looking advice:

- **"Leg day tomorrow looks good — your HRV is trending up and you slept 8.1h"**
- **"Interview Thursday after Wednesday drinks = risky. Consider skipping the drinks or going easy"**
- **"You need to be asleep by 10:15pm to hit your sleep need before tomorrow's 7am meeting"**
- Dims your smart lights when it's time to wind down

## Modules

Each module runs independently or together:

| Module | What it does | Status |
|--------|-------------|--------|
| [whoop-core](./whoop-core/) | OAuth, data sync, local REST API | ✅ Built |
| [calendar-intel](./calendar-intel/) | Reads Google Calendar, classifies events, forecasts | ✅ Built |
| [recovery-forecast](./recovery-forecast/) | Multi-day recovery prediction model | ✅ Built |
| [base-menubar](./base-menubar/) | macOS menu bar widget (Swift) | ✅ Built |
| [lights-bridge](./lights-bridge/) | Smart light dimming at wind-down time | ✅ Built |

## Quick start

```bash
# 1. Set up whoop-core (see whoop-core/README.md for full guide)
cd whoop-core
pip install -e .
whoop-core auth
whoop-core serve

# 2. Other modules connect to http://localhost:9120
```

## Architecture

```
┌─────────────────┐     ┌──────────────────┐
│  Google Calendar │     │    WHOOP API     │
└────────┬────────┘     └────────┬─────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐     ┌──────────────────┐
│  calendar-intel │     │   whoop-core     │
│   :9121         │     │   :9120          │
└────────┬────────┘     └────────┬─────────┘
         │                       │
         └───────────┬───────────┘
                     ▼
          ┌─────────────────────┐
          │  recovery-forecast  │
          │       :9122         │
          └──────────┬──────────┘
                     │
         ┌───────────┼───────────┐
         ▼           ▼           ▼
┌──────────────┐ ┌────────┐ ┌──────────────┐
│ base-menubar│ │ alerts │ │ lights-bridge│
└──────────────┘ └────────┘ └──────────────┘
```

## Privacy & security

- All data stored locally in SQLite (`~/.base/whoop.db`)
- OAuth tokens in your system keychain
- APIs bind to `127.0.0.1` only
- No cloud services, no telemetry, no data sharing
- Calendar scanning uses local keyword matching — event titles never leave your machine
