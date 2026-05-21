# Arquitectura general del repositorio

## Objetivo

El repositorio `simarro-ia-project` agrupa los casos de uso del equipo en una única estructura mantenible. No se crea un repositorio por caso de uso porque los casos comparten infraestructura, datos, convenciones, utilidades y documentación.

## Decisión arquitectónica

Se usa un monorepo organizado por responsabilidad técnica:

```text
src/simarro/common/   → código común
src/simarro/bronze/   → capa bronce
src/simarro/silver/   → capa plata
src/simarro/gold/     → capa oro
src/simarro/mlops/    → Caso F
src/simarro/cases/    → lógica específica de cada caso
```

Esta estructura evita duplicar código de conexión, logging, validación, configuración y trazabilidad.

## Directorios principales

| Directorio | Propósito |
|---|---|
| `docs/` | Documentación técnica, runbooks, arquitectura y distribución de tareas. |
| `infra/` | Dockerfiles, configuración de servicios y despliegue local. |
| `config/` | Configuración declarativa: schema CAPTIA, MLflow, lakeFS, logging y experimentos. |
| `data/` | Estructura vacía para datos locales. Los datos reales no se suben a Git. |
| `notebooks/` | Notebooks documentados, numerados y separados por caso. |
| `src/` | Código fuente Python empaquetable. |
| `scripts/` | Scripts operativos ejecutables desde terminal. |
| `tests/` | Pruebas automatizadas. |
| `reports/` | Informes, figuras, exportaciones y resultados. |
| `artifacts/` | Artefactos ligeros o placeholders. Los modelos grandes van a MLflow. |

## Flujo técnico general

```text
Dataset original
        ↓
Capa bronce versionada en lakeFS
        ↓
ETL a schema CAPTIA
        ↓
Capa plata en InfluxDB
        ↓
Features / modelos / informes
        ↓
Capa oro
        ↓
MLflow + Grafana + documentación
```

## Servicios previstos

| Servicio | Uso |
|---|---|
| MLflow | Registro de experimentos, métricas, parámetros, modelos y artefactos. |
| lakeFS | Versionado de datasets y schema CAPTIA. |
| InfluxDB | Capa plata con schema CAPTIA. |
| Grafana | Visualización de métricas, series temporales y dashboards. |
| Streamlit/API | Interfaces ligeras de demo. |

## Criterio de diseño

El código que lea datos para modelos debe hacerlo desde la capa plata siempre que sea posible. El uso directo de CSV queda limitado a exploración inicial o bootstrap.
