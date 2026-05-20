# CASO D — Predicción de ocupación en aulas de Australia

Proyecto de clasificación binaria para inferir si un aula está ocupada o no a partir de variables ambientales interiores del dataset **In-Gauge and En-Gage**, publicado en PhysioNet.

- Fuente oficial: https://physionet.org/content/in-gauge-and-en-gage/1.0.0/
- Dataset: **In-Gauge and En-Gage: Understanding Occupants' Behaviour, Engagement, Emotion, and Comfort Indoors with Heterogeneous Sensors and Wearables**
- Versión: `1.0.0`
- Caso de uso: **CASO D - Calidad del aire, confort interior y ocupación**
- Subcaso: **Aulas de Australia / Classroom Occupancy Prediction**

---

## 1. Objetivos del caso

El objetivo principal es construir un modelo de Machine Learning capaz de predecir la variable binaria `Occupied`, que indica si un aula está ocupada o no.

```text
Occupied = 0 -> aula no ocupada
Occupied = 1 -> aula ocupada
```

El enfoque del caso es intencionalmente restrictivo, ya que el modelo final debe utilizar únicamente variables ambientales interiores que podrían obtenerse mediante sensórica instalada en el aula.

Variables usadas por el modelo:

```python
SENSOR_FEATURES = [
    "IndoorTemperature",
    "IndoorHumidity",
    "IndoorCO2",
    "IndoorNoise",
]
```

Se excluyen variables de calendario, horario, contexto docente y operación, aunque puedan ser predictivas. La razón es metodológica: el objetivo no es que el modelo aprenda el horario escolar, sino que infiera ocupación a partir de señales físicas medibles por sensores.

---

## 2. Alcance de la entrega

La entrega incluye:

1. Dataset de muestra con ficheros CSV de aulas.
2. Notebook principal de entrenamiento y evaluación.
3. Tablas generadas por el notebook.
4. Modelos entrenados en formato `.joblib`.
5. Proyecto local de inferencia con entrada JSON simulada.
6. Documentación del dataset y diccionario de datos.


La entrega permite:

- Cargar datos del dataset In-Gauge / Longitudinal.
- Realizar EDA sobre ocupación, variables ambientales y variables de contexto.
- Justificar la exclusión de variables de contexto docente.
- Entrenar distintos modelos de clasificación.
- Realizar selección de modelo e hiperparámetros usando validación temporal.
- Evaluar el modelo seleccionado en un test final temporal.
- Guardar modelos y resultados.
- Ejecutar inferencia local con casos simulados.

---

## 3. Estructura del proyecto

Estructura esperada del proyecto descomprimido:

```text
.
├── data/
│   ├── README_CASO_D_CLASSROOM_AUSTRALIA.md
│   ├── DATA_DICTIONARY_CASO_D_CLASSROOM_AUSTRALIA.md
│   └── occupancy_detection_muestra/
│       ├── 19.csv
│       ├── 41.csv
│       └── KB4.csv
│       .... (+ ficheros .csv)  
│
├── notebook/
│   ├── CASO_D_CLASSROOM_sensorica.ipynb
│   └── tables/
│       ├── feature_audit_sensorica_vs_contexto.csv
│       ├── hyperparameter_tuning_ingauge_occupancy_sensorica_validation.csv
│       ├── ingauge_engage_usable_dataset_sensorica.csv
│       ├── model_results_ingauge_occupancy_sensorica_test_final.csv
│       ├── model_selection_ingauge_occupancy_sensorica_validation.csv
│       ├── saved_models_index_ingauge_occupancy_sensorica.csv
│       └── split_summary_train_validation_test.csv
│
└── src/
    ├── inference/
    │   ├── infer_classroom_occupancy_json.py
    │   ├── best_sensorica_ambiental_LogisticRegression.joblib
    │   ├── best_model_metadata.json
    │   ├── simulated_cases.json
    │   ├── inference_results_classroom.csv
    │   ├── requirements.txt
    │   └── README.md
    │
    └── models/
        ├── best_sensorica_ambiental_LogisticRegression.joblib
        ├── sensorica_ambiental_Baseline_MostFrequent.joblib
        ├── sensorica_ambiental_DecisionTree.joblib
        ├── sensorica_ambiental_GaussianNB.joblib
        └── sensorica_ambiental_HistGradientBoosting.joblib
```

