# -*- coding: utf-8 -*-
r"""API sencilla para predicción de ocupación de aulas.

Caso D - In-Gauge and En-Gage classrooms.

Endpoints principales:
- GET  /health
- GET  /metadata
- POST /predict
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "models"
METADATA_PATH = BASE_DIR / "model_metadata.json"


def load_metadata() -> dict[str, Any]:
    """Carga la metadata del modelo desde el archivo JSON local."""
    with open(METADATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


metadata = load_metadata()
FEATURES = metadata["features"]
TARGET = metadata.get("target", "Occupied")
MODEL_PATH = MODEL_DIR / metadata["model_filename"]


def load_model() -> Any:
    """Carga el artefacto del modelo entrenado indicado en la metadata."""
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"No se encontró el modelo en {MODEL_PATH}")
    artifact = joblib.load(MODEL_PATH)
    if isinstance(artifact, dict) and "model" in artifact:
        return artifact["model"]
    return artifact


model = load_model()


class OccupancyInput(BaseModel):
    """Esquema del payload de entrada para predecir ocupación."""

    IndoorTemperature: float = Field(
        ..., description="Temperatura interior del aula en °C"
    )
    IndoorHumidity: float = Field(..., description="Humedad relativa interior en %")
    IndoorCO2: float = Field(..., description="CO2 interior en ppm")
    IndoorNoise: float = Field(..., description="Ruido interior en dB")


class PredictionResponse(BaseModel):
    """Esquema de respuesta devuelto por el endpoint de predicción."""

    prediction: int
    prediction_label: str
    probability_occupied: float | None = None
    probability_not_occupied: float | None = None
    features_used: dict[str, float]
    model_name: str
    interpretation: str


app = FastAPI(
    title="Caso D - API de predicción de ocupación de aulas",
    description=(
        "API sencilla para predecir si un aula está ocupada usando "
        "sensores ambientales."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    """Devuelve el estado del servicio y el nombre del modelo cargado."""
    return {"status": "ok", "model": metadata.get("model_name", "unknown")}


@app.get("/metadata")
def get_metadata() -> dict[str, Any]:
    """Devuelve la metadata usada por el modelo en ejecución."""
    return metadata


@app.post("/predict", response_model=PredictionResponse)
def predict(payload: OccupancyInput) -> PredictionResponse:
    """Predice la ocupación del aula a partir de las lecturas de sensores."""
    data = payload.model_dump()

    try:
        features_df = pd.DataFrame(
            [{feature: float(data[feature]) for feature in FEATURES}]
        )
        pred = int(model.predict(features_df)[0])

        prob_occupied = None
        prob_not_occupied = None
        if hasattr(model, "predict_proba"):
            probabilities = model.predict_proba(features_df)[0]
            if len(probabilities) >= 2:
                prob_not_occupied = float(probabilities[0])
                prob_occupied = float(probabilities[1])

        label = "Ocupado" if pred == 1 else "No ocupado"
        if prob_occupied is not None:
            interpretation = (
                f"El modelo estima que el aula está {label.lower()} "
                f"con probabilidad de ocupación {prob_occupied:.1%}."
            )
        else:
            interpretation = f"El modelo estima que el aula está {label.lower()}."

        return PredictionResponse(
            prediction=pred,
            prediction_label=label,
            probability_occupied=prob_occupied,
            probability_not_occupied=prob_not_occupied,
            features_used={k: float(v) for k, v in data.items()},
            model_name=metadata.get("model_name", "unknown"),
            interpretation=interpretation,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
