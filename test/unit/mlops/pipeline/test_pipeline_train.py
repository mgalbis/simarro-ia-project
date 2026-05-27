"""Pruebas unitarias para `pipeline_train.py` usando `CASES_CONFIG` real."""

from __future__ import annotations

import builtins
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pandas as pd
import pytest

from mlops.pipeline import pipeline_train as pt


def _build_classification_frames() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Construye train/test para dataset real `uci-occupancy` (caso D)."""
    train_df = pd.DataFrame(
        {
            "Temperature": [21.0, 21.2, 22.1, 23.0, 23.2, 22.8, 21.7, 22.9],
            "Humidity": [40.0, 42.5, 44.0, 43.0, 41.0, 45.0, 46.5, 43.5],
            "Light": [50, 120, 30, 400, 250, 500, 80, 450],
            "CO2": [500, 700, 550, 900, 850, 1000, 600, 950],
            "HumidityRatio": [
                0.004,
                0.0045,
                0.0042,
                0.0051,
                0.0049,
                0.0053,
                0.0044,
                0.0050,
            ],
            "Occupancy": [0, 0, 0, 1, 1, 1, 0, 1],
        }
    )
    test_df = pd.DataFrame(
        {
            "Temperature": [21.5, 22.7, 23.1, 22.0],
            "Humidity": [41.0, 44.0, 42.0, 45.5],
            "Light": [60, 420, 460, 70],
            "CO2": [520, 910, 980, 580],
            "HumidityRatio": [0.0041, 0.0050, 0.0052, 0.0043],
            "Occupancy": [0, 1, 1, 0],
        }
    )
    return train_df, test_df


def _build_regression_frames() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Construye train/test para dataset real `uci-appliances` (caso B)."""
    train_df = pd.DataFrame(
        {
            "lights": [10, 20, 30, 40, 50, 60],
            "T_out": [5.0, 6.5, 8.0, 10.0, 12.0, 14.0],
            "T1": [19.0, 19.5, 20.0, 20.5, 21.0, 21.5],
            "Appliances": [60.0, 75.0, 90.0, 110.0, 130.0, 150.0],
        }
    )
    test_df = pd.DataFrame(
        {
            "lights": [15, 35, 55],
            "T_out": [6.0, 9.0, 13.0],
            "T1": [19.2, 20.2, 21.2],
            "Appliances": [70.0, 100.0, 140.0],
        }
    )
    return train_df, test_df


def test_read_lakefs_parquet_uses_read_method_when_available(monkeypatch):
    """`_read_lakefs_parquet` prioriza `response.read()` si existe."""
    captured: dict[str, object] = {}
    payload = b"parquet_binary_payload"

    class _Resp:
        """Respuesta lakeFS con método `read`."""

        def read(self):
            return payload

    class _ObjectsAPI:
        """API lakeFS simulada para capturar args."""

        def get_object(self, repository: str, ref: str, path: str):
            captured["args"] = (repository, ref, path)
            return _Resp()

    monkeypatch.setattr(pt, "LAKEFS_CLIENT", SimpleNamespace(objects_api=_ObjectsAPI()))

    expected_df = pd.DataFrame({"x": [1]})
    monkeypatch.setattr(
        pt.pd,
        "read_parquet",
        lambda bio: expected_df if bio.getvalue() == payload else None,
    )

    df = pt._read_lakefs_parquet("repo", "tag", "gold/train.parquet")

    assert captured["args"] == ("repo", "tag", "gold/train.parquet")
    assert df.equals(expected_df)


def test_read_lakefs_parquet_falls_back_to_data_field(monkeypatch):
    """`_read_lakefs_parquet` usa `response.data` cuando no hay método `read`."""
    payload = b"payload_from_data"

    class _Resp:
        """Respuesta lakeFS sin `read`, con campo `data`."""

        data = payload

    monkeypatch.setattr(
        pt,
        "LAKEFS_CLIENT",
        SimpleNamespace(
            objects_api=SimpleNamespace(get_object=lambda **kwargs: _Resp())
        ),
    )

    expected_df = pd.DataFrame({"x": [2]})
    monkeypatch.setattr(
        pt.pd,
        "read_parquet",
        lambda bio: expected_df if bio.getvalue() == payload else None,
    )

    df = pt._read_lakefs_parquet("repo", "tag", "gold/test.parquet")
    assert df.equals(expected_df)


