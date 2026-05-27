"""Resolución de eventos webhook a triggers de pipeline."""

from __future__ import annotations

import re
from dataclasses import dataclass

from mlops.config import CASES_CONFIG

TOKEN_RE = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")
VERSION_RE = r"[A-Za-z0-9][A-Za-z0-9._-]*"
GENERIC_TOKEN_RE = r"[A-Za-z0-9][A-Za-z0-9._-]*"


@dataclass(frozen=True)
class PipelineTrigger:
    """Representa un trigger validado y listo para disparar entrenamiento.

    Instancias de esta clase contienen los campos normalizados mínimos que
    necesita `pipeline_train.py` para ejecutar el pipeline de forma trazable.
    """

    repository: str
    dataset: str
    case_id: str
    commit_hash: str
    committer: str
    tag_id: str


class TriggerResolverError(Exception):
    """Define el error base para fallos durante la resolución de triggers.

    Incluye un `status_code` HTTP que permite mapear la excepción a la
    respuesta del webhook sin lógica adicional en el servidor.
    """

    status_code = 400


class TriggerIgnoredError(TriggerResolverError):
    """Indica que el evento es válido pero no aplica para lanzar pipeline.

    Se usa para eventos que deben ignorarse de forma explícita sin tratarse
    como error funcional del sistema.
    """

    status_code = 200


class TriggerValidationError(TriggerResolverError):
    """Indica que el payload del evento es inválido o inconsistente.

    Se usa cuando faltan campos obligatorios, no encajan patrones o existe
    incoherencia semántica en los datos recibidos.
    """

    status_code = 400


class PipelineTriggerResolver:
    """Valida eventos de lakeFS y construye objetos `PipelineTrigger`.

    Esta clase concentra las reglas de negocio para aceptar, ignorar o
    rechazar eventos de webhook antes de iniciar un pipeline de entrenamiento.
    """

    EVENT_TYPE = "post-create-tag"

    def __init__(self):
        """Inicializa resolver desde ``CASES_CONFIG`` de forma estricta.

        Carga y valida:
        - datasets configurados con su ``case`` asociado.
        - patrón de tags.
        - patrón de nombre de repositorio.
        """
        self._dataset_case_map = self._build_dataset_case_map()
        if not self._dataset_case_map:
            raise ValueError("No hay datasets configurados en cases_config.json")

        self._tag_pattern = CASES_CONFIG.tag_pattern.strip()
        if not self._tag_pattern:
            raise ValueError("tag_pattern no puede estar vacío")

        repo_pattern = CASES_CONFIG.repo_name_pattern.strip()
        if not repo_pattern:
            raise ValueError("repo_name_pattern no puede estar vacío")
        self._repo_regex = self._compile_repo_regex(repo_pattern)

    def resolve(self, event: dict) -> PipelineTrigger:
        """Valida payload y devuelve trigger; lanza excepción si no aplica."""
        event_type = str(event.get("event_type", "")).strip()
        if event_type != self.EVENT_TYPE:
            raise TriggerIgnoredError(f"Ignorado (no es {self.EVENT_TYPE})")

        repository = self._require(event, "repository", "repository_id")
        repo_match = self._repo_regex.fullmatch(repository)
        if not repo_match:
            raise TriggerValidationError(
                f"Nombre de repositorio inválido: '{repository}'"
            )

        dataset = (repo_match.group("dataset") or "").strip()
        if not dataset:
            raise TriggerValidationError(
                "No se pudo extraer dataset desde repository con repo_name_pattern"
            )
        if dataset not in self._dataset_case_map:
            raise TriggerIgnoredError(f"No existe pipeline para {repository}")

        case_id = CASES_CONFIG.case_for_dataset(dataset)

        tag_id = self._require(event, "tag_id")
        tag_regex = self._build_tag_regex(dataset)
        if not re.fullmatch(tag_regex, tag_id):
            raise TriggerValidationError(
                f"Tag inválido para dataset '{dataset}': '{tag_id}'"
            )

        commit_hash = self._require(event, "commit_id")
        committer = str(event.get("committer", "unknown"))

        return PipelineTrigger(
            repository=repository,
            dataset=dataset,
            case_id=case_id,
            commit_hash=commit_hash,
            committer=committer,
            tag_id=tag_id,
        )

    @staticmethod
    def _build_dataset_case_map() -> dict[str, str]:
        """Construye el mapeo ``dataset -> case_id`` desde CASES_CONFIG.

        Ignora entradas inválidas y normaliza el identificador de caso
        a mayúsculas sin espacios.
        """
        mapping: dict[str, str] = {}
        for dataset, cfg in CASES_CONFIG.datasets.items():
            if not isinstance(dataset, str) or not isinstance(cfg, dict):
                continue
            raw_case = cfg.get("case")
            if raw_case is None:
                continue
            case_id = str(raw_case).strip().upper()
            if not case_id:
                continue
            mapping[dataset] = case_id
        return mapping

    @staticmethod
    def _require(event: dict, key: str, alt_key: str | None = None) -> str:
        value = event.get(key)
        if alt_key and (value is None or str(value).strip() == ""):
            value = event.get(alt_key)
        normalized = str(value).strip() if value is not None else ""
        if normalized:
            return normalized
        if alt_key:
            raise TriggerValidationError(f"Falta '{key}'/'{alt_key}' en el payload")
        raise TriggerValidationError(f"Falta '{key}' en el payload")

    @staticmethod
    def _compile_repo_regex(pattern: str) -> re.Pattern[str]:
        parts: list[str] = []
        idx = 0
        dataset_seen = False
        for match in TOKEN_RE.finditer(pattern):
            parts.append(re.escape(pattern[idx : match.start()]))
            token = match.group(1)
            if token == "dataset":
                if dataset_seen:
                    raise TriggerValidationError(
                        "repo_name_pattern no puede incluir '{dataset}' más de una vez"
                    )
                parts.append(r"(?P<dataset>" + GENERIC_TOKEN_RE + r")")
                dataset_seen = True
            else:
                parts.append(GENERIC_TOKEN_RE)
            idx = match.end()
        parts.append(re.escape(pattern[idx:]))
        if not dataset_seen:
            raise TriggerValidationError(
                "repo_name_pattern debe incluir placeholder '{dataset}'"
            )
        return re.compile("".join(parts))

    def _build_tag_regex(self, dataset: str) -> str:
        parts: list[str] = []
        idx = 0
        for match in TOKEN_RE.finditer(self._tag_pattern):
            parts.append(re.escape(self._tag_pattern[idx : match.start()]))
            token = match.group(1)
            if token == "dataset":
                parts.append(re.escape(dataset))
            elif token == "version":
                parts.append(VERSION_RE)
            else:
                raise TriggerValidationError(
                    f"Placeholder no soportado en tag_patterns: '{token}'"
                )
            idx = match.end()
        parts.append(re.escape(self._tag_pattern[idx:]))
        return "".join(parts)
