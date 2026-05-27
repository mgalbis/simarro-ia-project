import os
import mlflow
from mlflow.tracking import MlflowClient

# configuración
MLFLOW_URI = os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5000")

mlflow.set_tracking_uri(MLFLOW_URI)

# Definición de experimentos
# Por convención tendrán la npomenclatura con formato: [caso_uso]_[dataset]_[algoritmo]_[fecha]
# No incluimos aquí ni la fecha ni el algoritmo porque estos son los experimentos base
EXPERIMENTS = [
    {
        "nombre": "CasoB_UCI",
        "descripcion": "Predicción de consumo energético",
        "equipo": "caso_b",
        "dataset": "uci-appliances",
        "tags": {
            "caso_uso": "CasoB",
            "dataset": "uci_appliances",
            "proyecto": "simarro",
        },
    },
    {
        "nombre": "CasoC_ingauge",
        "descripcion": "Detección de anomalías en sistemas HVAC",
        "equipo": "caso_c",
        "dataset": "ingauge",
        "tags": {
            "caso_uso": "CasoC",
            "dataset": "ingauge",
            "proyecto": "simarro",
        },
    },
    {
        "nombre": "CasoD_bdg2",
        "descripcion": "Predicción de ocupación de espacios",
        "equipo": "caso_d",
        "dataset": "bdg2",
        "tags": {
            "caso_uso": "CasoD",
            "dataset": "bdg2",
            "proyecto": "simarro",
        },
    },
]


# Verificación de conexión al servior mlflow
def verify_conexion(client: MlflowClient) -> bool:
    """
    Comprueba el estado del servidor mlflow
    """
    try:
        # lista los experimentos y da un error es porque no estamos conectados al servidor mlflow
        client.search_experiments()
        return True
    except Exception as e:
        print(f"No se ha podido conectar con MLflow en {MLFLOW_URI}")
        print(f"  Error: {e}")
        return False


# Creación de experimentos
def create_experiments(client: MlflowClient):
    """
    Creamos los experimentos del proyecto si no existen.
    """
    print("Crear experimentos en MLflow...\n")

    for exp in EXPERIMENTS:
        nombre = exp["nombre"]

        # Comprobamos si el experimento ya existe
        # get_experiment_by_name devuelve None si no existe
        isExperiment = client.get_experiment_by_name(nombre)

        # Si el experimentos ya existe mostramos un mensaje y pasamos al siguiente
        if isExperiment:
            print(f"  Experimento '{nombre}' ha sido creado anteriormente")
            continue

        # Si no ha sido creado lo creamos y mostramos info por pantalla
        experiment_id = client.create_experiment(name=nombre, tags=exp["tags"])

        print(f"  Experimento '{nombre}' creado con id {experiment_id})")
        print(f"    Caso: {exp['tags']['caso_uso']}")
        print(f"    Dataset: {exp['tags']['dataset']}")
        print()


# Verificación de modelo base ────────────────────
def create_models_registry(client: MlflowClient):
    """
    Registra los nombres de modelos en el Model Registry.
    Con esto reservamos el nombre y establecemos la convención antes de que los demás equipos empiecen a trabajar con el entorno
    """

    print("Registrando los nombres de los modelos en Model Registry...\n")

    modelos = [
        ("simarro-caso-b", "Modelo de predicción de consumo energético"),
        ("simarro-caso-c", "Modelo de detección de anomalías HVAC"),
        ("simarro-caso-d", "Modelo de predicción de ocupación"),
    ]

    for nombre_modelo, descripcion in modelos:
        try:
            client.create_registered_model(
                name=nombre_modelo,
                description=descripcion,
                tags={"proyecto": "simarro"},
            )
            print(f"Modelo registrado: '{nombre_modelo}'")

        except mlflow.exceptions.MlflowException as e:
            # Si existe el modelo devuelve RESOURCE_ALREADY_EXISTS
            if "RESOURCE_ALREADY_EXISTS" in str(e):
                print(f"  El modelo '{nombre_modelo}' ya existe")
            else:
                print(f"  Error registrando '{nombre_modelo}': {e}")


# Resumen
def show_summary(client: MlflowClient):
    """
    Muestra el estado final de experimentos y de modelos registrados
    """
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


if __name__ == "__main__":
    print(f"Conectando con MLflow en {MLFLOW_URI}...\n")

    client = MlflowClient(tracking_uri=MLFLOW_URI)

    if not verify_conexion(client):
        exit(1)

    create_experiments(client)
    create_models_registry(client)
    show_summary(client)

    print("\nMLFlow inicializado correctamente")
