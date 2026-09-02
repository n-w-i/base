import argparse
import json
import sys


def main():
    parser = argparse.ArgumentParser(
        prog="calendar-intel",
        description="Base calendar-intel — Google Calendar event classifier and forecast",
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("auth", help="Authenticate with Google Calendar")

    forecast_p = sub.add_parser("forecast", help="Show classified forecast for upcoming days")
    forecast_p.add_argument("--days", type=int, default=3, help="Days to forecast")
    forecast_p.add_argument("--json", action="store_true", help="Output raw JSON")

    sub.add_parser("today", help="Show today's classified events")

    serve_p = sub.add_parser("serve", help="Start the local REST API")
    serve_p.add_argument("--port", type=int, default=9121, help="Port to listen on")

    args = parser.parse_args()

    if args.command == "auth":
        from calendar_intel.auth import get_calendar_service
        get_calendar_service()
        print("Google Calendar authenticated successfully.")

    elif args.command == "forecast":
        from calendar_intel.forecast import build_forecast, format_forecast
        forecast = build_forecast(args.days)
        if args.json:
            print(json.dumps(forecast, indent=2))
        else:
            print(format_forecast(forecast))

    elif args.command == "today":
        from calendar_intel.forecast import build_forecast, format_forecast
        forecast = build_forecast(1)
        print(format_forecast(forecast))

    elif args.command == "serve":
        import uvicorn
        uvicorn.run(
            "calendar_intel.api:app",
            host="127.0.0.1",
            port=args.port,
            log_level="info",
        )

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
