"""Pruebas unitarias para PipelineTriggerResolver."""

from __future__ import annotations

import re

import pytest

from mlops.config import CASES_CONFIG
from mlops.pipeline.trigger_resolver import (
    PipelineTrigger,
    PipelineTriggerResolver,
    TriggerIgnoredError,
    TriggerValidationError,
)

TOKEN_RE = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")


def _build_repository_name(dataset: str) -> str:
    """Construye un nombre de repositorio válido usando repo_name_pattern."""
    pattern = CASES_CONFIG.repo_name_pattern
    dataset_cfg = CASES_CONFIG.datasets[dataset]
    case_id = str(dataset_cfg.get("case", "")).strip().lower() or "x"

    def _replace_token(match: re.Match[str]) -> str:
        token = match.group(1)
        if token == "dataset":
            return dataset
        if token == "case":
            return case_id
        return "owner"

    return TOKEN_RE.sub(_replace_token, pattern)


def test_resolve_returns_pipeline_trigger_for_valid_event():
    """Valida el camino feliz completo.

    Comprueba que un evento `post-create-tag` bien formado, con:
    - repositorio que cumple `repo_name_pattern`,
    - `tag_id` que cumple `tag_patterns`,
    - `commit_id` y `committer`,
    produce un `PipelineTrigger` con todos los campos esperados
    (incluida la extracción correcta de `dataset`).
    """
    resolver = PipelineTriggerResolver()
    repository = _build_repository_name("uci-appliances")
    event = {
        "event_type": "post-create-tag",
        "repository": repository,
        "tag_id": "uci-appliances_v1",
        "commit_id": "abc123",
        "committer": "caso_b",
    }

    trigger = resolver.resolve(event)

    assert trigger == PipelineTrigger(
        repository=repository,
        dataset="uci-appliances",
        case_id="B",
        commit_hash="abc123",
        committer="caso_b",
        tag_id="uci-appliances_v1",
    )


def test_resolve_ignores_non_post_create_tag_event():
    """Verifica que eventos de tipo distinto se ignoran.

    El resolver debe lanzar `TriggerIgnoredError` cuando `event_type`
    no sea `post-create-tag`, sin evaluar el resto del payload.
    """
    resolver = PipelineTriggerResolver()
    repository = _build_repository_name("uci-appliances")
    event = {
        "event_type": "pre-merge",
        "repository": repository,
        "tag_id": "uci-appliances_v1",
        "commit_id": "abc123",
    }

    with pytest.raises(TriggerIgnoredError) as exc:
        resolver.resolve(event)

    assert "post-create-tag" in str(exc.value)


def test_resolve_accepts_repository_id_when_repository_missing():
    """Valida el fallback `repository_id`.

    Si `repository` no viene en el payload, el resolver debe aceptar
    `repository_id` como fuente alternativa y continuar normalmente.
    """
    resolver = PipelineTriggerResolver()
    repository = _build_repository_name("era5")
    event = {
        "event_type": "post-create-tag",
        "repository_id": repository,
        "tag_id": "era5_v2",
        "commit_id": "deadbeef",
    }

    trigger = resolver.resolve(event)

    assert trigger.repository == repository
    assert trigger.dataset == "era5"
    assert trigger.commit_hash == "deadbeef"


def test_resolve_rejects_repository_name_not_matching_pattern():
    """Rechaza repositorios que no cumplen `repo_name_pattern`.

    Asegura que el resolver falle con `TriggerValidationError` cuando
    el nombre del repositorio no puede parsearse para extraer dataset.
    """
    resolver = PipelineTriggerResolver()
    event = {
        "event_type": "post-create-tag",
        "repository": "uci-appliances",  # Falta prefijo owner/case.
        "tag_id": "uci-appliances_v1",
        "commit_id": "abc123",
    }

    with pytest.raises(TriggerValidationError) as exc:
        resolver.resolve(event)

    assert "repositorio inválido" in str(exc.value)


