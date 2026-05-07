# Runbook de instalación y ejecución

## 1. Requisitos previos

Sistema recomendado:

- Ubuntu 22.04 LTS o superior.
- Python 3.11.
- Docker y Docker Compose.
- Git.
- 8 GB de RAM mínimo.
- 15 GB libres en disco.

Comprobar versiones:

```bash
git --version
python3 --version
docker --version
docker compose version
```

## 2. Clonado del repositorio

```bash
git clone <URL_DEL_REPOSITORIO> simarro-ia-project
cd simarro-ia-project
```

## 3. Variables de entorno

Copiar el fichero de ejemplo:

```bash
cp .env.example .env
```

Variables previstas:

```bash
MLFLOW_TRACKING_URI=http://localhost:5000
INFLUXDB_URL=http://localhost:8086
INFLUXDB_ORG=simarro
INFLUXDB_BUCKET=occupancy
INFLUXDB_TOKEN=change-me
LAKEFS_ENDPOINT=http://localhost:8000
LAKEFS_ACCESS_KEY_ID=change-me
LAKEFS_SECRET_ACCESS_KEY=change-me
```

No subir `.env` a Git.

## 4. Instalación de dependencias Python

Crear entorno virtual:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Comprobar instalación:

```bash
python -c "import pandas, sklearn, mlflow; print('OK')"
```

## 5. Arranque de servicios

Arrancar infraestructura:

```bash
docker compose up -d
```

Comprobar contenedores:

```bash
docker compose ps
```

Servicios esperados:

| Servicio | URL |
|---|---|
| MLflow | http://localhost:5000 |
| lakeFS | http://localhost:8000 |
| InfluxDB | http://localhost:8086 |
| Grafana | http://localhost:3000 |
| Streamlit | http://localhost:8501 |

## 6. Preparación de datos

Descargar o colocar el dataset UCI Occupancy en la carpeta local correspondiente.

Estructura esperada:

```text
data/
├── raw/
│   └── occupancy/
│       ├── datatraining.txt
│       ├── datatest.txt
│       └── datatest2.txt
└── processed/
```

Ejecutar preparación:

```bash
python -m src.data.prepare_occupancy
```

Ejecutar validación de calidad:

```bash
python -m src.data.validate_quality
```

Salida esperada:

```text
reports/data_quality_occupancy.csv
data/processed/occupancy_train.csv
data/processed/occupancy_test1.csv
data/processed/occupancy_test2.csv
```

## 7. Versionado en lakeFS

Crear repositorio de datos:

```bash
python -m src.mlops.lakefs_utils create-repo uci_occupancy
```

Subir dataset procesado:

```bash
python -m src.mlops.lakefs_utils upload data/processed/occupancy_train.csv uci_occupancy/main/processed/occupancy_train.csv
```

Crear tag:

```bash
python -m src.mlops.lakefs_utils tag uci_occupancy main uci_occupancy_clean_v1
```

## 8. Entrenamiento de modelos

Entrenar baseline:

```bash
python -m src.models.baseline
```

Entrenar modelos principales:

```bash
python -m src.models.train_logistic_regression
python -m src.models.train_random_forest
python -m src.models.train_xgboost
python -m src.models.train_svm
```

Cada entrenamiento debe registrar en MLflow:

- Parámetros.
- Métricas.
- Modelo.
- Matriz de confusión.
- Curva ROC si aplica.
- Tag lakeFS.
- Commit Git.

## 9. Escritura en InfluxDB

Simular envío de datos:

```bash
python -m src.ingestion.simulate_stream
```

Escribir predicciones:

```bash
python -m src.ingestion.write_influx
```

## 10. Grafana

Acceder a:

```text
http://localhost:3000
```

Paneles esperados:

- CO₂ temporal.
- Temperatura y humedad.
- Ocupación real vs predicha.
- Índice IAQ.
- Alertas de CO₂ elevado.

## 11. QABot

Arrancar API demo:

```bash
uvicorn src.sample_app.main:app --reload --port 8001
```

Ejecutar QABot por CLI:

```bash
python -m src.qabot.router --input examples/openapi_sample.yaml
```

Ejecutar pruebas generadas:

```bash
python -m src.qabot.executor
```

Arrancar UI:

```bash
streamlit run src/ui/app.py
```

## 12. Tests del repositorio

```bash
pytest
```

Calidad de código:

```bash
black src tests
flake8 src tests
```

## 13. Parada de servicios

```bash
docker compose down
```

Eliminar volúmenes si se desea empezar desde cero:

```bash
docker compose down -v
```

## 14. Troubleshooting

### MLflow no abre

Comprobar contenedor:

```bash
docker compose logs mlflow
```

Comprobar puerto 5000:

```bash
lsof -i :5000
```

### Grafana no muestra datos

Comprobar que InfluxDB tiene mediciones:

```bash
docker compose logs influxdb
```

Revisar token, bucket y organización en `.env`.

### QABot genera tests pero fallan por conexión

Comprobar que la API demo está levantada:

```bash
curl http://localhost:8001/health
```

### Los notebooks no encuentran módulos `src`

Ejecutar desde la raíz del repositorio:

```bash
export PYTHONPATH=$PWD
jupyter notebook
```

## 15. Criterio de éxito

El entorno se considera reproducible si una persona externa puede:

1. Clonar el repositorio.
2. Levantar servicios.
3. Preparar datos.
4. Entrenar modelos.
5. Ver runs en MLflow.
6. Ver datasets versionados en lakeFS.
7. Ver dashboard en Grafana.
8. Ejecutar QABot.
9. Generar un informe de pruebas.
