# CASO 4 (D) — Calidad del Aire, Confort Interior y Ocupación

## 1. Objetivo del caso

El objetivo del caso es analizar variables de confort interior y desarrollar modelos capaces de detectar si un aula o sala está ocupada a partir de variables ambientales, sin utilizar cámaras ni sensores explícitos de presencia.

El problema principal es de **clasificación binaria supervisada**:

- `Occupancy = 0` → sala no ocupada.
- `Occupancy = 1` → sala ocupada.

La idea de fondo es que mantener climatización o iluminación activa en un aula vacía supone un uso ineficiente de energía. Si se puede inferir la ocupación a partir de sensores ambientales, se puede alimentar un sistema de optimización de climatización, iluminación, confort interior o eficiencia energética.

En este MVP se usa el dataset **UCI Occupancy Detection**, un dataset pequeño, limpio y adecuado para una primera aproximación docente al problema.

## 2. Problema de predicción que se resuelve

Se entrena un modelo de Machine Learning para predecir si una sala está ocupada o no a partir de estas variables de entrada:

| Variable | Unidad | Descripción |
|---|---:|---|
| `Temperature` | °C | Temperatura ambiente interior. |
| `Humidity` | % | Humedad relativa interior. |
| `Light` | lux aprox. | Nivel de luminosidad. Valores altos suelen indicar sala iluminada. |
| `CO2` | ppm | Concentración de dióxido de carbono. Suele aumentar cuando hay personas respirando en la sala. |
| `HumidityRatio` | kg/kg | Razón de humedad: kg de vapor de agua por kg de aire seco. |

La variable objetivo es:

| Variable | Tipo | Descripción |
|---|---|---|
| `Occupancy` | Entero binario | Etiqueta de ocupación: `0` no ocupado, `1` ocupado. |

Aunque el enunciado general del Caso D menciona CO₂, temperatura, humedad, ruido, luminosidad, horario lectivo y consumo eléctrico, este MVP se centra en el dataset UCI, que incluye temperatura, humedad, luz, CO₂ y ratio de humedad. No incluye ruido ni consumo eléctrico.

## 3. Contexto de los datos de entrada

El dataset representa lecturas temporales de sensores ambientales en una sala interior. Cada fila corresponde a una medición en un instante temporal y contiene valores ambientales más la etiqueta real de ocupación.

Ejemplo de entrada para inferencia:

```json
{
  "Temperature": 20.3,
  "Humidity": 27.2,
  "Light": 0.0,
  "CO2": 455.0,
  "HumidityRatio": 0.00475
}
```

Interpretación:

| Variable | Valor | Lectura |
|---|---:|---|
| `Temperature` | `20.3` | 20.3 °C. |
| `Humidity` | `27.2` | 27.2 % de humedad relativa. |
| `Light` | `0.0` | 0 lux aproximadamente, sala apagada u oscura. |
| `CO2` | `455.0` | 455 ppm, nivel bajo/cercano al aire exterior. |
| `HumidityRatio` | `0.00475` | kg vapor de agua / kg aire seco. |

En términos intuitivos:

- `Light` alto + `CO2` alto suele ser un patrón compatible con sala ocupada.
- `Light` bajo + `CO2` bajo suele ser un patrón compatible con sala no ocupada.
- `HumidityRatio` es una variable derivada de temperatura y humedad, por eso tiene valores pequeños.

## 4. Estructura del proyecto

Estructura relevante de carpetas y ficheros:

```text
.
├── data/
│   ├── README.md
│   └── occupancy_detection/
│       ├── datatraining.txt
│       ├── datatest.txt
│       └── datatest2.txt
│
├── notebooks/
│   ├── CASO_D_UCI_occupancy_eda_ml.ipynb
│   ├── best_model_LogisticRegression.joblib
│   ├── best_model_metadata.json
│   └── model_results_with_time_comparison.csv
│
└── src/
    ├── auto-eda/
    │   └── auto_eda_uci_occupancy.py
    │
    └── inference/
        ├── infer_uci_occupancy_json.py
        ├── simulated_cases.json
        ├── best_model_LogisticRegression.joblib
        ├── best_model_metadata.json
        └── inference_results.csv
```

