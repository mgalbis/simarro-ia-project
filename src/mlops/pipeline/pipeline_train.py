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

import mlflow
import mlflow.sklearn
import pandas as pd
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

from mlops.config import CASES_CONFIG
from mlops.utils.lakefs_manager import LakeFSManager

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [TRAIN] %(levelname)s — %(message)s"
)
log = logging.getLogger(__name__)

MLFLOW_URI = os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5000")

# Funciones auxiliares
LAKEFS_MANAGER = LakeFSManager(cases_config=CASES_CONFIG)


def _read_lakefs_parquet(dataset: str, ref: str, path: str) -> pd.DataFrame:
    """Compatibilidad: delega lectura parquet al manager lakeFS."""
    return LAKEFS_MANAGER.read_parquet(repository=dataset, ref=ref, path=path)


def descargar_datos(dataset: str, tag: str):
    """Descarga train/test de Gold desde lakeFS a partir de un tag."""
    log.info(f"Descargando datos de lakeFS. Repo: {dataset}  Tag: {tag}")

    gold_paths = LAKEFS_MANAGER.resolve_gold_paths()
    train_path = gold_paths["train"]
    test_path = gold_paths["test"]

    log.info(f"Descargando Gold train: {train_path}")
    train_df = LAKEFS_MANAGER.read_parquet(dataset, tag, train_path)

    log.info(f"Descargando Gold test: {test_path}")
    test_df = LAKEFS_MANAGER.read_parquet(dataset, tag, test_path)

    log.info("Gold cargado: " f"train={len(train_df)} filas, test={len(test_df)} filas")
    return train_df, test_df


def entrenar_modelo(train_df, test_df, caso: str, dataset: str, config_caso: dict):
    """Entrena el modelo correspondiente del caso de uso."""
    log.info(f"Entrenando modelo para Caso de Uso {caso}")

    feature_columns = CASES_CONFIG.resolve_feature_columns(dataset)
    target_column = CASES_CONFIG.resolve_target_column(dataset)

    x_train = train_df[feature_columns].copy()
    x_test = test_df[feature_columns].copy()
    y_train = train_df[target_column].copy()
    y_test = test_df[target_column].copy()

    # TODO: obtener los modelos a entrenar y sus parametros de configuración
    # a partir de los últimos ejecutados en mlflow
    if config_caso.get("problem_type") == "binary_classification":
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
        snapshot = report.run(reference_data=reference, current_data=current)

        with tempfile.TemporaryDirectory(prefix="evidently_") as tmp_dir:
            html_path = os.path.join(tmp_dir, "evidently_report.html")
            json_path = os.path.join(tmp_dir, "evidently_report.json")

            snapshot.save_html(html_path)
            snapshot.save_json(json_path)

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


def ejecutar_pipeline(
    caso: str, repository: str, dataset: str, commit: str, committer: str, tag: str
):
    """Ejecuta el pipeline completo de reentrenamiento.

    Pasos:
        1. Descarga datos de Gold desde el tag de lakeFS
        2. Valida calidad
        3. Entrena modelo
        4. Registra en MLflow con trazabilidad completa
        5. Promueve a Staging si supera el umbral
    """
    config_caso = CASES_CONFIG.cases.get(caso)
    if not config_caso:
        log.error(
            f"El Caso de uso {caso} no está registrado. "
            f"Casos válidos: {list(CASES_CONFIG.cases.keys())}"
        )
        sys.exit(1)

    log.info(f"Pipeline iniciado. Caso de uso {caso}. Dataset {dataset}. Tag {tag}")

    # Paso 1: Descarga de datos
    try:
        train_df, test_df = descargar_datos(repository, tag)
    except Exception as e:
        log.error(f"Error descargando datos: {e}")
        sys.exit(1)

    # Paso 2: Entrenar y registrar en MLflow
    experiment = CASES_CONFIG.resolve_experiment_name(caso)
    mlflow.set_tracking_uri(MLFLOW_URI)
    mlflow.set_experiment(experiment)

    # Entrenar antes de abrir el run para derivar el nombre real del algoritmo
    modelo, params, metricas, x_train, x_test, y_test, preds = entrenar_modelo(
        train_df, test_df, caso, dataset, config_caso
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
                "dataset_commit": commit,
                "dataset_tag": tag,
                "disparado_por": "webhook_lakefs",
                "committer": committer,
                "run_type": "automatico",
                "algorithm": algoritmo,
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

        model_name = config_caso.get("functional_model_name")

        # Registrar el modelo
        mlflow.sklearn.log_model(
            sk_model=modelo,
            name="model",
            serialization_format="skops",
            registered_model_name=model_name,
            metadata={
                "caso_uso": caso,
                "framework": "scikit-learn",
                "task": config_caso.get("problem_type"),
            },
        )

        run_id = run.info.run_id
        log.info(f"Run registrado en MLflow: {run_id}")

        _llevar_a_staging(model_name, run_id)

    log.info("Pipeline completado correctamente")


def _llevar_a_staging(nombre_modelo: str, run_id: str):
    """Asigna el alias `staging` a la versión más reciente del run en registry."""
    from mlflow.tracking import MlflowClient

    client = MlflowClient(tracking_uri=MLFLOW_URI)

    versiones = list(client.search_model_versions(f"name='{nombre_modelo}'"))
    if not versiones:
        log.warning("No se encontró versión")
        return

    versiones_run = [v for v in versiones if getattr(v, "run_id", None) == run_id]
    candidatas = versiones_run or versiones
    ultima_version = str(max(candidatas, key=lambda v: int(v.version)).version)

    client.set_registered_model_alias(
        name=nombre_modelo,
        alias="staging",
        version=ultima_version,
    )
    log.info(f"Modelo '{nombre_modelo}' alias 'staging' -> v{ultima_version}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Pipeline de reentrenamiento automático"
    )
    parser.add_argument("--caso", required=True, help="Letra del caso (B, C, D, E)")
    parser.add_argument("--repository", required=True, help="")
    parser.add_argument("--dataset", required=True, help="Nombre del repo en lakeFS")
    parser.add_argument("--commit", required=True, help="Commit hash de lakeFS")
    parser.add_argument(
        "--committer", default="auto", help="Usuario que hizo el tag de versión"
    )
    parser.add_argument("--tag", required=True, help="Tag de versión creado")
    args = parser.parse_args()

    ejecutar_pipeline(
        caso=args.caso,
        repository=args.repository,
        dataset=args.dataset,
        commit=args.commit,
        committer=args.committer,
        tag=args.tag,
    )
