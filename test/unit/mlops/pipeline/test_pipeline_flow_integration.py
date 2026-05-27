"""Prueba de integración del flujo trigger -> pipeline_train con clientes mockeados."""

from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace

import pandas as pd

from mlops.config import CASES_CONFIG
from mlops.pipeline import pipeline_train as pt
from mlops.pipeline.trigger_resolver import PipelineTriggerResolver


def _build_train_test_frames() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Construye DataFrames válidos para `uci-occupancy` (caso D)."""
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


def test_integration_trigger_to_pipeline_uses_expected_client_calls(monkeypatch):
    """Integra resolver + pipeline y valida llamadas a lakeFS/MLflow.

    Flujo cubierto:
    1. Carga body fake desde `test/resources/post-create-tag-body.json`.
    2. Resuelve trigger real con `PipelineTriggerResolver`.
    3. Ejecuta `ejecutar_pipeline` con clientes externos mockeados.
    4. Verifica que lakeFS y MLflow reciben dataset/tag/commit/modelo esperados.
    """
    root = Path(__file__).resolve().parents[4]
    body_path = root / "test" / "resources" / "post-create-tag-body.json"
    event = json.loads(body_path.read_text(encoding="utf-8"))
    event["commit_id"] = "abcdef1234567890"
    event["committer"] = "integration_tester"

    trigger = PipelineTriggerResolver().resolve(event)

    train_df, test_df = _build_train_test_frames()
    train_bytes = b"train_bytes_marker"
    test_bytes = b"test_bytes_marker"

    lakefs_calls: list[dict[str, str]] = []

    class _FakeLakeFSResponse:
        """Simula respuesta binaria de lakeFS."""

        def __init__(self, payload: bytes):
            self.data = payload

    class _FakeObjectsAPI:
        """Cliente `objects_api` simulado para capturar llamadas get_object."""

        def get_object(self, repository: str, ref: str, path: str):
            lakefs_calls.append(
                {
                    "repository": repository,
                    "ref": ref,
                    "path": path,
                }
            )
            if path.endswith("train.parquet"):
                return _FakeLakeFSResponse(train_bytes)
            return _FakeLakeFSResponse(test_bytes)

    monkeypatch.setattr(
        pt, "LAKEFS_CLIENT", SimpleNamespace(objects_api=_FakeObjectsAPI())
    )

    def _fake_read_parquet(buffer: BytesIO):
        payload = buffer.getvalue()
        if payload == train_bytes:
            return train_df
        if payload == test_bytes:
            return test_df
        raise AssertionError("Payload parquet inesperado en test de integración")

    monkeypatch.setattr(pt.pd, "read_parquet", _fake_read_parquet)

    captured: dict[str, object] = {}

    class _RunCtx:
        """Context manager de run MLflow simulado."""

        def __enter__(self):
            return SimpleNamespace(info=SimpleNamespace(run_id="run_integration_1"))

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(
        pt.mlflow,
        "set_tracking_uri",
        lambda uri: captured.setdefault("tracking_uri", uri),
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
        pt.mlflow,
        "set_tags",
        lambda tags: captured.setdefault("tags", tags),
    )
    monkeypatch.setattr(
        pt.mlflow,
        "log_params",
        lambda params: captured.setdefault("params", params),
    )
    monkeypatch.setattr(
        pt.mlflow,
        "log_metrics",
        lambda metrics: captured.setdefault("metrics", metrics),
    )
    monkeypatch.setattr(
        pt.mlflow.sklearn,
        "log_model",
        lambda **kwargs: captured.setdefault("log_model", kwargs),
    )

    monkeypatch.setattr(pt, "registrar_report_evidently", lambda **kwargs: None)

    stage_calls: dict[str, object] = {}

    class _FakeMlflowClient:
        """Cliente registry de MLflow simulado para validar transición."""

        def __init__(self, tracking_uri=None):
            stage_calls["tracking_uri"] = tracking_uri

        def get_latest_versions(self, name, stages):
            stage_calls["get_latest_versions"] = (name, stages)
            return [SimpleNamespace(version="3")]

        def transition_model_version_stage(self, **kwargs):
            stage_calls["transition"] = kwargs

    monkeypatch.setattr("mlflow.tracking.MlflowClient", _FakeMlflowClient)

    pt.ejecutar_pipeline(
        caso=trigger.case_id,
        repository=trigger.repository,
        dataset=trigger.dataset,
        commit=trigger.commit_hash,
        committer=trigger.committer,
        tag=trigger.tag_id,
    )

    gold_paths = CASES_CONFIG.resolve_gold_paths()
    assert lakefs_calls == [
        {
            "repository": trigger.repository,
            "ref": trigger.tag_id,
            "path": gold_paths["train"],
        },
        {
            "repository": trigger.repository,
            "ref": trigger.tag_id,
            "path": gold_paths["test"],
        },
    ]

    expected_experiment = CASES_CONFIG.resolve_experiment_name(trigger.case_id)
    assert captured["tracking_uri"] == pt.MLFLOW_URI
    assert captured["experiment"] == expected_experiment
    assert captured["tags"]["dataset"] == trigger.dataset
    assert captured["tags"]["dataset_commit"] == trigger.commit_hash
    assert captured["tags"]["dataset_tag"] == trigger.tag_id
    assert "algorithm" in captured["tags"]
    assert isinstance(captured["params"], dict) and captured["params"]
    assert isinstance(captured["metrics"], dict) and captured["metrics"]

    expected_model_name = CASES_CONFIG.cases[trigger.case_id]["functional_model_name"]
    assert captured["log_model"]["registered_model_name"] == expected_model_name
    assert stage_calls["get_latest_versions"] == (expected_model_name, ["None"])
    assert stage_calls["transition"]["name"] == expected_model_name
    assert stage_calls["transition"]["stage"] == "Staging"
