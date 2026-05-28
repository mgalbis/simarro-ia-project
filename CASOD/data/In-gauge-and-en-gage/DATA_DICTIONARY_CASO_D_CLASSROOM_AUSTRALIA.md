# Diccionario de datos — CASO D / Classroom Occupancy Prediction Australia

Este documento describe los datos del caso de predicción de ocupación en aulas usando el dataset **In-Gauge and En-Gage**, publicado en PhysioNet.

Ruta de referencia del dataset:

```text
https://physionet.org/content/in-gauge-and-en-gage/1.0.0/
```

El proyecto consta de un dataset de 16 Ficheros con la siguiente estructura:


## 1. Esquema de columnas

| Columna | Tipo observado en pandas | Unidad / valores | Descripción | Uso recomendado |
|---|---|---|---|---|
| `Time` | `object` | `HH:MM:SS` | Hora anonimizada del día. Hay 288 valores por día, consistente con intervalos de 5 minutos. | EDA temporal. No usar como feature principal. |
| `Day` | `int64` | 1 a 169 en la muestra | Día anonimizado de la medición. | EDA temporal y split temporal. No usar como feature principal. |
| `Occupied` | `int64` | 0/1 | Variable objetivo. `0` = aula no ocupada, `1` = aula ocupada. | Target. |
| `SchoolDay` | `int64` | 0/1 | Indica si corresponde a día escolar. | Contexto docente. Excluir del modelo principal. |
| `Hour` | `int64` | 0 a 23 | Hora del día derivada. | EDA temporal. Excluir del modelo principal. |
| `LessonNumber` | `int64` | -1 a 9 en la muestra | Número de lección o clase; `-1` suele indicar fuera de clase. | Contexto docente. Excluir del modelo principal. |
| `LessonPct` | `float64` | -1 a 1,875 en la muestra | Progreso relativo dentro de la lección. | Contexto docente. Excluir del modelo principal. |
| `IndoorTemperature` | `float64` | °C | Temperatura interior del aula. | Feature de entrada del modelo. |
| `IndoorHumidity` | `int64` | % | Humedad relativa interior. | Feature de entrada del modelo. |
| `IndoorCO2` | `int64` | ppm | Concentración de CO2 interior. | Feature de entrada del modelo. |
| `IndoorNoise` | `int64` | dB aprox. | Nivel de ruido interior. | Feature de entrada del modelo. |
| `OutdoorTemperature` | `float64` | °C | Temperatura exterior. | EDA/variable auxiliar. No usada en el modelo sensórico interior principal. |
| `OutdoorHumidity` | `float64` | % | Humedad relativa exterior. | EDA/variable auxiliar. |
| `OutdoorDewpoint` | `float64` | °C | Punto de rocío exterior. | EDA/variable auxiliar. |
| `OutdoorWindDirection` | `float64` | grados | Dirección del viento exterior. | EDA/variable auxiliar. |
| `OutdoorWindSpeed` | `float64` | velocidad del viento | Velocidad del viento exterior. | EDA/variable auxiliar. |
| `OutdoorGustSpeed` | `float64` | velocidad de ráfaga | Velocidad de ráfagas exteriores. | EDA/variable auxiliar. |
| `Precipitation` | `float64` | precipitación | Precipitación registrada. | EDA/variable auxiliar. |
| `UvLevel` | `float64` | índice UV | Nivel de radiación UV. | EDA/variable auxiliar. |
| `SolarRadiation` | `float64` | radiación solar | Radiación solar exterior. | EDA/variable auxiliar. |
| `CoolingState` | `int64` | 0/1 | Estado de refrigeración HVAC. | Variable de operación. Excluir del modelo principal. |
| `HeatingState` | `int64` | 0/1 | Estado de calefacción HVAC. | Variable de operación. Excluir del modelo principal. |
| `UsabilityMask` | `bool` | True/False | Indicador de calidad/usabilidad del registro. | Filtro de calidad. No usar como feature. |

## 2. Variable objetivo

```text
Occupied = 0 -> aula no ocupada
Occupied = 1 -> aula ocupada
```

## 3. Variables usadas para entrenamiento

El modelo principal debe usar únicamente variables ambientales interiores, es decir, variables que podrían provenir de sensórica instalada en el aula:

