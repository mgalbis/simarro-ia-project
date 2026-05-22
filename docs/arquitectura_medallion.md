# Arquitectura Medallion aplicada al proyecto MLOps CENTINELA+

## 1. Objetivo

Este documento describe cómo se ha aplicado la arquitectura Medallion al caso de uso MLOps del proyecto **CENTINELA+**,
integrando:

- **lakeFS** para el versionado de datasets.
- **MLflow** para el registro de experimentos, métricas, modelos y artefactos.
- **JupyterHub** como entorno colaborativo de ejecución de notebooks.
- **schema_captia.json** como contrato común de variables, tags y nomenclatura.
- Una capa Medallion simplificada y reproducible basada en lakeFS.

El objetivo principal es garantizar que cada modelo entrenado pueda responder a las siguientes preguntas:

- ¿Con qué versión exacta del dataset fue entrenado?
- ¿Qué transformaciones se aplicaron a los datos?
- ¿Qué parámetros y métricas tuvo el entrenamiento?
- ¿Qué modelo y artefactos se generaron?
- ¿Cómo puede reproducirse el experimento?


## 2. Decisión arquitectónica

En una arquitectura Medallion clásica, las capas son:

```text
Bronze → Silver → Gold
````

En el contexto de CENTINELA+, la referencia del proyecto define la capa **Silver** como una representación operacional
compatible con CAPTIA, normalmente basada en InfluxDB y el schema canónico `captia_point`.

Sin embargo, en este proyecto no se dispone de infraestructura CAPTIA real. Además, incluir InfluxDB en la
infraestructura MLOps aumentaría la complejidad sin ser imprescindible para demostrar trazabilidad, reproducibilidad y
versionado de modelos.

Por tanto, se ha adoptado la siguiente decisión:

```text
Bronze:
  Datos originales versionados en lakeFS.

Silver:
  Datos normalizados al schema CAPTIA,
  almacenados como Parquet/CSV en lakeFS.

Gold:
  Datasets finales de entrenamiento/test/features,
  versionados en lakeFS y usados por MLflow.

Tracking:
  Experimentos, métricas, parámetros, modelos y artefactos
  registrados en MLflow.
```

Esta decisión permite simular la arquitectura Medallion de forma reproducible y compatible con CAPTIA, sin depender de
infraestructura externa.


## 3. Relación entre Medallion, lakeFS y MLflow

La arquitectura aplicada queda definida así:

```text
Dataset original
      ↓
lakeFS /bronze
      ↓
Transformación al schema CAPTIA
      ↓
lakeFS /silver
      ↓
Generación de features y splits
      ↓
lakeFS /gold
      ↓
Entrenamiento desde JupyterHub
      ↓
MLflow Tracking
```

Cada capa se versiona mediante commits y tags en lakeFS.
Cada entrenamiento en MLflow referencia explícitamente el tag del dataset usado.


## 4. Capa Bronze

### 4.1 Propósito

La capa **Bronze** contiene los datos originales tal como llegan desde la fuente.

No se modifican, limpian ni normalizan. Su función es preservar la fuente histórica de verdad.

### 4.2 Contenido

Ejemplos de datos Bronze:

```text
uci-appliances:
  energydata_complete.csv

bdg2:
  electricity.csv
  weather.csv

ingauge:
  CSV originales de aulas

uci-occupancy:
  datatraining.txt
  datatest.txt

era5:
  ficheros NetCDF originales

lbnl-fdd:
  ZIP/CSV originales de sistemas HVAC
```

### 4.3 Estructura en lakeFS

Ejemplo para `uci-appliances`:

```text
lakefs://uci-appliances/
└── bronze/
    └── energydata_complete.csv
```

### 4.4 Versionado

Cada ingesta Bronze debe generar:

* Un commit descriptivo.
* Un tag de versión.

Ejemplo:

```text
Commit:
  "Ingest raw UCI Appliances dataset into bronze"

Tag:
  uci-appliances_bronze_v1
