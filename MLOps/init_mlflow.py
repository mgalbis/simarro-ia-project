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
        "nombre": "CasoB_UCI_",
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
def verificar_conexion(client: MlflowClient) -> bool:
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
def crear_experimentos(client: MlflowClient):
    """
    Creamos los experimentos del proyecto si no existen.
    """
    print("Crear experimentos en MLflow...\n")

    for exp in EXPERIMENTOS:
        nombre = exp["nombre"]

        # Comprobamos si el experimento ya existe
        # get_experiment_by_name devuelve None si no existe
        existente = client.get_experiment_by_name(nombre)

        # Si el experimentos ya existe mostramos un mensaje y pasamos al siguiente
        if existente:
            print(f"  Experimento '{nombre}' ha sido creado anteriormente")
            continue

        # Si no ha sido creado lo creamos y mostramos info por pantalla
        experiment_id = client.create_experiment(name=nombre, tags=exp["tags"])

        print(f"  Experimento '{nombre}' creado con id {experiment_id})")
        print(f"    Caso: {exp['tags']['caso_uso']}")
        print(f"    Dataset: {exp['tags']['dataset']}")
        print()