### Descripción de directorios

| Directorio | Contenido |
|---|---|
| `data/` | Documentación del dataset y muestra de ficheros CSV. |
| `data/occupancy_detection_muestra/` | Ficheros de muestra de aulas: `19.csv`, `41.csv`, `KB4.csv`. |
| `notebook/` | Notebook principal de análisis, entrenamiento y evaluación. |
| `notebook/tables/` | Resultados tabulares exportados por el notebook. |
| `src/models/` | Modelos entrenados y guardados como `.joblib`. |
| `src/inference/` | Script de inferencia local, modelo final, metadata, casos simulados y salida CSV. |

---

## 4. Datos de entrada

El notebook principal está preparado para leer los CSV del componente **In-Gauge / Longitudinal** desde Google Drive.

En Colab, la ruta configurada es:

```python
DATA_DIR = Path("/content/drive/MyDrive/simarro-cursoia/caso-d-classrooms")
```

Fuera de Colab, el notebook contempla una ruta alternativa:

```python
DATA_DIR = Path("G:/Mi unidad/simarro-cursoia/caso-d-classrooms")
```

La lectura del notebook espera los siguientes ficheros CSV:

```python
CSV_FILES = [
    "19.csv", "20.csv", "27.csv", "28.csv", "29.csv", "30.csv", "31.csv",
    "40.csv", "41.csv", "43.csv",
    "KB1.csv", "KB2.csv", "KB3.csv", "KB4.csv", "KB5.csv", "KB6.csv",
]
```

Cada fichero representa un aula. Durante la carga, el notebook agrega una columna auxiliar:

```python
df_i["classroom_id"] = path.stem
```

Esto permite identificar el aula de origen de cada registro y hacer particiones temporales por aula.

La muestra incluida en esta entrega contiene:

| Fichero | Filas | Columnas | Observación |
|---|---:|---:|---|
| `19.csv` | 48.672 | 23 | Aula de muestra. |
| `41.csv` | 48.672 | 23 | Aula de muestra. |
| `KB4.csv` | 48.672 | 23 | Aula de muestra. |

Cada fichero tiene 288 registros por día, consistente con una frecuencia de 5 minutos.

---

## 5. Variables del problema

### Variable objetivo

| Variable | Tipo | Descripción |
|---|---|---|
| `Occupied` | `int` | Variable objetivo binaria. `0` = aula no ocupada, `1` = aula ocupada. |

### Variables usadas en el modelo

| Variable | Descripción | Motivo de uso |
|---|---|---|
| `IndoorTemperature` | Temperatura interior del aula. | Variable ambiental de sensórica directa. |
| `IndoorHumidity` | Humedad relativa interior. | Variable ambiental de sensórica directa. |
| `IndoorCO2` | Concentración de CO2 interior. | Señal asociada a presencia humana y ventilación. |
| `IndoorNoise` | Ruido interior. | Señal acústica asociada a actividad en el aula. |

### Variables excluidas del modelo principal

| Variable | Motivo de exclusión |
|---|---|
| `Day` | Información temporal. Puede inducir aprendizaje de calendario. |
| `Hour` | Información horaria. Puede inducir aprendizaje de patrones lectivos. |
| `relative_weekday` | Variable derivada para EDA; puede representar calendario. |
| `SchoolDay` | Contexto escolar directo. |
| `LessonNumber` | Contexto docente directo. |
| `LessonPct` | Progreso de la lección. |
| `CoolingState` | Estado operativo HVAC. |
| `HeatingState` | Estado operativo HVAC. |
| `Time` | Hora anonimizada del día. |
| `classroom_id` | Identificador de aula; no es una señal ambiental. |
| `UsabilityMask` | Máscara de calidad; se usa como filtro, no como predictor. |

### Otras variables disponibles para EDA

El dataset también contiene variables exteriores, por ejemplo:

