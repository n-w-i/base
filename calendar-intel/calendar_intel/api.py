from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from calendar_intel.forecast import build_forecast

app = FastAPI(title="Base — calendar-intel", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/forecast")
def forecast(days: int = Query(default=3, le=14)):
    return build_forecast(days)


@app.get("/today")
def today():
    forecast = build_forecast(1)
    return forecast[0] if forecast else {}
