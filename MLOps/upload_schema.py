# Este script sube el schema CAPTIA a lakeFS para que quede versionado.
# Se ejecuta una vez tras crear los repositorios.

import os
import json
import lakefs_sdk
from lakefs_sdk.client import LakeFSClient

LAKEFS_HOST = os.environ.get("LAKEFS_ENDPOINT", "http://localhost:8001")
LAKEFS_ACCESS = os.environ.get("LAKEFS_ACCESS_KEY_ID", "AKIASIMARRO")
LAKEFS_SECRET = os.environ.get("LAKEFS_SECRET_ACCESS_KEY", "simarrosecret")

# El schema se versiona en un repositorio dedicado a la infraestructura MLOps
REPO = "mlops-config"
BRANCH = "main"
PATH = "schema/schema_captia.json"


def subir_schema():
    cfg = lakefs_sdk.Configuration(
        host=LAKEFS_HOST,
        username=LAKEFS_ACCESS,
        password=LAKEFS_SECRET,
    )

    with LakeFSClient(configuration=cfg) as client:

        # Crear el repositorio mlops-config si no existe
        try:
            client.repositories_api.create_repository(
                lakefs_sdk.RepositoryCreation(
                    name=REPO,
                    storage_namespace=f"local://{REPO}",
                    default_branch=BRANCH,
                )
            )
            print(f"Repositorio '{REPO}' creado")
        except lakefs_sdk.exceptions.ApiException as e:
            if e.status == 409:
                print(f"Repositorio '{REPO}' ya existe")

        # Leer el schema local
        with open("schema_captia.json", "rb") as f:
            contenido = f.read()

        # Subir el fichero
        client.objects_api.upload_object(
            repository=REPO,
            branch=BRANCH,
            path=PATH,
            content=contenido,
        )

        # Hacer commit
        client.commits_api.commit(
            repository=REPO,
            branch=BRANCH,
            commit_creation=lakefs_sdk.CommitCreation(
                message="feat: schema CAPTIA v1.0 — tags y variables por caso de uso",
                metadata={"version": "1.0"},
            ),
        )

        # Obtener el commit hash para distribuirlo al resto de equipos
        commits = client.commits_api.log_branch_commits(repository=REPO, branch=BRANCH)
        commit_hash = commits.results[0].id

        print(f"\nSchema subido correctamente")
        print(f"Repositorio: {REPO}")
        print(f"Ruta:        {PATH}")
        print(f"Commit hash: {commit_hash}")
        print(f"\nDistribuir este hash a todos los grupos")


if __name__ == "__main__":
    subir_schema()
