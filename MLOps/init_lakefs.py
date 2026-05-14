import os
import time
import lakefs_sdk
from lakefs_sdk.client import LakeFSClient
from lakefs_sdk.models import RepositoryCreation, BranchCreation

# configuración de conexión
LAKEFS_HOST = os.environ.get("LAKEFS_ENDPOINT", "http://localhost:8001")
LAKEFS_ACCESS_KEY = os.environ.get("LAKEFS_ACCESS_KEY_ID", "AKIASIMARRO")
LAKEFS_SECRET_KEY = os.environ.get("LAKEFS_SECRET_ACCESS_KEY", "simarrosecret")

# datasets: cada dataset tendrá su propio repositorio en lakeFS
DATASETS = [
    {
        "name": "bdg2",
        "description": "Building Data Genome 2:  https://github.com/buds-lab/building-datagenome-project-2 — 3.053 contadores, 1.636 edificios, 53M+ registros horarios, metadatos de edificio y meteor",
    },
    {
        "name": "ingauge",
        "description": "In-Gauge / En-Gage: https://physionet.org/content/in-gauge-and-en-gage/1.0.0/ — 16 CSVs de aulas educativas reales, 1 min. — Variables interiores (T, HR, CO₂, ruido), exteriores, ocupación y estado HVAC. Usado en Caso A (pipeline IoT) y Caso D (calidad del aire).",
    },
    {
        "name": "uci-appliances",
        "description": "UCI Appliances Energy Prediction: https://archive.ics.uci.edu/dataset/374 — 19.735 obs. a 10 min., consumo de electrodomésticos e iluminación, T1–T9, RH_1–RH_9 y meteorología exterior.",
    },
    {
        "name": "uci-occupancy",
        "description": "UCI Occupancy - predicción de ocupación de espacios",
    },
    {
        "name": "era5",
        "description": "ERA5 (ECMWF Reanalysis v5): https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels",
    },
    {
        "name": "lbnl-fdd",
        "description": "LBNL Fault Detection Dataset: https://faultdetection.lbl.gov/",
    },
]

# ramas: la rama main se crea automáticamente, solo añadimos las adicionales que necesitamos para las pipelines
BRANCHES = ["dev", "staging"]


# conexión
def create_client() -> LakeFSClient:
    """
    Crea y devuelve un cliente autenticado de lakeFS.
    """
    configuracion = lakefs_sdk.Configuration(
        host=LAKEFS_HOST,
        username=LAKEFS_ACCESS_KEY,
        password=LAKEFS_SECRET_KEY,
    )
    return LakeFSClient(configuration=configuracion)


# inicialización
def inicialize_lakefs():
    """
    Crea todos los repositorios y ramas del proyecto en función de la configuración
    """

    print("Conectando con lakeFS...")
    client = create_client()

    try:
        client.health_check_api.health_check()
        print("lakeFS disponible\n")
    except Exception as e:
        print(f"No se puede conectar con lakeFS: {e}")
        return

    # crear repositorios
    repos_api = client.repositories_api

    for dataset in DATASETS:
        nombre = dataset["name"]
        print(f"Creando repositorio: {nombre}")

        try:
            repos_api.create_repository(
                repository_creation=RepositoryCreation(
                    name=nombre,
                    storage_namespace=f"local://{nombre}",
                    default_branch="main",
                )
            )
            print(f"Repositorio '{nombre}' creado")

        except lakefs_sdk.exceptions.ApiException as e:
            if e.status == 409:
                # El código de error 409 indica que el repositorio ya existe
                print(f"Repositorio '{nombre}' creado previamente")
            else:
                print(f"Error creando '{nombre}': {e}")
                continue

        # crear ramas adicionales
        ramas_api = client.branches_api

        for rama in BRANCHES:
            try:
                ramas_api.create_branch(
                    repository=nombre,
                    branch_creation=BranchCreation(
                        name=rama,
                        source="main",
                    ),
                )
                print(f"Rama '{rama}' creada")

            except lakefs_sdk.exceptions.ApiException as e:
                if e.status == 409:
                    print(f"Rama '{rama}' creada previamente")
                else:
                    print(f"Error creando rama '{rama}': {e}")

        print("")

    # comprobaciones iniciales
    print("_" * 75)
    print("Verificación del estado final:\n")

    repos = repos_api.list_repositories().results
    for repo in repos:
        ramas = client.branches_api.list_branches(repository=repo.id).results
        nombres_ramas = [r.id for r in ramas]

        print(f"  {repo.id}")
        print(f"    Ramas: {', '.join(nombres_ramas)}")

    print("\nInicialización completada.")
    print(f"Acceso a lakeFS en la url: {LAKEFS_HOST}")


# ── Punto de entrada ──────────────────────────────────────────
if __name__ == "__main__":
    inicialize_lakefs()
