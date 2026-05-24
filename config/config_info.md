# Justificación conjunta de `schema_captia.json` y `cases_config.json`

El proyecto separa la información en dos ficheros porque hay dos niveles distintos de configuración:

```text
schema_captia.json
  Define el contrato común de la capa Silver.

cases_config.json
  Define cómo cada caso de uso y cada dataset aplican ese contrato.
```

Esta separación evita mezclar el modelo común de datos con detalles operativos de datasets, repositorios, modelos o
métricas.



## `schema_captia.json`

### Propósito

`schema_captia.json` define el contrato estructural común de la capa Silver compatible con CAPTIA.

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

Su función es conectar el contrato común definido en `schema_captia.json` con los datasets reales usados en el proyecto,
indicando cómo debe procesarse cada fuente de datos para producir capas Bronze, Silver y Gold trazables.

Mientras `schema_captia.json` describe la estructura común que debe cumplir cualquier dato normalizado en la capa
Silver, `cases_config.json` describe cómo se aplica ese contrato a cada caso de uso concreto.


### `schema_id`, `version`, `project` y `description`

Estos campos identifican el fichero de configuración y su versión.

Son necesarios para saber qué configuración operativa se ha usado en un momento concreto del proyecto. Si cambian los
datasets, las rutas lakeFS, los mappings o las métricas requeridas, debe actualizarse la versión del fichero.


### `variables`

La sección `variables` define el catálogo de variables de proyecto que pueden aparecer como valores del tag `variable`
en la capa Silver.

Cada variable incluye:

- `metric_kind`;
- unidad;
- tipo de dato;
- valores permitidos cuando aplica.

Ejemplo:

```json
"co2": {
  "metric_kind": "analog_gauge",
  "unit": "ppm",
  "data_type": "float"
}
```

Esta información no está en `schema_captia.json` porque no describe la estructura común del punto Silver, sino el
vocabulario semántico usado por el proyecto.

Debe estar aquí porque los datasets concretos necesitan mapear sus columnas originales a estas variables.


### `repository_schema`

La sección `repository_schema` define la estructura esperada de los repositorios lakeFS asociados a datasets.

Incluye las capas Medallion:

```text
bronze/
silver/
gold/
metadata/
```

Esta información pertenece a `cases_config.json` porque lakeFS es una decisión operativa del proyecto. No forma parte
del contrato CAPTIA, pero sí es necesaria para que todos los casos usen una estructura homogénea de versionado.

#### `bronze`

Contiene los datasets originales sin modificar.

Ejemplos:

```text
datatraining.txt
datatest.txt
datatest2.txt
electricity.csv
weather.csv
```

#### `silver`

Contiene los datos normalizados conforme a `schema_captia.json`.

En este proyecto, la capa Silver puede materializarse como fichero Parquet o CSV en lakeFS, simulando la estructura que
tendría en InfluxDB.

#### `gold`

Contiene los datasets preparados para consumo por modelos, informes o dashboards.

Ejemplos:

```text
train.parquet
test.parquet
features_schema.json
class_balance_report.json
```

#### `metadata`

Contiene información de lineage, calidad y reproducibilidad.

Ejemplos:

```text
lineage.json
quality_report.json
schema_captia.json
cases_config.json
```


### `lakefs_conventions`

Esta sección define convenciones de ramas y tags lakeFS.

Debe estar en `cases_config.json` porque depende del sistema de versionado usado por el proyecto, no del contrato
CAPTIA.

Los tags permiten identificar versiones estables de cada capa:

```text
{dataset}_bronze_v{version}
{dataset}_silver_v{version}
{dataset}_gold_caso{case}_v{version}
```

Esto permite que un experimento MLflow pueda referenciar de forma explícita la versión del dataset usada durante el
entrenamiento.


### `mlflow_conventions`

Esta sección define convenciones mínimas para registrar experimentos.

Debe estar en `cases_config.json` porque MLflow pertenece a la infraestructura MLOps, no al schema CAPTIA.

Incluye:

- patrón de nombre de experimento;
- patrón de nombre de run;
- tags obligatorios relacionados con lakeFS y schema.

La finalidad es garantizar que cada experimento pueda vincularse con:

- versión Bronze;
- versión Silver;
- versión Gold;
- versión del schema CAPTIA.


### `cases`

La sección `cases` describe cada caso de uso del proyecto.

Para cada caso se define:

- nombre;
- tipo de problema;
- datasets asociados;
- variable objetivo si aplica;
- modelos esperados;
- métricas requeridas;
- outputs relevantes.

Ejemplo:

```json
"D": {
  "name": "Calidad del Aire, Confort Interior y Ocupación",
  "problem_type": "binary_classification",
  "datasets": ["uci_occupancy", "ingauge"],
  "target_variable": "occupancy",
  "models": ["logistic_regression", "random_forest", "svm", "xgboost"],
  "metrics": ["accuracy", "precision", "recall", "f1_score", "auc_roc"]
}
```

Esta sección permite que la infraestructura MLOps sepa qué se espera de cada caso sin codificarlo directamente en los
notebooks.


### `datasets`

La sección `datasets` contiene la configuración operativa de cada dataset.

