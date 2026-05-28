# -*- coding: utf-8 -*-
r"""
Script de inferencia para CASO D - CLASSROOM / Occupancy Detection.

Este script carga desde el DIRECTORIO ACTUAL:
- Un modelo entrenado .joblib con prefijo best_*.joblib
- simulated_cases.json
- Opcionalmente: models_metadata.json o best_model_metadata.json

Ejemplo en Windows / PowerShell:

cd .\src\In-gauge-and-en-gage\inference

& "C:/Program Files/Python31210/python.exe" "./infer_classroom_occupancy_json.py"

Estructura esperada:

src/In-gauge-and-en-gage/inference/
│
├── infer_classroom_occupancy_json.py
├── best_sensorica_ambiental_<Modelo>.joblib
├── simulated_cases.json
└── best_model_metadata.json              # opcional si el .joblib ya trae metadata

Variables esperadas en simulated_cases.json:
- IndoorTemperature
- IndoorHumidity
- IndoorCO2
- IndoorNoise
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

# =============================================================================
# Configuración de rutas
# =============================================================================

BASE_DIR = Path.cwd()
CASES_FILENAME = "simulated_cases.json"
METADATA_CANDIDATES = [
    "models_metadata.json",
    "best_model_metadata.json",
]

CASES_PATH = BASE_DIR / CASES_FILENAME
OUTPUT_FILENAME = "inference_results_classroom.csv"
OUTPUT_PATH = BASE_DIR / OUTPUT_FILENAME

DEFAULT_FEATURES = [
    "IndoorTemperature",
    "IndoorHumidity",
    "IndoorCO2",
    "IndoorNoise",
]
DEFAULT_TARGET = "Occupied"


# =============================================================================
# Funciones auxiliares
# =============================================================================


def find_best_model_path(metadata: dict[str, Any] | None = None) -> Path:
    """
    Busca el modelo a cargar.

    Prioridad:
    1. metadata['model_filename'] si existe.
    2. metadata['models'][best_model_name]['path'] si existe.
    3. Primer archivo local con patrón best_*.joblib.
    """
    if metadata:
        model_filename = metadata.get("model_filename")
        if model_filename:
            candidate = BASE_DIR / model_filename
            if candidate.exists():
                return candidate

        best_model_name = metadata.get("best_model_name")
        models = metadata.get("models")
        if best_model_name and isinstance(models, dict):
            best_info = models.get(best_model_name, {})
            model_path_value = best_info.get("path")
            if model_path_value:
                candidate = Path(model_path_value)
                if not candidate.is_absolute():
                    candidate = BASE_DIR / candidate
                if candidate.exists():
                    return candidate

    local_best_models = sorted(BASE_DIR.glob("best_*.joblib"))
    if local_best_models:
        return local_best_models[0]

    raise FileNotFoundError(
        "No se encontró ningún modelo best_*.joblib en el directorio actual.\n\n"
        f"Directorio actual: {BASE_DIR}\n\n"
        "Solución:\n"
        "Copiá en esta carpeta el modelo generado por el notebook, por ejemplo:\n"
        "best_sensorica_ambiental_LogisticRegression.joblib"
    )


def load_metadata() -> dict[str, Any]:
    """Carga metadata si está disponible; si no existe, devuelve metadata mínima."""
    for filename in METADATA_CANDIDATES:
        path = BASE_DIR / filename
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)

    return {
        "case": "CASO D - CLASSROOM",
        "features": DEFAULT_FEATURES,
        "target": DEFAULT_TARGET,
        "selection_metric": "unknown",
        "final_evaluation": "unknown",
        "notes": {
            "metadata_source": (
                "No se encontró JSON de metadata. " "Se usan features por defecto."
            )
        },
    }


def load_model_artifact(model_path: Path) -> tuple[Any, dict[str, Any]]:
    """
    Carga el .joblib.

    Soporta dos formatos:
    1. Pipeline/modelo directo de scikit-learn.
    2. Artefacto tipo dict con claves: model, features, target, metrics, etc.
    """
    loaded = joblib.load(model_path)

    if isinstance(loaded, dict) and "model" in loaded:
        model = loaded["model"]
        artifact_metadata = {
            key: value for key, value in loaded.items() if key != "model"
        }
        return model, artifact_metadata

    return loaded, {}


def load_model_and_metadata() -> tuple[Any, dict[str, Any], Path]:
    """Carga metadata y modelo desde el directorio actual."""
    print("=" * 80)
    print("Carga de modelo")
    print("=" * 80)
    print(f"Directorio actual de ejecución: {BASE_DIR}")
    print(f"Buscando casos simulados en: {CASES_PATH}")
    print()

    metadata = load_metadata()
    model_path = find_best_model_path(metadata)
    model, artifact_metadata = load_model_artifact(model_path)

    # La metadata embebida en el .joblib tiene prioridad para features/target/metrics.
    merged_metadata = {
        **metadata,
        **artifact_metadata,
        "model_path": str(model_path),
    }

    print(f"Modelo cargado desde: {model_path}")
    print()

    return model, merged_metadata, model_path


def load_cases_from_json() -> pd.DataFrame:
    """
    Carga los casos de inferencia desde simulated_cases.json.

    Formato esperado:

    [
      {
        "case_id": "caso_1",
        "IndoorTemperature": 21.4,
        "IndoorHumidity": 42.0,
        "IndoorCO2": 430.0,
        "IndoorNoise": 34.0
      }
    ]
    """
    if not CASES_PATH.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo de casos simulados en:\n{CASES_PATH}\n\n"
            f"Solución: copiá el archivo '{CASES_FILENAME}' en el directorio actual."
        )

    with open(CASES_PATH, "r", encoding="utf-8") as f:
        cases = json.load(f)

    if not isinstance(cases, list):
        raise ValueError(
            "El archivo JSON debe contener una lista de casos. "
            "Ejemplo: [{...}, {...}, {...}]"
        )

    if len(cases) == 0:
        raise ValueError("El archivo JSON no contiene casos para inferir.")

    cases_df = pd.DataFrame(cases)

    if "case_id" not in cases_df.columns:
        cases_df.insert(0, "case_id", [f"caso_{i + 1}" for i in range(len(cases_df))])

    return cases_df


def validate_input(df: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    """Valida columnas y devuelve features_df con las features en el orden correcto."""
    missing_features = [col for col in features if col not in df.columns]

    if missing_features:
        raise ValueError(
            "Faltan columnas requeridas para inferencia:\n"
            f"{missing_features}\n\n"
            "Columnas recibidas:\n"
            f"{df.columns.tolist()}"
        )

    features_df = df[features].copy()

    for col in features:
        features_df[col] = pd.to_numeric(features_df[col], errors="coerce")

    if features_df.isna().any().any():
        missing_by_column = features_df.isna().sum()
        missing_by_column = missing_by_column[missing_by_column > 0]

        raise ValueError(
            "Hay valores nulos o no numéricos en las variables de entrada:\n"
            f"{missing_by_column}"
        )

    return features_df


def predict_cases(
    model: Any, metadata: dict[str, Any], cases_df: pd.DataFrame
) -> pd.DataFrame:
    """Realiza inferencia usando el modelo cargado."""
    features = metadata.get("features") or DEFAULT_FEATURES
    target = metadata.get("target", DEFAULT_TARGET)

    if not features:
        raise ValueError(
            "La metadata no contiene la clave 'features'. "
            "No se puede saber qué columnas necesita el modelo."
        )

    print("=" * 80)
    print("Metadata del modelo")
    print("=" * 80)
    print(f"Caso: {metadata.get('case', 'CASO D - CLASSROOM')}")
    model_name = metadata.get("best_model_name") or metadata.get(
        "model_name", "desconocido"
    )
    print(f"Modelo: {model_name}")
    print(f"Target: {target}")
    print(f"Features usadas: {features}")
    print(f"Métrica de selección: {metadata.get('selection_metric', 'desconocida')}")
    print(f"Evaluación final: {metadata.get('final_evaluation', 'desconocida')}")

    best_params = metadata.get("best_params") or metadata.get("params")
    if best_params:
        print(f"Hiperparámetros: {best_params}")

    metrics = metadata.get("metrics")
    if metrics:
        print(f"Métricas asociadas al modelo: {metrics}")

    print()

    features_df = validate_input(cases_df, features)

    predictions = model.predict(features_df)

    results_df = cases_df.copy()
    results_df[f"{target}_pred"] = predictions
    results_df["pred_label"] = (
        results_df[f"{target}_pred"]
        .map(
            {
                0: "No ocupado",
                1: "Ocupado",
            }
        )
        .fillna(results_df[f"{target}_pred"].astype(str))
    )

    if hasattr(model, "predict_proba"):
        probabilities = model.predict_proba(features_df)

        if probabilities.shape[1] == 2:
            results_df["prob_no_ocupado"] = probabilities[:, 0]
            results_df["prob_ocupado"] = probabilities[:, 1]
        else:
            for idx in range(probabilities.shape[1]):
                results_df[f"prob_clase_{idx}"] = probabilities[:, idx]

    return results_df


def print_results(results_df: pd.DataFrame):
    """Imprime los resultados de forma legible."""
    print("=" * 80)
    print("Resultados de inferencia")
    print("=" * 80)

    base_columns = [
        "case_id",
        "IndoorTemperature",
        "IndoorHumidity",
        "IndoorCO2",
        "IndoorNoise",
    ]

    base_columns = [col for col in base_columns if col in results_df.columns]

    pred_columns = [
        col
        for col in results_df.columns
        if col.endswith("_pred")
        or col
        in [
            "pred_label",
            "prob_no_ocupado",
            "prob_ocupado",
        ]
    ]

    columns_to_show = base_columns + pred_columns

    print(results_df[columns_to_show].to_string(index=False))

    print()
    print("=" * 80)
    print("Interpretación")
    print("=" * 80)

    for _, row in results_df.iterrows():
        case_id = row["case_id"]
        label = row["pred_label"]

        if "prob_ocupado" in results_df.columns:
            prob_ocupado = row["prob_ocupado"]
            print(f"{case_id}: {label} | Probabilidad de ocupado: {prob_ocupado:.4f}")
        else:
            print(f"{case_id}: {label}")


def save_results_to_csv(results_df: pd.DataFrame):
    """Guarda los resultados en un CSV en el directorio actual."""
    results_df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")

    print()
    print("=" * 80)
    print("Salida")
    print("=" * 80)
    print(f"Resultados guardados en: {OUTPUT_PATH}")


def run_inference():
    """Ejecuta el flujo completo de inferencia."""
    model, metadata, _ = load_model_and_metadata()
    cases_df = load_cases_from_json()

    print("=" * 80)
    print("Casos de entrada cargados desde JSON")
    print("=" * 80)
    print(cases_df.to_string(index=False))
    print()

    results_df = predict_cases(model, metadata, cases_df)

    print_results(results_df)
    save_results_to_csv(results_df)


if __name__ == "__main__":
    try:
        run_inference()
    except Exception as exc:
        print()
        print("=" * 80)
        print("ERROR")
        print("=" * 80)
        print(exc)
        print()
        sys.exit(1)
