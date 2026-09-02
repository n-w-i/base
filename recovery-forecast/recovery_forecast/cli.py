import argparse
import json
import sys


def main():
    parser = argparse.ArgumentParser(
        prog="recovery-forecast",
        description="Base recovery-forecast — multi-day recovery prediction",
    )
    sub = parser.add_subparsers(dest="command")

    predict_p = sub.add_parser("predict", help="Predict recovery for upcoming days")
    predict_p.add_argument("--days", type=int, default=3, help="Days to forecast")
    predict_p.add_argument("--json", action="store_true", help="Output raw JSON")

    serve_p = sub.add_parser("serve", help="Start the local REST API")
    serve_p.add_argument("--port", type=int, default=9122, help="Port to listen on")

    args = parser.parse_args()

    if args.command == "predict":
        from recovery_forecast.predictor import build_prediction, format_prediction
        result = build_prediction(args.days)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(format_prediction(result))

    elif args.command == "serve":
        import uvicorn
        uvicorn.run(
            "recovery_forecast.api:app",
            host="127.0.0.1",
            port=args.port,
            log_level="info",
        )

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
