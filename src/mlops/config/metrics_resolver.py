"""Cálculo centralizado de métricas de evaluación definidas en `cases_config.json`."""

from __future__ import annotations

import math
from typing import Callable

import numpy as np
import pandas as pd
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


class MetricsResolver:
    """Calcula métricas para un modelo y un conjunto de evaluación.

    Soporta explícitamente todos los nombres de métrica usados en
    `config/cases_config.json`.
    """

    SUPPORTED_METRICS = (
        "mae",
        "rmse",
        "mape",
        "r2",
        "accuracy",
        "precision",
        "recall",
        "f1_score",
        "auc_roc",
        "precision_class_0",
        "precision_class_1",
        "recall_class_0",
        "recall_class_1",
        "f1_class_0",
        "f1_class_1",
        "pearson",
        "spearman",
    )

    def __init__(self, model, x_test, y_test=None):
        """Inicializa el calculador de métricas.

        Args:
            model: Modelo ya entrenado (debe implementar `predict`).
            x_test: Features de test.
            y_test: Target real de test. Es opcional.
        """
        self.model = model
        self.x_test = x_test
        self.y_test = None if y_test is None else np.asarray(y_test)
        self.prediction = np.asarray(model.predict(x_test))

    def _round(self, value: float) -> float:
        """Normaliza formato de salida a 4 decimales."""
        return round(float(value), 4)

    def _require_y_test(self) -> np.ndarray:
        """Devuelve `y_test` validado.

        Raises:
            ValueError: Si `y_test` no fue informado en el constructor.
        """
        if self.y_test is None:
            raise ValueError(
                "y_test no está disponible. Debes pasarlo al construir MetricsResolver."
            )
        return self.y_test

    def _is_binary_01(self) -> bool:
        """Indica si el target es binario estricto con etiquetas 0/1."""
        y_true = self._require_y_test()
        unique = set(np.unique(y_true).tolist())
        return unique.issubset({0, 1}) and len(unique) >= 1

    def _classification_average(self) -> str:
        """Selecciona estrategia de promedio para métricas globales de clase."""
        if self._is_binary_01():
            return "binary"
        return "weighted"

    def _prediction_score_for_auc(self) -> np.ndarray:
        """Obtiene scores continuos para `auc_roc`.

        Prioridad:
        1. `predict_proba` (probabilidad de clase positiva).
        2. `decision_function`.

        Raises:
            ValueError: Si el modelo no expone ninguna de las dos opciones.
        """
        if hasattr(self.model, "predict_proba"):
            proba = self.model.predict_proba(self.x_test)
            if not isinstance(proba, np.ndarray):
                proba = np.asarray(proba)
            if proba.ndim == 2 and proba.shape[1] >= 2:
                return proba[:, 1]
            raise ValueError("predict_proba no devuelve una matriz válida para AUC")

        if hasattr(self.model, "decision_function"):
            scores = self.model.decision_function(self.x_test)
            return np.asarray(scores)

        raise ValueError(
            "No se puede calcular auc_roc: el modelo no implementa "
            "'predict_proba' ni 'decision_function'"
        )

    def accuracy(self) -> float:
        """Calcula accuracy."""
        y_true = self._require_y_test()
        return self._round(accuracy_score(y_true, self.prediction))

    def precision(self) -> float:
        """Calcula precision global."""
        y_true = self._require_y_test()
        avg = self._classification_average()
        return self._round(
            precision_score(
                y_true,
                self.prediction,
                average=avg,
                zero_division=0,
            )
        )

    def recall(self) -> float:
        """Calcula recall global."""
        y_true = self._require_y_test()
        avg = self._classification_average()
        return self._round(
            recall_score(
                y_true,
                self.prediction,
                average=avg,
                zero_division=0,
            )
        )

    def f1_score(self) -> float:
        """Calcula F1 global."""
        y_true = self._require_y_test()
        avg = self._classification_average()
        return self._round(
            f1_score(
                y_true,
                self.prediction,
                average=avg,
                zero_division=0,
            )
        )

    def auc_roc(self) -> float:
        """Calcula AUC-ROC para clasificación binaria 0/1."""
        y_true = self._require_y_test()
        if not self._is_binary_01():
            raise ValueError("La métrica 'auc_roc' requiere target binario 0/1")
        scores = self._prediction_score_for_auc()
        return self._round(roc_auc_score(y_true, scores))

    def precision_class_0(self) -> float:
        """Calcula precision de la clase 0."""
        y_true = self._require_y_test()
        if not self._is_binary_01():
            raise ValueError("La métrica requiere target binario 0/1")
        values = precision_score(
            y_true,
            self.prediction,
            labels=[0, 1],
            average=None,
            zero_division=0,
        )
        return self._round(values[0])

    def precision_class_1(self) -> float:
        """Calcula precision de la clase 1."""
        y_true = self._require_y_test()
        if not self._is_binary_01():
            raise ValueError("La métrica requiere target binario 0/1")
        values = precision_score(
            y_true,
            self.prediction,
            labels=[0, 1],
            average=None,
            zero_division=0,
        )
        return self._round(values[1])

    def recall_class_0(self) -> float:
        """Calcula recall de la clase 0."""
        y_true = self._require_y_test()
        if not self._is_binary_01():
            raise ValueError("La métrica requiere target binario 0/1")
        values = recall_score(
            y_true,
            self.prediction,
            labels=[0, 1],
            average=None,
            zero_division=0,
        )
        return self._round(values[0])

    def recall_class_1(self) -> float:
        """Calcula recall de la clase 1."""
        y_true = self._require_y_test()
        if not self._is_binary_01():
            raise ValueError("La métrica requiere target binario 0/1")
        values = recall_score(
            y_true,
            self.prediction,
            labels=[0, 1],
            average=None,
            zero_division=0,
        )
        return self._round(values[1])

    def f1_class_0(self) -> float:
        """Calcula F1 de la clase 0."""
        y_true = self._require_y_test()
        if not self._is_binary_01():
            raise ValueError("La métrica requiere target binario 0/1")
        values = f1_score(
            y_true,
            self.prediction,
            labels=[0, 1],
            average=None,
            zero_division=0,
        )
        return self._round(values[0])

    def f1_class_1(self) -> float:
        """Calcula F1 de la clase 1."""
        y_true = self._require_y_test()
        if not self._is_binary_01():
            raise ValueError("La métrica requiere target binario 0/1")
        values = f1_score(
            y_true,
            self.prediction,
            labels=[0, 1],
            average=None,
            zero_division=0,
        )
        return self._round(values[1])

    def mae(self) -> float:
        """Calcula MAE."""
        y_true = self._require_y_test()
        return self._round(mean_absolute_error(y_true, self.prediction))

    def rmse(self) -> float:
        """Calcula RMSE."""
        y_true = self._require_y_test()
        return self._round(math.sqrt(mean_squared_error(y_true, self.prediction)))

    def mape(self) -> float:
        """Calcula MAPE."""
        y_true = self._require_y_test()
        return self._round(mean_absolute_percentage_error(y_true, self.prediction))

    def r2(self) -> float:
        """Calcula R2."""
        y_true = self._require_y_test()
        return self._round(r2_score(y_true, self.prediction))

    def pearson(self) -> float:
        """Calcula correlación de Pearson entre real y predicho."""
        y_true = pd.Series(self._require_y_test())
        y_pred = pd.Series(self.prediction)
        return self._round(y_true.corr(y_pred, method="pearson"))

    def spearman(self) -> float:
        """Calcula correlación de Spearman entre real y predicho."""
        y_true = pd.Series(self._require_y_test())
        y_pred = pd.Series(self.prediction)
        return self._round(y_true.corr(y_pred, method="spearman"))

    def get_metric_by_name(self, metric: str) -> float:
        """Calcula una métrica concreta por nombre.

        Args:
            metric: Nombre de la métrica.

        Returns:
            Valor numérico de la métrica.

        Raises:
            ValueError: Si la métrica no está soportada.
        """
        metric_name = str(metric).strip()
        alias_map = {"f1": "f1_score"}
        metric_name = alias_map.get(metric_name, metric_name)

        dispatch: dict[str, Callable[[], float]] = {
            "accuracy": self.accuracy,
            "precision": self.precision,
            "recall": self.recall,
            "f1_score": self.f1_score,
            "auc_roc": self.auc_roc,
            "precision_class_0": self.precision_class_0,
            "precision_class_1": self.precision_class_1,
            "recall_class_0": self.recall_class_0,
            "recall_class_1": self.recall_class_1,
            "f1_class_0": self.f1_class_0,
            "f1_class_1": self.f1_class_1,
            "mae": self.mae,
            "rmse": self.rmse,
            "mape": self.mape,
            "r2": self.r2,
            "pearson": self.pearson,
            "spearman": self.spearman,
        }

        metric_fn = dispatch.get(metric_name)
        if metric_fn is None:
            raise ValueError(
                f"Métrica no soportada: '{metric_name}'. "
                f"Soportadas: {list(dispatch.keys())}"
            )
        return metric_fn()

    def get_metrics_by_names(self, metrics: list[str]) -> dict[str, float]:
        """Calcula varias métricas y devuelve un diccionario `nombre -> valor`."""
        return {metric: self.get_metric_by_name(metric) for metric in metrics}
