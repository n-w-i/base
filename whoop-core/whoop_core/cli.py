import argparse
import sys


def main():
    parser = argparse.ArgumentParser(
        prog="whoop-core",
        description="Tempo whoop-core — local WHOOP data service",
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("auth", help="Authenticate with WHOOP via OAuth")
    sub.add_parser("logout", help="Clear stored tokens")

    sync_p = sub.add_parser("sync", help="Sync WHOOP data to local DB")
    sync_p.add_argument("--days", type=int, default=30, help="Days of history to sync")

    serve_p = sub.add_parser("serve", help="Start the local REST API")
    serve_p.add_argument("--port", type=int, default=9120, help="Port to listen on")
    serve_p.add_argument("--sync-interval", type=int, default=15, help="Auto-sync interval in minutes (0 to disable)")

    sub.add_parser("today", help="Print today's snapshot to stdout")

    args = parser.parse_args()

    if args.command == "auth":
        from whoop_core.auth import authorize
        authorize()
        print("Done! You can now run: whoop-core sync")

    elif args.command == "logout":
        from whoop_core.tokens import clear_tokens
        clear_tokens()
        print("Tokens cleared.")

    elif args.command == "sync":
        from whoop_core.db import init_db
        from whoop_core.client import sync_all
        init_db()
        result = sync_all(args.days)
        for resource, count in result.items():
            print(f"  {resource}: {count} records")

    elif args.command == "serve":
        import asyncio
        from whoop_core.db import init_db
        from whoop_core.server import run_server
        init_db()
        asyncio.run(run_server(args.port, args.sync_interval))

    elif args.command == "today":
        import json
        from whoop_core.db import init_db, query_recent
        init_db()
        cycles = query_recent("cycles", days=1, limit=1)
        recovery = query_recent("recoveries", days=1, limit=1)
        sleep = query_recent("sleeps", days=1, limit=1)
        snapshot = {
            "cycle": cycles[0] if cycles else None,
            "recovery": recovery[0] if recovery else None,
            "sleep": sleep[0] if sleep else None,
        }
        print(json.dumps(snapshot, indent=2))

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