## 5. Datos

Los datos están en:

```text
data/occupancy_detection/
```

Ficheros principales:

| Fichero | Uso | Descripción |
|---|---|---|
| `datatraining.txt` | Entrenamiento | Partición usada para entrenar los modelos. |
| `datatest.txt` | Test 1 | Primera partición de validación/test. |
| `datatest2.txt` | Test 2 | Segunda partición de validación/test. |

El notebook carga los tres ficheros, convierte la columna `date` a tipo fecha y añade una columna `split` para identificar el origen de cada registro.

## 6. Notebook de EDA y entrenamiento

El notebook principal está en:

```text
notebooks/CASO_D_UCI_occupancy_eda_ml.ipynb
```

Este notebook realiza el flujo completo del caso:

1. Carga de datos de entrenamiento y test.
2. Limpieza y validación básica.
3. Revisión inicial de columnas, tipos, nulos, duplicados y rango temporal.
4. Creación de variables temporales para EDA: hora, día de semana y fin de semana.
5. Estadística descriptiva.
6. Análisis del balance de clases.
7. Distribución de variables ambientales.
8. Comparación de variables según ocupación.
9. Evolución temporal de variables.
10. Matriz de correlación.
11. Preparación para Machine Learning.
12. Entrenamiento y comparación de modelos.
13. Selección y guardado del mejor modelo.

El modelo principal se entrena usando solo variables ambientales:

```python
SENSOR_FEATURES = [
    "Temperature",
    "Humidity",
    "Light",
    "CO2",
    "HumidityRatio",
]
```

Se evita usar variables como día de la semana, fin de semana u hora en el modelo principal para que el aprendizaje dependa de los sensores y no memorice patrones de calendario. Esto es importante porque un modelo que aprendiera que los fines de semana siempre está vacío podría fallar si hubiera una clase excepcional un sábado.

## 7. Modelos entrenados

El notebook compara varios clasificadores supervisados:

| Modelo | Descripción |
|---|---|
| `DummyClassifier` | Baseline simple para comparar si los modelos reales aportan valor. |
| `LogisticRegression` | Modelo lineal interpretable. |
| `SVM_RBF` | Clasificador de margen máximo con kernel RBF. |
| `RandomForest` | Ensamble de árboles de decisión. |
| `GradientBoosting` | Ensamble secuencial basado en boosting. |

Las métricas usadas son:

| Métrica | Interpretación |
|---|---|
| `accuracy` | Proporción total de aciertos. |
| `precision` | De los casos predichos como ocupados, cuántos eran realmente ocupados. |
| `recall` | De los casos realmente ocupados, cuántos detectó el modelo. |
| `f1` | Media armónica entre precision y recall. |
| `auc_roc` | Capacidad de separación entre clases a distintos umbrales. |

La selección del mejor modelo se realiza según `F1-score` sobre el test combinado.

## 8. Modelo seleccionado

El modelo seleccionado y guardado es:

```text
best_model_LogisticRegression.joblib
```

La metadata asociada está en:

```text
best_model_metadata.json
```

Contenido conceptual de la metadata:

```json
{
  "best_model_name": "LogisticRegression",
  "features": [
    "Temperature",
    "Humidity",
    "Light",
    "CO2",
    "HumidityRatio"
  ],
  "target": "Occupancy",
  "selection_metric": "f1 on test_combined"
}
```

El modelo guardado es un pipeline de scikit-learn. Por eso, en inferencia no hace falta escalar manualmente las variables de entrada si el escalado se guardó dentro del pipeline. El script de inferencia solo debe entregar las columnas correctas, en el orden esperado y con valores numéricos válidos.

## 9. Inferencia

Los ficheros de inferencia están en:

```text
src/inference/
```

Ficheros principales:

