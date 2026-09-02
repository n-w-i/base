import secrets
import threading
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlencode, urlparse, parse_qs

import httpx

from whoop_core.config import (
    WHOOP_AUTH_URL,
    WHOOP_TOKEN_URL,
    SCOPES,
    OAUTH_REDIRECT_PORT,
    OAUTH_REDIRECT_URI,
    get_settings,
)
from whoop_core.tokens import save_tokens, load_tokens, is_expired


class _OAuthCallbackHandler(BaseHTTPRequestHandler):
    auth_code: str | None = None

    def do_GET(self) -> None:
        query = parse_qs(urlparse(self.path).query)
        code = query.get("code", [None])[0]

        if code:
            _OAuthCallbackHandler.auth_code = code
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(
                b"<html><body><h2>Authenticated! You can close this tab.</h2></body></html>"
            )
        else:
            error = query.get("error", ["unknown"])[0]
            desc = query.get("error_description", [""])[0]
            hint = query.get("error_hint", [""])[0]
            print(f"\n[auth] Error: {error}")
            print(f"[auth] Description: {desc}")
            print(f"[auth] Hint: {hint}")
            self.send_response(400)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            msg = f"Error: {error}<br>Description: {desc}<br>Hint: {hint}"
            self.wfile.write(f"<html><body><h2>{msg}</h2></body></html>".encode())

        threading.Thread(target=self.server.shutdown).start()

    def log_message(self, format, *args) -> None:
        pass


def authorize() -> dict:
    """Run the full OAuth authorization code flow. Opens a browser for user consent."""
    settings = get_settings()
    if not settings.whoop_client_id or not settings.whoop_client_secret:
        raise RuntimeError(
            f"Set WHOOP_CLIENT_ID and WHOOP_CLIENT_SECRET in ~/.base/.env"
        )

    state = secrets.token_urlsafe(8)[:8]
    params = {
        "client_id": settings.whoop_client_id,
        "redirect_uri": OAUTH_REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "state": state,
    }
    auth_url = f"{WHOOP_AUTH_URL}?{urlencode(params)}"

    _OAuthCallbackHandler.auth_code = None
    server = HTTPServer(("localhost", OAUTH_REDIRECT_PORT), _OAuthCallbackHandler)

    print(f"Opening browser for WHOOP authorization...\n{auth_url}\n")
    webbrowser.open(auth_url)
    server.handle_request()
    server.server_close()

    code = _OAuthCallbackHandler.auth_code
    if not code:
        raise RuntimeError("Authorization failed — no code received")

    return _exchange_code(code, settings)


def _exchange_code(code: str, settings) -> dict:
    resp = httpx.post(
        WHOOP_TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": OAUTH_REDIRECT_URI,
            "client_id": settings.whoop_client_id,
            "client_secret": settings.whoop_client_secret,
        },
    )
    resp.raise_for_status()
    data = resp.json()
    save_tokens(data["access_token"], data["refresh_token"], data["expires_in"])
    print("Tokens saved to keychain.")
    return data


def refresh_access_token() -> dict:
    """Refresh the access token using the stored refresh token."""
    settings = get_settings()
    tokens = load_tokens()
    if not tokens or not tokens.get("refresh_token"):
        raise RuntimeError("No refresh token found — run 'whoop-core auth' first")

    resp = httpx.post(
        WHOOP_TOKEN_URL,
        data={
            "grant_type": "refresh_token",
            "refresh_token": tokens["refresh_token"],
            "client_id": settings.whoop_client_id,
            "client_secret": settings.whoop_client_secret,
            "scope": "offline",
        },
    )
    resp.raise_for_status()
    data = resp.json()
    save_tokens(data["access_token"], data["refresh_token"], data["expires_in"])
    return data


def get_valid_token() -> str:
    """Return a valid access token, refreshing if needed."""
    tokens = load_tokens()
    if not tokens:
        raise RuntimeError("Not authenticated — run 'whoop-core auth' first")

    if is_expired(tokens):
        tokens = refresh_access_token()
        return tokens["access_token"]

    return tokens["access_token"]
