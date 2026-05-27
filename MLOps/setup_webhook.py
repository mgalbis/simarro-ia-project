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

DATASETS_CON_PIPELINE = ["uci-appliances", "lbnl-fdd", "uci-occupancy", "era5"]


def registrar_webhooks():
    cfg = lakefs_sdk.Configuration(
        host=LAKEFS_HOST,
        username=LAKEFS_ACCESS,
        password=LAKEFS_SECRET,
    )

    client = LakeFSClient(configuration=cfg)

    for dataset in DATASETS_CON_PIPELINE:
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
      timeout: 10s
"""
        client.objects_api.upload_object(
            repository=dataset,
            branch="main",
            path="_lakefs_actions/pipeline.yaml",
            content=accion_yaml.encode(),
        )

        client.commits_api.commit(
            repository=dataset,
            branch="main",
            commit_creation=lakefs_sdk.CommitCreation(
                message="ci: registrar webhook de pipeline CI/CD",
                metadata={"mantenido_por": "G4-CasoF"},
            ),
        )

        print(f"Webhook registrado en: {dataset}")


if __name__ == "__main__":
    registrar_webhooks()
