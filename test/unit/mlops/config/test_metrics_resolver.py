"""Pruebas unitarias de `MetricsResolver` con modelos reales de scikit-learn."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from sklearn.dummy import DummyRegressor
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    mean_absolute_error,
    mean_absolute_percentage_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
    roc_auc_score,
)
from sklearn.svm import LinearSVC

from mlops.config.metrics_resolver import MetricsResolver


def _fit_regression_model():
    """Entrena un modelo de regresión real sobre un dataset pequeño."""
    x_train = np.array([[0.0], [1.0], [2.0], [3.0], [4.0], [5.0]])
    y_train = np.array([0.1, 1.2, 1.9, 3.1, 4.2, 5.1])
    x_test = np.array([[0.5], [1.5], [2.5], [3.5]])
    y_test = np.array([0.6, 1.4, 2.8, 3.2])
    model = LinearRegression().fit(x_train, y_train)
    return model, x_test, y_test


def _fit_binary_classifier_with_proba():
    """Entrena un clasificador binario real con `predict_proba`."""
    x_train = np.array(
        [
            [0.0, 0.0],
            [0.0, 1.0],
            [1.0, 0.0],
            [1.0, 1.0],
            [2.0, 0.0],
            [2.0, 1.0],
            [3.0, 0.0],
            [3.0, 1.0],
        ]
    )
    y_train = np.array([0, 0, 0, 0, 1, 1, 1, 1])
    x_test = np.array([[0.5, 0.0], [1.5, 0.0], [2.5, 0.0], [2.5, 1.0]])
    y_test = np.array([0, 0, 1, 1])

    model = LogisticRegression(solver="liblinear", random_state=42).fit(
        x_train, y_train
    )
    return model, x_test, y_test


def _fit_binary_classifier_with_decision_function():
    """Entrena un clasificador binario real con `decision_function`."""
    x_train = np.array(
        [
            [0.0, 0.0],
            [0.0, 1.0],
            [1.0, 0.0],
            [1.0, 1.0],
            [2.0, 0.0],
            [2.0, 1.0],
            [3.0, 0.0],
            [3.0, 1.0],
        ]
    )
    y_train = np.array([0, 0, 0, 0, 1, 1, 1, 1])
    x_test = np.array([[0.5, 0.0], [1.5, 0.0], [2.5, 0.0], [2.5, 1.0]])
    y_test = np.array([0, 0, 1, 1])

    model = LinearSVC(random_state=42, max_iter=10000).fit(x_train, y_train)
    return model, x_test, y_test


def _fit_multiclass_classifier():
    """Entrena un clasificador multiclase para validar reglas no binarias."""
    x_train = np.array([[0.0], [1.0], [2.0], [3.0], [4.0], [5.0]])
    y_train = np.array([0, 1, 2, 0, 1, 2])
    x_test = np.array([[0.5], [1.5], [2.5], [3.5]])
    y_test = np.array([0, 1, 2, 0])

    model = LogisticRegression(solver="lbfgs", max_iter=1000, random_state=42).fit(
        x_train, y_train
    )
    return model, x_test, y_test


def test_regression_metrics_match_sklearn_values():
    """MAE/RMSE/MAPE/R2 deben coincidir con cálculo de sklearn sobre modelo real."""
    model, x_test, y_test = _fit_regression_model()
    resolver = MetricsResolver(model=model, x_test=x_test, y_test=y_test)
    prediction = model.predict(x_test)

    assert resolver.mae() == round(mean_absolute_error(y_test, prediction), 4)
    assert resolver.rmse() == round(np.sqrt(mean_squared_error(y_test, prediction)), 4)
    assert resolver.mape() == round(
        mean_absolute_percentage_error(y_test, prediction), 4
    )
    assert resolver.r2() == round(r2_score(y_test, prediction), 4)


def test_correlation_metrics_match_real_prediction():
    """Pearson y Spearman deben coincidir con correlación real y redondeo."""
    model, x_test, y_test = _fit_regression_model()
    resolver = MetricsResolver(model=model, x_test=x_test, y_test=y_test)
    prediction = model.predict(x_test)

    expected_pearson = round(
        float(pd.Series(y_test).corr(pd.Series(prediction), method="pearson")), 4
    )
    expected_spearman = round(
        float(pd.Series(y_test).corr(pd.Series(prediction), method="spearman")), 4
    )

    assert resolver.pearson() == expected_pearson
    assert resolver.spearman() == expected_spearman


def test_binary_classification_metrics_match_sklearn_values():
    """Accuracy/Precision/Recall/F1 y métricas por clase deben cuadrar con sklearn."""
    model, x_test, y_test = _fit_binary_classifier_with_proba()
    resolver = MetricsResolver(model=model, x_test=x_test, y_test=y_test)
    prediction = model.predict(x_test)

    assert resolver.accuracy() == round(accuracy_score(y_test, prediction), 4)
    assert resolver.precision() == round(
        precision_score(y_test, prediction, average="binary", zero_division=0), 4
    )
    assert resolver.recall() == round(
        recall_score(y_test, prediction, average="binary", zero_division=0), 4
    )
    assert resolver.f1_score() == round(
        f1_score(y_test, prediction, average="binary", zero_division=0), 4
    )

    class_precision = precision_score(
        y_test, prediction, labels=[0, 1], average=None, zero_division=0
    )
    class_recall = recall_score(
        y_test, prediction, labels=[0, 1], average=None, zero_division=0
    )
    class_f1 = f1_score(
        y_test, prediction, labels=[0, 1], average=None, zero_division=0
    )

    assert resolver.precision_class_0() == round(class_precision[0], 4)
    assert resolver.precision_class_1() == round(class_precision[1], 4)
    assert resolver.recall_class_0() == round(class_recall[0], 4)
    assert resolver.recall_class_1() == round(class_recall[1], 4)
    assert resolver.f1_class_0() == round(class_f1[0], 4)
    assert resolver.f1_class_1() == round(class_f1[1], 4)


def test_auc_roc_uses_predict_proba_with_real_model():
    """AUC debe usar `predict_proba` cuando el modelo la expone."""
    model, x_test, y_test = _fit_binary_classifier_with_proba()
    resolver = MetricsResolver(model=model, x_test=x_test, y_test=y_test)

    scores = model.predict_proba(x_test)[:, 1]
    expected_auc = round(roc_auc_score(y_test, scores), 4)

    assert resolver.auc_roc() == expected_auc


def test_auc_roc_falls_back_to_decision_function_with_real_model():
    """AUC debe usar `decision_function` cuando no hay `predict_proba`."""
    model, x_test, y_test = _fit_binary_classifier_with_decision_function()
    resolver = MetricsResolver(model=model, x_test=x_test, y_test=y_test)

    scores = model.decision_function(x_test)
    expected_auc = round(roc_auc_score(y_test, scores), 4)

    assert resolver.auc_roc() == expected_auc


def test_auc_roc_raises_when_model_has_no_scoring_interface():
    """Falla en AUC cuando el modelo real no tiene proba ni decision_function."""
    x_train = np.array([[0.0], [1.0], [2.0], [3.0]])
    y_train = np.array([0.0, 1.0, 1.0, 0.0])
    x_test = np.array([[0.5], [1.5], [2.5], [3.5]])
    y_test = np.array([0, 1, 1, 0])
    model = DummyRegressor(strategy="mean").fit(x_train, y_train)
    resolver = MetricsResolver(model=model, x_test=x_test, y_test=y_test)

    with pytest.raises(ValueError, match="no implementa"):
        resolver.auc_roc()


def test_multiclass_global_metrics_use_weighted_average():
    """En multiclase, precision/recall/F1 deben usar `average='weighted'`."""
    model, x_test, y_test = _fit_multiclass_classifier()
    resolver = MetricsResolver(model=model, x_test=x_test, y_test=y_test)
    prediction = model.predict(x_test)

    assert resolver.precision() == round(
        precision_score(y_test, prediction, average="weighted", zero_division=0), 4
    )
    assert resolver.recall() == round(
        recall_score(y_test, prediction, average="weighted", zero_division=0), 4
    )
    assert resolver.f1_score() == round(
        f1_score(y_test, prediction, average="weighted", zero_division=0), 4
    )


def test_binary_specific_metrics_raise_for_multiclass_target():
    """Métricas binarias específicas deben fallar para target multiclase."""
    model, x_test, y_test = _fit_multiclass_classifier()
    resolver = MetricsResolver(model=model, x_test=x_test, y_test=y_test)

    with pytest.raises(ValueError, match="target binario 0/1"):
        resolver.auc_roc()
    with pytest.raises(ValueError, match="target binario 0/1"):
        resolver.precision_class_0()


def test_get_metric_by_name_and_bulk_metrics_with_real_model():
    """`get_metric_by_name`/`get_metrics_by_names` deben funcionar con alias y lote."""
    model, x_test, y_test = _fit_binary_classifier_with_proba()
    resolver = MetricsResolver(model=model, x_test=x_test, y_test=y_test)

    assert resolver.get_metric_by_name("f1") == resolver.f1_score()
    assert resolver.get_metrics_by_names(["accuracy", "f1"]) == {
        "accuracy": resolver.accuracy(),
        "f1": resolver.f1_score(),
    }

    with pytest.raises(ValueError, match="Métrica no soportada"):
        resolver.get_metric_by_name("metrica_inexistente")


def test_metrics_requiring_y_test_raise_when_missing_even_with_real_model():
    """Si no se pasa `y_test`, debe fallar aunque el modelo sea real."""
    model, x_test, _ = _fit_regression_model()
    resolver = MetricsResolver(model=model, x_test=x_test, y_test=None)

    with pytest.raises(ValueError, match="y_test no está disponible"):
        resolver.mae()