```

### 4.5 Metadatos mínimos

Cada commit o fichero de metadata asociado debe incluir:

```json
{
  "dataset": "uci-appliances",
  "layer": "bronze",
  "source_file": "energydata_complete.csv",
  "source_format": "csv",
  "schema_captia_version": "1.0",
  "created_by": "G4-CasoF-MLOps"
}
```


## 5. Capa Silver

### 5.1 Propósito

La capa **Silver** contiene los datos normalizados siguiendo el contrato definido en `schema_captia.json`.

En una infraestructura CAPTIA real, esta capa podría representarse en InfluxDB mediante:

```text
measurement: captia_point

tags:
  captia_env
  domain_id
  site_id
  asset_id
  variable

field:
  value
```

En este proyecto, para reducir complejidad, la capa Silver se simula en lakeFS mediante ficheros Parquet o CSV
normalizados.

### 5.2 Justificación

No se incluye InfluxDB en el MVP MLOps porque el objetivo principal del caso es garantizar:

* Versionado de datasets.
* Trazabilidad entre datos y modelos.
* Registro de experimentos.
* Reproducibilidad.
* Integración lakeFS + MLflow.

La representación Silver en lakeFS mantiene el mismo contrato semántico que CAPTIA y permite una futura carga en
InfluxDB sin cambiar la lógica de transformación.

### 5.3 Estructura Silver

Ejemplo:

```text
lakefs://uci-appliances/
└── silver/
    └── captia_points.parquet
```

### 5.4 Schema Silver

La capa Silver debe seguir esta estructura lógica:

```text
timestamp
captia_env
domain_id
site_id
asset_id
variable
value
metric_kind
unit
```

Ejemplo:

```text
timestamp              captia_env  domain_id      site_id         asset_id  variable             value  metric_kind
2016-01-11T17:00:00Z   prod        bms_buildings  uci_appliances  HOUSE01   power_01             60.0   counter
2016-01-11T17:00:00Z   prod        bms_buildings  uci_appliances  HOUSE01   temperature_outdoor  6.6    analog_gauge
```

### 5.5 Transformación desde Bronze

La transformación Bronze → Silver aplica el mapeo definido en `schema_captia.json`.

Ejemplo para `uci-appliances`:

```json
{
  "Appliances": {
    "variable_captia": "power_01",
    "metric_kind": "counter",
    "unidad": "Wh"
  },
  "T_out": {
    "variable_captia": "temperature_outdoor",
    "metric_kind": "analog_gauge",
    "unidad": "°C"
  }
}
```

Entrada Bronze:

```text
date,Appliances,T_out,lights,T1
2016-01-11 17:00:00,60,6.6,30,19.89
```

Salida Silver:

```text
timestamp,captia_env,domain_id,site_id,asset_id,variable,value,metric_kind,unit
2016-01-11T17:00:00Z,prod,bms_buildings,uci_appliances,HOUSE01,power_01,60,counter,Wh
2016-01-11T17:00:00Z,prod,bms_buildings,uci_appliances,HOUSE01,temperature_outdoor,6.6,analog_gauge,°C
```

### 5.6 Versionado Silver

Cada transformación Silver debe generar:

```text
Commit:
  "Create CAPTIA-normalized silver dataset for uci-appliances"

Tag:
  uci-appliances_silver_v1
```

Metadatos recomendados:

```json
{
  "dataset": "uci-appliances",
  "layer": "silver",
  "source_layer": "bronze",
  "source_tag": "uci-appliances_bronze_v1",
  "schema_captia_version": "1.0",
  "target_path": "silver/captia_points.parquet"
}
```


## 6. Capa Gold

### 6.1 Propósito

La capa **Gold** contiene los datasets finales preparados para casos de uso concretos.

A diferencia de Silver, que representa datos normalizados de forma genérica, Gold está orientada a consumo directo por
modelos, dashboards, informes o sistemas de evaluación.

En el caso MLOps, Gold contiene principalmente:

* Datasets de entrenamiento.
* Datasets de test.
* Features calculadas.
* Esquemas de features.
* Metadatos de lineage.
* Informes de calidad.
* Datasets preparados para baseline y modelos candidatos.

### 6.2 Estructura Gold

Ejemplo para predicción de consumo:

```text
lakefs://uci-appliances/
└── gold/
    ├── train.parquet
    ├── test.parquet
    ├── features_schema.json
    ├── dataset_metadata.json
    └── quality_report.json
