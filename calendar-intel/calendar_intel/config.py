from pathlib import Path

DATA_DIR = Path.home() / ".base"
CREDENTIALS_PATH = DATA_DIR / "google_credentials.json"
TOKEN_PATH = DATA_DIR / "google_token.json"

GOOGLE_SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

FORECAST_DAYS = 3
