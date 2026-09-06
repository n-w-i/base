from pathlib import Path

from pydantic_settings import BaseSettings

DATA_DIR = Path.home() / ".base"
DB_PATH = DATA_DIR / "hevy.db"

HEVY_API_BASE = "https://api.hevyapp.com/v1"

# Hevy's own docs ask clients not to poll exactly on the hour, so the
# background sync loop in server.py jitters its schedule instead of firing
# on a clean interval boundary.
DEFAULT_SYNC_INTERVAL_MINUTES = 20

# How much a working set's fatigue contribution decays per day — the
# muscle-fatigue model in muscle.py halves a set's weight every this many
# days, roughly tracking DOMS/recovery timelines rather than anything Hevy
# or WHOOP reports directly.
FATIGUE_HALF_LIFE_DAYS = 3.0


class Settings(BaseSettings):
    hevy_api_key: str = ""

    model_config = {
        "env_file": str(DATA_DIR / ".env"),
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


def get_settings() -> Settings:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return Settings()
