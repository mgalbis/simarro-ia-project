# Justificación conjunta de `captia_schema.json` y `cases_config.json`

El proyecto separa la información en dos ficheros porque hay dos niveles distintos de configuración:

```text
captia_schema.json
  Define el contrato común de la capa Silver.

cases_config.json
  Define cómo cada caso de uso y cada dataset aplican ese contrato.
```

Esta separación evita mezclar el modelo común de datos con detalles operativos de datasets, repositorios, modelos o
métricas.



## `captia_schema.json`

### Propósito

`captia_schema.json` define el contrato estructural común de la capa Silver compatible con CAPTIA.

El fichero contiene únicamente información común a todos los casos de uso. Su objetivo es fijar la forma que debe tener
cualquier observación normalizada, sin depender del dataset original, del caso de uso, del modelo entrenado ni del
repositorio lakeFS donde se versionen los datos.

### Metadatos

Los campos `schema_id`, `version`, `project` y `description` identifican el contrato usado por el proyecto.

Esta información permite referenciar una versión concreta del schema desde notebooks, validaciones y documentación.

### `silver_layer.logical_schema`

Esta sección define la estructura lógica de un punto CAPTIA.

Incluye:

- `measurement`: el measurement común `captia_point`.
- `field`: el field único `value`.
- `tags`: los cinco tags obligatorios que identifican entorno, dominio, sitio, activo y variable.

Estos elementos son comunes a todos los casos de uso.

### `silver_layer.file_schema`

Esta sección define la representación equivalente cuando la capa Silver se materializa como fichero Parquet o CSV.

Incluye las columnas necesarias para conservar la misma semántica que un punto CAPTIA:

- `timestamp`
- `captia_env`
- `domain_id`
- `site_id`
- `asset_id`
- `variable`
- `value`
- `metric_kind`
- `unit`

Cada columna incluye su tipo esperado para que la capa Silver pueda validarse antes de construir datasets Gold o
entrenar modelos.

### `metric_kinds`

Esta sección define los tipos de señal admitidos en la capa Silver.

Cada `metric_kind` indica cómo se interpreta la señal y qué estadísticas son válidas para ella. Esta información es
común a todos los casos de uso porque forma parte del contrato de datos normalizados.



## `cases_config.json`

### Propósito

`cases_config.json` define la configuración operativa del proyecto por caso de uso y por dataset.

Su función es conectar el contrato común definido en `captia_schema.json` con los datasets reales usados en el proyecto,
indicando cómo debe procesarse cada fuente de datos para producir capas Bronze, Silver y Gold trazables.

Mientras `captia_schema.json` describe la estructura común que debe cumplir cualquier dato normalizado en la capa
Silver, `cases_config.json` describe cómo se aplica ese contrato a cada caso de uso concreto.

### `schema_id`, `version`, `project` y `description`

Identifican la configuración operativa y su versión efectiva.

### `variables`

Es el catálogo semántico del proyecto (variable, `metric_kind`, unidad y tipo), usado por `datasets.column_mappings`.

### `repository_schema`

Describe la estructura esperada del repositorio lakeFS por capas:

```text
bronze/
silver/
gold/
metadata/
```

En la versión actual también documenta `files` por capa y `recommended_files`.

### `lakefs_conventions`

Define las convenciones activas:

- `repo_name_pattern`: `caso{case}--{dataset}`
- `branch_pattern`: `transform/v{version}`
- `tag_patterns`: `{dataset}_v{version}`

Importante: el proyecto ya usa **un único tag de versión** al finalizar Gold, no un tag por capa.

### `mlflow_conventions`

Establece convenciones de naming y tags mínimos para runs:

- `experiment_pattern`
- `run_pattern`
- `required_tags`

### `cases`

Define cada caso (`B`, `C`, `D`, `E`) con:

- nombre y descripción;
- tipo de problema;
- propósito funcional;
- datasets asociados;
- variable objetivo (si aplica);
- modelos esperados;
- métricas esperadas;
- reportes de calidad (si aplica).

Esta sección se usa para validar expectativas funcionales por caso (incluyendo modelos requeridos en webhook).

### `datasets`

Configura cada dataset con:

- `case` asociado;
- `source`;
- `fixed_tags` CAPTIA (`captia_env`, `domain_id`, `site_id`);
- `column_mappings` (columna origen -> variable CAPTIA + rol);
- campos opcionales como `advanced_time_windows` o `conversion`.

En la versión actual **no se define** `lakefs_repo` por dataset: el repo se resuelve con `repo_name_pattern`.

### `fixed_tags` y `column_mappings`

`fixed_tags` aporta los tags constantes para Silver.  
`column_mappings` conecta columnas heterogéneas con variables del catálogo común, incluyendo su `role` (`feature`, `target`, `context`).

## Elementos que ya no forman parte del esquema operativo actual

En el `cases_config.json` actual ya no se usan como contrato principal:

- tags por capa Bronze/Silver/Gold;
- secciones dedicadas de `paths` por dataset;
- secciones de `tracking` en el propio fichero;
- estrategia declarativa `default_asset_id` / `asset_id_column` / `asset_id_rule`.

## Resumen operativo actualizado

`cases_config.json` define:

```text
qué casos existen
qué datasets pertenecen a cada caso
cómo mapear cada dataset al vocabulario CAPTIA
qué convenciones lakeFS/MLflow aplicar
qué modelos/métricas exige cada caso
```

Y `captia_schema.json` define:

```text
la estructura formal de Silver (contrato de datos)
```

Esa separación mantiene estable el contrato técnico y permite evolucionar la operación por caso/dataset sin duplicar reglas estructurales.
