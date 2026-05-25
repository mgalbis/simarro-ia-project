"""Configuración de JupyterHub para el entorno MLOps del proyecto."""

import json
import os

from traitlets.config import get_config

c = get_config()

# configuración de Red
c.JupyterHub.ip = "0.0.0.0"  # para que sea accesible desde fuera del contenedor
c.JupyterHub.port = 8000  # puerto de JupyterHub
c.JupyterHub.base_url = "/jupyter/"

# configuración de autenticación
# TODO: para una primera aproximación usaremos PAM, que es el sistema de
#   autenticación local de Linux. Esto nos permitirá crear usuarios locales dentro
#   del contenedor y autenticarlos con sus contraseñas.
#   Cuando integremos con la infraestructura de ITI lo reemplazaremos por otro
#   sistema de autenticación
c.JupyterHub.authenticator_class = "pam"
c.LocalAuthenticator.create_system_users = True
c.Authenticator.delete_invalid_users = True

# usuarios permitidos (dinámicos desde cases_config.json)
CASES_CONFIG_PATH = os.environ.get("CASES_CONFIG_PATH", "/init/cases_config.json")
ADMIN_USER = os.environ.get("JUPYTERHUB_ADMIN", "admin")


def _load_case_users(config_path: str):
    """Carga usuarios permitidos desde el bloque ``cases`` del JSON."""
    users = {ADMIN_USER.lower()}
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        cases = data.get("cases", {})
        if isinstance(cases, dict):
            for case_id in cases.keys():
                case_text = str(case_id).strip().lower()
                if case_text:
                    users.add(f"caso{case_text}")
        else:
            print(f"[WARN] Campo 'cases' no es un objeto en {config_path}")
    except Exception as exc:
        print(f"[WARN] No se pudo cargar usuarios desde {config_path}: {exc}")
    return users


c.Authenticator.allowed_users = _load_case_users(CASES_CONFIG_PATH)

# usuarios con permisos de administración
c.Authenticator.admin_users = {ADMIN_USER.lower()}

# spawner: abre JupyterLab en lugar de la interfaz de Jupyter
c.Spawner.default_url = "/lab"
c.Spawner.start_timeout = (
    60  # TODO: 60 es el valor por defecto, hay comprobar que sea suficiente
)

# configuracion de entorno para los notebooks (para todos los usuarios)
c.Spawner.environment = {
    "MLFLOW_TRACKING_URI": os.environ.get(
        "MLFLOW_TRACKING_URI",
        "http://mlflow:5000/mlflow",
    ),  # direccion del servidor mlflow para registrar experimentos
    "LAKEFS_ENDPOINT": "http://lakefs:8000",
    "LAKEFS_ACCESS_KEY_ID": os.environ.get("LAKEFS_ACCESS_KEY_ID", ""),
    "LAKEFS_SECRET_ACCESS_KEY": os.environ.get("LAKEFS_SECRET_ACCESS_KEY", ""),
    "PROJECT_NAME": "simarro",
}

# configuración de los recursos
# TODO: aunque en esta primera aproximación no indiquemos límites, cuando
#   nos integremos con la infraestructura de ITI sí que tendremos que configurar
#   límites para evitar que un usuario consuma todos los recursos del sistema.
#   en este ejemplo limitamos a 2GB de RAM por usuario y 2 núcleos de CPU
c.Spawner.mem_limit = "2G"
c.Spawner.cpu_limit = 2.0

# configuración de almacenamiento
c.Spawner.notebook_dir = "/home/{username}"
