from pathlib import Path
import json

DATA_DIR = Path.home() / ".base"
CONFIG_PATH = DATA_DIR / "alerts.json"
STATE_PATH = DATA_DIR / "alerts_state.json"

WHOOP_CORE_URL = "http://localhost:9120"
CALENDAR_INTEL_URL = "http://localhost:9121"
RECOVERY_FORECAST_URL = "http://localhost:9122"

DEFAULTS = {
    "poll_interval_seconds": 60,
    "quiet_hours_start": "23:00",
    "quiet_hours_end": "07:00",
    "bedtime_reminder_minutes_before": 60,
    "forecast_lookahead_days": 3,
}


def load_config() -> dict:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            saved = json.load(f)
        return {**DEFAULTS, **saved}
    return dict(DEFAULTS)


def save_config(config: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)
