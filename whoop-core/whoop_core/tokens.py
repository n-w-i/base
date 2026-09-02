import json
import time

import keyring

SERVICE = "base-whoop"
TOKEN_KEY = "oauth_tokens"


def save_tokens(access_token: str, refresh_token: str, expires_in: int) -> None:
    data = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_at": int(time.time()) + expires_in,
    }
    keyring.set_password(SERVICE, TOKEN_KEY, json.dumps(data))


def load_tokens() -> dict | None:
    raw = keyring.get_password(SERVICE, TOKEN_KEY)
    if not raw:
        return None
    return json.loads(raw)


def is_expired(tokens: dict) -> bool:
    return time.time() >= tokens["expires_at"] - 60


def clear_tokens() -> None:
    try:
        keyring.delete_password(SERVICE, TOKEN_KEY)
    except keyring.errors.PasswordDeleteError:
        pass
