import os

# configuración de Red
c.JupyterHub.ip = "0.0.0.0"  # para que sea accesible desde fuera del contenedor
c.JupyterHub.port = 8000  # puerto de JupyterHub

# configuración de autenticación
# TODO: para una primera aproximación usaremos PAM, que es el sistema de autenticación local de Linux.
#   Esto nos permitirá crear usuarios locales dentro del contenedor y autenticarlos con sus contraseñas.
#   autenticador simple con contraseñas locales (PAM).
#   Cuando integremos con la infraestructura de ITI lo reemplazaremos por otro sistema de autenticación
c.JupyterHub.authenticator_class = "pam"
c.LocalAuthenticator.create_system_users = True
c.Authenticator.delete_invalid_users = True

# usuarios permitidos
# TODO: para esta primera aproximación, los usuarios serán los casos de uso del proyecto
c.Authenticator.allowed_users = {
    "admin",
    "casoA",
    "casoB",
    "casoC",
    "casoD",
    "casoE",
    "casoF",
    "casoG",
    "casoH",
    "casoI",
    "casoJ",
    "casoK",
}

# usuarios con permisos de administración
c.Authenticator.admin_users = {"admin"}

# spawner: abre JupyterLab en lugar de la interfaz de Jupyter
c.Spawner.default_url = "/lab"
c.Spawner.start_timeout = (
    60  # TODO: 60 es el valor por defecto, hay comprobar que sea suficiente
)

# configuracion de entorno para los notebooks (para todos los usuarios)
c.Spawner.environment = {
    "MLFLOW_TRACKING_URI": "http://mlflow:5000",  # dirección del servidor mlflow para registrar experimentos
    "LAKEFS_ENDPOINT": "http://lakefs:8000",  # conexión con lakefs para acceder a los datasets versionados
    "LAKEFS_ACCESS_KEY_ID": os.environ.get("LAKEFS_ACCESS_KEY_ID", ""),
    "LAKEFS_SECRET_ACCESS_KEY": os.environ.get("LAKEFS_SECRET_ACCESS_KEY", ""),
    "PROJECT_NAME": "simarro",
}

# configuración de los recursos
# TODO: aunque en esta primera aproximación no indiquemos límites, cuando nos integremos con la infraestructura de ITI sí que tendremos que configurar
# límites para evitar que un usuario consuma todos los recursos del sistema.
# en este ejemplo limitamos a 2GB de RAM por usuario y 2 núcleos de CPU
# c.Spawner.mem_limit = '2G'
# c.Spawner.cpu_limit = 2.0

# configuración de almacenamiento
c.Spawner.notebook_dir = "/home/{username}"

# configuraciones adicionales
c.JupyterHub.hub_name = "IES Simarro | Centinela+"
