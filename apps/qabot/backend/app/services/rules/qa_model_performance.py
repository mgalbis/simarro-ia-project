"""Regla QA para evaluación de desempeño de clasificación binaria."""

import math
from typing import Any, Optional

import pandas as pd


def check_model_performance(
    df: pd.DataFrame,
    target_column: Optional[str] = None,
    prediction_column: Optional[str] = None,
    threshold: float = 0.5,
    positive_class: Any = 1,
):
    """Evalúa métricas de clasificación binaria sin modificar artefactos."""
    if not target_column:
        return _error(
            "Missing target column.",
            "Indicar la variable real. Ejemplo: target es abandono.",
            available_columns=list(df.columns),
        )

    if not prediction_column:
        return _error(
            "Missing prediction or score column.",
            "Indicar la columna de predicción o score. Ejemplo: score es probabilidad_abandono.",
            available_columns=list(df.columns),
        )

    if target_column not in df.columns:
        return _error(
            f"Target column not found: {target_column}",
            "Revisar el nombre de la variable objetivo proporcionada.",
            available_columns=list(df.columns),
        )

    if prediction_column not in df.columns:
        return _error(
            f"Prediction column not found: {prediction_column}",
            "Revisar el nombre de la columna de predicción o score proporcionada.",
            available_columns=list(df.columns),
        )

    evaluation_df = df[[target_column, prediction_column]].dropna()

    if evaluation_df.empty:
        return _error(
            "No valid rows after dropping null target/prediction values.",
            "Revisar valores nulos en la variable real o en la predicción.",
        )

    target_values = set(evaluation_df[target_column].dropna().unique())

    if len(target_values) != 2:
        return _error(
            "Target column is not binary.",
            "Revisar que la variable real tenga exactamente dos clases para la evaluación binaria.",
            target_column=target_column,
            observed_classes=sorted(str(value) for value in target_values),
        )

    y_true_raw = evaluation_df[target_column]
    y_pred_raw = evaluation_df[prediction_column]

    y_true = _to_binary_series(y_true_raw, positive_class)

    is_score = pd.api.types.is_numeric_dtype(y_pred_raw) and (
        y_pred_raw.min() >= 0 and y_pred_raw.max() <= 1
    )

    if is_score and not 0 <= float(threshold) <= 1:
        return _error(
            "Threshold out of range.",
            "Indicar un umbral entre 0 y 1 para transformar el score en clase predicha.",
            threshold=threshold,
        )

    if is_score:
        y_score = y_pred_raw.astype(float)
        y_pred = (y_score >= threshold).astype(int)
    else:
        y_score = None
        y_pred = _to_binary_series(y_pred_raw, positive_class)

    tp = int(((y_true == 1) & (y_pred == 1)).sum())
    tn = int(((y_true == 0) & (y_pred == 0)).sum())
    fp = int(((y_true == 0) & (y_pred == 1)).sum())
    fn = int(((y_true == 1) & (y_pred == 0)).sum())

    accuracy = _safe_div(tp + tn, tp + tn + fp + fn)
    precision = _safe_div(tp, tp + fp)
    recall = _safe_div(tp, tp + fn)
    f1 = _safe_div(2 * precision * recall, precision + recall)

    metrics = {
        "rows_evaluated": int(len(evaluation_df)),
        "target_column": target_column,
        "prediction_column": prediction_column,
        "threshold": threshold if is_score else None,
        "prediction_interpreted_as_score": bool(is_score),
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "confusion_matrix": {
            "tp": tp,
            "tn": tn,
            "fp": fp,
            "fn": fn,
        },
    }

    if y_score is not None:
        metrics["roc_auc"] = _roc_auc(y_true.tolist(), y_score.tolist())

    warnings = []
    recommendations = []
    status = "PASS"

    if recall < 0.4:
        status = "FAIL"
        warnings.append(
            {
                "issue": "Recall below critical diagnostic reference.",
                "observed_recall": round(recall, 4),
                "critical_reference": 0.4,
            }
        )
        recommendations.append(
            "Revisar en una iteración posterior si la política de umbral o el entrenamiento del modelo permiten detectar más positivos reales."
        )
    elif recall < 0.6:
        status = "WARN"
        warnings.append(
            {
                "issue": "Recall below diagnostic reference.",
                "observed_recall": round(recall, 4),
                "warning_reference": 0.6,
            }
        )
        recommendations.append(
            "Analizar en una iteración posterior si el umbral actual reduce en exceso la detección de positivos reales."
        )

    if precision < 0.4:
        status = "FAIL"
        warnings.append(
            {
                "issue": "Precision below critical diagnostic reference.",
                "observed_precision": round(precision, 4),
                "critical_reference": 0.4,
            }
        )
        recommendations.append(
            "Revisar en una iteración posterior si el modelo produce demasiados falsos positivos."
        )
    elif precision < 0.6 and status != "FAIL":
        status = "WARN"
        warnings.append(
            {
                "issue": "Precision below diagnostic reference.",
                "observed_precision": round(precision, 4),
                "warning_reference": 0.6,
            }
        )
        recommendations.append(
            "Analizar en una iteración posterior el equilibrio entre falsos positivos y falsos negativos."
        )

    if f1 < 0.5 and status != "FAIL":
        status = "WARN"
        warnings.append(
            {
                "issue": "F1 below diagnostic reference.",
                "observed_f1": round(f1, 4),
                "warning_reference": 0.5,
            }
        )
        recommendations.append(
            "Revisar en una iteración posterior si el desempeño global del modelo es suficiente para el caso de uso."
        )

    return {
        "rule": "QA-MODEL-PERFORMANCE",
        "status": status,
        "metrics": metrics,
        "warnings": warnings,
        "recommendations": recommendations,
    }


def _error(issue: str, recommendation: str, **metrics):
    return {
        "rule": "QA-MODEL-PERFORMANCE",
        "status": "ERROR",
        "metrics": metrics,
        "warnings": [{"issue": issue}],
        "recommendations": [recommendation],
    }


def _to_binary_series(series: pd.Series, positive_class: Any):
    if set(series.dropna().unique()).issubset({0, 1, "0", "1"}):
        return series.astype(int)

    return (series == positive_class).astype(int)


def _safe_div(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def _roc_auc(y_true, y_score):
    """Implementación simple de ROC AUC sin depender de scikit-learn."""
    pairs = sorted(zip(y_score, y_true), key=lambda x: x[0])
    positives = sum(y_true)
    negatives = len(y_true) - positives

    if positives == 0 or negatives == 0:
        return None

    rank_sum = 0.0

    for rank, (_, label) in enumerate(pairs, start=1):
        if label == 1:
            rank_sum += rank

    auc = (rank_sum - positives * (positives + 1) / 2) / (positives * negatives)

    if math.isnan(auc):
        return None

    return round(float(auc), 4)
