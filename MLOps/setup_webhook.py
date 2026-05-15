# Registra el webhook en lakeFS para todos los repositorios de datasets.
# Este script debe ejecutarse una sola vez después de levantar el stack.

import os
import lakefs_sdk
from lakefs_sdk.client import LakeFSClient

LAKEFS_HOST = os.environ.get("LAKEFS_ENDPOINT", "http://localhost:8001")
LAKEFS_ACCESS = os.environ.get("LAKEFS_ACCESS_KEY_ID", "AKIASIMARRO")
LAKEFS_SECRET = os.environ.get("LAKEFS_SECRET_ACCESS_KEY", "simarrosecret")

# URL del servidor webhook (ojo: dentro de Docker se usa el nombre del servicio)
WEBHOOK_URL = "http://pipeline:8080"

# TODO: revisar los nombres de los datasets. Cualquier errata hará que el webhook no funcione
DATASETS_CON_PIPELINE = ["uci-appliances", "lbnl-fdd", "uci-occupancy", "era5"]


def registrar_webhooks():
    cfg = lakefs_sdk.Configuration(
        host=LAKEFS_HOST,
        username=LAKEFS_ACCESS,
        password=LAKEFS_SECRET,
    )

    with LakeFSClient(configuration=cfg) as client:
        for dataset in DATASETS_CON_PIPELINE:
            # El webhook se configura como una "action" de lakeFS en formato YAML dentro del propio repositorio
            accion_yaml = f"""
                name: pipeline-reentrenamiento
                on:
                  post-merge:
                    branches:
                      - main
                hooks:
                  - id: trigger-pipeline
                    type: webhook
                    properties:
                      url: {WEBHOOK_URL}
                      timeout: 30s
                """
            # Subimos el fichero de accion al repositorio
            client.objects_api.upload_object(
                repository=dataset,
                branch="main",
                path="_lakefs_actions/pipeline.yaml",
                content=accion_yaml.encode(),
            )

            # Commit del fichero de acción
            client.commits_api.commit(
                repository=dataset,
                branch="main",
                commit_creation=lakefs_sdk.CommitCreation(
                    message="ci: registrar webhook de pipeline CI/CD",
                    metadata={"mantenido_por": "G4"},
                ),
            )

            print(f"Webhook registrado correctamenteen: {dataset}")


if __name__ == "__main__":
    registrar_webhooks()
