from mcp.server.fastmcp import FastMCP

from hevy_intel.muscle import compute_muscle_fatigue, format_muscle_fatigue
from hevy_intel.summary import most_recent_workout, format_workout

mcp = FastMCP("hevy-intel")


@mcp.tool()
def muscle_group_fatigue(days: int = 14) -> str:
    """Get per-muscle-group training fatigue derived from logged Hevy
    workouts — which muscles were trained recently, how hard, and whether
    they're likely still fatigued. Use when the user asks what to train
    today, whether it's safe to train a muscle group again, or how sore
    they might still be."""
    fatigue = compute_muscle_fatigue(days)
    return format_muscle_fatigue(fatigue)


@mcp.tool()
def last_workout() -> str:
    """Get the most recently logged Hevy workout with its exercises and
    sets. Use when the user asks what they trained last, or wants a
    breakdown of their last session."""
    workout = most_recent_workout()
    return format_workout(workout) if workout else "No workout logged in the last 2 days."


def main():
    mcp.run()


if __name__ == "__main__":
    main()
