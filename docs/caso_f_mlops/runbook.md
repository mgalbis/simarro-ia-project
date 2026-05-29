# Runbook - Caso F MLOps

## Objetivo

Este runbook describe cómo preparar, arrancar, validar y detener la infraestructura MLOps del proyecto.

Stack incluido:

- `aclserver-db` (PostgreSQL),
- `aclserver`,
- `lakefs`,
- `mlflow`,
- `jupyterhub`,
- `nginx` (entrada única HTTPS).

## Requisitos previos

- Docker y Docker Compose instalados.
- Fichero `.env` en la raíz del repositorio.
- Puertos libres `80` y `443` para Nginx.

## 1) Preparar entorno

Si no existe `.env`, créalo a partir de `.env.example`.

- Unix:
```shell
cp .env.example .env
```

- Powershell:
```powershell
Copy-Item .env.example .env
```

Variables mínimas esperadas en `.env`:

- `JUPYTERHUB_IMAGE`
- `PIP_TOOLS_VERSION`
- `LAKEFS_ACCESS_KEY_ID`
- `LAKEFS_SECRET_ACCESS_KEY`
- `LAKEFS_SECRET_KEY`
- `DEFAULT_USER_PASSWORD`

## 2) Inicialización (requirements + certificados TLS)

```shell
make init
```

## 3) Construir imágenes del stack

```shell
make build
```

## 4) Arrancar infraestructura MLOps

```shell
make start
```

## 5) Validación operativa

### Estado de contenedores

```shell
docker compose ps
```

### Accesos esperados (vía Nginx)

- `https://localhost/jupyter/`
- `https://localhost/mlflow/`
- `https://localhost/lakefs/`

### Comprobación HTTP rápida

`curl` con `-k` para aceptar el certificado local autofirmado.

- Unix:
```shell
curl -k -I https://localhost/jupyter/
curl -k -I https://localhost/mlflow/
curl -k -I https://localhost/lakefs/
```

- Powershell:
```powershell
Invoke-WebRequest -Uri "https://localhost/jupyter/" -SkipCertificateCheck -Method Head
Invoke-WebRequest -Uri "https://localhost/mlflow/" -SkipCertificateCheck -Method Head
Invoke-WebRequest -Uri "https://localhost/lakefs/" -SkipCertificateCheck -Method Head
```

## 6) Logs y diagnóstico

### Logs globales del stack

```shell
docker compose logs -f
```

### Logs de un servicio concreto

```shell
docker compose logs -f lakefs
docker compose logs -f mlflow
docker compose logs -f jupyterhub
```

## 7) Parada controlada

### Parar y mantener volúmenes

```shell
docker compose down
```

o mediante objetivos:

```shell
make stop
```

### Parar y eliminar volúmenes

```shell
docker compose down --volumes
```

o mediante objetivos:

```shell
make destroy
```

## Troubleshooting rápido

### Error: falta `.env`

- Unix:
```shell
cp .env.example .env
```

- Powershell:
```powershell
Copy-Item .env.example .env
```

### Error de certificado TLS en navegador o `curl`

1. Regenerar certificados con `init`.
2. En pruebas por terminal usar `curl -k`.

### Puertos `80/443` en uso

```shell
docker compose down
```

y liberar los puertos ocupados antes de relanzar `start`.

