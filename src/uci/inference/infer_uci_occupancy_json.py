# -*- coding: utf-8 -*-
"""
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

from pathlib import Path
import json
import sys

import joblib
import pandas as pd


# =============================================================================
# Configuración de rutas
# =============================================================================

# Directorio actual desde donde se ejecuta el comando.
# En Windows / PowerShell depende de la carpeta donde estés parado con cd.
BASE_DIR = Path.cwd()

MODEL_FILENAME = "best_model_LogisticRegression.joblib"
METADATA_FILENAME = "best_model_metadata.json"
CASES_FILENAME = "simulated_cases.json"

MODEL_PATH = BASE_DIR / MODEL_FILENAME
METADATA_PATH = BASE_DIR / METADATA_FILENAME
CASES_PATH = BASE_DIR / CASES_FILENAME


# =============================================================================
# Funciones auxiliares
# =============================================================================

def load_model_and_metadata():
    """
    Carga el modelo y la metadata desde el directorio actual de ejecución.
    """

    print("=" * 80)
    print("Carga de modelo")
    print("=" * 80)
    print(f"Directorio actual de ejecución: {BASE_DIR}")
    print(f"Buscando modelo en: {MODEL_PATH}")
    print(f"Buscando metadata en: {METADATA_PATH}")
    print(f"Buscando casos simulados en: {CASES_PATH}")
    print()

    if not METADATA_PATH.exists():
        raise FileNotFoundError(
            f"No se encontró la metadata en:\n{METADATA_PATH}\n\n"
            f"Solución:\n"
            f"Copiá el archivo '{METADATA_FILENAME}' en el directorio actual:\n"
            f"{BASE_DIR}"
        )

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"No se encontró el modelo en:\n{MODEL_PATH}\n\n"
            f"Solución:\n"
            f"Copiá el archivo '{MODEL_FILENAME}' en el directorio actual:\n"
            f"{BASE_DIR}"
        )

    with open(METADATA_PATH, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    model = joblib.load(MODEL_PATH)

    return model, metadata


def load_cases_from_json() -> pd.DataFrame:
    """
    Carga los casos de inferencia desde simulated_cases.json.

    Formato esperado del JSON:

    [
      {
        "case_id": "caso_1",
        "Temperature": 20.3,
        "Humidity": 27.2,
        "Light": 0.0,
        "CO2": 455.0,
        "HumidityRatio": 0.00475
      }
    ]
    """

    if not CASES_PATH.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo de casos simulados en:\n{CASES_PATH}\n\n"
            f"Solución:\n"
            f"Copiá el archivo '{CASES_FILENAME}' en el directorio actual:\n"
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
    Valida que el DataFrame de entrada tenga las columnas esperadas
    y devuelve X con las columnas en el orden correcto.
    """

    missing_features = [col for col in features if col not in df.columns]

    if missing_features:
        raise ValueError(
            "Faltan columnas requeridas para inferencia:\n"
            f"{missing_features}\n\n"
            "Columnas recibidas:\n"
            f"{df.columns.tolist()}"
        )

    X = df[features].copy()

    for col in features:
        X[col] = pd.to_numeric(X[col], errors="coerce")

    if X.isna().any().any():
        missing_by_column = X.isna().sum()
        missing_by_column = missing_by_column[missing_by_column > 0]

        raise ValueError(
            "Hay valores nulos o no numéricos en las variables de entrada:\n"
            f"{missing_by_column}"
        )

    return X


def predict_cases(model, metadata: dict, cases_df: pd.DataFrame) -> pd.DataFrame:
    """
    Realiza inferencia usando el modelo cargado.
    """

    features = metadata.get("features")
    target = metadata.get("target", "Occupancy")

    if not features:
        raise ValueError(
            "La metadata no contiene la clave 'features'. "
            "No se puede saber qué columnas necesita el modelo."
        )

    print("=" * 80)
    print("Metadata del modelo")
    print("=" * 80)
    print(f"Modelo: {metadata.get('best_model_name', 'desconocido')}")
    print(f"Target: {target}")
    print(f"Features usadas: {features}")
    print()

    X = validate_input(cases_df, features)

    predictions = model.predict(X)

    results_df = cases_df.copy()
    results_df[f"{target}_pred"] = predictions
    results_df["pred_label"] = results_df[f"{target}_pred"].map(
        {
            0: "No ocupado",
            1: "Ocupado",
        }
    )

    if hasattr(model, "predict_proba"):
        probabilities = model.predict_proba(X)

        if probabilities.shape[1] == 2:
            results_df["prob_no_ocupado"] = probabilities[:, 0]
            results_df["prob_ocupado"] = probabilities[:, 1]
        else:
            for idx in range(probabilities.shape[1]):
                results_df[f"prob_clase_{idx}"] = probabilities[:, idx]

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
        "Temperature",
        "Humidity",
        "Light",
        "CO2",
        "HumidityRatio",
    ]

    base_columns = [col for col in base_columns if col in results_df.columns]

    pred_columns = [
        col for col in results_df.columns
        if col.endswith("_pred") or col in ["pred_label", "prob_no_ocupado", "prob_ocupado"]
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
    """
    Guarda los resultados en un CSV en el directorio actual.
    """

    output_path = BASE_DIR / "inference_results.csv"
    results_df.to_csv(output_path, index=False, encoding="utf-8-sig")

    print()
    print("=" * 80)
    print("Salida")
    print("=" * 80)
    print(f"Resultados guardados en: {output_path}")


def run_inference():
    """
    Flujo principal:
    1. Carga modelo y metadata.
    2. Carga casos desde JSON.
    3. Valida columnas.
    4. Ejecuta inferencia.
    5. Muestra resultados.
    6. Guarda resultados en CSV.
    """

    model, metadata = load_model_and_metadata()

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
