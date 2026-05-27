# -*- coding: utf-8 -*-
"""
Script de inferencia para CASO D - CLASSROOM / In-Gauge & En-Gage.

Este script realiza inferencia usando el mejor modelo generado por el notebook
sensorico del caso CLASSROOM. El modelo espera variables procedentes de
sensorica ambiental directa, no variables de calendario, horario ni contexto docente.

El script carga desde el DIRECTORIO ACTUAL:
- un modelo .joblib con prefijo best_ dentro del directorio actual, o el fichero
  indicado en MODEL_FILENAME
- simulated_cases_classroom.json

Ejemplo en Windows / PowerShell:

cd "C:/cursoia/ProyectoFinal/CASOD-Calidad del Aire Ocupacion/CLASSROOM/modelo-inferencia"

& "C:/Program Files/Python31210/python.exe" "./infer_ingauge_classroom_occupancy_json.py"

Estructura esperada:

modelo-inferencia/
|
├── infer_ingauge_classroom_occupancy_json.py
├── best_sensorica_ambiental_LogisticRegression.joblib
└── simulated_cases_classroom.json

Formato esperado de simulated_cases_classroom.json:

[
  {
    "case_id": "aula_vacia_baja_senal",
    "IndoorTemperature": 21.4,
    "IndoorHumidity": 42.0,
    "IndoorCO2": 430.0,
    "IndoorNoise": 34.0
  },
  {
    "case_id": "aula_ocupada_senal_alta",
    "IndoorTemperature": 23.2,
    "IndoorHumidity": 48.5,
    "IndoorCO2": 980.0,
    "IndoorNoise": 58.0
  }
]
"""

from pathlib import Path
import json
import sys
from typing import Any

import joblib
import pandas as pd


# =============================================================================
# Configuracion de rutas
# =============================================================================

BASE_DIR = Path.cwd()

# Si queres fijar un modelo concreto, indicarlo aca.
# Si queda en None, el script busca automaticamente un *.joblib con prefijo best_.
MODEL_FILENAME = None

CASES_FILENAME = "simulated_cases_classroom.json"

DEFAULT_SENSOR_FEATURES = [
    "IndoorTemperature",
    "IndoorHumidity",
    "IndoorCO2",
    "IndoorNoise",
]

TARGET_DEFAULT = "Occupied"

CASES_PATH = BASE_DIR / CASES_FILENAME


# =============================================================================
# Funciones auxiliares
# =============================================================================

def find_best_model_path() -> Path:
    """
    Localiza el modelo a utilizar.

    Prioridad:
    1. MODEL_FILENAME, si se especifico.
    2. Fichero .joblib con prefijo best_ en el directorio actual.
    3. Error explicativo si no encuentra ninguno.
    """

    if MODEL_FILENAME:
        model_path = BASE_DIR / MODEL_FILENAME
        if not model_path.exists():
            raise FileNotFoundError(
                f"No se encontro el modelo indicado en MODEL_FILENAME:\n{model_path}"
            )
        return model_path

    candidate_models = sorted(BASE_DIR.glob("best_*.joblib"))

    if len(candidate_models) == 0:
        raise FileNotFoundError(
            "No se encontro ningun modelo con prefijo 'best_' en el directorio actual.\n\n"
            "Solucion:\n"
            "Copiar en esta carpeta el modelo generado por el notebook, por ejemplo:\n"
            "best_sensorica_ambiental_LogisticRegression.joblib\n\n"
            f"Directorio actual:\n{BASE_DIR}"
        )

    if len(candidate_models) > 1:
        print("Advertencia: se encontro mas de un modelo con prefijo best_.")
        print("Se usara el primero ordenado alfabeticamente:")
        for path in candidate_models:
            print(f"- {path.name}")
        print()

    return candidate_models[0]


def load_model_artifact() -> tuple[Any, dict, Path]:
    """
    Carga el artefacto .joblib.

    El notebook CLASSROOM guarda un diccionario con esta estructura aproximada:
    {
      "model": modelo_entrenado,
      "model_name": "LogisticRegression",
      "feature_set": "sensorica_ambiental",
      "features": [...],
      "target": "Occupied",
      "metrics": {...},
      "is_best": True,
      "excluded_context_features": [...],
      "justification": "..."
    }

    Para mayor robustez, tambien soporta el caso en el que el .joblib sea
    directamente un estimador sklearn.
    """

    model_path = find_best_model_path()

    print("=" * 80)
    print("Carga de modelo")
    print("=" * 80)
    print(f"Directorio actual de ejecucion: {BASE_DIR}")
    print(f"Modelo seleccionado: {model_path}")
    print(f"Casos simulados: {CASES_PATH}")
    print()

    artifact = joblib.load(model_path)

    if isinstance(artifact, dict) and "model" in artifact:
        model = artifact["model"]
        metadata = artifact.copy()
        metadata.pop("model", None)
    else:
        model = artifact
        metadata = {
            "model_name": model_path.stem,
            "feature_set": "sensorica_ambiental",
            "features": DEFAULT_SENSOR_FEATURES,
            "target": TARGET_DEFAULT,
            "warning": (
                "El .joblib cargado no contenia metadata. "
                "Se usaron las features ambientales por defecto."
            ),
        }

    return model, metadata, model_path


