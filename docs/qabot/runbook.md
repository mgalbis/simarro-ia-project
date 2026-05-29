# Runbook de Instalación y Configuración - QA Bot

## Objetivo

Este documento describe el procedimiento completo para instalar, configurar y ejecutar la plataforma QA Bot desde cero
en un entorno local.

Incluye backend FastAPI, frontend React y despliegue mediante Docker Compose.

El objetivo es que cualquier persona externa al proyecto pueda reproducir e implementar el sistema de extremo a extremo
sin asistencia adicional.

---

## Requisitos previos

### Software requerido

- Python 3.11+
- Node.js 20+
- npm 10+
- Docker
- Git

---

## Clonado del repositorio

```bash
git clone <URL_DEL_REPOSITORIO>
cd <NOMBRE_DEL_REPOSITORIO>
```

---

Estructura relevante:

```text
simarro-ia-project/
└── apps/
    └── qabot/
        ├── backend/
        ├── frontend/
        ├── docker-compose.yml
        └── README-QABOT.md
```

---

## Ejecucion local (desarrollo)

### 1) Backend (FastAPI)

```bash
cd apps/qabot/backend
```

Crear entorno virtual:

Linux / macOS:

```bash
python3 -m venv venv
source venv/bin/activate
```

Windows (PowerShell):

```powershell
python -m venv venv
.\venv\Scripts\activate
```

Instalar dependencias y arrancar:

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

URLs backend:

- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs

Nota: al iniciar por primera vez, se crea automaticamente la base SQLite en `apps/qabot/backend/data/qabot_state.db`.

### 2) Frontend (React + Vite)

```bash
cd apps/qabot/frontend
npm install
npm run dev
```

URL frontend en desarrollo:

- http://localhost:5173

---

## Despliegue con Docker

Desde `apps/qabot`:

```bash
cd apps/qabot
docker compose up --build -d
```

Parar servicios:

```bash
docker compose down
```

---

## Servicios disponibles

| Servicio | Local (dev) | Docker |
|----------|-------------|--------|
| Frontend | http://localhost:5173 | http://localhost:8080 |
| Backend API | http://localhost:8000 | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs | http://localhost:8000/docs |

---

## Troubleshooting

### Puerto 8000 ocupado (backend)

```bash
uvicorn app.main:app --reload --port 8001
```

Importante: el frontend actual llama a `http://localhost:8000` de forma explicita.  
Si cambias el puerto backend, debes ajustar esas URLs en el frontend.

### Error en dependencias Python

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### `node_modules` corrupto

Linux / macOS:

```bash
rm -rf node_modules package-lock.json
npm install
```

Windows (PowerShell):

```powershell
Remove-Item -Recurse -Force node_modules
Remove-Item -Force package-lock.json
npm install
```

### Docker no arranca

```bash
cd apps/qabot
docker compose down
docker compose up --build
```

Opcional (mas agresivo, elimina recursos no usados):

```bash
docker system prune -a
```

---

## Logs

Backend local:

- logs en la terminal de Uvicorn

Docker backend:

```bash
docker logs -f qabot-backend
```

Docker frontend:

```bash
docker logs -f qabot-frontend
```

Frontend local:

- logs en terminal de Vite y en consola del navegador (F12)