```

### 6.3 Ejemplo de columnas Gold

Para el Caso B, el dataset Gold puede contener:

```text
timestamp
power_01
temperature_outdoor
light_consumption
hour
day_of_week
month
lag_1h
lag_24h
rolling_mean_24h
target_power_01
```

### 6.4 Versionado Gold

Cada dataset Gold debe versionarse con tag, ya que será la entrada directa de los modelos.

Ejemplo:

```text
Commit:
  "Create gold training dataset for CasoB consumption prediction"

Tag:
  uci-appliances_gold_casoB_v1
```

Este tag debe registrarse obligatoriamente en MLflow.


## 7. Lineage entre capas

Cada capa debe conservar la trazabilidad hacia la capa anterior.

Ejemplo de lineage:

```json
{
  "dataset": "uci-appliances",
  "schema_captia_version": "1.0",
  "bronze": {
    "tag": "uci-appliances_bronze_v1",
    "path": "bronze/energydata_complete.csv"
  },
  "silver": {
    "tag": "uci-appliances_silver_v1",
    "path": "silver/captia_points.parquet"
  },
  "gold": {
    "tag": "uci-appliances_gold_casoB_v1",
    "path_train": "gold/train.parquet",
    "path_test": "gold/test.parquet"
  }
}
```

Este fichero puede guardarse en:

```text
metadata/lineage.json
```


## 8. Integración con MLflow

Cada notebook de entrenamiento debe registrar en MLflow:

* Nombre del experimento.
* Nombre del run.
* Parámetros del modelo.
* Métricas de evaluación.
* Artefactos.
* Modelo entrenado.
* Tag Bronze de lakeFS.
* Tag Silver de lakeFS.
* Tag Gold de lakeFS.
* Versión del schema CAPTIA.
* Commit de código, si está disponible.

### 8.1 Experimentos MLflow

Según `schema_captia.json`, los experimentos son contenedores permanentes por problema.

Formato:

```text
Caso[letra]_[descripcion_del_problema]
```

Ejemplos:

```text
CasoB_Prediccion_de_consumo_electrico
CasoC_Deteccion_de_anomalias_HVAC
CasoD_Calidad_aire_confort_ocupacion
CasoE_Meteorologia_integracion_exterior_interior
```

### 8.2 Runs MLflow

Formato recomendado:

```text
[algoritmo]_[fecha]_[descripcion_corta]
```

Ejemplos:

```text
BaselineMean_20260510123456_baseline
XGBoost_20260510123456_gold_v1
RandomForest_20260510123456_features_temporales
IsolationForest_20260510123456_hvac_v1
```

### 8.3 Tags MLflow obligatorios

Ejemplo:

```python
mlflow.set_tags({
    "caso": "B",
    "dataset": "uci-appliances",
    "schema": "captia",
    "schema_captia_version": "1.0",
    "lakefs_bronze_tag": "uci-appliances_bronze_v1",
    "lakefs_silver_tag": "uci-appliances_silver_v1",
    "lakefs_gold_tag": "uci-appliances_gold_casoB_v1",
    "gold_train_path": "gold/train.parquet",
    "gold_test_path": "gold/test.parquet",
    "target_variable": "power_01"
})
```

### 8.4 Parámetros y métricas

Ejemplo para regresión:

```python
mlflow.log_param("algorithm", "XGBoost")
mlflow.log_param("n_estimators", 200)
mlflow.log_param("max_depth", 6)
mlflow.log_param("learning_rate", 0.05)

