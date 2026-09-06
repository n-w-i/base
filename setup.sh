#!/usr/bin/env bash
# Bootstraps a local Base install: creates a venv per Python module and
# installs it editable. Doesn't touch credentials or launchd — see README.md
# for the full walkthrough, and scripts/install-launchd.sh for auto-start.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY_MODULES=(whoop-core calendar-intel hevy-intel recovery-forecast alerts lights-bridge)

echo "Setting up Base at $REPO_DIR"
echo

for module in "${PY_MODULES[@]}"; do
    dir="$REPO_DIR/$module"
    echo "== $module =="
    if [ ! -d "$dir/.venv" ]; then
        python3 -m venv "$dir/.venv"
    fi
    "$dir/.venv/bin/pip" install -e "$dir" -q
    echo "  ok"
done

echo
mkdir -p "$HOME/.base"

if command -v swift >/dev/null 2>&1; then
    echo "== base-menubar =="
    (cd "$REPO_DIR/base-menubar" && swift build -c release)
    echo "  ok"
else
    echo "== base-menubar =="
    echo "  swift not found — skipping (base-menubar is macOS-only)"
fi

echo
echo "Python modules installed and base-menubar built. Before running anything:"
echo
if [ ! -f "$HOME/.base/.env" ]; then
    echo "  [ ] Create a WHOOP developer app and write credentials to ~/.base/.env"
    echo "      See whoop-core/README.md 'Setup' section."
else
    echo "  [x] ~/.base/.env already exists"
fi
if [ ! -f "$HOME/.base/google_credentials.json" ]; then
    echo "  [ ] Create Google Calendar OAuth credentials at ~/.base/google_credentials.json"
    echo "      See calendar-intel/README.md 'Setup' section."
else
    echo "  [x] ~/.base/google_credentials.json already exists"
fi
if [ -f "$HOME/.base/.env" ] && grep -q "^HEVY_API_KEY=" "$HOME/.base/.env"; then
    echo "  [x] HEVY_API_KEY already set in ~/.base/.env"
else
    echo "  [ ] (Optional) Add HEVY_API_KEY to ~/.base/.env for muscle-group-fatigue data"
    echo "      Requires Hevy Pro — see hevy-intel/README.md 'Setup' section."
fi
echo
echo "Then authenticate each service once:"
echo "  cd whoop-core      && .venv/bin/whoop-core auth"
echo "  cd calendar-intel  && .venv/bin/calendar-intel auth"
echo
echo "Once both are authenticated, run scripts/install-launchd.sh to start"
echo "everything and have it survive reboots/logouts."
