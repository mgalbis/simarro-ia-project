# Runbook de Instalación y Configuración - QA Bot

## Objetivo

Este documento describe el procedimiento completo para instalar, configurar y ejecutar la plataforma QA Bot desde cero en un entorno local.

Incluye backend FastAPI, frontend React y despliegue mediante Docker Compose.

El objetivo es que cualquier persona externa al proyecto pueda reproducir e implementar el sistema de extremo a extremo sin asistencia adicional.

---

## Sistema operativo recomendado

- Ubuntu 22.04 LTS o superior (recomendado)
- Windows 10 / 11 (PowerShell o WSL2)
- macOS 13+

---

## Requisitos previos

### Software requerido

- Python 3.11+
- Node.js 20+
- npm 10+
- Docker Desktop 24+
- Git 2.40+

---

## Clonado del repositorio

```bash
git clone <URL_DEL_REPOSITORIO>
cd <NOMBRE_DEL_PROYECTO>
```

---

## Estructura esperada del proyecto

```
QABOT/
├── backend/
├── frontend/
├── docs/
├── docker-compose.yml
└── README.md
```

---

# BACKEND (FastAPI)

## Instalación

```bash
cd backend
```

---

## Crear entorno virtual

### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

### Windows (PowerShell)

```powershell
python -m venv venv
venv\Scripts\activate
```

---

## Instalación de dependencias

```bash
pip install -r requirements.txt
```

---

## Nota sobre persistencia

Al iniciar el servidor por primera vez, el sistema inicializa automáticamente la base de datos SQLite.

No se requieren migraciones ni scripts adicionales.

---

## Ejecución del backend

```bash
uvicorn app.main:app --reload
```

---

## URLs backend

- API: http://localhost:8000  
- Swagger UI: http://localhost:8000/docs  

---

# FRONTEND (React + Vite)

## Instalación

```bash
cd frontend
npm install
```

---

## Ejecución frontend

```bash
npm run dev
```

---

## URL frontend

- http://localhost:5173  

---

# DESPLIEGUE CON DOCKER

## Levantar sistema completo

Para ejecutar todo el sistema sin instalación local:

```bash
docker compose up --build
```

---

## Parar servicios

```bash
docker compose down
```

---

# SERVICIOS DISPONIBLES

| Servicio | URL local | Docker |
|----------|----------|--------|
| Frontend | http://localhost:5173 | http://localhost:5173 |
| Backend API | http://localhost:8000 | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs | http://localhost:8000/docs |

---

# TROUBLESHOOTING

## Puerto 8000 ocupado

```bash
uvicorn app.main:app --port 8001
```

Si se cambia el puerto, actualizar la URL del frontend.

---

## Error en dependencias Python

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

## node_modules corrupto

### Linux / macOS

```bash
rm -rf node_modules package-lock.json
npm install
```

### Windows

```powershell
rmdir /s /q node_modules
del package-lock.json
npm install
```

---

## Docker no arranca

```bash
docker system prune -a
docker compose up --build
```

---

# LOGS

## Backend

Logs visibles en terminal de Uvicorn o Docker logs.

## Frontend

Logs visibles en consola del navegador (F12).