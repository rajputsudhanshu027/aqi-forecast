from contextlib import asynccontextmanager
from pathlib import Path

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException

from aqi.serve.schemas import PredictionRequest, PredictionResponse

MODEL_PATH = Path("artifacts/model.joblib")

model_state: dict[str, object] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    if MODEL_PATH.exists():
        model_state["model"] = joblib.load(MODEL_PATH)

    yield

    model_state.clear()


app = FastAPI(
    title="AQI Forecast API",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
def health() -> dict[str, object]:
    if "model" not in model_state:
        raise HTTPException(
            status_code=503,
            detail="Model is not loaded.",
        )

    return {
        "status": "healthy",
        "model_loaded": True,
    }


@app.post(
    "/predict",
    response_model=PredictionResponse,
)
def predict(request: PredictionRequest) -> PredictionResponse:
    if "model" not in model_state:
        raise HTTPException(
            status_code=503,
            detail="Model is not loaded.",
        )

    input_df = pd.DataFrame([request.model_dump()])

    model = model_state["model"]

    prediction = model.predict(input_df)[0]

    return PredictionResponse(
        predicted_pm25=float(prediction),
        model_version="local-v1",
    )


@app.get("/metrics")
def metrics() -> dict[str, str]:
    return {"message": "Metrics instrumentation comes later."}
