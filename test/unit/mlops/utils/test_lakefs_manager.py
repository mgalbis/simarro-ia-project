"""Pruebas unitarias de `LakeFSManager`."""

from __future__ import annotations

from types import SimpleNamespace

import pandas as pd
import pytest

from mlops.utils.lakefs_manager import LakeFSManager


class _FakeCasesConfig:
    """Config fake mínima para validar convenciones de lakeFS."""

    default_branch = "main"
    repo_name_pattern = "caso{case}--{dataset}"
    tag_pattern = "{dataset}_{case}_v{version}"

    @staticmethod
    def case_for_dataset(dataset: str) -> str:
        mapping = {
            "uci-appliances": "B",
            "uci-occupancy": "D",
        }
        return mapping[dataset]

    @staticmethod
    def resolve_gold_paths() -> dict[str, str]:
        return {
            "train": "gold/train.parquet",
            "test": "gold/test.parquet",
        }


def test_manager_creates_client_internally_when_not_provided(monkeypatch):
    """Si no se informa `client`, debe construirse dentro de `LakeFSManager`."""
    fake_client = SimpleNamespace(objects_api=SimpleNamespace())
    captured: dict[str, object] = {}

    def _fake_create_client(
        *,
        endpoint: str | None = None,
        access_key_id: str | None = None,
        secret_access_key: str | None = None,
    ):
        captured["args"] = (endpoint, access_key_id, secret_access_key)
        return fake_client

    patched_factory = staticmethod(_fake_create_client)
    monkeypatch.setattr(LakeFSManager, "_create_client", patched_factory)

    manager = LakeFSManager(cases_config=_FakeCasesConfig())

    assert manager.client is fake_client
    assert captured["args"] == (None, None, None)


def test_resolve_repository_name_uses_cases_config_pattern():
    """Resuelve nombres de repo usando `repo_name_pattern` y caso asociado."""
    manager = LakeFSManager(
        client=SimpleNamespace(),
        cases_config=_FakeCasesConfig(),
    )

    assert manager.resolve_repository_name("uci-appliances") == "casob--uci-appliances"
    assert (
        manager.resolve_repository_name("uci-occupancy", case_id="D")
        == "casod--uci-occupancy"
    )


def test_build_tag_uses_cases_config_tag_pattern():
    """Construye tags aplicando placeholders de `tag_pattern`."""
    manager = LakeFSManager(
        client=SimpleNamespace(),
        cases_config=_FakeCasesConfig(),
    )

    assert manager.build_tag("uci-appliances", 7) == "uci-appliances_b_v7"
    assert (
        manager.build_tag("uci-occupancy", "12", case_id="D") == "uci-occupancy_d_v12"
    )


def test_default_branch_property_reads_cases_config():
    """Expone la rama por defecto definida en `CASES_CONFIG`."""
    manager = LakeFSManager(
        client=SimpleNamespace(),
        cases_config=_FakeCasesConfig(),
    )
    assert manager.default_branch == "main"


def test_normalize_object_bytes_supports_read_data_and_raw_bytes():
    """Normaliza respuestas lakeFS con `read`, `data` o bytes directos."""

    class _ReadResp:
        @staticmethod
        def read():
            return b"abc"

    class _DataResp:
        data = bytearray(b"abc")

    assert LakeFSManager._normalize_object_bytes(_ReadResp()) == b"abc"
    assert LakeFSManager._normalize_object_bytes(_DataResp()) == b"abc"
    assert LakeFSManager._normalize_object_bytes(memoryview(b"abc")) == b"abc"


def test_normalize_object_bytes_raises_for_invalid_payload():
    """Falla si la respuesta lakeFS no puede convertirse a bytes."""
    with pytest.raises(TypeError, match="Respuesta lakeFS inválida"):
        LakeFSManager._normalize_object_bytes(object())


def test_read_object_bytes_calls_objects_api_get_object_with_expected_args():
    """Lee objeto en lakeFS delegando en `objects_api.get_object`."""
    captured: dict[str, object] = {}

    class _Resp:
        @staticmethod
        def read():
            return b"payload"

    class _ObjectsApi:
        def get_object(self, repository: str, ref: str, path: str):
            captured["args"] = (repository, ref, path)
            return _Resp()

    manager = LakeFSManager(
        client=SimpleNamespace(objects_api=_ObjectsApi()),
        cases_config=_FakeCasesConfig(),
    )
    payload = manager.read_object_bytes("repo-a", "tag-1", "gold/train.parquet")

    assert payload == b"payload"
    assert captured["args"] == ("repo-a", "tag-1", "gold/train.parquet")


def test_read_parquet_reads_dataframe_from_lakefs_bytes(monkeypatch):
    """`read_parquet` convierte bytes lakeFS en DataFrame de pandas."""
    expected_df = pd.DataFrame({"x": [1, 2]})

    class _Resp:
        @staticmethod
        def read():
            return b"parquet-bytes"

    client = SimpleNamespace(
        objects_api=SimpleNamespace(
            get_object=lambda **kwargs: _Resp(),
        )
    )
    manager = LakeFSManager(client=client, cases_config=_FakeCasesConfig())

    def _fake_read_parquet(buffer):
        if buffer.getvalue() == b"parquet-bytes":
            return expected_df
        raise AssertionError("Contenido binario inesperado")

    monkeypatch.setattr(
        "mlops.utils.lakefs_manager.pd.read_parquet", _fake_read_parquet
    )

    df = manager.read_parquet("repo-a", "tag-1", "gold/train.parquet")
    assert df.equals(expected_df)


def test_download_gold_data_uses_paths_from_cases_config(monkeypatch):
    """Descarga train/test usando rutas Gold definidas en configuración."""
    manager = LakeFSManager(
        client=SimpleNamespace(),
        cases_config=_FakeCasesConfig(),
    )

    calls: list[tuple[str, str, str]] = []
    train_df = pd.DataFrame({"x": [1]})
    test_df = pd.DataFrame({"x": [2]})

    def _fake_read_parquet(repository: str, ref: str, path: str):
        calls.append((repository, ref, path))
        if path.endswith("train.parquet"):
            return train_df
        return test_df

    monkeypatch.setattr(manager, "read_parquet", _fake_read_parquet)

    out_train, out_test = manager.download_gold_data("repo-a", "tag-1")

    assert calls == [
        ("repo-a", "tag-1", "gold/train.parquet"),
        ("repo-a", "tag-1", "gold/test.parquet"),
    ]
    assert out_train.equals(train_df)
    assert out_test.equals(test_df)
