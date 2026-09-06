import signal
import time
from datetime import datetime

from alerts.config import load_config
from alerts.state import load_state, save_state
from alerts.notifier import send_notification
from alerts.rules import check_recovery, check_calendar_advice, check_forecast_risk, check_bedtime


def _in_quiet_hours(config: dict) -> bool:
    now = datetime.now().strftime("%H:%M")
    start, end = config["quiet_hours_start"], config["quiet_hours_end"]
    if start <= end:
        return start <= now < end
    return now >= start or now < end  # window wraps past midnight


def run_once(config: dict, state: dict) -> int:
    sent = 0
    quiet = _in_quiet_hours(config)

    notifications = []
    notifications.append(check_recovery(state))
    notifications.extend(check_calendar_advice(state, config["forecast_lookahead_days"]))
    notifications.append(check_forecast_risk(state, config["forecast_lookahead_days"]))

    # Bedtime reminders are time-critical by design, so they still fire in quiet hours.
    bedtime_alert = check_bedtime(state, config["bedtime_reminder_minutes_before"])

    for n in notifications:
        if n and not quiet:
            send_notification(n["title"], n["message"])
            print(f"  [{n['title']}] {n['message']}", flush=True)
            sent += 1

    if bedtime_alert:
        send_notification(bedtime_alert["title"], bedtime_alert["message"])
        print(f"  [{bedtime_alert['title']}] {bedtime_alert['message']}", flush=True)
        sent += 1

    return sent


def run_daemon():
    config = load_config()
    state = load_state()
    running = True

    def handle_stop(sig, frame):
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, handle_stop)
    signal.signal(signal.SIGTERM, handle_stop)

    print("alerts daemon started", flush=True)
    print(f"  poll interval: {config['poll_interval_seconds']}s", flush=True)
    print(f"  quiet hours: {config['quiet_hours_start']}-{config['quiet_hours_end']}", flush=True)

    while running:
        try:
            sent = run_once(config, state)
            save_state(state)
            if sent == 0:
                print("  no new alerts", flush=True)
        except Exception as e:
            print(f"  [error] {e}", flush=True)

        for _ in range(config["poll_interval_seconds"]):
            if not running:
                break
            time.sleep(1)

    print("alerts daemon stopped", flush=True)