Cada dataset puede incluir:

- caso de uso asociado;
- fuente original;
- repositorio lakeFS;
- ficheros Bronze;
- rutas Bronze, Silver y Gold;
- tags fijos CAPTIA;
- regla para `asset_id`;
- columna temporal;
- variable objetivo;
- mapping de columnas originales a variables CAPTIA.

Esta información pertenece a `cases_config.json` porque depende del dataset concreto.


### `fixed_tags`

`fixed_tags` define los valores comunes de algunos tags CAPTIA para un dataset.

Ejemplo:

```json
"fixed_tags": {
  "captia_env": "prod",
  "domain_id": "bms_classrooms",
  "site_id": "uci_occupancy"
}
```

Estos valores son necesarios para generar Silver, porque `schema_captia.json` exige los cinco tags CAPTIA:

```text
captia_env
domain_id
site_id
asset_id
variable
```

De esos cinco:

- `captia_env`, `domain_id` y `site_id` suelen ser fijos por dataset;
- `asset_id` puede ser fijo, derivado de una columna o generado por regla;
- `variable` sale del mapping de columnas.

Si un dataset no tiene `fixed_tags` ni una forma equivalente de derivarlos, no tiene información suficiente para generar una capa Silver válida.

---

## `default_asset_id`, `asset_id_column` y `asset_id_rule`

Cada punto Silver debe tener `asset_id`.

Dependiendo del dataset, puede obtenerse de distintas formas.

### `default_asset_id`

Se usa cuando el dataset representa una única entidad lógica.

Ejemplo:

```json
"default_asset_id": "ROOM01"
```

### `asset_id_column`

Se usa cuando el dataset contiene una columna que identifica el activo.

Ejemplo:

```json
"asset_id_column": "building_id"
```

### `asset_id_rule`

Se usa cuando el activo debe construirse mediante una regla.

Ejemplo:

```json
"asset_id_rule": "AULA{classroom_number}"
```

Al menos una de estas tres estrategias debe estar definida para cada dataset que se vaya a transformar a Silver.

---

## `column_mappings`

`column_mappings` define cómo se transforman las columnas originales de cada dataset en variables CAPTIA.

Ejemplo para UCI Occupancy:

```json
"column_mappings": {
  "Temperature": {
    "variable": "temperature_01",
    "role": "feature"
  },
  "CO2": {
    "variable": "co2",
    "role": "feature"
  },
  "Occupancy": {
    "variable": "occupancy",
    "role": "target"
  }
}
```

Esta sección no pertenece a `schema_captia.json` porque cada dataset usa nombres de columnas distintos.

El mapping permite transformar datasets heterogéneos a una representación común:

```text
Temperature      → temperature_01
IndoorCO2        → co2
Appliances       → power_01
SA_TEMP          → temperature_supply
2m_temperature   → temperature_outdoor
```

---

## `paths`

La sección `paths` indica dónde se escriben las salidas dentro del repositorio lakeFS.

Ejemplo:

```json
"paths": {
  "bronze": "bronze/",
  "silver": "silver/captia_points.parquet",
  "gold_train": "gold/train.parquet",
  "gold_test": "gold/test.parquet"
}
```

Esta información es operativa. Sirve para que notebooks, scripts o pipelines escriban y lean de ubicaciones homogéneas.

---

## `tracking`

La sección `tracking` define requisitos mínimos de trazabilidad.

Incluye:

- datasets de entrenamiento versionados en lakeFS;
- experimentos registrados en MLflow;
- tags lakeFS registrados en los runs;
- métricas, parámetros, artefactos y modelos guardados.

Debe estar en `cases_config.json` porque pertenece al flujo MLOps del proyecto, no al contrato estructural CAPTIA.

---

## Información que no debe estar en `cases_config.json`

`cases_config.json` no debe redefinir la estructura Silver común.

No debe contener:

- definición de `measurement`;
- definición del field `value`;
- lista de tags obligatorios como contrato estructural;
- tipos estructurales de la capa Silver;
- reglas estructurales generales de validación.

Esa información pertenece a `schema_captia.json`.

---

## Resumen

`cases_config.json` contiene la información necesaria para aplicar el contrato CAPTIA a los casos de uso reales del proyecto.

Su contenido se justifica porque define:

```text
qué caso usa qué dataset
dónde se versiona
qué ficheros componen Bronze
cómo se genera Silver
qué rutas usa lakeFS
cómo se genera Gold
qué modelos y métricas se esperan
qué trazabilidad debe registrarse
```

El fichero actúa como puente entre:

```text
schema_captia.json
  contrato común Silver

notebooks/scripts
  implementación concreta

lakeFS/MLflow
  trazabilidad y reproducibilidad
```

---

# Criterio final

La frontera correcta es:

```text
schema_captia.json
  Qué forma tiene un dato Silver.

cases_config.json
  Cómo se genera ese dato Silver desde cada dataset y cómo se usa en cada caso.
```

Por eso `schema_captia.json` es estable y común, mientras que `cases_config.json` puede crecer o cambiar a medida que se añadan datasets, casos, modelos, métricas o repositorios.
