from mcp.server.fastmcp import FastMCP

from calendar_intel.forecast import build_forecast, format_forecast

mcp = FastMCP("calendar-intel")


@mcp.tool()
def whats_on_my_calendar(days: int = 3) -> str:
    """Get a classified forecast of upcoming calendar events and their impact on
    recovery and strain. Use when the user asks what's coming up, what their
    week looks like, or how their schedule affects their training."""
    forecast = build_forecast(days)
    return format_forecast(forecast)


@mcp.tool()
def calendar_advice_for_today() -> str:
    """Get today's calendar events classified by impact on recovery/strain,
    with actionable advice. Use when the user asks what they should focus on
    today or how today's schedule affects their training."""
    forecast = build_forecast(1)
    if not forecast:
        return "No forecast available."
    day = forecast[0]
    lines = [f"Today ({day['day_name']}, {day['date']}):\n"]
    for e in day["events"]:
        cat = e["category"].replace("_", " ")
        lines.append(f"  {e['title']} — {cat}")
        if e["category"] != "other":
            lines.append(f"    Impact: {e['recovery_impact']}")
    lines.append("")
    for a in day["advice"]:
        lines.append(f"  Advice: {a}")
    return "\n".join(lines)


def main():
    mcp.run()


if __name__ == "__main__":
    main()