- `OutdoorTemperature`
- `OutdoorHumidity`
- `OutdoorDewpoint`
- `OutdoorWindDirection`
- `OutdoorWindSpeed`
- `OutdoorGustSpeed`
- `Precipitation`
- `UvLevel`
- `SolarRadiation`

Estas variables pueden ser útiles para análisis de confort o climatización, pero no se incluyen en el modelo principal de ocupación basado en sensórica interior.

---

## 6. Resumen del notebook ipynb

Notebook:

```text
notebook/CASO_D_CLASSROOM_sensorica.ipynb
```

El flujo del notebook es:

### 6.1 Imports y configuración

- Importa `pandas`, `numpy`, `matplotlib`, `joblib` y componentes de `scikit-learn`.
- Montar Google Drive si se ejecuta en Colab.
- Define `DATA_DIR` y `OUTPUT_DIR`.

### 6.2 Carga de CSV

- Lee los CSV de aulas definidos en `CSV_FILES`.
- Agrega `classroom_id` a cada fichero.
- Concatena todos los CSV en un único DataFrame.

### 6.3 Limpieza básica

- Convierte `UsabilityMask` a booleano.
- Crea `time_index` como índice temporal relativo.
- Convierte `Occupied` a entero.
- Revisa tipos, nulos y duplicados.
- Filtra el dataset de modelado usando `UsabilityMask=True`.

### 6.4 EDA

El análisis exploratorio incluye:

- Balance global de `Occupied`.
- Balance de ocupación por aula.
- Distribución de variables interiores según ocupación.
- Boxplots de sensores frente a ocupación.
- Ocupación media por variables de contexto docente.
- Análisis de `Hour`, `SchoolDay`, `LessonNumber`, `LessonPct` y `relative_weekday`.
- Mapa horario `SchoolDay x Hour`.
- Correlación entre `Occupied`, sensores y variables de contexto.

El EDA muestra que las variables de contexto pueden ser predictivas, pero se excluyen del modelo final para evitar que el modelo aprenda calendario u organización docente.

### 6.5 Split temporal por aula

La partición no es aleatoria. Se hace temporalmente para cada aula:

```text
Primer 60% temporal por aula    -> entrenamiento
Siguiente 20% temporal por aula -> validación / selección de modelo
Último 20% temporal por aula    -> test final
```

Resumen generado por el notebook:

| Split | Filas | Tasa de ocupación | Día mínimo | Día máximo |
|---|---:|---:|---:|---:|
| `train` | 183.168 | 0,1495 | 2 | 156 |
| `validation` | 61.632 | 0,1559 | 41 | 162 |
| `test_final` | 63.648 | 0,1494 | 66 | 169 |

### 6.6 Entrenamiento e hiperparametrización

Se prueban varios modelos y grillas acotadas de hiperparámetros.

Modelos evaluados:

- `Baseline_MostFrequent`
- `LogisticRegression`
- `GaussianNB`
- `DecisionTree`
- `RandomForest`
- `HistGradientBoosting`

La selección de modelo se realiza usando `F1` en la partición de validación. Luego, los modelos finales se reentrenan con `train + validation` y se evalúan en `test_final`.

### 6.7 Evaluación final

El notebook genera:

- Ranking de modelos en validación.
- Ranking de modelos en test final.
- Comparativa visual de métricas.
- Matriz de confusión del mejor modelo.
- Curva ROC del mejor modelo.
- Importancia de variables cuando el modelo lo permite.

### 6.8 Guardado de artefactos

El notebook guarda:

- Modelos `.joblib`.
- Mejor modelo con prefijo `best_`.
- Resultados de test final.
- Resultados de validación.
- Resultados de hiperparametrización.
- Dataset usable.
- Auditoría de variables usadas y excluidas.

---

## 7. Ejecución en Google Colab

### 7.1 Preparar Drive

Crear en Google Drive la carpeta:

```text
Mi unidad/simarro-cursoia/caso-d-classrooms/
```

Dentro de esa carpeta deben estar los CSV del dataset:

```text
19.csv
20.csv
27.csv
28.csv
29.csv
30.csv
31.csv
40.csv
41.csv
43.csv
KB1.csv
KB2.csv
KB3.csv
KB4.csv
KB5.csv
KB6.csv
```

