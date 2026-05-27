# CASO D - Classroom Occupancy Prediction / In-Gauge & En-Gage

Fuente: PhysioNet, dataset **In-Gauge and En-Gage: Understanding Occupants' Behaviour, Engagement, Emotion, and Comfort Indoors with Heterogeneous Sensors and Wearables**, versión 1.0.0.

URL: https://physionet.org/content/in-gauge-and-en-gage/1.0.0/

## 1. Contexto del dataset

El dataset procede de un estudio de campo realizado en un colegio privado K-12 en las afueras de Melbourne, Australia. El recurso combina datos ambientales de aulas, condiciones exteriores, estados de climatización, información de ocupación según horarios de aula y, en otra parte del dataset, datos fisiológicos recogidos con wearables.

Para este caso se utiliza el componente **In-Gauge / Longitudinal**, orientado a sensórica ambiental y comportamiento de ocupación en aulas.

Según la documentación del dataset, el estudio longitudinal In-Gauge contiene ficheros CSV por aula, con una resolución de registro de **5 minutos por fila**. Cada CSV incluye información temporal anonimizada, condiciones meteorológicas exteriores, clima interior, ocupación según horario de clase y estado de los equipos de aire acondicionado.

## 2. Objetivo del caso de uso

El objetivo es construir un modelo de clasificación binaria para predecir si un aula está ocupada o no usando únicamente señales ambientales procedentes de sensórica interior.

```text
Occupied = 0 -> aula no ocupada
Occupied = 1 -> aula ocupada
```

El enfoque del modelo evita usar variables de calendario, horario o contexto docente, aunque puedan ser predictivas. La razón es metodológica: se busca demostrar que la ocupación puede inferirse desde señales físicas medibles por sensores, no desde información administrativa como hora, día, calendario lectivo o número de lección.

## 3. Ficheros de datos

La carpeta longitudinal del dataset contiene un fichero CSV por aula, siendo la estructura observada en los ficheros:

- 169 días anonimizados.
- 288 registros por día, consistentes con una frecuencia de 5 minutos.
- Variable objetivo `Occupied`.
- Variables interiores: temperatura, humedad, CO2 y ruido.
- Variables exteriores: temperatura, humedad, viento, precipitación, radiación solar, etc.
- Variables de contexto docente y calendario.
- Variables de operación HVAC.
- `UsabilityMask` como indicador de calidad/usabilidad.

## 4. Variables principales

Variables usadas como entrada del modelo principal:

```python
SENSOR_FEATURES = [
    "IndoorTemperature",
    "IndoorHumidity",
    "IndoorCO2",
    "IndoorNoise",
]
```

Variable objetivo:

```python
TARGET = "Occupied"
```

Variables excluidas del modelo principal:

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

Estas variables pueden utilizarse en el análisis exploratorio para entender patrones de ocupación, pero no se incluyen como predictores del modelo final.


## 5. Estrategia de modelado recomendada

Para evitar fuga temporal, se recomienda una partición temporal por aula:

```text
Primer 60% temporal por aula   -> entrenamiento
Siguiente 20% temporal por aula -> validación / selección de modelo
Último 20% temporal por aula   -> test final
```

La validación se usa para seleccionar modelo e hiperparámetros. El test final se reserva para una evaluación honesta del rendimiento final.

## 6. Inferencia

El script de inferencia espera un fichero JSON con una lista de casos simulados.

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