def test_descargar_datos_reads_train_and_test_from_real_gold_paths(monkeypatch):
    """`descargar_datos` usa rutas de `resolve_gold_paths` reales de CASES_CONFIG."""
    expected_paths = pt.CASES_CONFIG.resolve_gold_paths()

    train_df = pd.DataFrame({"a": [1, 2]})
    test_df = pd.DataFrame({"a": [3]})
    calls: list[tuple[str, str, str]] = []

    def _fake_read(repo: str, ref: str, path: str):
        calls.append((repo, ref, path))
        if path == expected_paths["train"]:
            return train_df
        return test_df

    monkeypatch.setattr(pt, "_read_lakefs_parquet", _fake_read)

    loaded_train, loaded_test = pt.descargar_datos("repo-dataset", "tag_v1")

    assert calls == [
        ("repo-dataset", "tag_v1", expected_paths["train"]),
        ("repo-dataset", "tag_v1", expected_paths["test"]),
    ]
    assert loaded_train.equals(train_df)
    assert loaded_test.equals(test_df)


def test_registrar_report_evidently_sets_unavailable_when_import_fails(monkeypatch):
    """Marca estado `unavailable` si Evidently no está instalado/importable."""
    captured_tags: dict[str, str] = {}

    real_import = builtins.__import__

    def _fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name.startswith("evidently"):
            raise ImportError("evidently not installed")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", _fake_import)
    monkeypatch.setattr(
        pt.mlflow, "set_tag", lambda k, v: captured_tags.setdefault(k, v)
    )

    pt.registrar_report_evidently(
        x_train=pd.DataFrame({"a": [1]}),
        x_test=pd.DataFrame({"a": [2]}),
        caso="D",
        dataset="uci-occupancy",
        commit="abc123",
    )

    assert captured_tags["evidently_status"] == "unavailable"


def test_registrar_report_evidently_sets_error_when_report_generation_fails(
    monkeypatch,
):
    """Marca estado `error` cuando Evidently lanza excepción en ejecución."""
    evidently_mod = ModuleType("evidently")
    presets_mod = ModuleType("evidently.presets")

    class _DataDriftPreset:
        """Preset dummy de drift."""

    class _DataSummaryPreset:
        """Preset dummy de summary."""

    class _Report:
        """Report dummy que falla al ejecutar."""

        def __init__(self, metrics):
            self.metrics = metrics

        def run(self, reference_data, current_data):
            raise RuntimeError("boom-report")

    presets_mod.DataDriftPreset = _DataDriftPreset
    presets_mod.DataSummaryPreset = _DataSummaryPreset
    evidently_mod.Report = _Report

    monkeypatch.setitem(sys.modules, "evidently", evidently_mod)
    monkeypatch.setitem(sys.modules, "evidently.presets", presets_mod)

    tags: dict[str, str] = {}
    monkeypatch.setattr(pt.mlflow, "set_tag", lambda k, v: tags.setdefault(k, v))

    pt.registrar_report_evidently(
        x_train=pd.DataFrame({"a": [1]}),
        x_test=pd.DataFrame({"a": [2]}),
        caso="D",
        dataset="uci-occupancy",
        commit="abc123",
    )

    assert tags["evidently_status"] == "error"
    assert "boom-report" in tags["evidently_error"]


def test_registrar_report_evidently_logs_artifacts_and_tags_on_success(
    monkeypatch, tmp_path
):
    """En camino feliz registra artefactos HTML/JSON y tags de resumen."""
    evidently_mod = ModuleType("evidently")
    presets_mod = ModuleType("evidently.presets")

    class _DataDriftPreset:
        """Preset dummy de drift."""

    class _DataSummaryPreset:
        """Preset dummy de summary."""

    class _Snapshot:
        """Snapshot dummy que genera ficheros de salida."""

        def save_html(self, path: str):
            Path(path).write_text("<html></html>", encoding="utf-8")

        def save_json(self, path: str):
            Path(path).write_text("{}", encoding="utf-8")

    class _Report:
        """Report dummy con ejecución correcta."""

        def __init__(self, metrics):
            self.metrics = metrics

        def run(self, reference_data, current_data):
            return _Snapshot()

    presets_mod.DataDriftPreset = _DataDriftPreset
    presets_mod.DataSummaryPreset = _DataSummaryPreset
    evidently_mod.Report = _Report

    monkeypatch.setitem(sys.modules, "evidently", evidently_mod)
    monkeypatch.setitem(sys.modules, "evidently.presets", presets_mod)

    class _TmpCtx:
        """Context manager para forzar salida de artefactos en `tmp_path`."""

        def __init__(self, path):
            self._path = str(path)

        def __enter__(self):
            return self._path

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(
        pt.tempfile,
        "TemporaryDirectory",
        lambda prefix=None: _TmpCtx(tmp_path),
    )

    artifacts: list[tuple[str, str]] = []
    tags: dict[str, str] = {}
    monkeypatch.setattr(
        pt.mlflow,
        "log_artifact",
        lambda path, artifact_path=None: artifacts.append((path, artifact_path)),
    )
    monkeypatch.setattr(pt.mlflow, "set_tags", lambda d: tags.update(d))

    pt.registrar_report_evidently(
        x_train=pd.DataFrame({"a": [1, 2]}),
        x_test=pd.DataFrame({"a": [2, 3]}),
        caso="D",
        dataset="uci-occupancy",
        commit="abc123",
    )

    assert len(artifacts) == 2
    assert all(a[1] == "monitoring/evidently" for a in artifacts)
    assert tags["evidently_status"] == "ok"
    assert tags["evidently_case"] == "D"
    assert tags["evidently_dataset"] == "uci-occupancy"
    assert tags["evidently_dataset_version"] == "abc123"


