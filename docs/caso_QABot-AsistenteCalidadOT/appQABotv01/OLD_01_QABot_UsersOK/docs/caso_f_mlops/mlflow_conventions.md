# Convenciones MLflow

## Objetivo

Definir una forma común de registrar experimentos para todos los casos de uso.

## Nombre de experimento

Formato:

```text
Caso{CASO}_{DATASET}_{OBJETIVO}
```

Ejemplos:

```text
CasoF_MLOps_Demo
CasoD_UCI_Occupancy
CasoD_InGauge_Occupancy
CasoQABot_TestQuality
```

## Nombre de run

Formato:

```text
{algorithm}_{dataset}_{YYYYMMDD_HHMM}_{author}
```

Ejemplo:

```text
RandomForest_uci_occupancy_20260512_1830_federico
```

## Tags obligatorios

Todo run debe incluir:

```python
{
    "case_use": "F",
    "dataset": "mlops_demo",
    "data_layer": "gold",
    "algorithm": "RandomForest",
    "stage": "dev",
    "author": "nombre",
    "git_commit": "abc123",
    "git_branch": "feature/case-f-mlops",
    "lakefs_repo": "uci_occupancy",
    "lakefs_branch": "main",
    "lakefs_commit": "def456",
    "lakefs_tag": "uci_occupancy_gold_v1",
    "captia_schema_version": "captia_schema_v1"
}
```

## Métricas mínimas

### Clasificación

```text
accuracy
precision
recall
f1
roc_auc
```

### Regresión

```text
mae
rmse
mape
r2
```

### Calidad / QABot

```text
tests_generated
tests_executed
pass_rate
fail_rate
execution_time_seconds
```

## Artefactos mínimos

```text
metrics.json
params.json
training_config.yml
requirements.txt
model.pkl
confusion_matrix.png
feature_importance.png
```

## Estados del experimento

| Stage | Uso |
|---|---|
| `dev` | Experimento en desarrollo. |
| `candidate` | Modelo candidato a validación. |
| `validated` | Modelo revisado y aceptado. |
| `production-ready` | Preparado para reutilización futura. |
| `archived` | Descartado o reemplazado. |
