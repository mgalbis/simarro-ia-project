# -*- coding: utf-8 -*-
r"""
Script de inferencia para el modelo UCI Occupancy Detection.

Este script carga desde el DIRECTORIO ACTUAL:
- best_model_LogisticRegression.joblib
- best_model_metadata.json
- simulated_cases.json

Ejemplo en Windows / PowerShell:

cd .\src\uci\inference

& "C:/Program Files/Python31210/python.exe" "./infer_uci_occupancy_json.py"

Estructura esperada:

src/In-gauge-and-en-gage/inference/
│
├── infer_uci_occupancy_json.py
├── best_model_LogisticRegression.joblib
├── best_model_metadata.json
└── simulated_cases.json
"""

import json
from pathlib import Path

import joblib
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "best_model.joblib"
METADATA_PATH = BASE_DIR / "best_model_metadata.json"
CASES_PATH = BASE_DIR / "simulated_cases.json"


def load_json(path):
    """Carga un archivo JSON."""
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_model_and_metadata():
    """Carga el modelo, la metadata y los casos simulados."""
    print("=" * 80)
    print("Carga de modelo")
    print("=" * 80)
    print(f"Directorio actual de ejecución: {BASE_DIR}")
    print(f"Buscando modelo en: {MODEL_PATH}")
    print(f"Buscando metadata en: {METADATA_PATH}")
    print(f"Buscando casos simulados en: {CASES_PATH}")
    print()

    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"No se encontró el modelo: {MODEL_PATH}")

    if not METADATA_PATH.exists():
        raise FileNotFoundError(f"No se encontró la metadata: {METADATA_PATH}")

    if not CASES_PATH.exists():
        raise FileNotFoundError(f"No se encontró el JSON de casos: {CASES_PATH}")

    model = joblib.load(MODEL_PATH)
    metadata = load_json(METADATA_PATH)
    cases = load_json(CASES_PATH)

    return model, metadata, cases


def get_features(metadata):
    """Obtiene las variables del modelo desde la metadata."""
    features = metadata.get("features")

    if not features:
        raise ValueError(
            "No se encontró la lista de variables/features en la metadata."
        )

    return features


def cases_to_dataframe(cases):
    """Convierte los casos simulados de JSON a DataFrame."""
    if isinstance(cases, dict):
        if "cases" in cases:
            records = cases["cases"]
        elif "simulated_cases" in cases:
            records = cases["simulated_cases"]
        else:
            records = [cases]
    elif isinstance(cases, list):
        records = cases
    else:
        raise ValueError("El fichero simulated_cases.json no tiene formato válido.")

    if not records:
        raise ValueError("No hay casos simulados para inferir.")

    return pd.DataFrame(records)


def validate_input(cases_df, features):
    """Valida que estén presentes todas las variables esperadas."""
    missing_features = [
        feature for feature in features if feature not in cases_df.columns
    ]

    if missing_features:
        raise ValueError(
            "Faltan variables requeridas por el modelo: "
            f"{', '.join(missing_features)}"
        )

    features_df = cases_df[features].copy()

    for feature in features:
        features_df[feature] = pd.to_numeric(features_df[feature], errors="coerce")

    if features_df.isna().any().any():
        invalid_columns = features_df.columns[features_df.isna().any()].tolist()
        raise ValueError(
            "Hay valores nulos o no numéricos en las variables: "
            f"{', '.join(invalid_columns)}"
        )

    return features_df


def predict_cases(model, cases_df, features):
    """Ejecuta predicciones para los casos proporcionados."""
    features_df = validate_input(cases_df, features)

    predictions = model.predict(features_df)

    if hasattr(model, "predict_proba"):
        probabilities = model.predict_proba(features_df)[:, 1]
    else:
        probabilities = [None] * len(predictions)

    results_df = cases_df.copy()
    results_df["predicted_occupied"] = predictions
    results_df["predicted_label"] = results_df["predicted_occupied"].map(
        {0: "No ocupada", 1: "Ocupada"}
    )
    results_df["occupancy_probability"] = probabilities

    return results_df


def print_metadata(metadata, features):
    """Imprime un resumen breve de la metadata."""
    print("=" * 80)
    print("Metadata del modelo")
    print("=" * 80)
    print(f"Modelo: {metadata.get('model_name', metadata.get('model', 'N/D'))}")
    print(f"Dataset: {metadata.get('dataset', 'UCI Occupancy Detection')}")
    print(f"Variables usadas: {features}")

    metrics = metadata.get("metrics", {})
    if metrics:
        print("Métricas:")
        for metric_name, metric_value in metrics.items():
            print(f"  - {metric_name}: {metric_value}")

    print()


def print_results(results_df):
    """Imprime los resultados de inferencia."""
    print("=" * 80)
    print("Resultados de inferencia")
    print("=" * 80)

    display_columns = [
        column for column in results_df.columns if column not in {"predicted_occupied"}
    ]

    print(results_df[display_columns].to_string(index=False))
    print()


def main():
    """Ejecuta la inferencia de ocupación para UCI."""
    model, metadata, cases = load_model_and_metadata()
    features = get_features(metadata)
    cases_df = cases_to_dataframe(cases)

    print_metadata(metadata, features)

    results_df = predict_cases(model, cases_df, features)

    print_results(results_df)


if __name__ == "__main__":
    main()