mlflow.log_metric("mae", mae)
mlflow.log_metric("rmse", rmse)
mlflow.log_metric("mape", mape)
mlflow.log_metric("r2", r2)
```

Ejemplo para clasificación:

```python
mlflow.log_metric("accuracy", accuracy)
mlflow.log_metric("precision", precision)
mlflow.log_metric("recall", recall)
mlflow.log_metric("f1_score", f1)
mlflow.log_metric("auc_roc", auc_roc)
```


## 9. Estructura general en lakeFS

Cada repositorio lakeFS representa un dataset principal.

```text
lakeFS
├── bdg2
│   ├── bronze/
│   ├── silver/
│   ├── gold/
│   └── metadata/
├── ingauge
│   ├── bronze/
│   ├── silver/
│   ├── gold/
│   └── metadata/
├── uci-appliances
│   ├── bronze/
│   ├── silver/
│   ├── gold/
│   └── metadata/
├── uci-occupancy
│   ├── bronze/
│   ├── silver/
│   ├── gold/
│   └── metadata/
├── lbnl-fdd
│   ├── bronze/
│   ├── silver/
│   ├── gold/
│   └── metadata/
└── era5
    ├── bronze/
    ├── silver/
    ├── gold/
    └── metadata/
```


## 10. Convención de tags lakeFS

### 10.1 Bronze

```text
[dataset]_bronze_v[num]
```

Ejemplos:

```text
uci-appliances_bronze_v1
bdg2_bronze_v1
ingauge_bronze_v1
```

### 10.2 Silver

```text
[dataset]_silver_v[num]
```

Ejemplos:

```text
uci-appliances_silver_v1
bdg2_silver_v1
ingauge_silver_v1
```

### 10.3 Gold

```text
[dataset]_gold_caso[letra]_v[num]
```

Ejemplos:

```text
uci-appliances_gold_casoB_v1
bdg2_gold_casoB_v1
ingauge_gold_casoD_v1
lbnl-fdd_gold_casoC_v1
era5_gold_casoE_v1
```


## 11. Convención de ramas lakeFS

Para evitar trabajar directamente sobre `main`, se usan ramas temporales por fase.

```text
main
ingest/[dataset]/[fecha]
transform/silver/[dataset]/[fecha]
transform/gold/[dataset]/[caso]/[fecha]
experiment/[caso]/[dataset]/[fecha]
```

Ejemplos:

```text
ingest/uci-appliances/20260510
transform/silver/uci-appliances/20260510
transform/gold/uci-appliances/casoB/20260510
experiment/casoB/uci-appliances/20260510
```

Cada rama se mergea a `main` cuando la validación correspondiente es correcta.


## 12. Calidad de datos

Cada paso debe generar un informe mínimo de calidad.

### 12.1 Bronze

Comprobaciones mínimas:

* Fichero existe.
* Formato correcto.
* Número de filas.
* Número de columnas.
* Hash del fichero original.

### 12.2 Silver

Comprobaciones mínimas:

* Todos los puntos tienen `timestamp`.
* Todos los puntos tienen los 5 tags CAPTIA.
* Todas las variables existen en `schema_captia.json`.
* El campo `value` es numérico.
* Las unidades son coherentes.
* No hay timestamps inválidos.

### 12.3 Gold

Comprobaciones mínimas:

* No hay leakage temporal.
* Train/test están separados correctamente.
* La variable objetivo existe.
* Las features esperadas existen.
* No hay nulos críticos.
* El número de filas es suficiente.
* El split está documentado.

Los informes pueden guardarse en:

```text
metadata/quality/
gold_quality_report.json
```

o dentro de la carpeta Gold:

```text
gold/quality_report.json
```


## 13. Notebooks del flujo Medallion

La estructura recomendada es:

```text
notebooks/
├── CasoB/
│   ├── 01_prepare_dataset.ipynb
│   └── 02_train_model.ipynb
├── CasoC/
│   ├── 01_prepare_dataset.ipynb
│   └── 02_train_model.ipynb
└── CasoD/
    ├── 01_prepare_dataset.ipynb
    └── 02_train_model.ipynb
```

En ese caso:

```text
01_prepare_dataset.ipynb:
  bronze → silver → gold

02_train_model.ipynb:
  gold → MLflow
