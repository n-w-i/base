import json

from alerts.config import STATE_PATH

DEFAULTS = {
    "last_recovery_alert_date": None,
    "last_recovery_zone": None,
    "notified_advice": [],
    "last_bedtime_alert_date": None,
    "last_forecast_alert_date": None,
}


def load_state() -> dict:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if STATE_PATH.exists():
        with open(STATE_PATH) as f:
            saved = json.load(f)
        return {**DEFAULTS, **saved}
    return dict(DEFAULTS)


def save_state(state: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    # cap notified_advice so it doesn't grow forever
    state["notified_advice"] = state.get("notified_advice", [])[-100:]
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2)
