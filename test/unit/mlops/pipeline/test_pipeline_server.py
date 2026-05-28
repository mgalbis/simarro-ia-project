"""Pruebas unitarias para el servidor webhook de pipeline."""

from __future__ import annotations

import io
import json
from datetime import datetime as real_datetime

from mlops.config import CASES_CONFIG
from mlops.pipeline import pipeline_server as ps
from mlops.pipeline.trigger_resolver import (
    PipelineTrigger,
    TriggerIgnoredError,
    TriggerResolverError,
)


class _DummyPostHandler:
    """Handler mínimo para invocar `do_POST` sin servidor HTTP real."""

    def __init__(self, body: bytes):
        self.headers = {"Content-Length": str(len(body))}
        self.rfile = io.BytesIO(body)
        self.responses: list[tuple[int, str]] = []
        self.launch_calls: list[dict[str, str]] = []

    def _responder(self, codigo: int, mensaje: str):
        self.responses.append((codigo, mensaje))

    def _lanzar_pipeline(
        self,
        *,
        repository: str,
        dataset: str,
        case_id: str,
        commit_hash: str,
        committer: str,
        tag_id: str,
    ):
        self.launch_calls.append(
            {
                "repository": repository,
                "dataset": dataset,
                "case_id": case_id,
                "commit_hash": commit_hash,
                "committer": committer,
                "tag_id": tag_id,
            }
        )


class _DummyResponseHandler:
    """Handler mínimo para validar `_responder`."""

    def __init__(self):
        self.status = None
        self.headers: list[tuple[str, str]] = []
        self.ended = False
        self.wfile = io.BytesIO()

    def send_response(self, code: int):
        self.status = code

    def send_header(self, key: str, value: str):
        self.headers.append((key, value))

    def end_headers(self):
        self.ended = True


def _set_config_property(monkeypatch, name: str, value):
    """Parchea una propiedad de `CASES_CONFIG` para pruebas controladas."""
    cfg_type = type(CASES_CONFIG)
    monkeypatch.setattr(cfg_type, name, property(lambda self: value))


def test_format_configured_datasets_returns_sorted_tabulated_block(monkeypatch):
    """Lista datasets válidos en orden alfabético y con tabulación por línea."""
    _set_config_property(
        monkeypatch,
        "datasets",
        {
            "zeta": {"case": "A"},
            "alpha": {"case": "B"},
            "broken": "invalid",
            123: {"case": "C"},
        },
    )

    formatted = ps._format_configured_datasets()

    assert formatted == "\t- alpha\n\t- zeta"


def test_do_get_returns_healthcheck_ok():
    """`do_GET` delega en `_responder` con 200/OK."""
    handler = _DummyPostHandler(body=b"")

    ps.WebhookHandler.do_GET(handler)

    assert handler.responses == [(200, "OK")]


def test_do_post_rejects_invalid_json_payload():
    """Responde 400 cuando el body no es JSON válido."""
    handler = _DummyPostHandler(body=b"{invalid")

    ps.WebhookHandler.do_POST(handler)

    assert handler.responses == [(400, "Payload inválido")]
    assert handler.launch_calls == []


def test_do_post_handles_ignored_trigger(monkeypatch):
    """Responde el código/mensaje de `TriggerIgnoredError` sin lanzar pipeline."""

    class _Resolver:
        def resolve(self, _event):
            raise TriggerIgnoredError("Ignorado (test)")

    monkeypatch.setattr(ps, "TRIGGER_RESOLVER", _Resolver())
    handler = _DummyPostHandler(body=json.dumps({"event_type": "x"}).encode())

    ps.WebhookHandler.do_POST(handler)

    assert handler.responses == [(200, "Ignorado (test)")]
    assert handler.launch_calls == []


def test_do_post_handles_trigger_validation_error(monkeypatch):
    """Responde con código semántico cuando falla la validación del trigger."""

    class _ValidationError(TriggerResolverError):
        status_code = 422

    class _Resolver:
        def resolve(self, _event):
            raise _ValidationError("Payload inconsistente")

    monkeypatch.setattr(ps, "TRIGGER_RESOLVER", _Resolver())
    handler = _DummyPostHandler(body=json.dumps({"event_type": "x"}).encode())

    ps.WebhookHandler.do_POST(handler)

    assert handler.responses == [(422, "Payload inconsistente")]
    assert handler.launch_calls == []