```python
SENSOR_FEATURES = [
    "IndoorTemperature",
    "IndoorHumidity",
    "IndoorCO2",
    "IndoorNoise",
]
```

Estas variables representan:

| Variable | Interpretación |
|---|---|
| `IndoorTemperature` | Condición térmica interior. |
| `IndoorHumidity` | Humedad relativa interior. |
| `IndoorCO2` | Señal asociada a presencia humana y ventilación. |
| `IndoorNoise` | Señal acústica asociada a actividad en el aula. |

## 4. Variables excluidas del modelo principal

Las siguientes variables pueden ser predictivas, pero se excluyen del modelo principal porque codifican calendario, horario, planificación docente, operación o calidad del registro:

```python
EXCLUDED_CONTEXT_FEATURES = [
    "Day",
    "Hour",
    "SchoolDay",
    "LessonNumber",
    "LessonPct",
    "CoolingState",
    "HeatingState",
    "Time",
    "UsabilityMask",
]
```

Criterio de exclusión:

| Variable | Motivo |
|---|---|
| `Day`, `Hour`, `Time` | Codifican información temporal. El modelo podría aprender horarios en lugar de sensórica. |
| `SchoolDay`, `LessonNumber`, `LessonPct` | Codifican contexto docente y calendario lectivo. |
| `CoolingState`, `HeatingState` | Codifican operación HVAC, que puede estar asociada indirectamente a horarios o reglas de operación. |
| `UsabilityMask` | Es una máscara de calidad, útil para filtrar pero no para predecir. |


## 5. Estrategia de partición de datos

La partición recomendada es temporal, no aleatoria:

```text
Primer 60% temporal por aula   -> entrenamiento
Siguiente 20% temporal por aula -> validación / selección de modelo
Último 20% temporal por aula   -> test final
```

Motivo:

- Evita que el modelo entrene con datos futuros y evalúe sobre datos pasados.
- Respeta la naturaleza secuencial del problema.
- Permite usar validación para selección de modelo e hiperparámetros.
- Reserva el test final para una evaluación honesta.

## 6. Tipos esperados para inferencia

El fichero de inferencia `simulated_cases.json` debe contener una lista de objetos JSON.

Ejemplo:

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

Tipos esperados:

| Campo | Tipo JSON | Obligatorio | Comentario |
|---|---|---|---|
| `case_id` | `string` | No, pero recomendado | Identificador legible del caso. |
| `IndoorTemperature` | `number` | Sí | Temperatura interior. |
| `IndoorHumidity` | `number` | Sí | Humedad relativa interior. |
| `IndoorCO2` | `number` | Sí | CO2 interior en ppm. |
| `IndoorNoise` | `number` | Sí | Ruido interior. |

No se debe incluir `Occupied` en casos nuevos de inferencia.

## 7. Salida de inferencia

El script de inferencia genera un fichero CSV con resultados, por ejemplo:

```text
src/inference/inference_results_classroom.csv
```

Columnas habituales:

| Columna | Descripción |
|---|---|
| `case_id` | Identificador del caso. |
| `IndoorTemperature`, `IndoorHumidity`, `IndoorCO2`, `IndoorNoise` | Variables usadas por el modelo. |
| `Occupied_pred` | Predicción binaria: `0` o `1`. |
| `pred_label` | Etiqueta legible: `No ocupado` u `Ocupado`. |
| `prob_no_ocupado` | Probabilidad estimada de clase 0, si el modelo lo permite. |
| `prob_ocupado` | Probabilidad estimada de clase 1, si el modelo lo permite. |

## 8. Notas de calidad de datos

- La ocupación se deriva del horario de clases, no necesariamente de un sensor de presencia físico.
- Las variables `SchoolDay`, `LessonNumber` y `LessonPct` pueden tener alta capacidad predictiva, pero se excluyen del modelo principal para evitar dependencia del calendario.
- El desbalance de clases es relevante: en `19.csv`, la clase ocupada representa aproximadamente el 11,30% del total.
- `UsabilityMask` debe tratarse como filtro de calidad, no como predictor.
- Las variables tienen escalas distintas; si se usan modelos sensibles a escala, conviene guardar el modelo como `Pipeline` con escalado interno.
