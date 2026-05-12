
# simarro-ia-project

Proyecto final del Curso de Especialización en Inteligencia Artificial y Big Data del IES Dr. Lluís Simarro.

El repositorio contiene una solución integrada para trabajar con datos de edificios inteligentes, calidad ambiental, MLOps y agentes de calidad software, alineada con la arquitectura de CENTINELA+.

## Casos de uso incluidos

Este repositorio agrupa los casos de uso desarrollados por el equipo:

- **Caso F — MLOps y ciclo de vida de modelos**
  - MLflow para registro de experimentos.
  - lakeFS para versionado de datasets.
  - Trazabilidad entre código, datos, modelos y métricas.

- **Caso D — Calidad del aire, confort interior y ocupación**
  - Análisis de variables ambientales.
  - Predicción de ocupación.
  - Índice IAQ.
  - Visualización en Grafana.

- **Caso nuevo — Agentes especialistas de calidad**
  - Validación de datos.
  - Auditoría de experimentos.
  - Generación y evaluación de pruebas.
  - Evaluación de respuestas de sistemas IA.

## Arquitectura

El proyecto sigue una arquitectura Medallion:

```text
Capa Bronce  → datos originales versionados
Capa Plata   → datos normalizados con schema CAPTIA en InfluxDB
Capa Oro     → features, modelos, métricas, informes y artefactos
````

Flujo general:

```text
Datasets públicos
    ↓
lakeFS
    ↓
ETL bronce → plata
    ↓
InfluxDB con schema CAPTIA
    ↓
features / modelos / agentes
    ↓
MLflow + Grafana + reports
```

## Estructura del repositorio

```text
simarro-ia-project/
├── docs/              # Documentación técnica y runbooks
├── infra/             # Dockerfiles y configuración de infraestructura
├── config/            # Configuración declarativa del proyecto
├── data/              # Estructura local de datos, sin datasets pesados
├── notebooks/         # Notebooks documentados por caso de uso
├── src/               # Código fuente principal
├── scripts/           # Scripts operativos
├── tests/             # Tests automatizados
├── reports/           # Informes y resultados generados
└── artifacts/         # Artefactos ligeros o placeholders
```

## Requisitos

* Docker
* Docker Compose
* Python 3.10
* Git

## Configuración inicial

Clonar el repositorio:

```bash
git clone <repo-url>
cd simarro-ia-project
```

TODO

## Arranque de servicios

### Servicios MLOps

TODO

### Servicios de datos y visualización

TODO

### Servicios de notebooks

TODO


## Caso F — MLOps

TODO


## Datos

Los datasets completos no deben subirse al repositorio.

Reglas:

* `data/raw/` contiene solo placeholders o muestras pequeñas.
* Los datasets se versionan en lakeFS.
* Los modelos se registran en MLflow.
* Los artefactos pesados no van a Git.

## Calidad de código

TODO

## Documentación

La documentación principal está en:

```text
docs/
├── arquitectura.md
├── arquitectura_medallion.md
├── runbook.md
├── distribucion_tareas.md
├── caso_f_mlops/
├── caso_d_iaq_ocupacion/
└── caso_qabot/
```

## Licencia

Este proyecto se distribuye bajo licencia MIT.

Los datasets, modelos entrenados, credenciales y artefactos pesados no forman parte del repositorio.

