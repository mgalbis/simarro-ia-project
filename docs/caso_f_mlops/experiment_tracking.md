# Seguimiento de experimentos

## Objetivo

Garantizar que cada experimento queda asociado a su código, datos, parámetros, métricas y artefactos.

## Flujo mínimo

```text
1. Dataset versionado en lakeFS
2. Schema CAPTIA versionado
3. Código versionado en Git
4. Entrenamiento ejecutado
5. Run registrado en MLflow
6. Integridad validada
```

## Información que debe guardar cada run

### Parámetros

Ejemplos:

```text
model_type
n_estimators
max_depth
random_state
train_split
test_split
```

### Métricas

Según el tipo de problema:

```text
accuracy, precision, recall, f1, roc_auc
mae, rmse, mape, r2
pass_rate, fail_rate, execution_time_seconds
```

### Tags de trazabilidad

```text
case_use
dataset
data_layer
algorithm
stage
author
git_commit
git_branch
lakefs_repo
lakefs_branch
lakefs_commit
lakefs_tag
captia_schema_version
```

### Artefactos

```text
model.pkl
metrics.json
params.json
training_config.yml
requirements.txt
plots/*.png
```

## Validación de integridad

Un run es válido si:

- tiene todos los tags obligatorios;
- contiene métricas;
- contiene parámetros;
- contiene al menos un artefacto;
- referencia un tag lakeFS existente;
- referencia un commit Git;
- indica versión del schema CAPTIA.

Script previsto:

```bash
python scripts/mlops/check_mlops_integrity.py
```
