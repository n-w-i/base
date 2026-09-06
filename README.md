# Base

A modular, calendar-aware performance coach powered by your WHOOP data. Runs locally on your machine — your health data never leaves your laptop.

## What it does

Base reads your WHOOP recovery/strain/sleep data alongside your Google Calendar to give you actionable, forward-looking advice:

- **"Leg day tomorrow looks good — your HRV is trending up and you slept 8.1h"**
- **"Interview Thursday after Wednesday drinks = risky. Consider skipping the drinks or going easy"**
- **"You need to be asleep by 10:15pm to hit your sleep need before tomorrow's 7am meeting"**
- Dims your smart lights when it's time to wind down

## Where the numbers come from

Your current recovery, strain, HRV, and sleep are real — straight from WHOOP's own sensors, unmodified. Everything about *future* days is a guess Base makes, not WHOOP (WHOOP itself never forecasts, only reports on today and the past). That guess is built from your real training history plus your calendar, using ideas borrowed from sports science (a "fitness vs. fatigue" model used by tools like TrainingPeaks) — not machine learning, and not validated against your actual outcomes. Full plain-language breakdown of exactly how it's calculated: [recovery-forecast/README.md](./recovery-forecast/).

## Modules

Each module runs independently or together:

| Module | What it does | Status |
|--------|-------------|--------|
| [whoop-core](./whoop-core/) | OAuth, data sync, local REST API | ✅ Built |
| [calendar-intel](./calendar-intel/) | Reads Google Calendar, classifies events, forecasts | ✅ Built |
| [recovery-forecast](./recovery-forecast/) | Multi-day recovery prediction model | ✅ Built |
| [base-menubar](./base-menubar/) | macOS menu bar widget (Swift) | ✅ Built |
| [alerts](./alerts/) | Proactive macOS notifications (recovery, risky days, bedtime) | ✅ Built |
| [lights-bridge](./lights-bridge/) | Smart light dimming at wind-down time | ✅ Built |

## Quick start

Base is designed to be self-hosted — every install is independent, runs entirely on your own machine, and uses your own credentials. There's no shared server; if a friend also wears WHOOP, they run their own copy the same way.

```bash
# 1. Install every module (creates a venv per module, builds base-menubar)
./setup.sh

# 2. Get your own credentials (one-time, per person):
#    - WHOOP developer app → whoop-core/README.md "Setup"
#    - Google Calendar OAuth → calendar-intel/README.md "Setup"

# 3. Authenticate (opens a browser for each)
cd whoop-core     && .venv/bin/whoop-core auth      && cd ..
cd calendar-intel && .venv/bin/calendar-intel auth  && cd ..

# 4. Start everything and make it survive reboot/logout
./scripts/install-launchd.sh
```

That covers whoop-core, calendar-intel, recovery-forecast, alerts, and base-menubar. `lights-bridge` is left out of auto-start deliberately — it needs a light-control method (Shortcuts/Hue/Home Assistant/Tuya) configured first; see [lights-bridge/README.md](./lights-bridge/).

Check on things any time with `launchctl list | grep com.base`; logs land in `~/.base/logs/`.

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
│ base-menubar │ │ alerts │ │ lights-bridge│
└──────────────┘ └────────┘ └──────────────┘
```

## Privacy & security

- All data stored locally in SQLite (`~/.base/whoop.db`)
- OAuth tokens in your system keychain
- APIs bind to `127.0.0.1` only
- No cloud services, no telemetry, no data sharing
- Calendar scanning uses local keyword matching — event titles never leave your machine
