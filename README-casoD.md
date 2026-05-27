# CASO D - Calidad del Aire, Confort Interior y Ocupación

Este proyecto contiene dos aproximaciones al problema de detección de ocupación en aulas mediante variables ambientales:

1. **UCI Occupancy Detection**, como dataset pequeño de referencia para EDA, entrenamiento e inferencia.
2. **In-Gauge and En-Gage classrooms**, como dataset de aulas reales con sensórica ambiental de CO₂, temperatura, humedad y ruido.

Además, esta versión incorpora una aplicación sencilla compuesta por:

- una **API FastAPI** para predecir ocupación;
- un **frontend web** que simula una sala de escuela y permite modificar visualmente los parámetros del modelo;
- ejecución completa con `docker compose up --build`.

## Objetivo del caso

El objetivo es demostrar que se puede inferir si un aula está ocupada usando variables de sensórica ambiental, sin cámaras ni sensores explícitos de presencia. Esta predicción puede apoyar decisiones de climatización, ventilación, iluminación y eficiencia energética en edificios educativos.

## Alcance de la entrega

La entrega incluye:

- datasets de trabajo y diccionarios de datos;
- notebooks de EDA, preparación, entrenamiento y evaluación;
- modelos entrenados y scripts de inferencia;
- API REST para inferencia online;
- frontend web demostrativo;
- archivos Docker para ejecutar API y frontend de forma reproducible.

## Nueva estructura del proyecto

```text
main/
├── data/
│   ├── uci/
│   └── In-gauge-and-en-gage/
├── notebooks/
│   ├── uci/
│   └── In-gauge-and-en-gage/
├── src/
│   ├── uci/
│   ├── In-gauge-and-en-gage/
│   ├── api-In-gauge-and-en-gage/
│   └── frontend-In-gauge-and-en-gage/
├── docker-compose-caso-d-ingauge.yml
└── README.md
```

### Contenido de cada directorio

- `data/uci/`: datos originales del caso UCI Occupancy Detection y documentación del dataset.
- `data/In-gauge-and-en-gage/`: muestra de datos del dataset In-Gauge and En-Gage y diccionarios asociados.
- `notebooks/uci/`: notebook, tablas y figuras del análisis UCI.
- `notebooks/In-gauge-and-en-gage/`: notebook, tablas y resultados del análisis de aulas In-Gauge/En-Gage.
- `src/uci/`: scripts de inferencia, modelos y utilidades del caso UCI.
- `src/In-gauge-and-en-gage/`: modelos entrenados y scripts de inferencia batch del caso In-Gauge/En-Gage.
- `src/api-In-gauge-and-en-gage/`: API FastAPI para predicción online de ocupación.
- `src/frontend-In-gauge-and-en-gage/`: frontend web que consume la API y simula visualmente un aula.

## Datos de entrada

### UCI Occupancy Detection

El caso UCI usa archivos de entrenamiento y test ubicados en:

```text
data/uci/occupancy_detection/
├── datatraining.txt
├── datatest.txt
└── datatest2.txt
```

Variables principales usadas en el enfoque de sensórica:

- `Temperature`
- `Humidity`
- `Light`
- `CO2`
- `HumidityRatio`
- `Occupancy` --> como variable objetivo.

### In-Gauge and En-Gage classrooms

El caso de aulas usa una muestra de ficheros CSV ubicada en:

```text
data/In-gauge-and-en-gage/occupancy_detection_muestra/
├── 19.csv
├── 41.csv
└── KB4.csv
```

Variables usadas por el modelo desplegado en la API:

- `IndoorTemperature`
- `IndoorHumidity`
- `IndoorCO2`
- `IndoorNoise`
- `Occupied` como variable objetivo.

En esta versión se evita usar variables de calendario, horario lectivo o contexto docente para que la predicción dependa de señales ambientales medibles por sensores.

## Resumen del notebook principal In-Gauge/En-Gage

El notebook principal se encuentra en:

```text
notebooks/In-gauge-and-en-gage/CASO_D_CLASSROOM_sensorica.ipynb
```

