from pathlib import Path
import json

DATA_DIR = Path.home() / ".base"
CONFIG_PATH = DATA_DIR / "lights.json"

WHOOP_CORE_URL = "http://localhost:9120"
CALENDAR_INTEL_URL = "http://localhost:9121"

DEFAULTS = {
    "wind_down_minutes": 30,
    "dim_steps": 6,
    "dim_interval_seconds": 300,
    "method": "shortcut",
    "shortcut_name": "Dim Lights",
    "hue_bridge_ip": "",
    "hue_username": "",
    "hue_lights": [],
    "homeassistant_url": "",
    "homeassistant_token": "",
    "homeassistant_entity": "",
    "tuya_access_id": "",
    "tuya_access_secret": "",
    "tuya_api_endpoint": "",
    "tuya_device_id": "",
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
