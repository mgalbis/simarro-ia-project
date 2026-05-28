# Dockerización de QABot-OTI

Esta versión añade una dockerización completa para ejecutar la aplicación web con dos contenedores:

- `backend`: API FastAPI expuesta internamente en el puerto `8000` y publicada también en `localhost:8000` para depuración.
- `frontend`: aplicación React/Vite compilada y servida por Nginx en `localhost:8080`.

El estado de la aplicación, la base SQLite y los artefactos generados se persisten en el volumen Docker `qabot_data`, montado sobre `/app/app/data` dentro del backend.

## Arranque rápido

Desde la raíz del proyecto:

```bash
docker compose up --build
```

Abrir la aplicación en:

```text
http://localhost:8080
```

El backend queda disponible para pruebas directas en:

```text
http://localhost:8000
```

Usuario inicial creado por la aplicación:

```text
usuario: admin
contraseña: admin
```

## Parada

```bash
docker compose down
```

Para eliminar también la base de datos y artefactos persistidos:

```bash
docker compose down -v
```

## Ficheros añadidos

```text
.dockerignore
backend/Dockerfile
frontend/Dockerfile
frontend/nginx.conf
docker-compose.yml
.env.example
DOCKER.md
```

## Cambios aplicados en el frontend

El frontend tenía llamadas directas a `http://localhost:8000`. Se han sustituido por una constante:

```js
export const API_BASE = import.meta.env.VITE_API_BASE_URL || "";
```

En Docker se deja vacía para que el navegador llame al mismo origen (`http://localhost:8080`) y Nginx actúe como reverse proxy hacia el backend. Esto evita problemas de CORS y permite desplegar frontend y backend detrás de un único endpoint HTTP.

Para desarrollo local sin Docker, puedes seguir usando dos procesos:

```bash
# Terminal 1
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2
cd frontend
npm install
npm run dev
```

El `vite.config.js` incluye proxy de desarrollo para las rutas del backend. Alternativamente, puedes crear un `.env.local` en `frontend/` con:

```text
VITE_API_BASE_URL=http://localhost:8000
```

## Nota técnica relevante

El fichero `backend/requirements.txt` venía codificado como UTF-16. Se ha normalizado a UTF-8 para que `pip install -r requirements.txt` funcione correctamente durante la construcción de la imagen.
