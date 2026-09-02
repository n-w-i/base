# lights-bridge

Smart light dimming at bedtime, powered by your WHOOP sleep need and calendar.

Part of **Base** — runs standalone or alongside the other modules.

## What it does

1. Reads your **sleep need** from whoop-core (baseline + debt + strain)
2. Checks your **first event tomorrow** from calendar-intel
3. Calculates your ideal **bedtime** (wake time minus sleep need)
4. Gradually **dims your lights** over a 30-minute wind-down period

## Supported light systems

| Method | How it works |
|---|---|
| **Apple Shortcuts** (default) | Runs a Shortcut called "Dim Lights" with a brightness value. Works with any lights that Shortcuts can control (HomeKit, Lepro via Tuya, etc.) |
| **Philips Hue** | Direct Hue Bridge API — no cloud needed |
| **Home Assistant** | REST API call to any HA-controlled light |

## Setup

```bash
cd lights-bridge
python -m venv .venv && source .venv/bin/activate
pip install -e .
```

### Apple Shortcuts method (easiest)

1. Open Shortcuts.app on your Mac
2. Create a shortcut called **"Dim Lights"**
3. Add a "Set brightness" action for your lights
4. Use the **Shortcut Input** as the brightness value (0-100)

That's it — lights-bridge will call this shortcut with decreasing brightness values.

### Philips Hue method

```bash
lights-bridge configure \
  --set method=hue \
  --set hue_bridge_ip=192.168.1.50 \
  --set hue_username=YOUR_HUE_USERNAME \
  --set hue_lights=1,2,3
```

### Home Assistant method

```bash
lights-bridge configure \
  --set method=homeassistant \
  --set homeassistant_url=http://homeassistant.local:8123 \
  --set homeassistant_token=YOUR_LONG_LIVED_TOKEN \
  --set homeassistant_entity=light.bedroom
```

## Usage

```bash
# Check when bedtime is and whether dimming should start
lights-bridge status

# Start the dimming daemon
lights-bridge run

# View or change settings
lights-bridge configure
lights-bridge configure --set wind_down_minutes=45 --set dim_steps=9
```

## How dimming works

The default wind-down is 30 minutes with 6 steps, 5 minutes apart:

```
Step 1: 83% brightness
Step 2: 67%
Step 3: 50%
Step 4: 33%
Step 5: 17%
Step 6: 0% (off)
```

## Dependencies

- **whoop-core** running on `:9120` — for sleep need data
- **calendar-intel** running on `:9121` (optional) — for tomorrow's first event

Without whoop-core, sleep need defaults to 8 hours. Without calendar-intel, wake time defaults to 7:00 AM.

## Config

Stored at `~/.base/lights.json`. All settings:

| Key | Default | Description |
|---|---|---|
| `method` | `shortcut` | `shortcut`, `hue`, or `homeassistant` |
| `wind_down_minutes` | `30` | How long before bedtime to start dimming |
| `dim_steps` | `6` | Number of dimming steps |
| `dim_interval_seconds` | `300` | Seconds between each step |
| `shortcut_name` | `Dim Lights` | Name of the Apple Shortcut to run |
