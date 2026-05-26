"""Pipeline de reentrenamiento automático.

Se invoca desde ``pipeline_server.py`` cuando hay un merge a main.

Uso (manual para pruebas):
    python pipeline_train.py --caso B
                             --dataset uci-appliances
                             --commit abc123
                             --committer caso_b
"""

import argparse
import logging
import os
import sys
import tempfile
from datetime import datetime
from io import BytesIO

import lakefs_sdk
import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd
from lakefs_sdk.client import LakeFSClient
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [TRAIN] %(levelname)s — %(message)s"
)
log = logging.getLogger(__name__)

# Configuración
MLFLOW_URI = os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5000")
LAKEFS_HOST = os.environ.get("LAKEFS_ENDPOINT", "http://localhost:8001")
LAKEFS_ACCESS = os.environ.get("LAKEFS_ACCESS_KEY_ID")
LAKEFS_SECRET = os.environ.get("LAKEFS_SECRET_ACCESS_KEY")

# Mapa de casos a experimentos y modelos en MLflow
CASOS = {
    "B": {
        "experimento": "CasoB_Prediccion_de_consumo_electrico",
        "modelo_registry": "simarro-caso-b",
        "loader": "default_csv",
        "trainer": "default_regression",
    },
    "C": {
        "experimento": "CasoC_Deteccion_de_anomalias_HVAC",
        "modelo_registry": "simarro-caso-c",
        "loader": "default_csv",
        "trainer": "default_regression",
    },
    "D": {
        "experimento": "CasoD_Calidad_del_aire",
        "modelo_registry": "simarro-caso-d-occupancy",
        "loader": "uci_occupancy",
        "trainer": "occupancy_classification",
    },
    "E": {
        "experimento": "CasoE_Datos_meteorologicos",
        "modelo_registry": "simarro-caso-e",
        "loader": "default_csv",
        "trainer": "default_regression",
    },
}

SENSOR_FEATURES_D = ["Temperature", "Humidity", "Light", "CO2", "HumidityRatio"]
TARGET_D = "Occupancy"

# Funciones auxiliares


def get_lakefs_client() -> LakeFSClient:
    """Crea un cliente de lakeFS con credenciales de entorno."""
    cfg = lakefs_sdk.Configuration(
        host=LAKEFS_HOST,
        username=LAKEFS_ACCESS,
        password=LAKEFS_SECRET,
    )
    return LakeFSClient(configuration=cfg)


def _read_lakefs_csv(
    client: LakeFSClient, dataset: str, commit: str, path: str
) -> pd.DataFrame:
    respuesta = client.objects_api.get_object(
        repository=dataset,
        ref=commit,
        path=path,
    )
    contenido = respuesta.read() if hasattr(respuesta, "read") else respuesta.data
    return pd.read_csv(BytesIO(contenido))


def descargar_datos(dataset: str, commit: str, config_caso: dict):
    """Descarga el dataset desde lakeFS en el commit que disparó el pipeline."""
    log.info(f"Descargando datos de lakeFS. Repo: {dataset}  Commit: {commit[:8]}")

    client = get_lakefs_client()

    if config_caso.get("loader") == "uci_occupancy":
        archivos = [
            "data/datatraining.txt",
            "data/datatest.txt",
            "data/datatest2.txt",
        ]
        datasets = {}
        for ruta in archivos:
            log.info(f"Descargando: {ruta}")
            df = _read_lakefs_csv(client, dataset, commit, ruta)
            if "date" in df.columns:
                df["date"] = pd.to_datetime(df["date"], errors="coerce")
            datasets[os.path.basename(ruta)] = df

        total_filas = sum(len(df) for df in datasets.values())
        log.info(
            "Dataset occupancy cargado: "
            f"{total_filas} filas totales en {len(datasets)} ficheros"
        )
        return datasets

    # Lista los objetos en el commit exacto
    objetos = client.objects_api.list_objects(
        repository=dataset,
        ref=commit,
    ).results

    # Descargar el primer CSV encontrado
    csv_objects = [o for o in objetos if o.path.endswith(".csv")]

    if not csv_objects:
        raise FileNotFoundError(f"No hay CSVs en {dataset}@{commit[:8]}")

    ruta_objeto = csv_objects[0].path
    log.info(f"Descargando: {ruta_objeto}")

    df = _read_lakefs_csv(client, dataset, commit, ruta_objeto)
    log.info(f"Dataset cargado: {len(df)} filas, {len(df.columns)} columnas")
    return df


