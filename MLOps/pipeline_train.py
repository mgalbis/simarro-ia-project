# Script de reentrenamiento automático.
# Se invoca desde pipeline_server.py cuando hay un merge a main.
#
# Uso (manual para pruebas):
#   python pipeline_train.py --caso B
#                            --dataset uci-appliances
#                            --commit abc123
#                            --committer caso_b

import os
import sys
import argparse
import logging
import mlflow
import mlflow.sklearn
import lakefs_sdk
from lakefs_sdk.client import LakeFSClient
from datetime import date
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import pandas as pd
import numpy as np

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [TRAIN] %(levelname)s — %(message)s"
)
log = logging.getLogger(__name__)

# Configuración
MLFLOW_URI = os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5000")
LAKEFS_HOST = os.environ.get("LAKEFS_ENDPOINT", "http://localhost:8001")
LAKEFS_ACCESS = os.environ.get("LAKEFS_ACCESS_KEY_ID")
LAKEFS_SECRET = os.environ.get("LAKEFS_SECRET_ACCESS_KEY")

# Umbral mínimo de R² para pasar a Staging.
# Si el modelo no supera este valor, no se promueve.
# TODO: Definir un umbral para cada caso de uso? De momento lo dejamos en 0.70 para todos
UMBRAL_R2 = 0.70

# Mapa de casos a experimentos y modelos en MLflow
CASOS = {
    "B": {
        "experimento": "CasoB_Prediccion_de_consumo_electrico",
        "modelo_registry": "simarro-caso-b",
    },
    "C": {
        "experimento": "CasoC_Deteccion_de_anomalias_HVAC",
        "modelo_registry": "simarro-caso-c",
    },
    "D": {
        "experimento": "CasoD_Calidad_del_aire_y_ocupacion",
        "modelo_registry": "simarro-caso-d",
    },
    "E": {
        "experimento": "CasoE_Datos_meteorologicos",
        "modelo_registry": "simarro-caso-e",
    },
}

# Funciones auxiliares


def get_lakefs_client() -> LakeFSClient:
    cfg = lakefs_sdk.Configuration(
        host=LAKEFS_HOST,
        username=LAKEFS_ACCESS,
        password=LAKEFS_SECRET,
    )
    return LakeFSClient(configuration=cfg)


def descargar_datos(dataset: str, commit: str) -> pd.DataFrame:
    """
    Descarga el dataset desde lakeFS en el commit exacto que disparó el pipeline.
    """
    log.info(f"Descargando datos de lakeFS. Repo: {dataset}  Commit: {commit[:8]}")

    client = get_lakefs_client()

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

    respuesta = client.objects_api.get_object(
        repository=dataset,
        ref=commit,
        path=ruta_objeto,
    )

    # Carga el csv en un dataframe de pandas
    df = pd.read_csv(respuesta)
    log.info(f"Dataset cargado: {len(df)} filas, {len(df.columns)} columnas")
    return df


# TODO: Revisar si esta validación no pisa la validación que hacemos con el agente
def validar_datos(df: pd.DataFrame, dataset: str) -> bool:
    """
    Validación básica de calidad antes de entrenar.
    Devuelve True si los datos son válidos, False si hay problemas.
    """
    log.info("Validando calidad de los datos...")

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


def entrenar_modelo(df: pd.DataFrame, caso: str):
    """
    Entrena el modelo correspondiente del caso de uso.
    """
    log.info(f"Entrenando modelo para Caso de Uso {caso}")

    # Preparar features
    columnas_numericas = df.select_dtypes(include=[np.number]).columns.tolist()
    target = columnas_numericas[-1]
    features = columnas_numericas[:-1]

    X = df[features].fillna(df[features].median())
    y = df[target].fillna(df[target].median())

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    params = {"n_estimators": 100, "max_depth": 6, "random_state": 42}
    modelo = RandomForestRegressor(**params)
    modelo.fit(X_train, y_train)

    predicciones = modelo.predict(X_test)
    metricas = {
        "rmse": round(mean_squared_error(y_test, predicciones) ** 0.5, 4),
        "mae": round(mean_absolute_error(y_test, predicciones), 4),
        "r2": round(r2_score(y_test, predicciones), 4),
    }

    log.info(f"Métricas: {metricas}")
    return modelo, params, metricas, X_train, X_test, y_test, predicciones


def ejecutar_pipeline(caso: str, dataset: str, commit: str, committer: str):
    """
    Ejecuta el pipeline completo de reentrenamiento siguiendo los pasos:
        1. Descarga datos del commit exacto de lakeFS
        2. Valida calidad
        3. Entrena modelo
        4. Registra en MLflow con trazabilidad completa
        5. Promueve a Staging si supera el umbral
    """
    config_caso = CASOS.get(caso)
    if not config_caso:
        log.error(
            f"El Caso de uso {caso} no está registrado. Casos válidos: {list(CASOS.keys())}"
        )
        sys.exit(1)

    log.info(
        f"Pipeline iniciado. Caso de uso {caso}. Dataset {dataset}. Commit {commit[:8]}"
    )

    # Paso 1: Descarga de datos
    try:
        df = descargar_datos(dataset, commit)
    except Exception as e:
        log.error(f"Error descargando datos: {e}")
        sys.exit(1)

    # Paso 2: Validar datos
    if not validar_datos(df, dataset):
        log.error("Validación fallida. Pipeline cancelada")
        sys.exit(1)

    # Paso 3 y 4: Entrenar y registrar en MLflow
    mlflow.set_tracking_uri(MLFLOW_URI)
    mlflow.set_experiment(config_caso["experimento"])

    run_name = f"auto_{date.today().strftime('%Y%m%d')}_{commit[:8]}"

    with mlflow.start_run(run_name=run_name) as run:

        # Tags de trazabilidad
        mlflow.set_tags(
            {
                "caso_uso": caso,
                "grupo": f"G{'1' if caso=='B' else '3' if caso in ('C','E') else '4'}",
                "dataset": dataset,
                "dataset_version": commit,  # commit hash exacto de lakeFS. Sino no tiene trazabilidad
                "dataset_branch": "main",
                "capa_medallion": "oro",
                "disparado_por": "webhook_lakefs",
                "committer": committer,
                "run_type": "automatico",
            }
        )

        # Entrenar
        modelo, params, metricas, X_train, X_test, y_test, preds = entrenar_modelo(
            df, caso
        )

        # Registrar parámetros y métricas
        mlflow.log_params(params)
        mlflow.log_metrics(metricas)

        # Registrar el modelo
        mlflow.sklearn.log_model(
            sk_model=modelo,
            artifact_path="model",
            registered_model_name=config_caso["modelo_registry"],
        )

        run_id = run.info.run_id
        log.info(f"Run registrado en MLflow: {run_id}")

        _llevar_a_staging(config_caso["modelo_registry"], run_id)

    log.info("Pipeline completado correctamente")


def _llevar_a_staging(nombre_modelo: str, run_id: str):
    """
    Promueve la última versión del modelo a estado Staging en el registry.
    """
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
