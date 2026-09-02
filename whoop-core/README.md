# whoop-core

Local WHOOP data service for [Base](../README.md). Handles OAuth authentication, data syncing, and exposes a local REST API that other Base modules consume.

## Setup

### 1. Create a WHOOP Developer App

1. Go to [developer-dashboard.whoop.com](https://developer-dashboard.whoop.com)
2. Sign in with your WHOOP account
3. Create a Team (if you haven't already)
4. Create a new App with these settings:
   - **Scopes**: `read:recovery`, `read:cycles`, `read:sleep`, `read:workout`, `read:body_measurement`
   - **Redirect URI**: `http://localhost:8742/callback`
5. Copy your **Client ID** and **Client Secret**

### 2. Configure credentials

```bash
mkdir -p ~/.base
cat > ~/.base/.env << 'EOF'
WHOOP_CLIENT_ID=your_client_id_here
WHOOP_CLIENT_SECRET=your_client_secret_here
EOF
```

### 3. Install

```bash
cd whoop-core
pip install -e .
```

### 4. Authenticate

```bash
whoop-core auth
```

This opens your browser to authorize the app with your WHOOP account. Tokens are stored securely in your system keychain.

### 5. Sync & run

```bash
# One-time sync of last 30 days
whoop-core sync --days 30

# Start the local API server (auto-syncs every 15 min)
whoop-core serve

# Or just check today's data
whoop-core today
```

## Local API

Runs on `http://localhost:9120` by default.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Service health check |
| `/today` | GET | Today's cycle, recovery, sleep, workouts |
| `/cycles?days=30` | GET | Recent cycles |
| `/recoveries?days=30` | GET | Recent recoveries |
| `/sleeps?days=30` | GET | Recent sleep data |
| `/workouts?days=30` | GET | Recent workouts |
| `/profile` | GET | WHOOP user profile |
| `/body` | GET | Body measurements |
| `/sync?days=30` | POST | Trigger a manual sync |

## Architecture

- **OAuth tokens** → macOS Keychain (via `keyring`)
- **Data storage** → SQLite at `~/.base/whoop.db`
- **API** → FastAPI on localhost only (never exposed to network)
- **Auto-sync** → background task every 15 minutes (configurable)

## Security

- Client secret lives in `~/.base/.env` (gitignored, local only)
- Access/refresh tokens are in your system keychain, never in plaintext files
- The API binds to `127.0.0.1` only — not accessible from other machines
- All WHOOP communication is over HTTPS
