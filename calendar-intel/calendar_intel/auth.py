from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from calendar_intel.config import CREDENTIALS_PATH, TOKEN_PATH, GOOGLE_SCOPES


def get_calendar_service():
    creds = None

    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), GOOGLE_SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_PATH.exists():
                raise RuntimeError(
                    f"Google credentials not found at {CREDENTIALS_PATH}\n"
                    "Download your OAuth client JSON from Google Cloud Console\n"
                    "and save it as ~/.base/google_credentials.json"
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_PATH), GOOGLE_SCOPES
            )
            creds = flow.run_local_server(port=8743)

        TOKEN_PATH.write_text(creds.to_json())

    return build("calendar", "v3", credentials=creds)