### 7.2 Abrir notebook

Subir o abrir en Colab:

```text
notebook/CASO_D_CLASSROOM_sensorica.ipynb
```

### 7.3 Ejecutar celdas

Ejecutar todas las celdas en orden:

```text
Entorno de ejecución -> Ejecutar todo
```

El notebook montará Google Drive y usará:

```python
from google.colab import drive
drive.mount("/content/drive")
```

### 7.4 Salidas esperadas en Drive

El notebook generará la carpeta:

```text
/content/drive/MyDrive/simarro-cursoia/caso-d-classrooms/outputs_ingauge_engage_sensorica/
```

Dentro se guardarán, entre otros:

```text
models/
model_results_ingauge_occupancy_sensorica_test_final.csv
model_selection_ingauge_occupancy_sensorica_validation.csv
hyperparameter_tuning_ingauge_occupancy_sensorica_validation.csv
saved_models_index_ingauge_occupancy_sensorica.csv
feature_audit_sensorica_vs_contexto.csv
split_summary_train_validation_test.csv
models_metadata.json
```

---

## 8. Resultados alcanzados

La selección de modelo se realizó usando `F1` en validación. El mejor modelo fue:

```text
LogisticRegression
```

Hiperparámetros seleccionados:

```python
{
    "model__C": 10.0,
    "model__class_weight": "balanced"
}
```

Resultados en `test_final`:

| Modelo | Accuracy | Precision | Recall | F1 | AUC ROC |
|---|---:|---:|---:|---:|---:|
| `LogisticRegression` | 0,8848 | 0,5737 | 0,8911 | 0,6980 | 0,9397 |
| `RandomForest` | 0,8688 | 0,5384 | 0,8546 | 0,6606 | 0,9362 |
| `HistGradientBoosting` | 0,8966 | 0,6647 | 0,6217 | 0,6425 | 0,9410 |
| `GaussianNB` | 0,8913 | 0,6196 | 0,7057 | 0,6599 | 0,9338 |
| `DecisionTree` | 0,8544 | 0,5067 | 0,9483 | 0,6605 | 0,9383 |
| `Baseline_MostFrequent` | 0,8506 | 0,0000 | 0,0000 | 0,0000 | 0,5000 |

Lectura de resultados:

- `LogisticRegression` obtuvo el mejor `F1` final, con buena sensibilidad para detectar ocupación.
- `HistGradientBoosting` obtuvo el mayor `Accuracy` y un AUC ROC levemente superior, pero menor `F1` que Logistic Regression.
- El baseline logra accuracy alto por el desbalance de clases, pero no detecta ocupación, por eso su F1 es 0.
- La métrica más relevante para seleccionar el modelo fue `F1`, porque combina precisión y recall en un problema con desbalance de clases.

---

## 9. Modelos entrenados

Los modelos se guardan en:

```text
src/models/
```

Modelos incluidos:

| Modelo | Fichero | Mejor modelo |
|---|---|---|
| `LogisticRegression` | `best_sensorica_ambiental_LogisticRegression.joblib` | Sí |
| `Baseline_MostFrequent` | `sensorica_ambiental_Baseline_MostFrequent.joblib` | No |
| `DecisionTree` | `sensorica_ambiental_DecisionTree.joblib` | No |
| `GaussianNB` | `sensorica_ambiental_GaussianNB.joblib` | No |
| `HistGradientBoosting` | `sensorica_ambiental_HistGradientBoosting.joblib` | No |

El prefijo `best_` identifica el modelo seleccionado como mejor según la métrica de validación.

---

## 10. Inferencia

La inferencia local está en:

```text
src/inference/
```

Archivos principales:

```text
infer_classroom_occupancy_json.py
best_sensorica_ambiental_LogisticRegression.joblib
best_model_metadata.json
simulated_cases.json
requirements.txt
```

### 10.1 Entrada esperada

El script espera un fichero JSON llamado:

```text
simulated_cases.json
```

Ejemplo:

