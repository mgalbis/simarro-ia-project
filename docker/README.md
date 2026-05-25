# Docker Stack del Proyecto

Este directorio contiene la infraestructura local completa del proyecto MLOps:
lakeFS (versionado de datos), MLflow (tracking y model registry), JupyterHub
(entorno de trabajo), ACL server (autorización RBAC de lakeFS) y Nginx
(punto de entrada único).

## Vista general

Flujo principal:

1. `aclserver-db` levanta Postgres para políticas/identidades ACL.
2. `aclserver` expone API de autorización para lakeFS.
3. `lakefs` arranca y ejecuta `init_lakefs.sh` para bootstrap inicial.
4. `mlflow` arranca servidor y ejecuta `init_mlflow.py` para bootstrap inicial.
5. `jupyterhub` crea usuarios locales y arranca el hub.
6. `nginx` publica todo por `http://localhost/` y enruta por prefijos.

## Servicios (qué hace cada uno y por qué)

### `aclserver-db` (PostgreSQL)
- **Qué hace:** almacena datos de autenticación/autorización del ACL server.
- **Por qué existe:** desacopla RBAC de lakeFS en un backend persistente y transaccional.
- **Persistencia:** volumen `aclserver-db-data`.

### `aclserver`
- **Qué hace:** servicio ACL de lakeFS (`/api/v1`) para usuarios, grupos y políticas.
- **Por qué existe:** permite gestión de permisos por caso (`casoX`) y control fino de acceso.
- **Build:** `docker/aclserver/Dockerfile` compila el binario `acl` desde el repo de lakeFS.

### `lakefs`
- **Qué hace:** servidor de versionado de datos (repos, ramas, tags, commits).
- **Por qué existe:** habilita flujo tipo Git para datasets y trazabilidad de transformaciones.
- **Bootstrap:** `docker/lakefs/entrypoint.sh` arranca lakeFS y ejecuta `init_lakefs.sh`.
- **Comportamiento actual de init (estricto y create-only):**
  - crea usuarios/repos que faltan,
  - no modifica usuarios/repos existentes,
  - falla ante errores en vez de degradar silenciosamente.
- **Persistencia:** volumen `lakefs-data`.

### `mlflow`
- **Qué hace:** tracking server + artefactos + metadatos de experimentos/modelos.
- **Por qué existe:** centraliza runs, métricas, parámetros y modelos registrados.
- **Bootstrap:** `docker/mlflow/entrypoint.sh` inicia MLflow y ejecuta
  `init_mlflow.py` para crear/actualizar metadata desde `cases_config.json`.
- **Persistencia:** volumen `mlflow-data`.

### `jupyterhub`
- **Qué hace:** portal multiusuario de notebooks/JupyterLab.
- **Por qué existe:** entorno operativo para desarrollo y ejecución de notebooks MLOps.
- **Bootstrap:** `docker/jupyterhub/entrypoint.sh` crea usuarios locales (`admin`, `casoX`)
  y arranca JupyterHub con `docker/jupyterhub/config.py`.
- **Integración:** inyecta `MLFLOW_TRACKING_URI` y credenciales/endpoint de lakeFS en el entorno.
- **Persistencia:** volumen `jupyterhub-data`.

### `nginx`
- **Qué hace:** reverse proxy y punto único de acceso.
- **Por qué existe:** unifica rutas y simplifica acceso desde navegador:
  - `/jupyter/` -> JupyterHub
  - `/mlflow/` -> MLflow
  - `/lakefs/` -> lakeFS
  - `/` -> landing + fallback hacia UI/API de lakeFS según configuración.
- **Config:** `docker/nginx/nginx.conf`, `docker/nginx/index.html`.

## Ficheros de inicialización relevantes

- `docker/lakefs/init_lakefs.sh`: bootstrap de usuarios, permisos y repos de lakeFS
  a partir de `config/cases_config.json`.
- `docker/lakefs/hook-retrain.yml`: hook de lakeFS para disparar webhook de reentrenamiento.
- `docker/mlflow/init_mlflow.py`: bootstrap de experimentos/modelos en MLflow.
- `docker/jupyterhub/config.py`: política de autenticación, usuarios permitidos y entorno.

## Persistencia (volúmenes)

- `lakefs-data`: metadatos/objetos locales de lakeFS.
- `mlflow-data`: DB SQLite de MLflow + artefactos.
- `jupyterhub-data`: estado local de JupyterHub.
- `aclserver-db-data`: datos de Postgres del ACL server.

## Política de reinicio (`restart: unless-stopped`)

Todos los servicios usan `restart: unless-stopped` por estos motivos:

- **Recuperación automática:** si un contenedor cae o se reinicia Docker/host, el servicio vuelve a levantarse sin
intervención manual.
- **Disponibilidad del stack completo:** evita que queden piezas clave (Postgres, ACL, lakeFS, MLflow, JupyterHub o
Nginx) apagadas tras fallos puntuales.
- **Control operativo:** si se detiene explícitamente un servicio (`docker compose stop`), Docker respeta esa decisión y
no lo relanza hasta que se arranque de nuevo.

## Objetivo de diseño

Separar claramente:
- **plataforma de datos/versionado** (`lakefs`, `aclserver`, `aclserver-db`),
- **plataforma de experimentación** (`mlflow`),
- **entorno de trabajo de usuarios** (`jupyterhub`),
- **frontal de acceso** (`nginx`).

Esta separación reduce acoplamiento, mejora trazabilidad y permite escalar o sustituir
componentes sin rehacer todo el entorno.
