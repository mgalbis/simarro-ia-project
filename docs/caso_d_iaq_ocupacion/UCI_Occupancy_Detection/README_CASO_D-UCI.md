# CASO 4 (D) — Calidad del Aire, Confort Interior y Ocupación

## 1. Objetivo del caso

El objetivo del Caso D es demostrar cómo se puede inferir si una sala o aula está ocupada a partir de variables ambientales, sin utilizar cámaras ni sensores explícitos de presencia.

El problema se formula como una **clasificación binaria supervisada**:

| Clase | Significado |
|---:|---|
| `0` | Sala no ocupada |
| `1` | Sala ocupada |

La motivación operativa es clara: si se puede detectar ocupación a partir de sensores de confort interior, se pueden tomar decisiones de climatización, ventilación, iluminación o eficiencia energética sin invadir la privacidad de las personas.

En esta entrega se trabaja el MVP del caso usando el dataset **UCI Occupancy Detection**, disponible en https://archive.ics.uci.edu/dataset/357/occupancy+detection

---

## 2. Alcance de esta entrega

El enunciado general del Caso D contempla calidad del aire, confort interior, ruido, luminosidad, ocupación, horario lectivo y consumo eléctrico. Esta entrega se limita al dataset UCI, que contiene:

- temperatura interior;
- humedad relativa interior;
- luminosidad;
- concentración de CO₂;
- ratio de humedad;
- etiqueta binaria de ocupación.

El dataset **no incluye** ruido interior, consumo eléctrico, calendario escolar real ni estado de climatización. Esos elementos quedan como posibles extensiones del caso.

---

## 3. Estructura del proyecto

La estructura relativa de la entrega es la siguiente:

```text
.
├── README_CASO_D-UCI.md
│
├── data/
│   ├── README.md
│   ├── DATA_DICTIONARY_CASO_D.md
│   └── occupancy_detection/
│       ├── datatraining.txt
│       ├── datatest.txt
│       └── datatest2.txt
│
├── doc/
│
├── notebooks/
│   ├── CASO_D_UCI_occupancy_eda_ml_v2.ipynb
│   ├── figures/
│   │   ├── balance_clases_train.png
│   │   ├── balance_clases_test1.png
│   │   ├── balance_clases_test2.png
│   │   ├── comparacion_modelos_accuracy.png
│   │   ├── comparacion_modelos_precision.png
│   │   ├── comparacion_modelos_recall.png
│   │   ├── comparacion_modelos_f1.png
│   │   ├── comparacion_modelos_auc_roc.png
│   │   ├── confusion_matrix_best_model.png
│   │   ├── curvas_roc_test_combinado.png
│   │   ├── feature_importance_best_model.png
│   │   ├── matriz_correlacion.png
│   │   └── otros gráficos de EDA
│   └── tables/
│       ├── balance_clases.csv
│       ├── classification_report_best_model.csv
│       ├── confusion_matrix_best_model.csv
│       ├── correlacion_con_occupancy.csv
│       ├── estadistica_descriptiva.csv
│       ├── feature_importance_best_model.csv
│       ├── matriz_correlacion.csv
│       ├── model_results_sensor_features.csv
│       └── model_results_test_combined_ranking.csv
│
└── src/
    ├── auto-eda/
    │   ├── auto_eda_uci_occupancy.py
    │   └── outputs/
    │       └── eda_uci_occupancy/
    │           ├── eda_uci_occupancy_full.html
    │           ├── eda_uci_occupancy_training.html
    │           └── uci_occupancy_clean.csv
    │
    ├── inference/
    │   ├── infer_uci_occupancy_json.py
    │   ├── simulated_cases.json
    │   ├── best_model_LogisticRegression.joblib
    │   ├── best_model_metadata.json
    │   └── inference_results.csv
    │
    └── models/
        ├── Baseline_MostFrequent.joblib
        ├── best_LogisticRegression.joblib
        ├── SVM_RBF.joblib
        ├── RandomForest.joblib
        ├── GradientBoosting.joblib
        └── models_metadata.json
```


---

## 4. Datos de entrada

Los datos originales usados por el notebook están en:

```text
data/occupancy_detection/
```

| Fichero | Uso en la entrega | Descripción |
|---|---|---|
| `data/occupancy_detection/datatraining.txt` | Entrenamiento | Partición usada para ajustar los modelos. |
| `data/occupancy_detection/datatest.txt` | Test 1 | Primera partición de evaluación. |
| `data/occupancy_detection/datatest2.txt` | Test 2 | Segunda partición de evaluación. |

Documentación auxiliar:

| Fichero | Descripción |
|---|---|
| `data/README.md` | Resumen del dataset, fuente y variables principales. |
| `data/DATA_DICTIONARY_CASO_D.md` | Diccionario de datos, tipos, rangos observados y formato de inferencia. |

---

## 5. Variables del problema

Variables de entrada usadas por el modelo principal:

