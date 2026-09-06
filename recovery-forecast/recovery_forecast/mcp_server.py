from mcp.server.fastmcp import FastMCP

from recovery_forecast.predictor import build_prediction, format_prediction

mcp = FastMCP("recovery-forecast")


@mcp.tool()
def predict_my_recovery(days: int = 3) -> str:
    """Predict recovery scores for the next few days based on WHOOP history
    and upcoming calendar events. Use when the user asks about their recovery
    forecast, whether they should train hard, or how their week will go
    physically. Requires whoop-core to be running on :9120. Calendar-intel
    on :9121 and hevy-intel on :9123 are both optional but add calendar-aware
    and muscle-group-fatigue-aware predictions respectively."""
    result = build_prediction(days)
    return format_prediction(result)


def main():
    mcp.run()


if __name__ == "__main__":
    main()
