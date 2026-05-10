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

# MlFlow
https://mlflow.org/docs/latest/genai/

Jerarquía de un experimento MLflow:
Experimento (contenedor que agrupa todas las ejecuciones. tendrá multiples runs con las combinaciones de los parámetros)
    Run (ejecución)
        Parámetros (n_estimators, learning_rate, etc)
        Métricas (rmse=0.34, mae=0.21, r2=0.89, etc)
        Artefactos (el modelo serializado, gráficas, CSVs, etc)
        Tags (metadatos: quién lo ejecutó, versión del dato, etc)

# JupyterHub
https://jupyterhub.readthedocs.io/en/stable/#