from pathlib import Path

from pydantic_settings import BaseSettings


DATA_DIR = Path.home() / ".base"
DB_PATH = DATA_DIR / "whoop.db"

WHOOP_AUTH_URL = "https://api.prod.whoop.com/oauth/oauth2/auth"
WHOOP_TOKEN_URL = "https://api.prod.whoop.com/oauth/oauth2/token"
WHOOP_API_BASE = "https://api.prod.whoop.com/developer"

SCOPES = [
    "read:recovery",
    "read:cycles",
    "read:sleep",
    "read:workout",
    "read:profile",
    "read:body_measurement",
    "offline",
]

OAUTH_REDIRECT_PORT = 8742
OAUTH_REDIRECT_URI = f"http://localhost:{OAUTH_REDIRECT_PORT}/callback"


class Settings(BaseSettings):
    whoop_client_id: str = ""
    whoop_client_secret: str = ""

    model_config = {
        "env_file": str(DATA_DIR / ".env"),
        "env_file_encoding": "utf-8",
    }


def get_settings() -> Settings:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return Settings()