def validar_datos(df, dataset: str, config_caso: dict) -> bool:
    """Valida la calidad básica de los datos antes de entrenar.

    Devuelve True si los datos son válidos y False si hay problemas.
    """
    log.info("Validando calidad de los datos...")

    if config_caso.get("loader") == "uci_occupancy":
        required_files = {"datatraining.txt", "datatest.txt", "datatest2.txt"}
        if set(df.keys()) != required_files:
            log.error(
                "Archivos esperados ausentes. "
                f"Esperados: {required_files}. Recibidos: {set(df.keys())}"
            )
            return False

        train_df = df["datatraining.txt"]
        test_df = pd.concat(
            [df["datatest.txt"], df["datatest2.txt"]], ignore_index=True
        )

        if len(train_df) < 100 or len(test_df) < 100:
            log.error(
                "Dataset occupancy demasiado pequeño: "
                f"train={len(train_df)}, test={len(test_df)} "
                "(mínimo 100 por split)"
            )
            return False

        columnas_requeridas = set(SENSOR_FEATURES_D + [TARGET_D])
        columnas_train = set(train_df.columns)
        columnas_test = set(test_df.columns)
        if not columnas_requeridas.issubset(
            columnas_train
        ) or not columnas_requeridas.issubset(columnas_test):
            log.error("Faltan columnas requeridas para el caso D")
            return False

        pct_nulos = max(
            train_df[SENSOR_FEATURES_D].isnull().mean().max(),
            test_df[SENSOR_FEATURES_D].isnull().mean().max(),
        )
        if pct_nulos > 0.3:
            log.error(f"Demasiados nulos en features del caso D: {pct_nulos:.1%}")
            return False

        return True

    # 1. Comprobar que no está vacío
    if len(df) < 100:
        log.error(f"Dataset demasiado pequeño: {len(df)} filas (mínimo 100)")
        return False

    # 2. Comprobar porcentaje de nulos
    pct_nulos = df.isnull().mean().max()
    if pct_nulos > 0.3:
        log.error(f"Demasiados nulos: {pct_nulos:.1%} en alguna columna")
        return False

    return True


