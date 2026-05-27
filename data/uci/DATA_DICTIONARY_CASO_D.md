# Diccionario de datos — CASO D / UCI Occupancy Detection

Este documento describe los datos ubicados en:

```text
data/occupancy_detection/
```

## 1. Ficheros disponibles

| Fichero | Filas | Columnas | Uso |
|---|---:|---:|---|
| `datatraining.txt` | 8.143 | 7 | Entrenamiento del modelo. |
| `datatest.txt` | 2.665 | 7 | Primera partición de test. |
| `datatest2.txt` | 9.752 | 7 | Segunda partición de test. |

Los tres ficheros tienen la misma estructura de columnas.

## 2. Esquema de columnas

| Columna | Tipo en pandas | Unidad | Descripción | Uso en modelo |
|---|---|---:|---|---|
| `date` | `datetime64[ns]` después de conversión | — | Marca temporal de la medición. En origen se lee como texto y luego se convierte a fecha. | No se usa como feature principal. Se usa para EDA temporal. |
| `Temperature` | `float64` | °C | Temperatura interior de la sala. | Feature de entrada. |
| `Humidity` | `float64` | % | Humedad relativa interior. | Feature de entrada. |
| `Light` | `float64` | lux aprox. | Nivel de luminosidad medido por sensor. | Feature de entrada. |
| `CO2` | `float64` | ppm | Concentración de CO₂. | Feature de entrada. |
| `HumidityRatio` | `float64` | kg/kg | Razón de humedad: kg de vapor de agua por kg de aire seco. | Feature de entrada. |
| `Occupancy` | `int64` | 0/1 | Variable objetivo. `0` significa no ocupado y `1` ocupado. | Target. |

## 3. Variable objetivo

```text
Occupancy = 0 → sala no ocupada
Occupancy = 1 → sala ocupada
```

El objetivo del modelo es inferir esta variable a partir de los sensores ambientales.

## 4. Variables usadas para entrenamiento

El modelo principal usa únicamente variables ambientales:

```python
SENSOR_FEATURES = [
    "Temperature",
    "Humidity",
    "Light",
    "CO2",
    "HumidityRatio",
]
```

No se usan como features principales:

- `date`
- `hour`
- `day_of_week`
- `is_weekend`

Estas variables temporales sí pueden crearse para análisis exploratorio, pero no se incluyen en el modelo principal para evitar que el modelo aprenda reglas de calendario en lugar de patrones de sensórica.

## 5. Variables temporales derivadas para EDA

A partir de `date`, el notebook puede crear columnas auxiliares:

| Columna derivada | Tipo | Descripción | Uso |
|---|---|---|---|
| `hour` | `int` | Hora del día, de 0 a 23. | Análisis exploratorio. |
| `day_of_week` | `int` | Día de la semana: lunes = 0, domingo = 6. | Análisis exploratorio. |
| `is_weekend` | `int` | `1` si es sábado o domingo, `0` en caso contrario. | Análisis exploratorio. |
| `day_name` | `str` | Nombre del día en español. | Visualización. |
| `weekend_label` | `str` | `Entre semana` o `Fin de semana`. | Visualización. |

Estas columnas no existen en los ficheros originales. Se generan en el notebook.

## 6. Rangos observados por fichero

### `datatraining.txt`

| Variable | Mínimo | Máximo | Media |
|---|---:|---:|---:|
| `Temperature` | 19.000000 | 23.180000 | 20.619084 |
| `Humidity` | 16.745000 | 39.117500 | 25.731507 |
| `Light` | 0.000000 | 1546.333333 | 119.519375 |
| `CO2` | 412.750000 | 2028.500000 | 606.546243 |
| `HumidityRatio` | 0.002674 | 0.006476 | 0.003863 |
| `Occupancy` | 0 | 1 | 0.212330 |

### `datatest.txt`

| Variable | Mínimo | Máximo | Media |
|---|---:|---:|---:|
| `Temperature` | 20.200000 | 24.408333 | 21.433876 |
| `Humidity` | 22.100000 | 31.472500 | 25.353937 |
| `Light` | 0.000000 | 1697.250000 | 193.227556 |
| `CO2` | 427.500000 | 1402.250000 | 717.906470 |
| `HumidityRatio` | 0.003303 | 0.005378 | 0.004027 |
| `Occupancy` | 0 | 1 | 0.364728 |

### `datatest2.txt`

| Variable | Mínimo | Máximo | Media |
|---|---:|---:|---:|
| `Temperature` | 19.500000 | 24.390000 | 21.001768 |
| `Humidity` | 21.865000 | 39.500000 | 29.891910 |
| `Light` | 0.000000 | 1581.000000 | 123.067930 |
| `CO2` | 484.666667 | 2076.500000 | 753.224832 |
| `HumidityRatio` | 0.003275 | 0.005769 | 0.004589 |
| `Occupancy` | 0 | 1 | 0.210111 |

## 7. Tipos esperados para inferencia

El fichero `src/inference/simulated_cases.json` debe contener una lista de objetos JSON. Cada objeto representa un caso a inferir.

Ejemplo:

```json
{
  "case_id": "caso_1_sala_apagada_bajo_co2",
  "Temperature": 20.3,
  "Humidity": 27.2,
  "Light": 0.0,
  "CO2": 455.0,
  "HumidityRatio": 0.00475
}
```

Tipos esperados:

| Campo | Tipo JSON | Obligatorio | Comentario |
|---|---|---|---|
| `case_id` | `string` | No, pero recomendado | Identificador del caso. Si no existe, el script puede generarlo. |
| `Temperature` | `number` | Sí | Temperatura en °C. |
| `Humidity` | `number` | Sí | Humedad relativa en %. |
| `Light` | `number` | Sí | Iluminancia en lux aprox. |
| `CO2` | `number` | Sí | Concentración de CO₂ en ppm. |
| `HumidityRatio` | `number` | Sí | Razón de humedad kg/kg. |

No se debe incluir `Occupancy` en los casos nuevos, porque es la variable que el modelo predice.

## 8. Salida de inferencia

El script de inferencia genera un fichero:

```text
src/inference/inference_results.csv
```

Columnas habituales de salida:

| Columna | Descripción |
|---|---|
| `case_id` | Identificador del caso. |
| `Temperature`, `Humidity`, `Light`, `CO2`, `HumidityRatio` | Valores de entrada usados por el modelo. |
| `Occupancy_pred` | Predicción binaria del modelo: `0` o `1`. |
| `pred_label` | Etiqueta legible: `No ocupado` u `Ocupado`. |
| `prob_no_ocupado` | Probabilidad estimada de clase 0, si el modelo lo permite. |
| `prob_ocupado` | Probabilidad estimada de clase 1, si el modelo lo permite. |

## 9. Notas de calidad de datos

- El dataset es limpio y adecuado para prácticas introductorias.
- No se esperan grandes tareas de imputación de nulos.
- Las variables tienen escalas muy diferentes; por ejemplo, `CO2` está en cientos o miles de ppm, mientras `HumidityRatio` está alrededor de 0.003 a 0.006.
- Si el modelo se guarda como pipeline con escalado interno, no es necesario escalar manualmente en inferencia.
- En inferencia se deben validar siempre columnas faltantes, valores nulos y tipos no numéricos.
