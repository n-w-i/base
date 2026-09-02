from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from recovery_forecast.predictor import build_prediction

app = FastAPI(title="Base — recovery-forecast", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/predict")
def predict(days: int = Query(default=3, le=7)):
    return build_prediction(days)