def test_resolve_ignores_unknown_dataset_extracted_from_repository():
    """Ignora repos válidos por forma pero sin dataset configurado.

    El nombre del repo puede cumplir el patrón, pero si el dataset
    extraído no existe en `CASES_CONFIG.datasets`, se considera evento
    no aplicable y debe lanzar `TriggerIgnoredError`.
    """
    resolver = PipelineTriggerResolver()
    repository = _build_repository_name("uci-appliances").replace(
        "uci-appliances", "dataset-no-existe"
    )
    event = {
        "event_type": "post-create-tag",
        "repository": repository,
        "tag_id": "dataset-no-existe_v1",
        "commit_id": "abc123",
    }

    with pytest.raises(TriggerIgnoredError) as exc:
        resolver.resolve(event)

    assert "No existe pipeline" in str(exc.value)


def test_resolve_rejects_tag_not_matching_pattern():
    """Rechaza tags que incumplen `lakefs_conventions.tag_patterns`.

    Comprueba que, para un dataset válido, un `tag_id` con formato
    incorrecto dispare `TriggerValidationError`.
    """
    resolver = PipelineTriggerResolver()
    repository = _build_repository_name("lbnl-fdd")
    event = {
        "event_type": "post-create-tag",
        "repository": repository,
        "tag_id": "tag-invalido",
        "commit_id": "abc123",
    }

    with pytest.raises(TriggerValidationError) as exc:
        resolver.resolve(event)

    assert "Tag inválido" in str(exc.value)


def test_resolve_rejects_missing_commit_id():
    """Valida campo obligatorio `commit_id`.

    Si falta `commit_id` el resolver debe fallar con
    `TriggerValidationError`, evitando construir trigger incompleto.
    """
    resolver = PipelineTriggerResolver()
    repository = _build_repository_name("uci-occupancy")
    event = {
        "event_type": "post-create-tag",
        "repository": repository,
        "tag_id": "uci-occupancy_v3",
    }

    with pytest.raises(TriggerValidationError) as exc:
        resolver.resolve(event)

    assert "commit_id" in str(exc.value)


def test_init_rejects_empty_datasets(monkeypatch):
    """Falla al inicializar si no hay datasets válidos en CASES_CONFIG."""
    cfg_type = type(CASES_CONFIG)
    monkeypatch.setattr(cfg_type, "datasets", property(lambda self: {}))

    with pytest.raises(ValueError) as exc:
        PipelineTriggerResolver()

    assert "No hay datasets" in str(exc.value)


def test_init_rejects_empty_tag_pattern(monkeypatch):
    """Falla al inicializar si `tag_pattern` está vacío tras normalización."""
    cfg_type = type(CASES_CONFIG)
    monkeypatch.setattr(
        cfg_type, "datasets", property(lambda self: {"uci-appliances": {"case": "B"}})
    )
    monkeypatch.setattr(cfg_type, "tag_pattern", property(lambda self: "   "))

    with pytest.raises(ValueError) as exc:
        PipelineTriggerResolver()

    assert "tag_pattern" in str(exc.value)


def test_init_rejects_empty_repo_name_pattern(monkeypatch):
    """Falla al inicializar si `repo_name_pattern` está vacío."""
    cfg_type = type(CASES_CONFIG)
    monkeypatch.setattr(
        cfg_type, "datasets", property(lambda self: {"uci-appliances": {"case": "B"}})
    )
    monkeypatch.setattr(
        cfg_type, "tag_pattern", property(lambda self: "{dataset}_v{version}")
    )
    monkeypatch.setattr(cfg_type, "repo_name_pattern", property(lambda self: " "))

    with pytest.raises(ValueError) as exc:
        PipelineTriggerResolver()

    assert "repo_name_pattern" in str(exc.value)


