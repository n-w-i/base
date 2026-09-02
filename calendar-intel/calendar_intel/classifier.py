import re

CATEGORIES = {
    "high_strain": {
        "keywords": [
            "leg day", "upper body", "push day", "pull day", "squat", "deadlift",
            "crossfit", "hiit", "run", "running", "sprint", "cycling", "swim",
            "basketball", "football", "soccer", "tennis", "boxing", "sparring",
            "gym", "workout", "training", "lift", "strength", "cardio",
            "peloton", "spin", "bootcamp", "circuit",
        ],
        "strain_impact": "high",
        "recovery_impact": "high drain",
        "description": "Intense physical activity — needs good recovery beforehand",
    },
    "moderate_strain": {
        "keywords": [
            "yoga", "pilates", "walk", "walking", "hike", "hiking",
            "stretch", "mobility", "recovery session", "easy run", "light workout",
            "golf", "climbing",
        ],
        "strain_impact": "moderate",
        "recovery_impact": "moderate drain",
        "description": "Moderate physical activity — manageable on yellow recovery",
    },
    "high_stress": {
        "keywords": [
            "interview", "presentation", "pitch", "review", "exam", "test",
            "deadline", "board meeting", "performance review", "final",
            "defense", "viva", "demo day", "launch",
        ],
        "strain_impact": "low",
        "recovery_impact": "stress — needs good sleep before",
        "description": "High-cognitive or high-pressure event",
    },
    "recovery_negative": {
        "keywords": [
            "drinks", "beer", "wine", "cocktail", "pub", "bar", "party",
            "night out", "happy hour", "brunch", "club", "festival",
            "late dinner", "red eye", "overnight",
        ],
        "strain_impact": "low",
        "recovery_impact": "will hurt tomorrow's recovery",
        "description": "Activity likely to impair next-day recovery",
    },
    "travel": {
        "keywords": [
            "flight", "travel", "airport", "fly", "train", "road trip",
            "commute", "layover", "check-in", "check-out", "hotel",
        ],
        "strain_impact": "low",
        "recovery_impact": "disrupts sleep routine",
        "description": "Travel — may disrupt sleep schedule",
    },
    "cognitive": {
        "keywords": [
            "project", "meeting", "standup", "sync", "workshop", "planning",
            "brainstorm", "focus", "deep work", "writing", "study", "lecture",
            "class", "seminar", "office hours", "1:1", "one on one",
        ],
        "strain_impact": "low",
        "recovery_impact": "minimal",
        "description": "Cognitive work — low physical impact",
    },
    "rest": {
        "keywords": [
            "rest day", "day off", "recovery day", "massage", "sauna",
            "spa", "meditation", "nap", "sleep in",
        ],
        "strain_impact": "none",
        "recovery_impact": "positive — aids recovery",
        "description": "Rest or recovery activity",
    },
}


def classify_event(title: str) -> dict:
    title_lower = title.lower().strip()

    for category, info in CATEGORIES.items():
        for keyword in info["keywords"]:
            if re.search(r'\b' + re.escape(keyword) + r'\b', title_lower):
                return {
                    "category": category,
                    "matched_keyword": keyword,
                    "strain_impact": info["strain_impact"],
                    "recovery_impact": info["recovery_impact"],
                    "description": info["description"],
                }

    return {
        "category": "other",
        "matched_keyword": None,
        "strain_impact": "unknown",
        "recovery_impact": "unknown",
        "description": "Unclassified event",
    }
