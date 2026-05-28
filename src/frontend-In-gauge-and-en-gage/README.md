# Frontend - Caso D In-Gauge and En-Gage

Frontend estático servido con **Nginx**. Simula visualmente una sala de escuela y permite modificar los parámetros usados por el modelo.

## Funcionalidades

- Inputs visuales tipo slider para temperatura, humedad, CO₂ y ruido.
- Información de cada parámetro, unidad y rango aceptable orientativo.
- Botón **Predecir ocupación** conectado a la API FastAPI.
- Cambio visual del aula cuando el modelo predice ocupación.

## Ejecución

Desde la raíz `develop/`:

```bash
docker compose up --build
```

Abrir:

```text
http://localhost:8080
```
