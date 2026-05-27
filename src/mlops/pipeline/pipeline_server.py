"""Servidor webhook que recibe eventos de lakeFS y dispara reentrenamiento.

LakeFS llama a este servidor vía HTTP POST cuando ocurre un evento de tag
en cualquier repositorio de datasets.
"""

import json
import logging
import os
import subprocess
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from mlops.config import CASES_CONFIG
from mlops.pipeline.trigger_resolver import (
    PipelineTriggerResolver,
    TriggerIgnoredError,
    TriggerResolverError,
)

# Configuración
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [PIPELINE] %(levelname)s — %(message)s"
)
log = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
PORT = int(os.environ.get("PIPELINE_PORT", 8080))
TRIGGER_RESOLVER = PipelineTriggerResolver()


def _format_configured_datasets() -> str:
    """Devuelve datasets configurados en formato multilinea tabulado."""
    dataset_names = sorted(
        name
        for name, cfg in CASES_CONFIG.datasets.items()
        if isinstance(name, str) and isinstance(cfg, dict)
    )
    return "\n".join(f"\t- {dataset}" for dataset in dataset_names)


class WebhookHandler(BaseHTTPRequestHandler):
    """Gestiona peticiones webhook HTTP enviadas por lakeFS.

    Implementa los endpoints de healthcheck y recepción de eventos, resuelve
    triggers con `PipelineTriggerResolver` y lanza `pipeline_train.py` cuando
    el evento es aplicable.
    """

    def do_GET(self):  # noqa: N802
        """Endpoint de healthcheck.

        Responde siempre ``200 OK`` con cuerpo JSON mínimo para facilitar
        comprobaciones de liveness/readiness del contenedor.
        """
        self._responder(200, "OK")

    def do_POST(self):  # noqa: N802
        """Procesa eventos webhook de lakeFS y dispara reentrenamiento.

        Flujo:
        1. Lee y parsea el JSON del request.
        2. Resuelve/valida trigger con ``PipelineTriggerResolver``.
        3. Si el trigger es válido, arranca ``pipeline_train.py`` en segundo
           plano y responde inmediatamente.

        Estrategia de errores:
        - ``TriggerIgnoredError``: se responde 200 con mensaje de ignorado.
        - ``TriggerResolverError``: se responde con código semántico (400).
        - Cualquier otro error: se responde 500.
        """
        longitud = int(self.headers.get("Content-Length", 0))
        cuerpo = self.rfile.read(longitud)

        try:
            evento = json.loads(cuerpo)
        except json.JSONDecodeError:
            log.error("Payload no es JSON válido")
            self._responder(400, "Payload inválido")
            return

        log.info(f"Evento recibido: {json.dumps(evento, indent=2)}")

        try:
            trigger = TRIGGER_RESOLVER.resolve(evento)
        except TriggerIgnoredError as exc:
            log.info(str(exc))
            self._responder(exc.status_code, str(exc))
            return
        except TriggerResolverError as exc:
            log.error(str(exc))
            self._responder(exc.status_code, str(exc))
            return
        except Exception as exc:
            log.exception("Error inesperado resolviendo trigger")
            self._responder(500, f"Error interno resolviendo trigger: {exc}")
            return

        log.info(
            f"Disparando pipeline para el repositorio '{trigger.repository}'. "
            f"Dataset: {trigger.dataset}. Tag: {trigger.tag_id}. "
            f"Commit: {trigger.commit_hash[:8]}"
        )
        self._lanzar_pipeline(
            dataset=trigger.dataset,
            case_id=trigger.case_id,
            commit_hash=trigger.commit_hash,
            committer=trigger.committer,
            tag_id=trigger.tag_id,
        )
        self._responder(
            200,
            f"Pipeline iniciado para el repositorio {trigger.repository}",
        )

    def _lanzar_pipeline(
        self,
        dataset: str,
        case_id: str,
        commit_hash: str,
        committer: str,
        tag_id: str,
    ):
        """Lanza ``pipeline_train.py`` de forma no bloqueante.

        Args:
            dataset: Dataset lógico extraído desde ``repositorio``.
            case_id: Identificador de caso de uso asociado al dataset.
            commit_hash: Commit exacto asociado al tag recibido.
            committer: Usuario que originó el evento.
            tag_id: Tag creado en lakeFS.

        Comportamiento:
        - Compone argumentos de proceso para evitar shell quoting manual.
        - Redirige stdout/stderr a un fichero de log con timestamp.
        - Usa ``subprocess.Popen`` para no bloquear el webhook.
        """
        comando_args = [
            "python",
            str(BASE_DIR / "pipeline_train.py"),
            "--caso",
            case_id,
            "--dataset",
            dataset,
            "--commit",
            commit_hash,
            "--committer",
            committer,
            "--tag",
            tag_id,
        ]

        log.info(f"Ejecutando: {' '.join(comando_args)}")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_path = f"/tmp/pipeline_{dataset}_{timestamp}.log"

        with open(log_path, "w") as log_file:
            subprocess.Popen(
                comando_args,
                stdout=log_file,
                stderr=log_file,
            )

        log.info(f"Pipeline lanzado. Log en: {log_path}")

    def _responder(self, codigo: int, mensaje: str):
        """Envía respuesta JSON uniforme al cliente webhook.

        Args:
            codigo: Código HTTP de respuesta.
            mensaje: Texto funcional de estado para trazabilidad.
        """
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        respuesta = json.dumps({"status": mensaje, "code": codigo})
        self.wfile.write(respuesta.encode())


if __name__ == "__main__":
    servidor = HTTPServer(("0.0.0.0", PORT), WebhookHandler)
    log.info(f"Servidor webhook arrancado en puerto {PORT}")
    log.info("Pipelines configurados:\n%s", _format_configured_datasets())
    log.info("Esperando eventos de lakeFS")

    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        log.info("Servidor detenido")