| Variable | Unidad aproximada | Descripción |
|---|---:|---|
| `Temperature` | °C | Temperatura interior. |
| `Humidity` | % | Humedad relativa interior. |
| `Light` | lux | Luminosidad medida por sensor. |
| `CO2` | ppm | Concentración de dióxido de carbono. |
| `HumidityRatio` | kg/kg | Ratio de humedad del aire. |

Variable objetivo:

| Variable | Tipo | Descripción |
|---|---|---|
| `Occupancy` | Binaria | `0` = no ocupado, `1` = ocupado. |

El modelo principal **no usa** `date`, `hour`, `day_of_week`, `is_weekend` ni otras variables temporales como features. Esas variables se generan solo para EDA. La razón es evitar que el modelo aprenda reglas de calendario (sesgos en los findes de semana sin clase) en lugar de patrones ambientales.

---

## 6. Notebook principal

El notebook principal está en:

```text
notebooks/CASO_D_UCI_occupancy_eda_ml_v2.ipynb
```

El notebook realiza el flujo completo:

1. carga de datos;
2. validación básica de columnas, tipos, nulos y duplicados;
3. análisis exploratorio;
4. generación de tablas en `notebooks/tables/`;
5. generación de gráficos en `notebooks/figures/`;
6. entrenamiento de modelos;
7. comparación de métricas sobre test combinado;
8. selección del mejor modelo por `f1`;
9. guardado de todos los modelos probados;
10. generación de metadata y manifest de artefactos.

### 6.1. Ejecución en Google Colab con Drive

La versión actualizada del notebook soporta Google Drive. La estructura recomendada en Drive es:

```text
MyDrive/simarro-cursoia/caso-d-uci/
├── data/
│   └── occupancy_detection/
│       ├── datatraining.txt
│       ├── datatest.txt
│       └── datatest2.txt
├── notebooks/
├── src/
└── README_CASO_D-UCI.md
```

Al ejecutar el notebook en Colab, los resultados nuevos se guardan en:

```text
outputs_uci_occupancy/
├── tables/
├── figures/
├── models/
├── models_metadata.json
└── artifacts_manifest.json
```

Siendo la ruta completa esperada de las salidas: 

```text
/content/drive/MyDrive/simarro-cursoia/caso-d-uci/outputs_uci_occupancy/
```

### 6.2. Ejecución local

También se puede ejecutar de forma local si se abre el notebook. En ese caso, el notebook busca los datos en rutas relativas como:

```text
data/occupancy_detection/
../data/occupancy_detection/
../../data/occupancy_detection/
```

---

## 7. Resultados incluidos en la entrega

### 7.1. Tablas generadas

Las tablas principales ya incluidas están en:

```text
notebooks/tables/
```

| Fichero | Contenido |
|---|---|
| `notebooks/tables/model_results_sensor_features.csv` | Métricas de todos los modelos en cada partición de test. |
| `notebooks/tables/model_results_test_combined_ranking.csv` | Ranking final sobre `test_combined`, ordenado por `f1`. |
| `notebooks/tables/classification_report_best_model.csv` | Classification report del mejor modelo. |
| `notebooks/tables/confusion_matrix_best_model.csv` | Matriz de confusión del mejor modelo. |
| `notebooks/tables/feature_importance_best_model.csv` | Importancia de variables del mejor modelo, cuando está disponible. |
| `notebooks/tables/correlacion_con_occupancy.csv` | Correlación de variables con `Occupancy`. |
| `notebooks/tables/estadistica_descriptiva.csv` | Estadística descriptiva del dataset. |

### 7.2. Figuras generadas

Las figuras principales ya incluidas están en:

```text
notebooks/figures/
```

Ejemplos relevantes:

| Fichero | Contenido |
|---|---|
| `notebooks/figures/comparacion_modelos_f1.png` | Comparación de modelos por F1. |
| `notebooks/figures/comparacion_modelos_auc_roc.png` | Comparación de modelos por AUC ROC. |
| `notebooks/figures/confusion_matrix_best_model.png` | Matriz de confusión del mejor modelo. |
| `notebooks/figures/curvas_roc_test_combinado.png` | Curvas ROC sobre test combinado. |
| `notebooks/figures/feature_importance_best_model.png` | Importancia de variables. |
| `notebooks/figures/matriz_correlacion.png` | Matriz de correlación. |

---

## 8. Modelos entrenados

Los modelos entrenados y entregados están en:

```text
src/models/
```

Modelos incluidos:

| Fichero | Modelo | Comentario |
|---|---|---|
| `src/models/Baseline_MostFrequent.joblib` | Baseline | Modelo de referencia que predice la clase más frecuente. |
| `src/models/best_LogisticRegression.joblib` | Logistic Regression | Mejor modelo según `f1` sobre `test_combined`. |
| `src/models/SVM_RBF.joblib` | SVM con kernel RBF | Modelo no lineal con escalado dentro del pipeline. |
| `src/models/RandomForest.joblib` | Random Forest | Ensamble de árboles. |
| `src/models/GradientBoosting.joblib` | Gradient Boosting | Ensamble secuencial basado en boosting. |
| `src/models/models_metadata.json` | Metadata | Ranking, features, target, métrica de selección y rutas relativas. |

