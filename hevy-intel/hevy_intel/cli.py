import argparse
import json
import sys

from hevy_intel.config import DEFAULT_SYNC_INTERVAL_MINUTES


def main():
    parser = argparse.ArgumentParser(
        prog="hevy-intel",
        description="Base hevy-intel — local Hevy workout sync and muscle-group fatigue",
    )
    sub = parser.add_subparsers(dest="command")

    sync_p = sub.add_parser("sync", help="Sync workouts and exercise templates from Hevy")
    sync_p.add_argument("--force-templates", action="store_true", help="Re-fetch exercise templates too")

    serve_p = sub.add_parser("serve", help="Start the local REST API")
    serve_p.add_argument("--port", type=int, default=9123, help="Port to listen on")
    serve_p.add_argument(
        "--sync-interval", type=int, default=DEFAULT_SYNC_INTERVAL_MINUTES,
        help="Auto-sync interval in minutes (0 to disable)",
    )

    fatigue_p = sub.add_parser("muscle-fatigue", help="Show per-muscle-group fatigue")
    fatigue_p.add_argument("--days", type=int, default=14, help="Lookback window")
    fatigue_p.add_argument("--json", action="store_true", help="Output raw JSON")

    sub.add_parser("today", help="Show the most recent logged workout")

    args = parser.parse_args()

    if args.command == "sync":
        from hevy_intel.db import init_db
        from hevy_intel.client import sync_all, sync_exercise_templates, HevyNotConfigured
        init_db()
        try:
            if args.force_templates:
                sync_exercise_templates(force=True)
            result = sync_all()
            for resource, count in result.items():
                print(f"  {resource}: {count} records")
        except HevyNotConfigured as e:
            print(f"Error: {e}")
            sys.exit(1)

    elif args.command == "serve":
        import asyncio
        from hevy_intel.db import init_db
        from hevy_intel.server import run_server
        init_db()
        asyncio.run(run_server(args.port, args.sync_interval))

    elif args.command == "muscle-fatigue":
        from hevy_intel.db import init_db
        from hevy_intel.muscle import compute_muscle_fatigue, format_muscle_fatigue
        init_db()
        fatigue = compute_muscle_fatigue(args.days)
        if args.json:
            print(json.dumps(fatigue, indent=2))
        else:
            print(format_muscle_fatigue(fatigue))

    elif args.command == "today":
        from hevy_intel.db import init_db
        from hevy_intel.summary import most_recent_workout, format_workout
        init_db()
        workout = most_recent_workout()
        print(format_workout(workout) if workout else "No workout logged in the last 2 days.")

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
