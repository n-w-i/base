# alerts

Proactive macOS notifications for [Base](../README.md). Turns the data the other modules already collect into things that actually reach you, instead of only showing up when you open the menu bar.

## What it does

Polls the other Base services and fires a native macOS notification when something is worth knowing:

| Trigger | Example |
|---|---|
| Today's recovery score comes in | "🟢 Recovery: 89% (green). HRV 100ms, slept 87% of need" |
| calendar-intel flags a risky day combo | "Drinks/late night today but Tuesday has a workout — consider skipping or going easy tonight." |
| recovery-forecast predicts a red/yellow day ahead | "Tuesday looks like it could be rough (28%, red) — Leg day" |
| Bedtime is coming up | "You need to be asleep by 22:15 to hit your sleep need before tomorrow's 7am meeting." |

Each alert fires at most once per day per trigger — state is tracked in `~/.base/alerts_state.json` so restarting the daemon doesn't re-notify.

## Dependencies

- **whoop-core** on `:9120` — recovery/sleep data
- **calendar-intel** on `:9121` (optional) — risky-day advice, bedtime wake time
- **recovery-forecast** on `:9122` (optional) — forecast risk warning

Any of the optional ones being down just means that trigger silently produces no alert — it doesn't stop the others.

## Setup

```bash
cd alerts
pip install -e .
```

## Use

```bash
# Fire a one-off test notification (also confirms macOS notification permissions)
alerts test

# Run all rule checks once and exit
alerts check

# Start the polling daemon (default: every 60s)
alerts run

# See when each alert last fired
alerts status

# View or change settings
alerts configure
alerts configure --set poll_interval_seconds=30 --set bedtime_reminder_minutes_before=45
```

If `alerts test` doesn't show a notification, check **System Settings → Notifications** for **Script Editor** (or **Terminal**, depending on how you're running this) and make sure alerts are allowed.

## Config

Stored at `~/.base/alerts.json`.

| Key | Default | Description |
|---|---|---|
| `poll_interval_seconds` | `60` | How often to check for new alerts |
| `quiet_hours_start` / `quiet_hours_end` | `23:00` / `07:00` | Suppresses recovery/calendar/forecast alerts in this window. Bedtime reminders still fire — they're time-critical by design. |
| `bedtime_reminder_minutes_before` | `60` | How far ahead of calculated bedtime to remind you |
| `forecast_lookahead_days` | `3` | How many days ahead calendar/forecast checks look |
