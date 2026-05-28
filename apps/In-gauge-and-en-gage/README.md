# Apps - Caso D (In-Gauge and En-Gage)

Esta carpeta agrupa las aplicaciones del Caso D:

- `api/`: API FastAPI para inferencia de ocupación.
- `frontend/`: frontend web estático servido con Nginx.

## Estructura

```text
apps/In-gauge-and-en-gage/
├── api/
│   ├── main.py
│   ├── requirements.txt
│   ├── model_metadata.json
│   ├── models/
│   ├── Dockerfile
│   └── README.md
├── frontend/
│   ├── index.html
│   ├── app.js
│   ├── styles.css
│   ├── nginx.conf
│   ├── Dockerfile
│   └── README.md
└── docker-compose.yml
```

## Ejecución conjunta con Docker Compose

Desde `apps/In-gauge-and-en-gage/`:

```powershell
cd .\apps\In-gauge-and-en-gage
docker compose up --build
```

Servicios:

- Frontend: `http://localhost:8080`
- API: `http://localhost:8000`

## Endpoints principales de la API

- `GET /health`
- `GET /metadata`
- `POST /predict`

Ejemplo de inferencia:

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"IndoorTemperature":22.5,"IndoorHumidity":45,"IndoorCO2":850,"IndoorNoise":52}'
```
