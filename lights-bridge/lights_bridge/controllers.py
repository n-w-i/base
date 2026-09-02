import subprocess
import httpx

from lights_bridge.tuya_client import TuyaClient


def dim_via_shortcut(shortcut_name: str, brightness: int) -> bool:
    """Trigger an Apple Shortcut to set light brightness. The shortcut should
    accept a brightness value (0-100) as input."""
    try:
        subprocess.run(
            ["shortcuts", "run", shortcut_name, "--input-type", "text", "--input", str(brightness)],
            timeout=15,
            capture_output=True,
        )
        return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def dim_via_hue(bridge_ip: str, username: str, light_ids: list[str], brightness: int) -> bool:
    """Set Philips Hue lights to a specific brightness (0-254 scale)."""
    hue_bri = int(brightness * 254 / 100)
    body = {"on": brightness > 0, "bri": max(1, hue_bri), "transitiontime": 50}

    try:
        with httpx.Client(timeout=10) as client:
            for light_id in light_ids:
                client.put(
                    f"http://{bridge_ip}/api/{username}/lights/{light_id}/state",
                    json=body,
                )
        return True
    except httpx.ConnectError:
        return False


def dim_via_tuya(access_id: str, access_secret: str, api_endpoint: str, device_id: str, brightness: int) -> bool:
    """Set brightness via the Tuya Cloud API (works for Tuya/Smart Life devices
    like Lepro bulbs, independent of HomeKit/Google Home). Uses the standard
    instruction set: switch_led + bright_value_v2 (10-1000 scale)."""
    try:
        client = TuyaClient(access_id, access_secret, api_endpoint)
        if brightness <= 0:
            return client.send_commands(device_id, [{"code": "switch_led", "value": False}])

        bright_value = int(10 + (brightness / 100) * (1000 - 10))
        return client.send_commands(device_id, [
            {"code": "switch_led", "value": True},
            {"code": "bright_value_v2", "value": bright_value},
        ])
    except (httpx.ConnectError, RuntimeError):
        return False


def dim_via_homeassistant(ha_url: str, token: str, entity_id: str, brightness: int) -> bool:
    """Set brightness via Home Assistant REST API."""
    headers = {"Authorization": f"Bearer {token}"}
    service = "light/turn_on" if brightness > 0 else "light/turn_off"
    body = {"entity_id": entity_id}
    if brightness > 0:
        body["brightness"] = int(brightness * 255 / 100)

    try:
        with httpx.Client(timeout=10) as client:
            client.post(
                f"{ha_url}/api/services/{service}",
                json=body,
                headers=headers,
            )
        return True
    except httpx.ConnectError:
        return False