def test_init_rejects_repo_pattern_without_dataset_placeholder(monkeypatch):
    """Falla al inicializar si `repo_name_pattern` no contiene `{dataset}`."""
    cfg_type = type(CASES_CONFIG)
    monkeypatch.setattr(
        cfg_type, "datasets", property(lambda self: {"uci-appliances": {"case": "B"}})
    )
    monkeypatch.setattr(
        cfg_type, "tag_pattern", property(lambda self: "{dataset}_v{version}")
    )
    monkeypatch.setattr(
        cfg_type, "repo_name_pattern", property(lambda self: "caso{case}--owner")
    )

    with pytest.raises(TriggerValidationError) as exc:
        PipelineTriggerResolver()

    assert "{dataset}" in str(exc.value)


def test_init_rejects_repo_pattern_with_duplicate_dataset_placeholder(monkeypatch):
    """Falla al inicializar si `{dataset}` aparece más de una vez en el patrón."""
    cfg_type = type(CASES_CONFIG)
    monkeypatch.setattr(
        cfg_type, "datasets", property(lambda self: {"uci-appliances": {"case": "B"}})
    )
    monkeypatch.setattr(
        cfg_type, "tag_pattern", property(lambda self: "{dataset}_v{version}")
    )
    monkeypatch.setattr(
        cfg_type, "repo_name_pattern", property(lambda self: "x{dataset}y{dataset}")
    )

    with pytest.raises(TriggerValidationError) as exc:
        PipelineTriggerResolver()

    assert "más de una vez" in str(exc.value)


def test_resolve_rejects_missing_repository_and_repository_id():
    """Falla cuando no llega ni `repository` ni `repository_id` en el payload."""
    resolver = PipelineTriggerResolver()
    event = {
        "event_type": "post-create-tag",
        "tag_id": "uci-appliances_v1",
        "commit_id": "abc123",
    }

    with pytest.raises(TriggerValidationError) as exc:
        resolver.resolve(event)

    assert "repository" in str(exc.value)


def test_resolve_uses_repository_id_when_repository_is_blank():
    """Usa `repository_id` si `repository` viene vacío."""
    resolver = PipelineTriggerResolver()
    repository = _build_repository_name("era5")
    event = {
        "event_type": "post-create-tag",
        "repository": "   ",
        "repository_id": repository,
        "tag_id": "era5_v4",
        "commit_id": "cafe1234",
    }

    trigger = resolver.resolve(event)

    assert trigger.repository == repository
    assert trigger.dataset == "era5"


def test_resolve_rejects_missing_tag_id():
    """Falla cuando falta `tag_id` aunque el repositorio sea válido."""
    resolver = PipelineTriggerResolver()
    repository = _build_repository_name("uci-appliances")
    event = {
        "event_type": "post-create-tag",
        "repository": repository,
        "commit_id": "abc123",
    }

    with pytest.raises(TriggerValidationError) as exc:
        resolver.resolve(event)

    assert "tag_id" in str(exc.value)


def test_resolve_uses_unknown_committer_when_missing():
    """Asigna `unknown` cuando el payload no incluye `committer`."""
    resolver = PipelineTriggerResolver()
    repository = _build_repository_name("uci-appliances")
    event = {
        "event_type": "post-create-tag",
        "repository": repository,
        "tag_id": "uci-appliances_v9",
        "commit_id": "abc999",
    }

    trigger = resolver.resolve(event)

    assert trigger.committer == "unknown"


def test_resolve_rejects_tag_pattern_with_unsupported_placeholder(monkeypatch):
    """Falla en resolución si `tag_pattern` usa placeholders no soportados."""
    cfg_type = type(CASES_CONFIG)
    monkeypatch.setattr(
        cfg_type, "tag_pattern", property(lambda self: "{dataset}_{foo}")
    )

    resolver = PipelineTriggerResolver()
    repository = _build_repository_name("uci-appliances")
    event = {
        "event_type": "post-create-tag",
        "repository": repository,
        "tag_id": "uci-appliances_x",
        "commit_id": "abc123",
    }

    with pytest.raises(TriggerValidationError) as exc:
        resolver.resolve(event)

    assert "Placeholder no soportado" in str(exc.value)
