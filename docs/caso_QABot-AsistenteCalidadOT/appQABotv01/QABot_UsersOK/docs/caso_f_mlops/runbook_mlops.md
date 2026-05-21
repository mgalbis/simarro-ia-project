# Runbook MLOps

## Objetivo

Arrancar y validar la infraestructura MLOps del proyecto.

## Servicios incluidos

- MLflow
- lakeFS
- Postgres
- MinIO, si se usa como artifact store

## Arranque

```bash
cp .env.example .env
docker compose --profile mlops up -d
```

## Inicialización

```bash
python scripts/mlops/create_lakefs_repos.py
python scripts/mlops/version_captia_schema.py
python scripts/mlops/create_mlflow_experiments.py
```

## Demo de experimento

```bash
python scripts/mlops/run_demo_experiment.py
```

## Validación

```bash
python scripts/mlops/check_mlops_integrity.py
```

## Parada

```bash
docker compose --profile mlops down
```

## Limpieza completa

```bash
docker compose --profile mlops down -v
```

## Variables de entorno relevantes

```text
MLFLOW_TRACKING_URI
MLFLOW_ARTIFACT_ROOT
LAKEFS_ENDPOINT
LAKEFS_ACCESS_KEY_ID
LAKEFS_SECRET_ACCESS_KEY
GIT_COMMIT
```

## Resultado esperado

Al finalizar la demo debe existir:

- un experimento en MLflow;
- al menos un run;
- métricas registradas;
- parámetros registrados;
- artefactos subidos;
- modelo serializado;
- tags de Git, lakeFS y schema CAPTIA;
- validación de integridad correcta.
