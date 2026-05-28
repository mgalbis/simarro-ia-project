# Runbook general

## Objetivo

Reproducir el entorno local del repositorio `simarro-ia-project` desde cero.

## Requisitos

- Git
- Docker
- Docker Compose
- Python 3.11+
- Make

## Preparación inicial

```bash
git clone <URL_DEL_REPOSITORIO>
cd simarro-ia-project
cp .env.example .env
```

Editar `.env` solo si los puertos o credenciales locales cambian.

## Instalación local sin Docker

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## Arranque por perfiles

El proyecto debe evitar levantar todos los servicios a la vez. Usar perfiles.

### MLOps

```bash
docker compose --profile mlops up -d
```

### Datos y visualización

```bash
docker compose --profile data up -d
```

### Notebooks

```bash
docker compose --profile notebooks up -d
```

### Demo completa

```bash
docker compose --profile mlops --profile data up -d
```

## Comandos Make recomendados

```bash
make mlops-up
make mlops-init
make mlops-demo
make mlops-check
make test
```

## Parada

```bash
docker compose down
```

Para borrar volúmenes locales:

```bash
docker compose down -v
```

## Validaciones mínimas

```bash
python scripts/mlops/check_mlops_integrity.py
pytest tests
```

## Troubleshooting

### Docker consume demasiada RAM

No usar:

```bash
docker compose up -d --build
```

Usar perfiles:

```bash
docker compose --profile mlops up -d
```

### MLflow no responde

Verificar contenedor:

```bash
docker compose ps
```

Ver logs:

```bash
docker compose logs mlflow
```

### lakeFS no responde

Verificar variables en `.env` y logs:

```bash
docker compose logs lakefs
```

### Python no encuentra el paquete `simarro`

Instalar el paquete en modo editable:

```bash
pip install -e .
```
