# Diccionario de datos — UCI Occupancy Detection

## 1. Objetivo del dataset

Dataset usado para entrenar modelos de detección de ocupación a partir de variables ambientales interiores.

Variable objetivo:

- `Occupancy`: indica si la estancia está ocupada (`1`) o no ocupada (`0`).

## 2. Ficheros esperados

| Fichero | Uso |
|---|---|
| `datatraining.txt` | Entrenamiento. |
| `datatest.txt` | Test 1. |
| `datatest2.txt` | Test 2. |

## 3. Variables

| Variable original | Nombre normalizado | Tipo | Unidad | Descripción |
|---|---|---|---|---|
| `date` | `timestamp` | datetime | ISO 8601 | Fecha y hora de la medición. |
| `Temperature` | `temperature` | float | °C | Temperatura interior. |
| `Humidity` | `humidity` | float | % | Humedad relativa interior. |
| `Light` | `light` | float | lux aprox. | Nivel de luminosidad. |
| `CO2` | `co2` | float | ppm | Concentración de dióxido de carbono. |
| `HumidityRatio` | `humidity_ratio` | float | kg/kg aprox. | Ratio de humedad. |
| `Occupancy` | `occupancy` | int | binario | Ocupación: 1 ocupado, 0 no ocupado. |

## 4. Reglas de validación

| Variable | Regla |
|---|---|
| `timestamp` | No nulo, parseable como fecha, sin duplicados. |
| `temperature` | Rango físico esperado: 0-50 °C. |
| `humidity` | Rango esperado: 0-100 %. |
| `light` | Valor no negativo. |
| `co2` | Rango esperado: 300-5000 ppm. |
| `humidity_ratio` | Valor no negativo. |
| `occupancy` | Solo valores 0 o 1. |

## 5. Transformaciones previstas

1. Renombrar columnas a `snake_case`.
2. Convertir `timestamp` a datetime.
3. Ordenar por `timestamp`.
4. Eliminar índice artificial si existe.
5. Validar nulos y duplicados.
6. Mantener particiones originales de train/test.
7. Exportar CSV procesado.

## 6. Features de modelado

Features base:

- `temperature`
- `humidity`
- `light`
- `co2`
- `humidity_ratio`

Features temporales opcionales:

- `hour`
- `day_of_week`
- `is_weekend`

Variable objetivo:

- `occupancy`

## 7. Consideraciones de modelado

- No mezclar test con entrenamiento.
- Comparar siempre contra baseline.
- Evaluar con métricas de clasificación binaria.
- No usar solo accuracy si hay desbalance de clases.
- Documentar importancia de variables.
- Registrar todos los experimentos en MLflow.

## 8. Métricas de calidad de datos

| Métrica | Descripción |
|---|---|
| Completitud | Porcentaje de valores no nulos por columna. |
| Consistencia | Porcentaje de valores dentro de rangos plausibles. |
| Unicidad | Ausencia de timestamps duplicados. |
| Validez temporal | Orden temporal y ausencia de gaps graves. |
| Balance de clases | Proporción de `occupancy=0` y `occupancy=1`. |

## 9. Salidas esperadas

```text
data/processed/occupancy_train.csv
data/processed/occupancy_test1.csv
data/processed/occupancy_test2.csv
reports/data_quality_occupancy.csv
```
