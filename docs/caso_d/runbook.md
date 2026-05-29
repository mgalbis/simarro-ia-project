# Runbook - Caso D

## Objetivo

Este runbook describe cómo ejecutar y validar el **Caso D** (predicción de ocupación en aulas) en local.

Incluye:

- inferencia batch (UCI e In-Gauge and En-Gage),
- despliegue de API + frontend con Docker Compose,
- comprobaciones básicas de salud.

## Requisitos previos

- Docker y Docker Compose instalados.
- Python 3.11+ para ejecución local de scripts de inferencia.
- Dependencias de Python instaladas en el entorno local para los scripts batch (`pandas`, `joblib`, etc.).

## Estructura relevante

```text
docs/caso_d/
  README.md
  arquitectura.md
  runbook.md

src/cased/uci/inference/
src/cased/In-gauge-and-en-gage/inference/

apps/In-gauge-and-en-gage/
  docker-compose.yml
```

## Ejecución de inferencia batch

### 1) UCI Occupancy Detection

```shell
cd ./src/cased/uci/inference
python ./infer_uci_occupancy_json.py
```

Salida esperada: resultados por consola y generación de `inference_results.csv` (si aplica en el flujo local).

### 2) In-Gauge and En-Gage

```shell
cd ./src/cased/In-gauge-and-en-gage/inference
python ./infer_classroom_occupancy_json.py
```

Salida esperada: fichero `inference_results_classroom.csv`.

## Despliegue API + frontend (Docker)

Desde la raíz del repositorio:

```shell
docker compose -f ./apps/In-gauge-and-en-gage/docker-compose.yml up --build
```

Servicios:

- Frontend: `http://localhost:8080`
- API: `http://localhost:8000`
- Swagger API: `http://localhost:8000/docs`

Para detener:

```shell
docker compose -f ./apps/In-gauge-and-en-gage/docker-compose.yml down
```

## Comprobaciones operativas

### Healthcheck de API

- Unix:
```shell
curl http://localhost:8000/health
```

- Powershell:
```powershell
Invoke-RestMethod -Method Get -Uri "http://localhost:8000/health"
```

Respuesta esperada (aprox):

```json
{"status":"ok","model":"LogisticRegression"}
```

### Predicción de ejemplo

- Unix:
```shell
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d "{\"IndoorTemperature\":22.5,\"IndoorHumidity\":45,\"IndoorCO2\":850,\"IndoorNoise\":52}"
```

- Powershell:
```powershell
$body = @{
  IndoorTemperature = 22.5
  IndoorHumidity    = 45
  IndoorCO2         = 850
  IndoorNoise       = 52
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri "http://localhost:8000/predict" -ContentType "application/json" -Body $body
```

## Troubleshooting rápido

### El puerto 8000 o 8080 está ocupado

Detener contenedores previos:

```shell
docker compose -f ./apps/In-gauge-and-en-gage/docker-compose.yml down
```


### Error de modelo no encontrado en API

Verificar que existe:

`apps/In-gauge-and-en-gage/api/models/best_sensorica_ambiental_LogisticRegression.joblib`

### Error en scripts batch por dependencias

Instalar dependencias en el entorno activo y reintentar:

```shell
pip install -r ./src/cased/In-gauge-and-en-gage/inference/requirements.txt
```