def test_entrenar_modelo_binary_classification_returns_expected_payload():
    """Entrena clasificación binaria para caso D con columnas reales del dataset."""
    train_df, test_df = _build_classification_frames()

    model, params, metrics, x_train, x_test, y_test, preds = pt.entrenar_modelo(
        train_df=train_df,
        test_df=test_df,
        caso="D",
        dataset="uci-occupancy",
        config_caso={"problem_type": "binary_classification"},
    )

    assert model.__class__.__name__ == "RandomForestClassifier"
    assert params["n_estimators"] == 100
    assert set(metrics.keys()) == {"accuracy", "precision", "recall", "f1", "auc_roc"}
    assert list(x_train.columns) == [
        "Temperature",
        "Humidity",
        "Light",
        "CO2",
        "HumidityRatio",
    ]
    assert list(x_test.columns) == [
        "Temperature",
        "Humidity",
        "Light",
        "CO2",
        "HumidityRatio",
    ]
    assert len(y_test) == len(test_df)
    assert len(preds) == len(test_df)


def test_entrenar_modelo_regression_returns_expected_payload():
    """Entrena regresión para caso B con columnas reales del dataset."""
    train_df, test_df = _build_regression_frames()

    model, params, metrics, x_train, x_test, y_test, preds = pt.entrenar_modelo(
        train_df=train_df,
        test_df=test_df,
        caso="B",
        dataset="uci-appliances",
        config_caso={"problem_type": "forecasting_regression"},
    )

    assert model.__class__.__name__ == "RandomForestRegressor"
    assert params["n_estimators"] == 100
    assert set(metrics.keys()) == {"rmse", "mae", "r2"}
    assert list(x_train.columns) == ["lights", "T_out", "T1"]
    assert list(x_test.columns) == ["lights", "T_out", "T1"]
    assert len(y_test) == len(test_df)
    assert len(preds) == len(test_df)


def test_ejecutar_pipeline_exits_when_case_is_not_configured():
    """Finaliza con `SystemExit(1)` si el caso no existe en CASES_CONFIG real."""
    with pytest.raises(SystemExit) as exc:
        pt.ejecutar_pipeline(
            caso="Z",
            repository="casoz--dataset",
            dataset="dataset",
            commit="abc123",
            committer="tester",
            tag="dataset_v1",
        )

    assert exc.value.code == 1


def test_ejecutar_pipeline_exits_when_data_download_fails(monkeypatch):
    """Finaliza con `SystemExit(1)` si falla la descarga desde lakeFS."""

    def _raise_download_error(_dataset: str, _tag: str):
        raise RuntimeError("lakefs error")

    monkeypatch.setattr(pt, "descargar_datos", _raise_download_error)

    with pytest.raises(SystemExit) as exc:
        pt.ejecutar_pipeline(
            caso="B",
            repository="casob--uci-appliances",
            dataset="uci-appliances",
            commit="abc123",
            committer="tester",
            tag="uci-appliances_v1",
        )

    assert exc.value.code == 1


