from datetime import datetime, timezone

import httpx

from hevy_intel.config import HEVY_API_BASE, get_settings
from hevy_intel.db import (
    upsert_workout,
    delete_workout,
    upsert_exercise_template,
    log_sync,
    get_cursor,
    set_cursor,
    exercise_template_count,
)

WORKOUTS_PAGE_SIZE = 10  # Hevy's max for /workouts and /workouts/events
TEMPLATES_PAGE_SIZE = 100  # Hevy's max for /exercise_templates
MAX_PAGES = 200  # safety cap on a full (bookmark-less) history sync

WORKOUTS_CURSOR_KEY = "workouts_since"


class HevyNotConfigured(Exception):
    pass


def _headers() -> dict:
    api_key = get_settings().hevy_api_key
    if not api_key:
        raise HevyNotConfigured(
            "HEVY_API_KEY not set. Add it to ~/.base/.env — see hevy-intel/README.md 'Setup'."
        )
    return {"api-key": api_key}


def _client() -> httpx.Client:
    return httpx.Client(base_url=HEVY_API_BASE, headers=_headers(), timeout=30)


def _full_sync_workouts() -> int:
    """No cursor yet — page through the entire history once. Hevy caps
    pageSize at 10 for this endpoint, so this is the expensive path;
    subsequent syncs use /workouts/events instead."""
    count = 0
    with _client() as client:
        page = 1
        while page <= MAX_PAGES:
            resp = client.get("/workouts", params={"page": page, "pageSize": WORKOUTS_PAGE_SIZE})
            resp.raise_for_status()
            body = resp.json()
            for w in body.get("workouts", []):
                upsert_workout(w)
                count += 1
            if page >= body.get("page_count", page):
                break
            page += 1
    return count


def _incremental_sync_workouts(since: str) -> int:
    """Applies updates/deletes reported since the last sync — the pattern
    Hevy's own docs recommend for keeping a local cache current without
    re-fetching everything."""
    count = 0
    with _client() as client:
        page = 1
        while page <= MAX_PAGES:
            resp = client.get(
                "/workouts/events",
                params={"page": page, "pageSize": WORKOUTS_PAGE_SIZE, "since": since},
            )
            resp.raise_for_status()
            body = resp.json()
            events = body.get("events", [])
            for event in events:
                if event.get("type") == "deleted":
                    delete_workout(event["id"])
                else:
                    workout = event.get("workout") or event
                    upsert_workout(workout)
                count += 1
            if page >= body.get("page_count", page):
                break
            page += 1
    return count


def sync_workouts() -> int:
    print("  Syncing workouts...", flush=True)
    cursor = get_cursor(WORKOUTS_CURSOR_KEY)
    next_cursor = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    if cursor:
        count = _incremental_sync_workouts(cursor)
    else:
        count = _full_sync_workouts()
    set_cursor(WORKOUTS_CURSOR_KEY, next_cursor)
    log_sync("workouts", count)
    return count


def sync_exercise_templates(force: bool = False) -> int:
    """Templates carry the muscle-group data and rarely change, so this only
    does the full paginated fetch when the local cache is empty or --force
    is passed — not on every periodic sync."""
    if not force and exercise_template_count() > 0:
        return 0

    print("  Syncing exercise templates...", flush=True)
    count = 0
    with _client() as client:
        page = 1
        while page <= MAX_PAGES:
            resp = client.get(
                "/exercise_templates", params={"page": page, "pageSize": TEMPLATES_PAGE_SIZE}
            )
            resp.raise_for_status()
            body = resp.json()
            for t in body.get("exercise_templates", []):
                upsert_exercise_template(t)
                count += 1
            if page >= body.get("page_count", page):
                break
            page += 1
    log_sync("exercise_templates", count)
    return count


def sync_all() -> dict:
    return {
        "exercise_templates": sync_exercise_templates(),
        "workouts": sync_workouts(),
    }
