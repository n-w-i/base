# hevy-intel

Local Hevy workout sync for [Base](../README.md). Syncs your logged strength workouts (exercises, sets, reps, weight, RPE) and derives per-muscle-group fatigue that WHOOP's whole-body strain can't see.

## What it does

WHOOP tells you your overall cardiovascular strain, but not which muscles you actually trained. hevy-intel fills that gap:

- Syncs every logged workout, exercise, and set from Hevy
- Tags each set with its primary/secondary muscle groups (from Hevy's exercise templates)
- Computes a recency- and intensity-weighted fatigue score per muscle group — how likely it is you're still sore/depleted there
- Feeds that into `recovery-forecast`, which cross-references it against calendar-guessed workout days: if calendar-intel spots "leg day" tomorrow and hevy-intel says quads are still fatigued from Tuesday's heavy squats, the forecast says so
- Shows today's actual exercise breakdown in the menu bar instead of just WHOOP's bare sport name + strain

This only helps with *past, logged* workouts — it has no way to know about a workout you haven't done yet, so future calendar days still rely on calendar-intel's keyword guessing.

## Setup

### 1. Get a Hevy API key

Requires a **Hevy Pro** subscription.

1. Open the Hevy app or web app, go to **Settings → Developer**
2. Copy your API key

### 2. Configure credentials

hevy-intel shares `~/.base/.env` with whoop-core:

```bash
mkdir -p ~/.base
cat >> ~/.base/.env << 'EOF'
HEVY_API_KEY=your_api_key_here
EOF
```

### 3. Install

```bash
cd hevy-intel
pip install -e .
```

### 4. Sync & run

```bash
# One-time sync (exercise templates, then full workout history)
hevy-intel sync

# Start the local API server (auto-syncs every 20 min)
hevy-intel serve

# Or just check things directly
hevy-intel muscle-fatigue
hevy-intel today
```

## How muscle fatigue is calculated

For every working set (warmups excluded) in the last 14 days, weight = 1.0 for the exercise's primary muscle group and 0.5 for each secondary muscle group. Each set's contribution decays exponentially with a 3-day half-life — a rough proxy for how fast soreness/fatigue actually fades, not a validated model. A muscle group is:

- **fatigued** — decayed score ≥ 3.0 (heavy/frequent recent work)
- **recovering** — decayed score ≥ 1.0
- **fresh** — below that, or not trained recently

## Local API

Runs on `http://localhost:9123` by default.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/today` | GET | Most recent logged workout (exercises + sets) |
| `/workouts?days=30` | GET | Recent workouts |
| `/muscle-fatigue?days=14` | GET | Per-muscle-group fatigue |
| `/sync` | POST | Trigger a manual sync |

## Claude MCP

```bash
claude mcp add hevy-intel -- /path/to/hevy-intel/.venv/bin/hevy-intel-mcp
```

Then ask Claude: "is it safe to train legs today?" or "what did I train last?"

## Privacy & sync behavior

- **Local storage only** — workouts and templates are cached in SQLite at `~/.base/hevy.db`, never sent anywhere else
- **API key** lives in `~/.base/.env` (gitignored, local only)
- **Incremental sync** — after the first full sync, subsequent syncs use Hevy's `/workouts/events` endpoint (updates/deletes since a cursor) instead of re-fetching everything
- Hevy's API asks clients not to poll exactly on the hour; the default 20-minute auto-sync interval avoids that
