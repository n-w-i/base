from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from whoop_core.client import sync_all, get_profile, get_body_measurement
from whoop_core.db import init_db, query_recent

app = FastAPI(title="Base — whoop-core", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/profile")
def profile():
    return get_profile()


@app.get("/body")
def body():
    return get_body_measurement()


@app.post("/sync")
def sync(days: int = Query(default=30, le=365)):
    result = sync_all(days)
    return {"synced": result}


@app.get("/cycles")
def cycles(days: int = Query(default=30, le=365), limit: int = Query(default=50, le=200)):
    return query_recent("cycles", days, limit)


@app.get("/recoveries")
def recoveries(days: int = Query(default=30, le=365), limit: int = Query(default=50, le=200)):
    return query_recent("recoveries", days, limit)


@app.get("/sleeps")
def sleeps(days: int = Query(default=30, le=365), limit: int = Query(default=50, le=200)):
    return query_recent("sleeps", days, limit)


@app.get("/workouts")
def workouts(days: int = Query(default=30, le=365), limit: int = Query(default=50, le=200)):
    return query_recent("workouts", days, limit)


@app.get("/today")
def today():
    """Snapshot of today's data — the main endpoint other modules will poll."""
    cycles_data = query_recent("cycles", days=1, limit=1)
    recovery_data = query_recent("recoveries", days=1, limit=1)
    sleep_data = query_recent("sleeps", days=1, limit=1)
    workouts_data = query_recent("workouts", days=1, limit=5)

    return {
        "cycle": cycles_data[0] if cycles_data else None,
        "recovery": recovery_data[0] if recovery_data else None,
        "sleep": sleep_data[0] if sleep_data else None,
        "workouts": workouts_data,
    }
