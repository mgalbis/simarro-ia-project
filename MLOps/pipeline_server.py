# Servidor webhook que recibe eventos de lakeFS y dispara el pipeline de reentrenamiento automático.
#
# LakeFS llama a este servidor vía HTTP POST cuando ocurre un merge a la rama main de cualquier repositorio de datasets.

import os
import json
import logging
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

# Configuración
PORT = int(os.environ.get("PIPELINE_PORT", 8080))

RAMA_PRODUCCION = "main"

# Definimos las pipelines en función de losrepositorios que tienen pipeline de reentrenamiento
# Clave: nombre del repositorio en lakeFS
# Valor: script de entrenamiento a ejecutar
PIPELINES = {
    "uci-appliances": "pipeline_train.py --caso B --dataset uci-appliances",
    "lbnl-fdd": "pipeline_train.py --caso C --dataset lbnl-fdd",
    "uci-occupancy": "pipeline_train.py --caso D --dataset uci-occupancy",
    "era5": "pipeline_train.py --caso E --dataset era5",
}

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [PIPELINE] %(levelname)s — %(message)s"
)
log = logging.getLogger(__name__)


# Handler del webhook
class WebhookHandler(BaseHTTPRequestHandler):
    """
    GEstiona las peticiones HTTP entrantes de lakeFS y LakeFS envía un POST con un JSON que describe el evento.
    """

    def do_GET(self):
        """
        Endpoint de salud para el healthcheck del contenedor. Responde con 200 OK a cualquier GET.
        """
        self._responder(200, "OK")

    def do_POST(self):
        """Punto de entrada para todos los eventos de lakeFS."""

        # Pasos del proceso:
        # 1. Leer el cuerpo de la petición
        longitud = int(self.headers.get("Content-Length", 0))
        cuerpo = self.rfile.read(longitud)

        try:
            evento = json.loads(cuerpo)
        except json.JSONDecodeError:
            log.error("Payload no es JSON válido")
            self._responder(400, "Payload inválido")
            return

        log.info(f"Evento recibido: {json.dumps(evento, indent=2)}")

        # 2. Extraer campos del evento de lakeFS
        # El payload de lakeFS tiene esta estructura:
        # {
        #   "event_type": "pre-merge" | "post-merge",
        #   "repository": "uci-appliances",
        #   "branch": "main",
        #   "source_ref": "dev",
        #   "commit_id": "abc123...",
        #   "committer": "caso_b",
        #   "commit_message": "mensaje del commit",
        # }
        tipo_evento = evento.get("event_type", "")
        repositorio = evento.get("repository") or evento.get("repository_id", "")
        rama_destino = evento.get("branch") or evento.get("branch_id", "")
        commit_hash = evento.get("commit_id", "")

        # 3. Filtrar: solo se procesarán los post-merge a main
        if tipo_evento != "post-merge":
            log.info(f"Evento ignorado ya que no es post-merge. Tipo: '{tipo_evento}'")
            self._responder(200, "Ignorado (no es post-merge)")
            return

        if rama_destino != RAMA_PRODUCCION:
            log.info(
                f"Evento ignorado ya que la rama de destino no es main. Rama: '{rama_destino}'"
            )
            self._responder(200, f"Ignorado (no es main)")
            return

        if repositorio not in PIPELINES:
            log.info(f"Repositorio '{repositorio}' sin pipeline configurado")
            self._responder(200, f"No existe pipeline para {repositorio}")
            return

        # 4. Lanzar el pipeline de reentrenamiento
        log.info(
            f"Disparando pipeline para el repositorio '{repositorio}'. Commit: {commit_hash[:8]}"
        )
        self._lanzar_pipeline(repositorio, commit_hash, evento)
        self._responder(200, f"Pipeline iniciado para el repositorio {repositorio}")

    def _lanzar_pipeline(self, repositorio: str, commit_hash: str, evento: dict):
        """
        Lanza el script de entrenamiento en un proceso separado.
        El proceso corre en segundo plano: el webhook responde inmediatamente sin esperar a que termine el entrenamiento.
        """
        comando_base = PIPELINES[repositorio]
        comando = (
            f"python {comando_base} "
            f"--commit {commit_hash} "
            f"--committer {evento.get('committer', 'unknown')}"
        )

        log.info(f"Ejecutando: {comando}")

        # subprocess.Popen lanza el proceso sin esperar su fin (no-blocking)
        # stdout y stderr se redirigen a un fichero de log
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_path = f"/tmp/pipeline_{repositorio}_{timestamp}.log"

        with open(log_path, "w") as log_file:
            subprocess.Popen(
                comando.split(),
                stdout=log_file,
                stderr=log_file,
            )

        log.info(f"Pipeline lanzado. Log en: {log_path}")

    def _responder(self, codigo: int, mensaje: str):
        """Envía una respuesta HTTP al webhook de lakeFS."""
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        respuesta = json.dumps({"status": mensaje, "code": codigo})
        self.wfile.write(respuesta.encode())

    def log_message(self, format, *args):
        pass


if __name__ == "__main__":
    servidor = HTTPServer(("0.0.0.0", PORT), WebhookHandler)
    log.info(f"Servidor webhook arrancado en puerto {PORT}")
    log.info(f"Pipelines configurados: {list(PIPELINES.keys())}")
    log.info("Esperando eventos de lakeFS")

    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        log.info("Servidor detenido")
