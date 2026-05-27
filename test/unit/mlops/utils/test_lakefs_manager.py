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
    tag_pattern = "{dataset}_v{version}"
    lakefs_conventions = {"branch_pattern": "transform/v{version}"}

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

    @staticmethod
    def as_dict() -> dict[str, object]:
        return {
            "repository_schema": {
                "layers": {
                    "bronze": {
                        "path": "raw/bronze/",
                    }
                }
            }
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

    assert manager.build_tag("uci-appliances", 7) == "uci-appliances_v7"
    assert manager.build_tag("uci-occupancy", "12", case_id="D") == "uci-occupancy_v12"


def test_default_branch_property_reads_cases_config():
    """Expone la rama por defecto definida en `CASES_CONFIG`."""
    manager = LakeFSManager(
        client=SimpleNamespace(),
        cases_config=_FakeCasesConfig(),
    )
    assert manager.default_branch == "main"


def test_resolve_transform_branch_reads_pattern_from_cases_config():
    """Resuelve `transform/vN` usando la última versión de tags + 1."""

    class _Tag:
        def __init__(self, tag_id: str):
            self.id = tag_id

    class _Page:
        def __init__(self, results):
            self.results = results
            self.pagination = SimpleNamespace(has_more=False, next_offset=None)

    class _TagsApi:
        @staticmethod
        def list_tags(repository: str, after=None, amount=1000):
            _ = (repository, after, amount)
            return _Page([_Tag("uci-appliances_v1"), _Tag("uci-appliances_v3")])

    manager = LakeFSManager(
        client=SimpleNamespace(tags_api=_TagsApi()),
        cases_config=_FakeCasesConfig(),
    )

    assert (
        manager.resolve_transform_branch(
            repository="casob--uci-appliances",
            dataset="uci-appliances",
            case_id="B",
        )
        == "transform/v4"
    )


def test_resolve_transform_branch_raises_when_pattern_missing():
    """Falla si no se define `lakefs_conventions.branch_pattern`."""

    class _BadCasesConfig(_FakeCasesConfig):
        lakefs_conventions = {}

    manager = LakeFSManager(
        client=SimpleNamespace(),
        cases_config=_BadCasesConfig(),
    )
    with pytest.raises(
        ValueError,
        match="cases_config.json debe definir lakefs_conventions.branch_pattern",
    ):
        manager.resolve_transform_branch(
            repository="casob--uci-appliances",
            dataset="uci-appliances",
            case_id="B",
        )


def test_resolve_transform_branch_returns_v1_when_no_matching_tags():
    """Si no hay tags compatibles con el patrón, debe devolver versión 1."""

    class _Tag:
        def __init__(self, tag_id: str):
            self.id = tag_id

    class _Page:
        def __init__(self, results):
            self.results = results
            self.pagination = SimpleNamespace(has_more=False, next_offset=None)

    class _TagsApi:
        @staticmethod
        def list_tags(repository: str, after=None, amount=1000):
            _ = (repository, after, amount)
            return _Page([_Tag("otro-dataset_v10"), _Tag("tag-invalido")])

    manager = LakeFSManager(
        client=SimpleNamespace(tags_api=_TagsApi()),
        cases_config=_FakeCasesConfig(),
    )

    assert (
        manager.resolve_transform_branch(
            repository="casob--uci-appliances",
            dataset="uci-appliances",
            case_id="B",
        )
        == "transform/v1"
    )


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


def test_new_transform_branch_creates_branch_when_missing():
    """Crea rama transform desde `default_branch` cuando no existe."""

    class _Tag:
        def __init__(self, tag_id: str):
            self.id = tag_id

    class _Page:
        def __init__(self, results):
            self.results = results
            self.pagination = SimpleNamespace(has_more=False, next_offset=None)

    class _TagsApi:
        @staticmethod
        def list_tags(repository: str, after=None, amount=1000):
            _ = (repository, after, amount)
            return _Page([_Tag("uci-appliances_v2")])

    created: dict[str, object] = {}

    class _BranchesApi:
        @staticmethod
        def get_branch(repository: str, branch: str):
            _ = (repository, branch)
            raise RuntimeError("missing")

        @staticmethod
        def create_branch(repository: str, branch_creation):
            created["repository"] = repository
            created["name"] = branch_creation.name
            created["source"] = branch_creation.source
            return {"ok": True}

    manager = LakeFSManager(
        client=SimpleNamespace(tags_api=_TagsApi(), branches_api=_BranchesApi()),
        cases_config=_FakeCasesConfig(),
    )

    branch = manager.new_transform_branch("casob--uci-appliances")

    assert branch == "transform/v3"
    assert created["repository"] == "casob--uci-appliances"
    assert created["name"] == "transform/v3"
    assert created["source"] == "main"


def test_new_transform_branch_returns_existing_branch_without_creating():
    """Si la rama transform ya existe, no intenta recrearla."""

    class _Page:
        def __init__(self, results):
            self.results = results
            self.pagination = SimpleNamespace(has_more=False, next_offset=None)

    class _TagsApi:
        @staticmethod
        def list_tags(repository: str, after=None, amount=1000):
            _ = (repository, after, amount)
            return _Page([])

    created_calls: list[object] = []

    class _BranchesApi:
        @staticmethod
        def get_branch(repository: str, branch: str):
            _ = (repository, branch)
            return {"ok": True}

        @staticmethod
        def create_branch(repository: str, branch_creation):
            created_calls.append((repository, branch_creation))
            return {"ok": True}

    manager = LakeFSManager(
        client=SimpleNamespace(tags_api=_TagsApi(), branches_api=_BranchesApi()),
        cases_config=_FakeCasesConfig(),
    )

    branch = manager.new_transform_branch("casob--uci-appliances")

    assert branch == "transform/v1"
    assert created_calls == []


def test_new_transform_branch_raises_when_repository_does_not_match_pattern():
    """Falla cuando no puede extraer dataset desde nombre de repositorio."""
    manager = LakeFSManager(
        client=SimpleNamespace(),
        cases_config=_FakeCasesConfig(),
    )

    with pytest.raises(ValueError, match="No se pudo extraer dataset desde repository"):
        manager.new_transform_branch("repositorio-invalido")


def test_new_transform_branch_resolves_repository_from_dataset_and_case():
    """Si no llega `repository`, lo resuelve desde `dataset` y `case_id`."""

    class _Tag:
        def __init__(self, tag_id: str):
            self.id = tag_id

    class _Page:
        def __init__(self, results):
            self.results = results
            self.pagination = SimpleNamespace(has_more=False, next_offset=None)

    class _TagsApi:
        @staticmethod
        def list_tags(repository: str, after=None, amount=1000):
            _ = (repository, after, amount)
            return _Page([_Tag("uci-appliances_v1")])

    created: dict[str, object] = {}

    class _BranchesApi:
        @staticmethod
        def get_branch(repository: str, branch: str):
            _ = (repository, branch)
            raise RuntimeError("missing")

        @staticmethod
        def create_branch(repository: str, branch_creation):
            created["repository"] = repository
            created["name"] = branch_creation.name
            created["source"] = branch_creation.source
            return {"ok": True}

    manager = LakeFSManager(
        client=SimpleNamespace(tags_api=_TagsApi(), branches_api=_BranchesApi()),
        cases_config=_FakeCasesConfig(),
    )

    branch = manager.new_transform_branch(dataset="uci-appliances", case_id="B")

    assert branch == "transform/v2"
    assert created["repository"] == "casob--uci-appliances"
    assert created["name"] == "transform/v2"
    assert created["source"] == "main"


def test_commit_bronze_uploads_files_and_creates_medallion_commit(tmp_path):
    """Sube ficheros a la ruta Bronze configurada y crea commit Medallion."""
    file_a = tmp_path / "a.csv"
    file_b = tmp_path / "b.csv"
    file_a.write_text("a,1\n", encoding="utf-8")
    file_b.write_text("b,2\n", encoding="utf-8")

    class _Tag:
        def __init__(self, tag_id: str):
            self.id = tag_id

    class _Page:
        def __init__(self, results):
            self.results = results
            self.pagination = SimpleNamespace(has_more=False, next_offset=None)

    class _TagsApi:
        @staticmethod
        def list_tags(repository: str, after=None, amount=1000):
            _ = (repository, after, amount)
            return _Page([_Tag("uci-appliances_v1")])

    uploaded: list[tuple[str, str, str, bytes]] = []

    class _ObjectsApi:
        @staticmethod
        def upload_object(repository: str, branch: str, path: str, content):
            payload = content.read() if hasattr(content, "read") else bytes(content)
            uploaded.append((repository, branch, path, payload))
            return {"ok": True}

    class _BranchesApi:
        @staticmethod
        def get_branch(repository: str, branch: str):
            _ = (repository, branch)
            raise RuntimeError("missing")

        @staticmethod
        def create_branch(repository: str, branch_creation):
            _ = (repository, branch_creation)
            return {"ok": True}

    captured_commit: dict[str, object] = {}

    class _CommitsApi:
        @staticmethod
        def commit(repository: str, branch: str, commit_creation):
            captured_commit["repository"] = repository
            captured_commit["branch"] = branch
            captured_commit["message"] = commit_creation.message
            captured_commit["metadata"] = dict(commit_creation.metadata)

            class _Commit:
                id = "commit-bronze-1"

            return _Commit()

    manager = LakeFSManager(
        client=SimpleNamespace(
            tags_api=_TagsApi(),
            objects_api=_ObjectsApi(),
            branches_api=_BranchesApi(),
            commits_api=_CommitsApi(),
        ),
        cases_config=_FakeCasesConfig(),
    )

    commit_id = manager.commit_bronze(
        files=[file_a, file_b],
        dataset="uci-appliances",
        case_id="B",
    )

    assert commit_id == "commit-bronze-1"
    assert len(uploaded) == 2
    assert uploaded[0][0] == "casob--uci-appliances"
    assert uploaded[0][1] == "transform/v2"
    assert uploaded[0][2] == "raw/bronze/a.csv"
    assert uploaded[1][2] == "raw/bronze/b.csv"
    assert captured_commit["repository"] == "casob--uci-appliances"
    assert captured_commit["branch"] == "transform/v2"
    assert "bronze" in str(captured_commit["message"]).lower()
    assert captured_commit["metadata"]["layer"] == "bronze"
    assert captured_commit["metadata"]["files_count"] == "2"


def test_commit_bronze_accepts_repository_and_single_file(tmp_path):
    """Acepta repositorio explícito y fichero único."""
    file_a = tmp_path / "a.csv"
    file_a.write_text("a,1\n", encoding="utf-8")

    uploaded: list[tuple[str, str, str]] = []

    class _ObjectsApi:
        @staticmethod
        def upload_object(repository: str, branch: str, path: str, content):
            _ = content.read()
            uploaded.append((repository, branch, path))
            return {"ok": True}

    class _CommitsApi:
        @staticmethod
        def commit(repository: str, branch: str, commit_creation):
            _ = (repository, branch, commit_creation)

            class _Commit:
                id = "c2"

            return _Commit()

    manager = LakeFSManager(
        client=SimpleNamespace(
            objects_api=_ObjectsApi(),
            commits_api=_CommitsApi(),
        ),
        cases_config=_FakeCasesConfig(),
    )

    commit_id = manager.commit_bronze(
        files=file_a,
        repository="casob--uci-appliances",
        branch="transform/v99",
    )

    assert commit_id == "c2"
    assert uploaded == [("casob--uci-appliances", "transform/v99", "raw/bronze/a.csv")]
