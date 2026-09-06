from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from hevy_intel.client import sync_all, HevyNotConfigured
from hevy_intel.db import init_db, query_recent_workouts
from hevy_intel.muscle import compute_muscle_fatigue
from hevy_intel.summary import most_recent_workout

app = FastAPI(title="Base — hevy-intel", version="0.1.0")

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


@app.post("/sync")
def sync():
    try:
        return {"synced": sync_all()}
    except HevyNotConfigured as e:
        raise HTTPException(status_code=412, detail=str(e))


@app.get("/workouts")
def workouts(days: int = Query(default=30, le=365), limit: int = Query(default=50, le=200)):
    return query_recent_workouts(days, limit)


@app.get("/today")
def today():
    """Most recent logged workout, if any in the last 2 days — the main
    endpoint other modules poll for "what did they actually train recently"."""
    return most_recent_workout() or {}


@app.get("/muscle-fatigue")
def muscle_fatigue(days: int = Query(default=14, le=60)):
    return compute_muscle_fatigue(days)
