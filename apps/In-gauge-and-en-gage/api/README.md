# API - Caso D In-Gauge and En-Gage

API sencilla en **FastAPI** para predecir ocupación de aulas a partir de variables ambientales.

## Variables de entrada

- `IndoorTemperature`: temperatura interior del aula, en °C.
- `IndoorHumidity`: humedad relativa interior, en %.
- `IndoorCO2`: CO₂ interior, en ppm.
- `IndoorNoise`: ruido interior, en dB.

## Endpoints

- `GET /health`: comprueba que la API está activa.
- `GET /metadata`: devuelve metadata del modelo, métricas y rangos de entrada.
- `POST /predict`: predice ocupación.

Ejemplo:

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"IndoorTemperature":22.5,"IndoorHumidity":45,"IndoorCO2":850,"IndoorNoise":52}'
```

## Ejecución individual

```bash
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Ejecución con Docker Compose

Desde la raíz del repositorio:

```bash
docker compose -f apps/In-gauge-and-en-gage/docker-compose.yml up --build
```

La API queda disponible en `http://localhost:8000`.