def entrenar_modelo(df, caso: str, config_caso: dict):
    """Entrena el modelo correspondiente del caso de uso."""
    log.info(f"Entrenando modelo para Caso de Uso {caso}")

    if config_caso.get("trainer") == "occupancy_classification":
        train_df = df["datatraining.txt"]
        test_df = pd.concat(
            [df["datatest.txt"], df["datatest2.txt"]], ignore_index=True
        )

        x_train = train_df[SENSOR_FEATURES_D].copy()
        y_train = train_df[TARGET_D].astype(int)
        x_test = test_df[SENSOR_FEATURES_D].copy()
        y_test = test_df[TARGET_D].astype(int)

        medianas = x_train.median(numeric_only=True)
        x_train = x_train.fillna(medianas)
        x_test = x_test.fillna(medianas)

        params = {
            "n_estimators": 100,
            "max_depth": 6,
            "random_state": 42,
            "n_jobs": -1,
        }
        modelo = RandomForestClassifier(**params)
        modelo.fit(x_train, y_train)

        predicciones = modelo.predict(x_test)
        proba = modelo.predict_proba(x_test)[:, 1]
        metricas = {
            "accuracy": round(accuracy_score(y_test, predicciones), 4),
            "precision": round(
                precision_score(y_test, predicciones, zero_division=0), 4
            ),
            "recall": round(recall_score(y_test, predicciones, zero_division=0), 4),
            "f1": round(f1_score(y_test, predicciones, zero_division=0), 4),
            "auc_roc": round(roc_auc_score(y_test, proba), 4),
        }

        log.info(f"Métricas: {metricas}")
        return modelo, params, metricas, x_train, x_test, y_test, predicciones

    # Preparar features
    columnas_numericas = df.select_dtypes(include=[np.number]).columns.tolist()
    target = columnas_numericas[-1]
    features = columnas_numericas[:-1]

    x = df[features].fillna(df[features].median())
    y = df[target].fillna(df[target].median())

    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.2, random_state=42
    )

    params = {"n_estimators": 100, "max_depth": 6, "random_state": 42}
    modelo = RandomForestRegressor(**params)
    modelo.fit(x_train, y_train)

    predicciones = modelo.predict(x_test)
    metricas = {
        "rmse": round(mean_squared_error(y_test, predicciones) ** 0.5, 4),
        "mae": round(mean_absolute_error(y_test, predicciones), 4),
        "r2": round(r2_score(y_test, predicciones), 4),
    }

    log.info(f"Métricas: {metricas}")
    return modelo, params, metricas, x_train, x_test, y_test, predicciones


def registrar_report_evidently(
    x_train: pd.DataFrame,
    x_test: pd.DataFrame,
    caso: str,
    dataset: str,
    commit: str,
) -> None:
    """Genera un informe básico de drift con Evidently.

    Adjunta el informe como artefacto en MLflow.
    """
    try:
        from evidently import Report
        from evidently.presets import DataDriftPreset, DataSummaryPreset
    except Exception as exc:
        log.warning(f"Evidently no se encuentra disponible: {exc}")
        mlflow.set_tag("evidently_status", "unavailable")
        return

    try:
        current = x_test.copy()
        reference = x_train.copy()

        # Evita errores y problemas con columnas no serializables
        for col in reference.columns:
            if str(reference[col].dtype).startswith("datetime"):
                reference[col] = reference[col].astype(str)
                if col in current.columns:
                    current[col] = current[col].astype(str)

        report = Report(metrics=[DataSummaryPreset(), DataDriftPreset()])
        report.run(reference_data=reference, current_data=current)

        with tempfile.TemporaryDirectory(prefix="evidently_") as tmp_dir:
            html_path = os.path.join(tmp_dir, "evidently_report.html")
            json_path = os.path.join(tmp_dir, "evidently_report.json")

            report.save_html(html_path)
            report.save_json(json_path)

            mlflow.log_artifact(html_path, artifact_path="monitoring/evidently")
            mlflow.log_artifact(json_path, artifact_path="monitoring/evidently")

        mlflow.set_tags(
            {
                "evidently_status": "ok",
                "evidently_reference_rows": str(len(reference)),
                "evidently_current_rows": str(len(current)),
                "evidently_case": caso,
                "evidently_dataset": dataset,
                "evidently_dataset_version": commit,
            }
        )
        log.info("Reporte Evidently registrado en MLflow")

    except Exception as exc:
        log.warning(f"No se pudo generar report Evidently: {exc}")
        mlflow.set_tag("evidently_status", "error")
        mlflow.set_tag("evidently_error", str(exc)[:250])


