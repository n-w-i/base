import hashlib
import hmac
import json
import time

import httpx


class TuyaClient:
    """Minimal Tuya Cloud API client: token exchange + signed device commands."""

    def __init__(self, access_id: str, access_secret: str, api_endpoint: str):
        self.access_id = access_id
        self.access_secret = access_secret
        self.api_endpoint = api_endpoint.rstrip("/")
        self._token = None
        self._token_expires_at = 0.0

    def _sign(self, method: str, path: str, body: str = "", access_token: str = "") -> tuple[str, str]:
        t = str(int(time.time() * 1000))
        content_sha256 = hashlib.sha256(body.encode()).hexdigest()
        string_to_sign = f"{method}\n{content_sha256}\n\n{path}"
        sign_str = self.access_id + access_token + t + string_to_sign
        sign = hmac.new(
            self.access_secret.encode(), sign_str.encode(), hashlib.sha256
        ).hexdigest().upper()
        return sign, t

    def _get_token(self) -> str:
        if self._token and time.time() < self._token_expires_at:
            return self._token

        path = "/v1.0/token?grant_type=1"
        sign, t = self._sign("GET", path)
        headers = {
            "client_id": self.access_id,
            "sign": sign,
            "t": t,
            "sign_method": "HMAC-SHA256",
        }
        with httpx.Client(timeout=10) as client:
            resp = client.get(f"{self.api_endpoint}{path}", headers=headers)
        data = resp.json()
        if not data.get("success"):
            raise RuntimeError(f"Tuya token request failed: {data}")

        result = data["result"]
        self._token = result["access_token"]
        self._token_expires_at = time.time() + result["expire_time"] - 60
        return self._token

    def send_commands(self, device_id: str, commands: list[dict]) -> bool:
        token = self._get_token()
        body = json.dumps({"commands": commands})
        path = f"/v1.0/iot-03/devices/{device_id}/commands"
        sign, t = self._sign("POST", path, body, access_token=token)
        headers = {
            "client_id": self.access_id,
            "access_token": token,
            "sign": sign,
            "t": t,
            "sign_method": "HMAC-SHA256",
            "Content-Type": "application/json",
        }
        with httpx.Client(timeout=10) as client:
            resp = client.post(f"{self.api_endpoint}{path}", content=body, headers=headers)
        return resp.json().get("success", False)
