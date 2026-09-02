from datetime import datetime, timedelta, timezone

import httpx

from whoop_core.auth import get_valid_token
from whoop_core.config import WHOOP_API_BASE
from whoop_core.db import (
    upsert_cycle,
    upsert_recovery,
    upsert_sleep,
    upsert_workout,
    log_sync,
)

PAGE_SIZE = 25


def _headers() -> dict:
    return {"Authorization": f"Bearer {get_valid_token()}"}


def _paginate(path: str, params: dict | None = None) -> list[dict]:
    results = []
    params = dict(params or {})
    params["limit"] = PAGE_SIZE

    with httpx.Client(base_url=WHOOP_API_BASE, headers=_headers(), timeout=30) as client:
        while True:
            resp = client.get(path, params=params)
            resp.raise_for_status()
            body = resp.json()
            results.extend(body.get("records", []))
            next_token = body.get("next_token")
            if not next_token:
                break
            params["nextToken"] = next_token

    return results


def get_profile() -> dict:
    with httpx.Client(base_url=WHOOP_API_BASE, headers=_headers(), timeout=30) as client:
        resp = client.get("/v2/user/profile/basic")
        resp.raise_for_status()
        return resp.json()


def get_body_measurement() -> dict:
    with httpx.Client(base_url=WHOOP_API_BASE, headers=_headers(), timeout=30) as client:
        resp = client.get("/v2/user/measurement/body")
        resp.raise_for_status()
        return resp.json()


def sync_cycles(days: int = 30) -> int:
    print("  Syncing cycles...", flush=True)
    start = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    records = _paginate("/v2/cycle", {"start": start})
    for r in records:
        upsert_cycle(r)
    log_sync("cycles", len(records))
    return len(records)


def sync_recoveries(days: int = 30) -> int:
    print("  Syncing recoveries...", flush=True)
    start = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    records = _paginate("/v2/recovery", {"start": start})
    for r in records:
        upsert_recovery(r)
    log_sync("recoveries", len(records))
    return len(records)


def sync_sleeps(days: int = 30) -> int:
    print("  Syncing sleeps...", flush=True)
    start = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    records = _paginate("/v2/activity/sleep", {"start": start})
    for r in records:
        upsert_sleep(r)
    log_sync("sleeps", len(records))
    return len(records)


def sync_workouts(days: int = 30) -> int:
    print("  Syncing workouts...", flush=True)
    start = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    records = _paginate("/v2/activity/workout", {"start": start})
    for r in records:
        upsert_workout(r)
    log_sync("workouts", len(records))
    return len(records)


def sync_all(days: int = 30) -> dict:
    print(f"Syncing last {days} days...", flush=True)
    return {
        "cycles": sync_cycles(days),
        "recoveries": sync_recoveries(days),
        "sleeps": sync_sleeps(days),
        "workouts": sync_workouts(days),
    }
