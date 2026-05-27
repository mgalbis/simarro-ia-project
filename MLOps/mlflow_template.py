# Plantilla para la integración MLflow para los equipos del proyecto final
# Esta plantilla pretende demostrar el ciclo completo: cargar datos --> entrenar --> registrar
#
# Uso:
#   1. Copiar este fichero en el notebook donde se entrenará el modelo
#   2. Cambiar EXPERIMENT_NAME por el del caso de uso ("simarro-caso-x")
#   3. Cambiar el modelo y las métricas por las que requiera el modelo a entrenar
#   4. Ejecutar y verificar en http://localhost:5000
#   TODO: modificar la uri del servidor cuando se utilice la infra de ITI
#
# Requisitos: instalar desde un entorno virtual del proyecto, por ejemplo
#   python -m pip install -r requirements.txt
# ─────────────────────────────────────────────────────────────

import os
import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd
from datetime import datetime
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

# Configuración

# Para ejecutar este script fuera de JupyterHub hay que descomentar esta línea
# mlflow.set_tracking_uri("http://localhost:5000")

MLFLOW_URI = os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5000")
mlflow.set_tracking_uri(MLFLOW_URI)

# Convención de nomenclatura del proyecto
# [caso]_[dataset]_[algoritmo]_[fecha], pero la fecha se añade posteriormente en la ejecución
EXPERIMENT_NAME = "CasoB_UCI_XGBoost"


# Datos sintéticos (sustituir por datos reales del dataset)
def load_data() -> tuple:
    """
    Aquí se debe carga el dataset desde lakeFS si es capa plata o desde una ruta local si es capa bronce
    En este ejemplo se cargan datos sintéticos para demostrar la integración

    Retorna: (X_train, X_test, y_train, y_test)
    """
    np.random.seed(42)
    numMuestras = 500

    # Simulamos features de consumo energético (temperatura exterior, hora del día, día de la semana, ocupación estimada, temperatura interior)
    X = pd.DataFrame(
        {
            "temp_exterior": np.random.uniform(0, 40, numMuestras),
            "hora_dia": np.random.randint(0, 24, numMuestras),
            "dia_semana": np.random.randint(0, 7, numMuestras),
            "ocupacion": np.random.uniform(0, 25, numMuestras),
            "temp_interior": np.random.uniform(10, 35, numMuestras),
        }
    )

    # Consumo energético simulado con algo de ruido
    y = (
        0.5 * X["temp_exterior"]
        + 2.0 * X["ocupacion"] * 10
        + np.random.normal(0, 2, numMuestras)
    )

    return train_test_split(X, y, test_size=0.2, random_state=42)


# Entrenamiento y registro
def train_registry(params: dict) -> str:
    """
    Entrena un modelo con los parámetros dados y lo registra en MLflow

    Args:
        params: diccionario de hiperparámetros del modelo

    Returns:
        run_id: identificador de la ejecución en MLflow
    """

    # Seleccionamos el experimento donde se registrará la ejecución
    mlflow.set_experiment(EXPERIMENT_NAME)

    # El nombre del run sigue la convención algoritmo_YYYYMMDDHHmmSS_descripcion
    run_name = f"RandomForestRegressor_{datetime.now().strftime('%Y%m%d%H%M%S')}_baseline"

    # Iniciamos la ejecución, y todo lo que se registre en este bloque quedará registrado
    with mlflow.start_run(run_name=run_name) as run:

        run_id = run.info.run_id
        print(f"Run iniciado: {run_id}")
        print(f"Experimento: {EXPERIMENT_NAME}")
        print(f"Nombre run: {run_name}\n")

        # 1- Registrar parámetros
        # Los parámetros son los hiperparámetros del modelo
        mlflow.log_params(params)
        print(" Parámetros registrados:")
        for k, v in params.items():
            print(f"    {k}: {v}")

        # 2- Cargar datos y registrar info del dataset
        X_train, X_test, y_train, y_test = load_data()

        # Registramos información del dataset como tags
        # Los tags son metadatos de texto libre sobre el run
        mlflow.set_tags(
            {
                "dataset": "uci_appliances",
                "dataset_version": "main",  # rama de lakeFS (cada CU tiene su propia rama)
                "n_train": len(X_train),
                "n_test": len(X_test),
                "features": ", ".join(X_train.columns.tolist()),
                "ejecutado_por": os.environ.get("JUPYTERHUB_USER", "local"),
            }
        )

        # 3- Entrenar el modelo
        print(
            "\nEntrenamiento del modelo iniciado. Este proceso puede tardar unos minutos..."
        )
        modelo = RandomForestRegressor(**params)
        modelo.fit(X_train, y_train)
        print("\nEntrenamiento completado")

        # 4 - Evaluar y registrar métricas
        predicciones = modelo.predict(X_test)

        rmse = mean_squared_error(y_test, predicciones) ** 0.5
        mae = mean_absolute_error(y_test, predicciones)
        r2 = r2_score(y_test, predicciones)

        mlflow.log_metrics(
            {
                "rmse": round(rmse, 4),
                "mae": round(mae, 4),
                "r2": round(r2, 4),
            }
        )

        print(f"\n Métricas registradas:")
        print(f"  RMSE: {rmse:.4f}")
        print(f"  MAE: {mae:.4f}")
        print(f"  R²: {r2:.4f}")

        # 5 - Registrar el modelo en el registry
        #   5.1 Guarda el modelo como artefacto del run
        #   5.2 Lo registra en el Model Registry con nombre oficial versionado
        model_info = mlflow.sklearn.log_model(
            sk_model=modelo,
            artifact_path="model",
            registered_model_name="simarro-caso-b-consumo",
            # Metadatos que viajan con el modelo
            metadata={
                "caso_uso": "B",
                "framework": "scikit-learn",
                "task": "regression",
            },
        )

        print(f"\n Modelo registrado en el registry")
        print(f"  Nombre: simarro-caso-b-consumo")
        print(f"  URI: {model_info.model_uri}")

        # Guardamos las predicciones como CSV para auditarlo
        df_predicciones = pd.DataFrame(
            {
                "real": y_test.values,
                "prediccion": predicciones,
                "error": y_test.values - predicciones,
            }
        )
        df_predicciones.to_csv("/tmp/predicciones.csv", index=False)
        mlflow.log_artifact("/tmp/predicciones.csv", artifact_path="evaluacion")

        print(f"  Artefactos guardados (predicciones CSV)")

        return run_id


# Experimento de comparación de hiperparámetros
def comparar_hiperparametros():
    """
    En este ejemplo lanzamos varios runs con distintos hiperparámetros para comparar cual da mejores métricas.
    """

    configuraciones = [
        {"n_estimators": 50, "max_depth": 3, "random_state": 42},
        {"n_estimators": 100, "max_depth": 5, "random_state": 42},
        {"n_estimators": 200, "max_depth": 10, "random_state": 42},
    ]

    print("-" * 75)
    print("Comparando configuraciones de hiperparámetros")
    print("-" * 75)

    run_ids = []
    for i, params in enumerate(configuraciones, 1):
        print(f"\n[{i}/{len(configuraciones)}] {params}")
        run_id = train_registry(params)
        run_ids.append(run_id)
        print(f"Run completado: {run_id}")

    print("\n" + "-" * 75)
    print("Comparación completada.")
    print(f"Para visualizar los resultados: {MLFLOW_URI}")
    print(f"Experimento: {EXPERIMENT_NAME}")
    print("-" * 75)

    return run_ids


if __name__ == "__main__":
    comparar_hiperparametros()
