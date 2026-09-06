#!/usr/bin/env bash
# Generates and loads launchd agents so whoop-core, calendar-intel,
# hevy-intel, recovery-forecast, alerts, and base-menubar start on login and
# restart if they crash. Paths are derived from this script's location and
# $HOME, so it works for any user/clone location — not just the original
# machine.
#
# Run setup.sh and authenticate whoop-core + calendar-intel first. hevy-intel
# is optional (requires Hevy Pro) — it starts either way and just logs that
# HEVY_API_KEY isn't set if you haven't configured it.
# lights-bridge is intentionally NOT included — it needs a light method
# configured (Shortcut/Hue/Home Assistant/Tuya) before it's safe to run
# unattended nightly. Start it manually with `lights-bridge run` once
# configured, or add your own agent for it following this same pattern.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AGENTS_DIR="$HOME/Library/LaunchAgents"
LOG_DIR="$HOME/.base/logs"
UID_NUM="$(id -u)"

mkdir -p "$AGENTS_DIR" "$LOG_DIR"

write_agent() {
    local label="$1" ; shift
    local plist="$AGENTS_DIR/com.base.$label.plist"
    local workdir="$1" ; shift
    local args_xml=""
    for arg in "$@"; do
        args_xml+="        <string>${arg}</string>"$'\n'
    done

    cat > "$plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.base.$label</string>
    <key>ProgramArguments</key>
    <array>
${args_xml}    </array>
    <key>WorkingDirectory</key>
    <string>${workdir}</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>${LOG_DIR}/${label}.log</string>
    <key>StandardErrorPath</key>
    <string>${LOG_DIR}/${label}.log</string>
</dict>
</plist>
PLIST

    if launchctl bootout "gui/$UID_NUM/com.base.$label" >/dev/null 2>&1; then
        # bootout is asynchronous — an immediate re-bootstrap of the same
        # label intermittently fails with EIO if it runs before launchd
        # finishes tearing down the old job, so poll until it's gone.
        for _ in $(seq 1 20); do
            launchctl print "gui/$UID_NUM/com.base.$label" >/dev/null 2>&1 || break
            sleep 0.2
        done
    fi
    launchctl bootstrap "gui/$UID_NUM" "$plist"
    echo "  loaded com.base.$label"
}

echo "Installing launchd agents from $REPO_DIR"
echo

write_agent whoop-core \
    "$REPO_DIR/whoop-core" \
    "$REPO_DIR/whoop-core/.venv/bin/whoop-core" serve --sync-interval 1

write_agent calendar-intel \
    "$REPO_DIR/calendar-intel" \
    "$REPO_DIR/calendar-intel/.venv/bin/calendar-intel" serve

write_agent hevy-intel \
    "$REPO_DIR/hevy-intel" \
    "$REPO_DIR/hevy-intel/.venv/bin/hevy-intel" serve

write_agent recovery-forecast \
    "$REPO_DIR/recovery-forecast" \
    "$REPO_DIR/recovery-forecast/.venv/bin/recovery-forecast" serve

write_agent alerts \
    "$REPO_DIR/alerts" \
    "$REPO_DIR/alerts/.venv/bin/alerts" run

MENUBAR_BIN="$REPO_DIR/base-menubar/.build/arm64-apple-macosx/release/Base"
if [ ! -f "$MENUBAR_BIN" ]; then
    MENUBAR_BIN="$REPO_DIR/base-menubar/.build/x86_64-apple-macosx/release/Base"
fi
if [ -f "$MENUBAR_BIN" ]; then
    write_agent menubar "$REPO_DIR/base-menubar" "$MENUBAR_BIN"
else
    echo "  base-menubar release binary not found — run setup.sh first, or build manually:"
    echo "    cd base-menubar && swift build -c release"
fi

echo
echo "Done. Check status any time with: launchctl list | grep com.base"
echo "Logs are in $LOG_DIR"