| Fichero | Descripción |
|---|---|
| `infer_uci_occupancy_json.py` | Script Python que carga el modelo, la metadata y los casos a inferir desde JSON. |
| `simulated_cases.json` | Casos simulados de entrada para probar el modelo. |
| `best_model_LogisticRegression.joblib` | Modelo entrenado guardado. |
| `best_model_metadata.json` | Metadata del modelo: features, target y nombre del modelo. |
| `inference_results.csv` | Salida generada con las predicciones. |

### 9.1. Formato del JSON de entrada

El fichero `simulated_cases.json` contiene una lista de casos:

```json
[
  {
    "case_id": "caso_1_sala_apagada_bajo_co2",
    "Temperature": 20.3,
    "Humidity": 27.2,
    "Light": 0.0,
    "CO2": 455.0,
    "HumidityRatio": 0.00475
  },
  {
    "case_id": "caso_2_luz_media_co2_moderado",
    "Temperature": 21.1,
    "Humidity": 27.8,
    "Light": 160.0,
    "CO2": 690.0,
    "HumidityRatio": 0.005
  },
  {
    "case_id": "caso_3_sala_iluminada_co2_alto",
    "Temperature": 22.0,
    "Humidity": 29.5,
    "Light": 430.0,
    "CO2": 1040.0,
    "HumidityRatio": 0.0057
  }
]
```

### 9.2. Ejecución en Windows / PowerShell

Desde la carpeta de inferencia:

```powershell
cd "C:\cursoia\ProyectoFinal\CASOD-Calidad del Aire Ocupación\UCI_Occupancy_Detection\src\inference"

& "C:\Program Files\Python31210\python.exe" ".\infer_uci_occupancy_json.py"
```

El script busca los ficheros en el directorio actual desde donde se ejecuta el comando:

```python
BASE_DIR = Path.cwd()
```

Por eso deben estar juntos en la misma carpeta:

```text
infer_uci_occupancy_json.py
simulated_cases.json
best_model_LogisticRegression.joblib
best_model_metadata.json
```

### 9.3. Tratamiento de la entrada en inferencia

El script realiza estas validaciones:

1. Carga el JSON externo.
2. Convierte la lista de casos a `pandas.DataFrame`.
3. Verifica que estén todas las columnas requeridas por `best_model_metadata.json`.
4. Ordena las columnas según el orden usado en entrenamiento.
5. Convierte los valores a numérico.
6. Lanza error si hay columnas faltantes, nulos o valores no numéricos.
7. Ejecuta `model.predict(X)` y, si está disponible, `model.predict_proba(X)`.
8. Guarda el resultado en `inference_results.csv`.

No se debe incluir la variable objetivo `Occupancy` en los casos nuevos, porque justamente es lo que se quiere predecir.

## 10. Auto EDA

El script:

```text
src/auto-eda/auto_eda_uci_occupancy.py
```

sirve como apoyo para generar un análisis exploratorio automático del dataset. Es útil para obtener rápidamente una revisión inicial de columnas, distribuciones, nulos, rangos y posibles relaciones entre variables.

## 11. Conclusiones del MVP

- El dataset es limpio y adecuado para un primer MVP del Caso D.
- La variable objetivo `Occupancy` permite plantear un problema claro de clasificación binaria.
- La baseline permite comprobar que los modelos realmente aportan valor.
- Las variables ambientales, especialmente `Light` y `CO2`, muestran una relación fuerte con la ocupación.
- El modelo seleccionado puede integrarse posteriormente en una app, dashboard o pipeline para estimar ocupación sin cámaras ni sensores explícitos de presencia.
- En este MVP se decidió no usar día de semana ni hora como variables de entrenamiento principal para evitar que el modelo dependa demasiado del calendario y no de la sensórica.

## 12. Posibles extensiones

Como evolución del caso, se podría ampliar el dataset con:

- Nivel de ruido interior.
- Consumo eléctrico por aula o zona.
- Horario lectivo real.
- Calendario escolar.
- Estado de climatización e iluminación.
- Datos por edificio, planta o aula.

Esto permitiría pasar de una predicción de ocupación a un sistema más completo de confort interior, eficiencia energética y operación inteligente de espacios docentes.
