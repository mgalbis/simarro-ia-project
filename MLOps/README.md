## DOCKER
# Arrancar todo
docker compose up -d

# Ver el estado de los contenedores
docker compose ps

# Ver los logs de un servicio concreto (en tiempo real). p.e. mlflow
docker compose logs -f mlflow

# Parar todo
docker compose down

# Parar todo y borrar los volúmenes
docker compose down -v

# Reiniciar un proyecto en concreto. p.e. jupyterhub
docker compose restart jupyterhub

## Enlaces de interés
# LakeFS
https://docs.lakefs.io/latest/quickstart/index.html
# LakeFS webhooks
https://docs.lakefs.io/understand/use_cases/cicd_for_data/

# MlFlow
https://mlflow.org/docs/latest/genai/
https://mlflow.org/docs/3.10.1/api_reference/python_api/index.html

Jerarquía de un experimento MLflow:
Experimento (contenedor que agrupa todas las ejecuciones. tendrá multiples runs con las combinaciones de los parámetros)
    Run (ejecución)
        Parámetros (n_estimators, learning_rate, etc)
        Métricas (rmse=0.34, mae=0.21, r2=0.89, etc)
        Artefactos (el modelo serializado, gráficas, CSVs, etc)
        Tags (metadatos: quién lo ejecutó, versión del dato, etc)

# JupyterHub
https://jupyterhub.readthedocs.io/en/stable/#

# Levantar el entorno (en terminal de Windows)
    1- Levantar los contenedors
        docker compose up -d
    2- Comprobar que los tres contenedores están levantados correctamente
        docker compose ps
    3- Comprobar en el navegador que se accede a los servicios
        lakeFS: http://localhost:8001
        MLflow: http://localhost:5000
        JupyterHub: http://localhost:8000
    4- Crear y activar un entorno virtual aislado
        py -3.10 -m venv .venv
        .\.venv\Scripts\Activate.ps1
    5- Actualizar pip dentro del entorno virtual
        python -m pip install --upgrade pip
    6- Instalar las dependencias de Python dentro del entorno virtual
        python -m pip install -r requirements.txt
    7- Inicializar lakeFS
        python init_lakefs.py
    8- Inicializar MLFlow
        python init_mlflow.py

## Comprobaciones en servidor ITI

# Comprobar en el servidor si el puerto está escuchando después arrancar el servidor
ss -tlnp | grep 8080

# Comprobar desde Windows si el puerto es accesible
Test-NetConnection -ComputerName 10.151.18.176 -Port 8080

# Arrancar el servidor
Comprobar que la configuración de .env está ok
docker compose up -d
docker compose ps

# Comprobar que los servicios están accesibles desde fuera
http://10.151.18.176:8001
http://10.151.18.176:5000
http://10.151.18.176:8000
http://10.151.18.176:8080