Flujo general:

1. carga de ficheros CSV por aula;
2. revisión de calidad y usabilidad;
3. selección de variables de sensórica ambiental;
4. partición temporal por aula en train, validation y test final;
5. entrenamiento de varios modelos;
6. selección del mejor modelo usando `F1` en validación;
7. evaluación final sobre `test_final`;
8. exportación de modelos y tablas de resultados.

## Resultados alcanzados

Para In-Gauge/En-Gage, el modelo seleccionado fue **LogisticRegression** usando variables ambientales. En el test final obtuvo aproximadamente:

| Métrica | Valor |
|---|---:|
| Accuracy | 0.8848 |
| Precision | 0.5737 |
| Recall | 0.8911 |
| F1 | 0.6980 |
| AUC ROC | 0.9397 |

La selección se realizó usando `F1` en validación porque el problema puede tener desbalance de clases y porque interesa equilibrar precisión y recall. Para ocupación, un buen recall es relevante porque dejar de detectar aulas ocupadas puede afectar confort, ventilación o climatización.

## Modelos entrenados

En el caso In-Gauge/En-Gage se conservan modelos en:

```text
src/In-gauge-and-en-gage/models/
```

Incluye, entre otros:

- `best_sensorica_ambiental_LogisticRegression.joblib`
- `sensorica_ambiental_DecisionTree.joblib`
- `sensorica_ambiental_GaussianNB.joblib`
- `sensorica_ambiental_HistGradientBoosting.joblib`
- `sensorica_ambiental_Baseline_MostFrequent.joblib`

La API usa el modelo:

```text
src/api-In-gauge-and-en-gage/models/best_sensorica_ambiental_LogisticRegression.joblib
```

## Inferencia batch

### UCI

Desde la raíz `develop/`:

```powershell
cd .\src\uci\inference
python .\infer_uci_occupancy_json.py
```

También puede ejecutarse indicando el Python concreto instalado:

```powershell
cd .\src\uci\inference
& "C:\Program Files\Python31210\python.exe" ".\infer_uci_occupancy_json.py"
```

### In-Gauge and En-Gage

Desde la raíz `develop/`:

```powershell
cd .\src\In-gauge-and-en-gage\inference
python .\infer_classroom_occupancy_json.py
```

## Ejecución de API + frontend con Docker Compose

Desde la raíz del proyecto:

```bash
cd develop
docker compose -f .\docker-compose-caso-d-ingauge.yml up --build
```

Servicios disponibles:

- Frontend: `http://localhost:8080`
- API: `http://localhost:8000`
- Documentación Swagger de la API: `http://localhost:8000/docs`

## Uso directo de la API

Ejemplo de predicción:

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"IndoorTemperature":22.5,"IndoorHumidity":45,"IndoorCO2":850,"IndoorNoise":52}'
```

Respuesta esperada, en formato aproximado:

```json
{
  "prediction": 1,
  "prediction_label": "Ocupado",
  "probability_occupied": 0.82,
  "probability_not_occupied": 0.18,
  "model_name": "LogisticRegression"
}
```

## Ejecución en Google Colab

Los notebooks pueden abrirse directamente desde `notebooks/uci/` o `notebooks/In-gauge-and-en-gage/`. En Colab, se recomienda subir la carpeta completa `develop/` a Google Drive y ajustar las rutas base al directorio montado, por ejemplo:

```python
from google.colab import drive
drive.mount('/content/drive')

BASE_DIR = '/content/drive/MyDrive/develop'
```

A partir de esa ruta, los datos quedan bajo `data/` y las salidas de entrenamiento pueden guardarse en `src/.../models` o en `notebooks/.../tables`.

## Notas importantes

- La API está pensada como demostrador sencillo, no como sistema productivo.
- El frontend consume la API en `http://localhost:8000`.
- El modelo desplegado no usa variables de calendario, hora escolar, número de lección ni estado HVAC.
- Las probabilidades deben interpretarse como apoyo a la decisión, no como verdad absoluta.