def load_cases_from_json() -> pd.DataFrame:
    """
    Carga los casos de inferencia desde simulated_cases_classroom.json.
    """

    if not CASES_PATH.exists():
        raise FileNotFoundError(
            f"No se encontro el archivo de casos simulados en:\n{CASES_PATH}\n\n"
            f"Solucion:\n"
            f"Copiar el archivo '{CASES_FILENAME}' en el directorio actual:\n"
            f"{BASE_DIR}"
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
    """
    Valida que el DataFrame tenga las columnas esperadas y devuelve X en el
    orden exacto usado durante entrenamiento.
    """

    missing_features = [col for col in features if col not in df.columns]

    if missing_features:
        raise ValueError(
            "Faltan columnas requeridas para inferencia:\n"
            f"{missing_features}\n\n"
            "Columnas recibidas:\n"
            f"{df.columns.tolist()}\n\n"
            "Para este caso CLASSROOM, el enfoque de inferencia espera solo "
            "variables de sensorica ambiental directa."
        )

    X = df[features].copy()

    for col in features:
        X[col] = pd.to_numeric(X[col], errors="coerce")

    if X.isna().any().any():
        missing_by_column = X.isna().sum()
        missing_by_column = missing_by_column[missing_by_column > 0]

        raise ValueError(
            "Hay valores nulos o no numericos en las variables de entrada:\n"
            f"{missing_by_column}"
        )

    return X


def predict_cases(model: Any, metadata: dict, cases_df: pd.DataFrame) -> pd.DataFrame:
    """
    Realiza inferencia usando el modelo cargado.
    """

    features = metadata.get("features") or DEFAULT_SENSOR_FEATURES
    target = metadata.get("target", TARGET_DEFAULT)
    model_name = metadata.get("model_name", "desconocido")
    feature_set = metadata.get("feature_set", "sensorica_ambiental")

    print("=" * 80)
    print("Metadata del modelo")
    print("=" * 80)
    print(f"Modelo: {model_name}")
    print(f"Feature set: {feature_set}")
    print(f"Target: {target}")
    print(f"Features usadas: {features}")

    excluded = metadata.get("excluded_context_features")
    if excluded:
        print(f"Variables de contexto excluidas: {excluded}")

    justification = metadata.get("justification")
    if justification:
        print()
        print("Justificacion del enfoque:")
        print(justification)

    if metadata.get("warning"):
        print()
        print("Advertencia:")
        print(metadata["warning"])

    print()

    X = validate_input(cases_df, features)

    predictions = model.predict(X)

    results_df = cases_df.copy()
    pred_col = f"{target}_pred"
    results_df[pred_col] = predictions
    results_df["pred_label"] = results_df[pred_col].map(
        {
            0: "No ocupado",
            1: "Ocupado",
            False: "No ocupado",
            True: "Ocupado",
        }
    )

    # Si aparece una clase distinta, se conserva como texto generico.
    results_df["pred_label"] = results_df["pred_label"].fillna(
        results_df[pred_col].astype(str)
    )

    if hasattr(model, "predict_proba"):
        probabilities = model.predict_proba(X)
        classes = list(getattr(model, "classes_", range(probabilities.shape[1])))

        for idx, class_value in enumerate(classes):
            if class_value in [0, False]:
                results_df["prob_no_ocupado"] = probabilities[:, idx]
            elif class_value in [1, True]:
                results_df["prob_ocupado"] = probabilities[:, idx]
            else:
                results_df[f"prob_clase_{class_value}"] = probabilities[:, idx]

    return results_df


def print_results(results_df: pd.DataFrame):
    """
    Imprime los resultados de forma legible.
    """

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
        col for col in results_df.columns
        if col.endswith("_pred")
        or col in ["pred_label", "prob_no_ocupado", "prob_ocupado"]
        or col.startswith("prob_clase_")
    ]

    columns_to_show = base_columns + pred_columns
    print(results_df[columns_to_show].to_string(index=False))

    print()
    print("=" * 80)
    print("Interpretacion")
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
    """
    Guarda los resultados en un CSV en el directorio actual.
    """

    output_path = BASE_DIR / "inference_results_classroom.csv"
    results_df.to_csv(output_path, index=False, encoding="utf-8-sig")

    print()
    print("=" * 80)
    print("Salida")
    print("=" * 80)
    print(f"Resultados guardados en: {output_path}")


def run_inference():
    """
    Flujo principal:
    1. Carga el mejor modelo .joblib.
    2. Carga casos desde JSON.
    3. Valida columnas.
    4. Ejecuta inferencia.
    5. Muestra resultados.
    6. Guarda resultados en CSV.
    """

    model, metadata, _ = load_model_artifact()
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