def ejecutar_pipeline(caso: str, dataset: str, commit: str, committer: str):
    """Ejecuta el pipeline completo de reentrenamiento.

    Pasos:
        1. Descarga datos del commit exacto de lakeFS
        2. Valida calidad
        3. Entrena modelo
        4. Registra en MLflow con trazabilidad completa
        5. Promueve a Staging si supera el umbral
    """
    config_caso = CASOS.get(caso)
    if not config_caso:
        log.error(
            f"El Caso de uso {caso} no está registrado. "
            f"Casos válidos: {list(CASOS.keys())}"
        )
        sys.exit(1)

    log.info(
        f"Pipeline iniciado. Caso de uso {caso}. Dataset {dataset}. Commit {commit[:8]}"
    )

    # Paso 1: Descarga de datos
    try:
        df = descargar_datos(dataset, commit, config_caso)
    except Exception as e:
        log.error(f"Error descargando datos: {e}")
        sys.exit(1)

    # Paso 2: Validar datos
    if not validar_datos(df, dataset, config_caso):
        log.error("Validación fallida. Pipeline cancelada")
        sys.exit(1)

    # Paso 3 y 4: Entrenar y registrar en MLflow
    mlflow.set_tracking_uri(MLFLOW_URI)
    mlflow.set_experiment(config_caso["experimento"])

    # Entrenar antes de abrir el run para derivar el nombre real del algoritmo
    modelo, params, metricas, x_train, x_test, y_test, preds = entrenar_modelo(
        df, caso, config_caso
    )

    algoritmo = modelo.__class__.__name__
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    run_name = f"{algoritmo}_{timestamp}_auto_{commit[:8]}"

    with mlflow.start_run(run_name=run_name) as run:

        # Tags de trazabilidad
        mlflow.set_tags(
            {
                "caso_uso": caso,
                "grupo": f"G{'1' if caso=='B' else '3' if caso in ('C','E') else '4'}",
                "dataset": dataset,
                "dataset_version": commit,
                "dataset_branch": "main",
                "capa_medallion": "oro",
                "disparado_por": "webhook_lakefs",
                "committer": committer,
                "run_type": "automatico",
            }
        )

        # Registrar parámetros y métricas
        mlflow.log_params(params)
        mlflow.log_metrics(metricas)

        # Informe de drift de datos
        registrar_report_evidently(
            x_train=x_train,
            x_test=x_test,
            caso=caso,
            dataset=dataset,
            commit=commit,
        )

        # Registrar el modelo
        mlflow.sklearn.log_model(
            sk_model=modelo,
            artifact_path="model",
            registered_model_name=config_caso["modelo_registry"],
            metadata={
                "caso_uso": caso,
                "framework": "scikit-learn",
                "task": (
                    "classification"
                    if config_caso.get("trainer") == "occupancy_classification"
                    else "regression"
                ),
            },
        )

        run_id = run.info.run_id
        log.info(f"Run registrado en MLflow: {run_id}")

        _llevar_a_staging(config_caso["modelo_registry"], run_id)

    log.info("Pipeline completado correctamente")


def _llevar_a_staging(nombre_modelo: str, run_id: str):
    """Promueve la última versión del modelo a estado Staging en el registry."""
    from mlflow.tracking import MlflowClient

    client = MlflowClient(tracking_uri=MLFLOW_URI)

    versiones = client.get_latest_versions(nombre_modelo, stages=["None"])
    if not versiones:
        log.warning("No se encontró versión")
        return

    ultima_version = versiones[0].version
    client.transition_model_version_stage(
        name=nombre_modelo,
        version=ultima_version,
        stage="Staging",
        archive_existing_versions=True,
    )
    log.info(f"Modelo '{nombre_modelo}' v{ultima_version} subido a Staging")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Pipeline de reentrenamiento automático"
    )
    parser.add_argument("--caso", required=True, help="Letra del caso (B, C, D, E)")
    parser.add_argument("--dataset", required=True, help="Nombre del repo en lakeFS")
    parser.add_argument("--commit", default="main", help="Commit hash de lakeFS")
    parser.add_argument("--committer", default="auto", help="Usuario que hizo el merge")
    args = parser.parse_args()

    ejecutar_pipeline(
        caso=args.caso,
        dataset=args.dataset,
        commit=args.commit,
        committer=args.committer,
    )