```


## 14. Pipeline MLOps

La arquitectura admite dos modos de ejecución.

### 14.1 Modo manual reproducible

Flujo principal del MVP:

```text
1. El usuario accede a JupyterHub.
2. Ejecuta el notebook de preparación del dataset.
3. Se generan las capas Bronze, Silver y Gold en lakeFS.
4. Se crean commits y tags.
5. El usuario ejecuta el notebook de entrenamiento.
6. El modelo se entrena usando el tag Gold.
7. El experimento se registra en MLflow.
```

Este modo es suficiente para demostrar el funcionamiento principal del sistema.

### 14.2 Modo automático

Como mejora, se puede automatizar mediante CI/CD:

```text
1. Se detecta cambio en datos o código.
2. Se ejecuta la pipeline de dataset.
3. Se comprueba si el dataset ha cambiado.
4. Si cambia, se genera nueva versión Bronze/Silver/Gold.
5. Si no cambia, se reutiliza el tag existente.
6. Se comprueba si cambian dataset, parámetros o código.
7. Si cambia algo, se reentrena.
8. Si no cambia, se reutiliza el modelo registrado en MLflow.
```

La firma de entrenamiento puede calcularse como:

```text
training_signature = hash(
  lakefs_gold_tag
  hyperparameters
  algorithm
  code_commit
  feature_set_version
)
```

Esa firma se registra en MLflow para evitar reentrenamientos innecesarios.


## 15. Baseline obligatoria

Todo caso de uso debe tener al menos una baseline registrada en MLflow.

Ejemplos:

```text
CasoB:
  baseline media histórica
  baseline último valor
  modelo candidato XGBoost/SARIMA/LSTM

CasoC:
  baseline umbral simple
  modelo candidato Isolation Forest/Autoencoder

CasoD:
  baseline mayoría de clase
  modelo candidato Random Forest/SVM/XGBoost
```

Cada baseline debe:

* Consumir un tag Gold de lakeFS.
* Registrar parámetros en MLflow.
* Registrar métricas en MLflow.
* Servir como comparación frente al modelo candidato.


## 16. Integración futura con CAPTIA

Aunque este proyecto no usa infraestructura CAPTIA real, la arquitectura se ha diseñado para ser compatible con ella.

La capa Silver en lakeFS tiene el mismo contrato lógico que una carga futura en InfluxDB CAPTIA:

```text
timestamp
captia_env
domain_id
site_id
asset_id
variable
value
metric_kind
unit
```

En una integración real, esta capa Silver podría cargarse en InfluxDB como:

```text
measurement:
  captia_point

tags:
  captia_env
  domain_id
  site_id
  asset_id
  variable

field:
  value
```

Por tanto, el proyecto no depende de CAPTIA, pero produce datos y modelos preparados para integrarse con una
infraestructura CAPTIA posterior.


## 17. Resumen de la arquitectura aplicada

```text
CAPA BRONZE
  Sistema: lakeFS
  Contenido: datasets originales sin modificar
  Evidencia: commit + tag bronze

CAPA SILVER
  Sistema: lakeFS
  Contenido: datos normalizados al schema CAPTIA
  Evidencia: commit + tag silver + quality report

CAPA GOLD
  Sistema: lakeFS
  Contenido: datasets train/test/features por caso de uso
  Evidencia: commit + tag gold + lineage

TRACKING
  Sistema: MLflow
  Contenido: experimentos, parámetros, métricas, artefactos y modelos
  Evidencia: run MLflow referenciando tag Gold lakeFS

EJECUCIÓN
  Sistema: JupyterHub
  Contenido: notebooks colaborativos documentados
  Evidencia: notebooks reproducibles con Markdown explicativo
```


## 18. Conclusión

La arquitectura Medallion aplicada al proyecto se implementa como una versión simplificada, reproducible y compatible
con CAPTIA.

La decisión principal es representar las tres capas en lakeFS:

```text
/bronze
/silver
/gold
```

donde:

* **Bronze** conserva los datos originales.
* **Silver** normaliza los datos según `schema_captia.json`.
* **Gold** produce datasets de entrenamiento y evaluación.
* **MLflow** registra los experimentos y modelos generados a partir de los tags Gold.
* **JupyterHub** proporciona el entorno colaborativo de ejecución.

Esta arquitectura permite demostrar trazabilidad completa:

```text
dataset original
  → dataset normalizado
  → dataset de entrenamiento
  → experimento MLflow
  → modelo versionado
```

Con esta trazabilidad, cualquier modelo registrado puede reproducirse sabiendo exactamente qué datos, transformaciones,
parámetros y código se utilizaron.