La regla aplicada es:

- todos los modelos probados se guardan en `src/models/`;
- el mejor modelo recibe el prefijo `best_`;
- el resto conserva su nombre normal;
- la metadata se guarda en `src/models/models_metadata.json`.

### 8.1. Ranking final incluido

Según la tabla incluida en:

```text
notebooks/tables/model_results_test_combined_ranking.csv
```

el mejor modelo es:

```text
LogisticRegression
```

con estas métricas aproximadas sobre `test_combined`:

| Modelo | Accuracy | Precision | Recall | F1 | AUC ROC |
|---|---:|---:|---:|---:|---:|
| LogisticRegression | 0.9888 | 0.9601 | 0.9954 | 0.9774 | 0.9952 |
| SVM_RBF | 0.9619 | 0.8667 | 0.9967 | 0.9272 | 0.9934 |
| RandomForest | 0.9540 | 0.8995 | 0.9129 | 0.9062 | 0.9907 |
| GradientBoosting | 0.9482 | 0.9483 | 0.8325 | 0.8867 | 0.9781 |
| Baseline_MostFrequent | 0.7567 | 0.0000 | 0.0000 | 0.0000 | 0.5000 |

---

## 9. Inferencia

La carpeta de inferencia está en:

```text
src/inference/
```

Ficheros incluidos:

| Fichero | Descripción |
|---|---|
| `src/inference/infer_uci_occupancy_json.py` | Script de inferencia desde JSON. |
| `src/inference/simulated_cases.json` | Casos simulados de ejemplo. |
| `src/inference/best_model_LogisticRegression.joblib` | Copia del mejor modelo para ejecutar inferencia directamente desde esta carpeta. |
| `src/inference/best_model_metadata.json` | Metadata necesaria para conocer features y target. |
| `src/inference/inference_results.csv` | Salida generada por el script de inferencia. |

### 9.1. Formato de entrada

Ejemplo de caso de entrada en `src/inference/simulated_cases.json`:

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

No se debe incluir `Occupancy` en inferencia, porque es la variable que el modelo predice.

### 9.2. Ejecución en Windows / PowerShell

Desde la raíz del ZIP descomprimido:

```powershell
cd .\src\inference
python .\infer_uci_occupancy_json.py
```

También puede ejecutarse indicando el Python concreto instalado:

```powershell
cd .\src\inference
& "C:\Program Files\Python31210\python.exe" ".\infer_uci_occupancy_json.py"
```

El script espera encontrar en la carpeta actual:

```text
best_model_LogisticRegression.joblib
best_model_metadata.json
simulated_cases.json
```

La salida se guarda en:

```text
src/inference/inference_results.csv
```

---

## 10. Auto EDA

El script de Auto EDA está en:

```text
src/auto-eda/auto_eda_uci_occupancy.py
```

Los resultados generados e incluidos están en:

```text
src/auto-eda/outputs/eda_uci_occupancy/
```

| Fichero | Descripción |
|---|---|
| `src/auto-eda/outputs/eda_uci_occupancy/eda_uci_occupancy_full.html` | EDA automático del dataset completo. |
| `src/auto-eda/outputs/eda_uci_occupancy/eda_uci_occupancy_training.html` | EDA automático del conjunto de entrenamiento. |
| `src/auto-eda/outputs/eda_uci_occupancy/uci_occupancy_clean.csv` | Dataset consolidado/limpio generado por el proceso de Auto EDA. |

---

## 11. Consistencia de la entrega

La entrega queda organizada con tres niveles de artefactos:

| Nivel | Ruta | Propósito |
|---|---|---|
| Datos | `data/occupancy_detection/` | Ficheros originales de entrenamiento y test. |
| Notebook y resultados | `notebooks/` | EDA, entrenamiento, tablas y figuras ya generadas. |
| Código reutilizable | `src/` | Auto EDA, modelos persistidos e inferencia. |

La versión actualizada del notebook mantiene consistencia con el ZIP porque:

- busca los datos en `data/occupancy_detection/`;
- guarda todos los modelos entrenados;
- marca el mejor con prefijo `best_`;
- actualiza `src/models/models_metadata.json` con rutas relativas;
- actualiza la copia de inferencia en `src/inference/`;
- evita usar variables temporales como features principales del modelo.

---

## 12. Conclusión del caso UCI

El MVP demuestra que, para este dataset, la ocupación puede predecirse con alta calidad usando únicamente variables ambientales. El mejor modelo incluido es `LogisticRegression`, guardado como:

```text
src/models/best_LogisticRegression.joblib
```

La inferencia operativa queda preparada mediante:

```text
src/inference/infer_uci_occupancy_json.py
```

Este caso puede evolucionar hacia un sistema más completo incorporando ruido, consumo energético, calendario lectivo, estado de climatización, información por aula/planta y nuevos datasets de edificios educativos.

El caso está planteado con datos muy limpios y relaciones claras, lo cual genera modelos demasiado precisos y posiblemente sobreajustados a estos caso de UCI.
