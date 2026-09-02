import time
import signal
import sys

from lights_bridge.config import load_config
from lights_bridge.bedtime import calculate_bedtime
from lights_bridge.controllers import dim_via_shortcut, dim_via_hue, dim_via_homeassistant


def _dim(config: dict, brightness: int) -> bool:
    method = config["method"]
    if method == "shortcut":
        return dim_via_shortcut(config["shortcut_name"], brightness)
    elif method == "hue":
        return dim_via_hue(
            config["hue_bridge_ip"], config["hue_username"],
            config["hue_lights"], brightness,
        )
    elif method == "homeassistant":
        return dim_via_homeassistant(
            config["homeassistant_url"], config["homeassistant_token"],
            config["homeassistant_entity"], brightness,
        )
    return False


def run_daemon():
    config = load_config()
    steps = config["dim_steps"]
    interval = config["dim_interval_seconds"]
    wind_down = config["wind_down_minutes"]

    running = True

    def handle_stop(sig, frame):
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, handle_stop)
    signal.signal(signal.SIGTERM, handle_stop)

    print("lights-bridge daemon started", flush=True)
    print(f"  method: {config['method']}", flush=True)
    print(f"  wind-down: {wind_down} min, {steps} steps, {interval}s apart", flush=True)

    dimming_started = False
    current_step = 0

    while running:
        bt = calculate_bedtime(wind_down_minutes=wind_down)
        print(
            f"  bedtime: {bt['bedtime']} | wind-down: {bt['wind_down_start']} | "
            f"dim now: {bt['should_dim_now']} | minutes until: {bt['minutes_until_wind_down']}",
            flush=True,
        )

        if bt["should_dim_now"] and not dimming_started:
            dimming_started = True
            current_step = 0
            print("  wind-down started — beginning to dim", flush=True)

        if dimming_started and current_step < steps:
            brightness = int(100 * (1 - (current_step + 1) / steps))
            brightness = max(0, brightness)
            ok = _dim(config, brightness)
            status = "ok" if ok else "FAILED"
            print(f"  step {current_step + 1}/{steps}: brightness → {brightness}% [{status}]", flush=True)
            current_step += 1
            time.sleep(interval)
        elif dimming_started and current_step >= steps:
            print("  dimming complete — lights off. goodnight!", flush=True)
            break
        else:
            time.sleep(60)

    print("lights-bridge daemon stopped", flush=True)