def test_ejecutar_pipeline_happy_path_calls_mlflow_and_staging(monkeypatch):
    """En camino feliz registra run en MLflow y promueve modelo a Staging."""
    config_caso = pt.CASES_CONFIG.cases["D"]
    train_df, test_df = _build_classification_frames()
    monkeypatch.setattr(pt, "descargar_datos", lambda _d, _t: (train_df, test_df))

    class _FakeModel:
        """Modelo mínimo para probar registro sin depender de entrenamiento real."""

        pass

    fake_model = _FakeModel()
    fake_return = (
        fake_model,
        {"n_estimators": 100},
        {"accuracy": 0.95},
        train_df[["Temperature", "Humidity", "Light", "CO2", "HumidityRatio"]],
        test_df[["Temperature", "Humidity", "Light", "CO2", "HumidityRatio"]],
        test_df["Occupancy"],
        [0, 1, 1, 0],
    )
    monkeypatch.setattr(pt, "entrenar_modelo", lambda *args, **kwargs: fake_return)

    captured: dict[str, object] = {}

    class _RunCtx:
        """Context manager de run MLflow simulado."""

        def __enter__(self):
            return SimpleNamespace(info=SimpleNamespace(run_id="run_123"))

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(
        pt.mlflow,
        "set_tracking_uri",
        lambda uri: captured.setdefault("uri", uri),
    )
    monkeypatch.setattr(
        pt.mlflow,
        "set_experiment",
        lambda exp: captured.setdefault("experiment", exp),
    )

    def _fake_start_run(run_name=None):
        captured["run_name"] = run_name
        return _RunCtx()

    monkeypatch.setattr(pt.mlflow, "start_run", _fake_start_run)
    monkeypatch.setattr(
        pt.mlflow, "set_tags", lambda tags: captured.setdefault("tags", tags)
    )
    monkeypatch.setattr(
        pt.mlflow, "log_params", lambda p: captured.setdefault("params", p)
    )
    monkeypatch.setattr(
        pt.mlflow, "log_metrics", lambda m: captured.setdefault("metrics", m)
    )
    monkeypatch.setattr(
        pt.mlflow.sklearn,
        "log_model",
        lambda **kwargs: captured.setdefault("log_model", kwargs),
    )
    monkeypatch.setattr(
        pt,
        "registrar_report_evidently",
        lambda **kwargs: captured.setdefault("evidently_kwargs", kwargs),
    )
    monkeypatch.setattr(
        pt,
        "_llevar_a_staging",
        lambda name, run_id: captured.setdefault("staging", (name, run_id)),
    )

    pt.ejecutar_pipeline(
        caso="D",
        repository="casod--uci-occupancy",
        dataset="uci-occupancy",
        commit="abcdef123456",
        committer="tester",
        tag="uci-occupancy_v1",
    )

    assert captured["uri"] == pt.MLFLOW_URI
    assert captured["experiment"] == pt.CASES_CONFIG.resolve_experiment_name("D")
    assert str(captured["run_name"]).startswith("_FakeModel_")
    assert captured["params"] == {"n_estimators": 100}
    assert captured["metrics"] == {"accuracy": 0.95}
    assert captured["tags"]["dataset_commit"] == "abcdef123456"
    assert captured["tags"]["dataset_tag"] == "uci-occupancy_v1"
    assert captured["tags"]["algorithm"] == "_FakeModel"
    assert (
        captured["log_model"]["registered_model_name"]
        == config_caso["functional_model_name"]
    )
    assert captured["staging"] == (config_caso["functional_model_name"], "run_123")


def test_llevar_a_staging_transitions_latest_version(monkeypatch):
    """Promueve a Staging la última versión disponible en estado `None`."""
    captured: dict[str, object] = {}

    class _FakeClient:
        """Cliente MLflow simulado para comprobar transición de stage."""

        def __init__(self, tracking_uri=None):
            captured["tracking_uri"] = tracking_uri

        def get_latest_versions(self, name, stages):
            captured["get_latest_versions"] = (name, stages)
            return [SimpleNamespace(version="7")]

        def transition_model_version_stage(self, **kwargs):
            captured["transition"] = kwargs

    monkeypatch.setattr("mlflow.tracking.MlflowClient", _FakeClient)

    pt._llevar_a_staging("OccupancyClassifier", "run_123")

    assert captured["tracking_uri"] == pt.MLFLOW_URI
    assert captured["get_latest_versions"] == ("OccupancyClassifier", ["None"])
    assert captured["transition"] == {
        "name": "OccupancyClassifier",
        "version": "7",
        "stage": "Staging",
        "archive_existing_versions": True,
    }


def test_llevar_a_staging_does_nothing_when_no_versions(monkeypatch):
    """No intenta transición cuando el registry no devuelve versiones."""
    captured: dict[str, object] = {}

    class _FakeClient:
        """Cliente MLflow simulado sin versiones publicadas."""

        def __init__(self, tracking_uri=None):
            captured["tracking_uri"] = tracking_uri

        def get_latest_versions(self, name, stages):
            captured["get_latest_versions"] = (name, stages)
            return []

        def transition_model_version_stage(self, **kwargs):
            captured["transition"] = kwargs

    monkeypatch.setattr("mlflow.tracking.MlflowClient", _FakeClient)

    pt._llevar_a_staging("OccupancyClassifier", "run_123")

    assert captured["tracking_uri"] == pt.MLFLOW_URI
    assert captured["get_latest_versions"] == ("OccupancyClassifier", ["None"])
    assert "transition" not in captured
