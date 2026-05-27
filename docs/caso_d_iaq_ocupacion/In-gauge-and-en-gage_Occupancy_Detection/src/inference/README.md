# CASO D - CLASSROOM - Proyecto de inferencia

Proyecto local para ejecutar inferencia sobre el modelo de ocupación de aulas entrenado con variables de sensórica ambiental del dataset **In-Gauge & En-Gage classrooms**.

## Objetivo

Predecir si un aula está ocupada (`Occupied`) usando únicamente variables ambientales procedentes de sensórica:

- `IndoorTemperature`
- `IndoorHumidity`
- `IndoorCO2`
- `IndoorNoise`

No se usan variables de contexto docente, calendario u operación, como `Day`, `Hour`, `SchoolDay`, `LessonNumber`, `LessonPct`, `CoolingState` o `HeatingState`.

## Estructura esperada

```text
modelo-inferencia/
│
├── infer_classroom_occupancy_json.py
├── best_sensorica_ambiental_<Modelo>.joblib
├── simulated_cases.json
├── best_model_metadata.json
└── requirements.txt
```

El archivo `.joblib` no está incluido en este ZIP porque debe ser el modelo real generado por tu notebook de entrenamiento. Copialo desde Drive, desde la carpeta `models/`, por ejemplo:

```text
best_sensorica_ambiental_LogisticRegression.joblib
```

El script también puede leer `models_metadata.json` si lo copiás desde la salida del notebook.

## Ejemplo de entrada

`simulated_cases.json` debe contener una lista de casos:

```json
[
  {
    "case_id": "caso_1_aula_vacia_bajo_co2_bajo_ruido",
    "IndoorTemperature": 21.4,
    "IndoorHumidity": 42.0,
    "IndoorCO2": 430.0,
    "IndoorNoise": 34.0
  }
]
```

## Instalación

Desde PowerShell o terminal:

```powershell
pip install -r requirements.txt
```

## Ejecución en Windows / PowerShell

```powershell
cd "C:/cursoia/ProyectoFinal/CASOD-Calidad del Aire Ocupacion/CLASSROOM/modelo-inferencia"

& "C:/Program Files/Python31210/python.exe" "./infer_classroom_occupancy_json.py"
```

También se puede ejecutar con:

```powershell
python ./infer_classroom_occupancy_json.py
```

## Salida

El script genera:

```text
inference_results_classroom.csv
```

Incluye:

- variables de entrada,
- predicción `Occupied_pred`,
- etiqueta legible `pred_label`,
- probabilidades `prob_no_ocupado` y `prob_ocupado`, si el modelo lo soporta.

## Notas

El script busca automáticamente un archivo local con patrón:

```text
best_*.joblib
```

Por eso no hace falta hardcodear el nombre exacto del modelo final.
