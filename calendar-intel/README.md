# calendar-intel

Google Calendar event classifier and forecast for [Base](../README.md). Reads your calendar, classifies events by their impact on recovery and strain, and produces a multi-day forecast with actionable advice.

## What it does

Scans your Google Calendar event titles for keywords and classifies them:

| Category | Examples | Impact |
|----------|----------|--------|
| High strain | leg day, HIIT, running, crossfit | Needs good recovery |
| Moderate strain | yoga, walking, hiking | Manageable on yellow |
| High stress | interview, presentation, deadline | Needs good sleep before |
| Recovery negative | drinks, party, late dinner | Hurts tomorrow's recovery |
| Travel | flight, road trip, hotel | Disrupts sleep routine |
| Cognitive | meeting, deep work, study | Low physical impact |
| Rest | rest day, massage, sauna | Aids recovery |

Then cross-references across days to give advice like:
- "Drinks tonight but leg day tomorrow — consider skipping or going easy"
- "Travel + training in one day — be flexible with the workout"

## Setup

### 1. Create Google Cloud OAuth credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a project (or use an existing one)
3. Enable the **Google Calendar API**
4. Go to **Credentials** → **Create Credentials** → **OAuth client ID**
5. Application type: **Desktop app**
6. Download the JSON and save it as `~/.base/google_credentials.json`

### 2. Install

```bash
cd calendar-intel
pip install -e .
```

### 3. Authenticate

```bash
calendar-intel auth
```

Opens your browser to authorize read-only access to your Google Calendar.

### 4. Use

```bash
# 3-day forecast
calendar-intel forecast

# Just today
calendar-intel today

# Raw JSON output
calendar-intel forecast --json --days 7

# Start the local API
calendar-intel serve
```

## Local API

Runs on `http://localhost:9121` by default.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/forecast?days=3` | GET | Classified multi-day forecast |
| `/today` | GET | Today's classified events |

## Claude MCP

Register as a Claude Code MCP server:

```bash
claude mcp add calendar-intel -- /path/to/calendar-intel/.venv/bin/calendar-intel-mcp
```

Then ask Claude: "what's on my calendar this week?"

## Privacy

- **Read-only access** — calendar-intel never modifies your calendar
- **Local keyword matching** — event titles are classified locally, never sent to any external service
- **Token stored locally** at `~/.base/google_token.json`
- **No event content is stored** — events are fetched fresh each time