```json
[
  {
    "case_id": "caso_1_aula_vacia_bajo_co2_bajo_ruido",
    "IndoorTemperature": 21.4,
    "IndoorHumidity": 42.0,
    "IndoorCO2": 430.0,
    "IndoorNoise": 34.0
  },
  {
    "case_id": "caso_2_posible_ocupacion_co2_moderado_ruido_medio",
    "IndoorTemperature": 22.1,
    "IndoorHumidity": 45.5,
    "IndoorCO2": 780.0,
    "IndoorNoise": 48.0
  }
]
```

No debe incluirse `Occupied`, porque es la variable que se desea predecir.

### 10.2 Ejecución en Windows / PowerShell

Desde la raíz del ZIP descomprimido:

```powershell
cd .\src\inference
python .\infer_classroom_occupancy_json.py
```

También puede ejecutarse indicando el Python concreto instalado:

```powershell
cd .\src\inference
& "C:\Program Files\Python31210\python.exe" ".\infer_classroom_occupancy_json.py"
```

El script espera encontrar en la carpeta actual:

```text
best_sensorica_ambiental_LogisticRegression.joblib
best_model_metadata.json
simulated_cases.json
```

También puede detectar automáticamente un modelo con patrón:

```text
best_*.joblib
```

### 10.3 Instalación de dependencias

Desde `src/inference`:

```powershell
pip install -r requirements.txt
```

Si aparecen problemas de compatibilidad con `numpy` en Anaconda, se recomienda crear un entorno virtual limpio:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install "numpy<2" pandas scikit-learn joblib
python .\infer_classroom_occupancy_json.py
```

### 10.4 Salida de inferencia

La salida se guarda en:

```text
src/inference/inference_results_classroom.csv
```

Columnas habituales de salida:

| Columna | Descripción |
|---|---|
| `case_id` | Identificador del caso. |
| `IndoorTemperature` | Temperatura interior usada como entrada. |
| `IndoorHumidity` | Humedad interior usada como entrada. |
| `IndoorCO2` | CO2 interior usado como entrada. |
| `IndoorNoise` | Ruido interior usado como entrada. |
| `Occupied_pred` | Predicción binaria del modelo. |
| `pred_label` | Etiqueta legible: `No ocupado` u `Ocupado`. |
| `prob_no_ocupado` | Probabilidad estimada de clase 0, si el modelo lo permite. |
| `prob_ocupado` | Probabilidad estimada de clase 1, si el modelo lo permite. |

---

## 11. Conclusiones generales

1. El caso demuestra que la ocupación de aulas puede inferirse razonablemente usando sensórica ambiental interior, especialmente CO2, ruido, temperatura y humedad.
2. Las variables de contexto docente y calendario tienen capacidad predictiva, pero fueron excluidas para evitar que el modelo aprenda reglas administrativas en lugar de señales físicas.
3. El uso de split temporal por aula mejora la validez metodológica frente a un split aleatorio, porque respeta la secuencia temporal de las mediciones.
4. La validación se usó para seleccionar modelo e hiperparámetros, y el test final quedó reservado para evaluación honesta.
5. El mejor modelo según `F1` fue `LogisticRegression`, con F1 de 0,6980 y AUC ROC de 0,9397 en test final.
6. El baseline muestra que la accuracy puede ser engañosa en un problema desbalanceado: acierta mucho prediciendo siempre la clase mayoritaria, pero no detecta ocupación.
7. La solución es fácilmente reutilizable en inferencia local porque el modelo se guarda como `.joblib` y el script recibe casos nuevos mediante JSON.
8. Para un entorno productivo real, sería recomendable validar con datos nuevos, incorporar monitorización de drift y revisar periódicamente el umbral de clasificación según el coste de falsos positivos y falsos negativos.

---

## 12. Referencias

- PhysioNet — In-Gauge and En-Gage v1.0.0: https://physionet.org/content/in-gauge-and-en-gage/1.0.0/
- DOI del recurso PhysioNet: https://doi.org/10.13026/srm3-7z33
- Publicación asociada: Gao, N., Marschall, M., Burry, J. et al. *Understanding occupants’ behaviour, engagement, emotion, and comfort indoors with heterogeneous sensors and wearables*. Scientific Data 9, 261 (2022).
