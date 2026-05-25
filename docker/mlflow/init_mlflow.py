"""Bootstrap de metadata en MLflow desde ``config/cases_config.json``."""

from __future__ import annotations

import json
import os
import time
from typing import Any

from mlflow import MlflowClient
from mlflow.exceptions import MlflowException

MLFLOW_URI = os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5000/mlflow")
CASES_CONFIG_PATH = os.environ.get(
    "CASES_CONFIG_PATH", "/mlflow/init/cases_config.json"
)
RETRIES = int(os.environ.get("MLFLOW_INIT_RETRIES", "60"))
RETRY_SECONDS = float(os.environ.get("MLFLOW_INIT_RETRY_SECONDS", "2"))


def _load_cases_config(path: str) -> dict[str, Any]:
    """Carga y valida el contenido mínimo del fichero de casos."""
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"Formato inválido de configuración en {path}")
    return data


def _wait_mlflow(client: MlflowClient) -> None:
    """Espera hasta que el tracking server responda o agota reintentos."""
    for attempt in range(1, RETRIES + 1):
        try:
            client.search_experiments(max_results=1)
            print(f"MLflow disponible en {MLFLOW_URI}")
            return
        except Exception as exc:  # noqa: BLE001
            print(f"Esperando MLflow ({attempt}/{RETRIES}) en {MLFLOW_URI}: {exc}")
            time.sleep(RETRY_SECONDS)
    raise TimeoutError("No se pudo conectar a MLflow dentro del tiempo esperado")


def create_experiments_from_cases(
    client: MlflowClient,
    cases_config: dict[str, Any],
) -> None:
    """Crea o actualiza experimentos definidos en el bloque ``cases``."""
    cases = cases_config.get("cases", {})
    if not isinstance(cases, dict):
        raise ValueError("Bloque 'cases' inválido en cases_config.json")
    project = str(cases_config.get("project", "")).strip()

    for case_id, case_cfg in cases.items():
        if not isinstance(case_cfg, dict):
            continue

        name = str(case_cfg.get("name", f"Case_{case_id}")).strip()
        description = str(case_cfg.get("description", "")).strip()
        problem_type = str(case_cfg.get("problem_type", "")).strip()
        experiment_name = f"Caso{case_id}_{name}"

        experiment = client.get_experiment_by_name(experiment_name)
        tags = {
            "case": str(case_id),
            "problem_type": problem_type,
            "project": project,
            "mlflow.note.content": description,
        }

        if experiment:
            for key, value in tags.items():
                client.set_experiment_tag(experiment.experiment_id, key, value)
            print(f"Experimento existente actualizado: {experiment_name}")
            continue

        experiment_id = client.create_experiment(name=experiment_name, tags=tags)
        print(f"Experimento creado: {experiment_name} (id={experiment_id})")


def register_models_from_cases(
    client: MlflowClient,
    cases_config: dict[str, Any],
) -> None:
    """Crea o actualiza modelos registrados definidos en ``cases``."""
    cases = cases_config.get("cases", {})
    if not isinstance(cases, dict):
        raise ValueError("Bloque 'cases' inválido en cases_config.json")
    project = str(cases_config.get("project", "")).strip()

    for case_id, case_cfg in cases.items():
        if not isinstance(case_cfg, dict):
            continue

        functional_model_name = str(case_cfg.get("functional_model_name", "")).strip()
        purpose = str(case_cfg.get("purpose", "")).strip()
        problem_type = str(case_cfg.get("problem_type", "")).strip()
        target_variable = str(case_cfg.get("target_variable", "")).strip()
        if not functional_model_name:
            print(
                f"Caso {case_id}: no se registra modelo "
                "(falta 'functional_model_name')"
            )
            continue

        model_name = f"Caso{case_id}_{functional_model_name}"
        tags = {
            "project": project,
            "case": str(case_id),
            "problem_type": problem_type,
        }
        if target_variable:
            tags["target_variable"] = target_variable

        try:
            client.create_registered_model(name=model_name, description=purpose)
            for key, value in tags.items():
                client.set_registered_model_tag(model_name, key, value)
            print(f"Modelo registrado: {model_name}")
        except MlflowException as exc:
            if "RESOURCE_ALREADY_EXISTS" in str(exc):
                client.update_registered_model(
                    name=model_name,
                    description=purpose,
                )
                for key, value in tags.items():
                    client.set_registered_model_tag(model_name, key, value)
                print(f"Modelo existente actualizado: {model_name}")
            else:
                raise


def show_summary(client: MlflowClient) -> None:
    """Muestra el estado final de experimentos y modelos registrados."""
    print("\n" + "_" * 75)
    print("Estado final de los experimentos y de los modelos en MLflow:\n")

    # Experimentos
    print("  EXPERIMENTOS:")
    experimentos = client.search_experiments()
    for exp in experimentos:
        print(f"    [{exp.experiment_id}] {exp.name}")

    # Modelos del registry
    print("\n  MODEL REGISTRY:")
    modelos = client.search_registered_models()
    for modelo in modelos:
        print(f"    {modelo.name}")
        print(f"      Versiones: {len(modelo.latest_versions)}")

    print(f"\n  UI disponible en: {MLFLOW_URI}")
    print("─" * 75)


def main() -> None:
    """Punto de entrada."""
    print(f"Inicializando experimentos MLflow desde: {CASES_CONFIG_PATH}")
    print(f"Tracking URI: {MLFLOW_URI}")

    config = _load_cases_config(CASES_CONFIG_PATH)
    client = MlflowClient(tracking_uri=MLFLOW_URI)
    _wait_mlflow(client)
    create_experiments_from_cases(client, config)
    register_models_from_cases(client, config)
    show_summary(client)

    print("Inicialización de experimentos y modelos completada")


if __name__ == "__main__":
    main()
