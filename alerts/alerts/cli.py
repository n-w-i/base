import argparse

from alerts.config import load_config, save_config, DEFAULTS
from alerts.state import load_state
from alerts.notifier import send_notification
from alerts.daemon import run_daemon, run_once


def cmd_configure(args):
    config = load_config()

    print("Current config:")
    for k, v in config.items():
        print(f"  {k}: {v}")

    print("\nTo change a setting, re-run with --set key=value")
    print("Example: alerts configure --set poll_interval_seconds=30")

    if args.set:
        for pair in args.set:
            key, _, value = pair.partition("=")
            if key not in DEFAULTS:
                print(f"  unknown key: {key}")
                continue
            if isinstance(DEFAULTS[key], int):
                value = int(value)
            config[key] = value
            print(f"  set {key} = {value}")
        save_config(config)
        print("saved to ~/.base/alerts.json")


def cmd_status(args):
    state = load_state()
    print("alerts status")
    print(f"  last recovery alert:  {state['last_recovery_alert_date']} ({state['last_recovery_zone']})")
    print(f"  last forecast alert:  {state['last_forecast_alert_date']}")
    print(f"  last bedtime alert:   {state['last_bedtime_alert_date']}")
    print(f"  advice notified:      {len(state['notified_advice'])} tracked")


def cmd_test(args):
    ok = send_notification("Base — Test", "If you can see this, notifications are working.")
    print("sent" if ok else "FAILED — check System Settings > Notifications for Script Editor/Terminal")


def cmd_check(args):
    config = load_config()
    state = load_state()
    sent = run_once(config, state)
    from alerts.state import save_state
    save_state(state)
    print(f"checked rules, {sent} notification(s) sent")


def cmd_run(args):
    run_daemon()


def main():
    parser = argparse.ArgumentParser(prog="alerts", description="Proactive notifications for Base")
    subs = parser.add_subparsers(dest="command")

    conf = subs.add_parser("configure", help="View or change settings")
    conf.add_argument("--set", nargs="*", metavar="key=value", help="Set config values")

    subs.add_parser("status", help="Show last-alerted state")
    subs.add_parser("test", help="Fire a test notification")
    subs.add_parser("check", help="Run all rule checks once and exit")
    subs.add_parser("run", help="Start the alerts daemon")

    args = parser.parse_args()

    if args.command == "configure":
        cmd_configure(args)
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "test":
        cmd_test(args)
    elif args.command == "check":
        cmd_check(args)
    elif args.command == "run":
        cmd_run(args)
    else:
        parser.print_help()
