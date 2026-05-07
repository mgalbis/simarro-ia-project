# Convenciones de MLflow

## 1. Objetivo

Estandarizar el registro de experimentos para que todos los resultados sean comparables y reproducibles.

## 2. Nombre de experimentos

Formato:

```text
<Caso>_<Dataset>_<Objetivo>
```

Ejemplos:

```text
CasoD_UCI_Occupancy
CasoD_IAQ_Rules
QABot_TestGeneration
```

## 3. Nombre de runs

Formato:

```text
<algoritmo>_<fecha>_<iniciales_responsable>
```

Ejemplos:

```text
random_forest_20260512_p3
xgboost_20260513_p3
qabot_api_agent_20260514_p5
```

## 4. Tags obligatorios

| Tag | Descripción | Ejemplo |
|---|---|---|
| `case_use` | Caso de uso | `D`, `F`, `QABot` |
| `dataset_name` | Nombre dataset | `uci_occupancy` |
| `lakefs_repo` | Repositorio lakeFS | `uci_occupancy` |
| `lakefs_tag` | Versión dataset | `uci_occupancy_clean_v1` |
| `git_commit` | Commit Git | `a1b2c3d` |
| `owner` | Responsable | `P3` |
| `stage` | Fase | `baseline`, `training`, `evaluation` |

## 5. Parámetros para modelos de ocupación

Parámetros comunes:

- `algorithm`
- `features`
- `target`
- `train_rows`
- `test_rows`
- `scaler`
- `random_state`

Parámetros específicos:

Random Forest:

- `n_estimators`
- `max_depth`
- `min_samples_split`
- `class_weight`

Logistic Regression:

- `penalty`
- `C`
- `solver`
- `max_iter`

SVM:

- `kernel`
- `C`
- `gamma`

XGBoost / Gradient Boosting:

- `n_estimators`
- `learning_rate`
- `max_depth`

## 6. Métricas para clasificación

Obligatorias:

- `accuracy`
- `precision`
- `recall`
- `f1_score`
- `auc_roc`

Opcionales:

- `specificity`
- `balanced_accuracy`
- `false_positive_rate`
- `false_negative_rate`

## 7. Artefactos obligatorios

Para cada modelo:

```text
classification_report.txt
confusion_matrix.png
roc_curve.png
feature_importance.png
model.joblib
params.json
```

Para QABot:

```text
qabot_report.html
generated_tests.zip
pytest_output.txt
execution_summary.json
```

## 8. Registro mínimo en código

Ejemplo conceptual:

```python
with mlflow.start_run(run_name=run_name):
    mlflow.set_tags(tags)
    mlflow.log_params(params)
    mlflow.log_metrics(metrics)
    mlflow.log_artifact("reports/classification_report.txt")
    mlflow.sklearn.log_model(model, artifact_path="model")
```

## 9. Comparación de modelos

La selección del modelo ganador debe justificarse por:

1. Métrica principal: F1-score.
2. Métrica secundaria: recall de la clase ocupada.
3. Estabilidad entre test1 y test2.
4. Interpretabilidad.
5. Simplicidad de despliegue.

## 10. Reglas

- Ningún modelo sin run MLflow se considera resultado final.
- Ningún run sin tag lakeFS se considera reproducible.
- Ningún resultado debe depender de datos no versionados.
- El notebook final debe incluir el `run_id` del modelo ganador.