def test_do_post_handles_unexpected_error(monkeypatch):
    """Responde 500 cuando aparece una excepción no controlada en el resolver."""

    class _Resolver:
        def resolve(self, _event):
            raise RuntimeError("boom")

    monkeypatch.setattr(ps, "TRIGGER_RESOLVER", _Resolver())
    handler = _DummyPostHandler(body=json.dumps({"event_type": "x"}).encode())

    ps.WebhookHandler.do_POST(handler)

    assert len(handler.responses) == 1
    assert handler.responses[0][0] == 500
    assert "Error interno resolviendo trigger" in handler.responses[0][1]
    assert "boom" in handler.responses[0][1]
    assert handler.launch_calls == []


def test_do_post_launches_pipeline_with_trigger_fields(monkeypatch):
    """En camino feliz, lanza pipeline con campos del trigger y responde 200."""
    trigger = PipelineTrigger(
        repository="casob--uci-appliances",
        dataset="uci-appliances",
        case_id="B",
        commit_hash="abc123",
        committer="caso_b",
        tag_id="uci-appliances_v1",
    )

    class _Resolver:
        def resolve(self, _event):
            return trigger

    monkeypatch.setattr(ps, "TRIGGER_RESOLVER", _Resolver())
    handler = _DummyPostHandler(
        body=json.dumps({"event_type": "post-create-tag"}).encode()
    )

    ps.WebhookHandler.do_POST(handler)

    assert handler.launch_calls == [
        {
            "repository": "casob--uci-appliances",
            "dataset": "uci-appliances",
            "case_id": "B",
            "commit_hash": "abc123",
            "committer": "caso_b",
            "tag_id": "uci-appliances_v1",
        }
    ]
    assert handler.responses == [
        (200, "Pipeline iniciado para el repositorio casob--uci-appliances")
    ]


def test_lanzar_pipeline_builds_expected_command_and_log_path(monkeypatch):
    """Construye args correctos y redirige stdout/stderr al log temporal esperado."""
    captured: dict[str, object] = {}

    class _FakeDateTime:
        @staticmethod
        def now():
            return real_datetime(2026, 1, 2, 3, 4, 5)

    class _FakeFile(io.StringIO):
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    def _fake_open(path, mode, *args, **kwargs):
        captured["open_path"] = path
        captured["open_mode"] = mode
        fake = _FakeFile()
        captured["log_file"] = fake
        return fake

    def _fake_popen(args, stdout=None, stderr=None):
        captured["popen_args"] = args
        captured["stdout"] = stdout
        captured["stderr"] = stderr

    monkeypatch.setattr(ps, "datetime", _FakeDateTime)
    monkeypatch.setattr("builtins.open", _fake_open)
    monkeypatch.setattr(ps.subprocess, "Popen", _fake_popen)

    ps.WebhookHandler._lanzar_pipeline(
        None,
        repository="casob--uci-appliances",
        dataset="uci-appliances",
        case_id="B",
        commit_hash="abc123",
        committer="caso_b",
        tag_id="uci-appliances_v1",
    )

    assert captured["open_path"] == "/tmp/pipeline_uci-appliances_20260102_030405.log"
    assert captured["open_mode"] == "w"
    assert captured["popen_args"] == [
        "python",
        str(ps.BASE_DIR / "pipeline_train.py"),
        "--caso",
        "B",
        "--repository",
        "casob--uci-appliances",
        "--dataset",
        "uci-appliances",
        "--commit",
        "abc123",
        "--committer",
        "caso_b",
        "--tag",
        "uci-appliances_v1",
    ]
    assert captured["stdout"] is captured["log_file"]
    assert captured["stderr"] is captured["log_file"]


def test_responder_writes_json_body_and_headers():
    """`_responder` envía status, header JSON y cuerpo serializado consistente."""
    handler = _DummyResponseHandler()

    ps.WebhookHandler._responder(handler, 201, "Aceptado")

    assert handler.status == 201
    assert ("Content-Type", "application/json") in handler.headers
    assert handler.ended is True
    body = json.loads(handler.wfile.getvalue().decode())
    assert body == {"status": "Aceptado", "code": 201}
