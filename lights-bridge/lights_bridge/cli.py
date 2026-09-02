import argparse
import json

from lights_bridge.config import load_config, save_config, DEFAULTS
from lights_bridge.bedtime import calculate_bedtime
from lights_bridge.daemon import run_daemon


def cmd_configure(args):
    config = load_config()

    print("Current config:")
    for k, v in config.items():
        print(f"  {k}: {v}")

    print("\nTo change a setting, re-run with --set key=value")
    print("Example: lights-bridge configure --set method=hue --set hue_bridge_ip=192.168.1.50")

    if args.set:
        for pair in args.set:
            key, _, value = pair.partition("=")
            if key not in DEFAULTS:
                print(f"  unknown key: {key}")
                continue
            if isinstance(DEFAULTS[key], int):
                value = int(value)
            elif isinstance(DEFAULTS[key], list):
                value = [v.strip() for v in value.split(",")]
            config[key] = value
            print(f"  set {key} = {value}")
        save_config(config)
        print("saved to ~/.base/lights.json")


def cmd_status(args):
    config = load_config()
    bt = calculate_bedtime(wind_down_minutes=config["wind_down_minutes"])

    print("lights-bridge status")
    print(f"  method:          {config['method']}")
    print(f"  wake time:       {bt['wake_time']} ({bt['wake_source']})")
    print(f"  sleep need:      {bt['sleep_need_hours']}h ({bt['sleep_source']})")
    print(f"  bedtime:         {bt['bedtime']}")
    print(f"  wind-down start: {bt['wind_down_start']}")
    if bt["should_dim_now"]:
        print("  >>> dimming should be active now")
    else:
        print(f"  starts in:       {bt['minutes_until_wind_down']} minutes")


def cmd_run(args):
    run_daemon()


def main():
    parser = argparse.ArgumentParser(prog="lights-bridge", description="Smart light dimming at bedtime")
    subs = parser.add_subparsers(dest="command")

    conf = subs.add_parser("configure", help="View or change settings")
    conf.add_argument("--set", nargs="*", metavar="key=value", help="Set config values")

    subs.add_parser("status", help="Show bedtime calculation and config")
    subs.add_parser("run", help="Start the dimming daemon")

    args = parser.parse_args()

    if args.command == "configure":
        cmd_configure(args)
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "run":
        cmd_run(args)
    else:
        parser.print_help()
