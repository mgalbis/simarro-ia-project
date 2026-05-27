"""Objeto global de configuración de cases_config.json."""

from __future__ import annotations

import copy
import json
import os
from pathlib import Path
from pathlib import PurePosixPath
from typing import Any


class CasesConfig:
    """Representa la configuración de casos cargada una vez al inicio."""

    def __init__(self, data: dict[str, Any], source_path: Path):
        """Construye el contenedor de configuración en memoria.

        Args:
            data: Objeto JSON ya deserializado desde ``cases_config.json``.
                Debe ser un diccionario raíz con la estructura esperada.
            source_path: Ruta absoluta del fichero usado como origen.

        Raises:
            ValueError: Si ``data`` no es un diccionario.
        """
        if not isinstance(data, dict):
            raise ValueError("cases_config.json debe ser un objeto JSON")
        self._data = data
        self.source_path = source_path

    @staticmethod
    def default_path() -> Path:
        """Devuelve la ruta por defecto de ``cases_config.json``.

        Resolución:
        1. Si existe variable de entorno ``CASES_CONFIG_PATH``, se usa.
        2. Si no, se usa ``<project_root>/config/cases_config.json``.

        Returns:
            Ruta candidata al fichero de configuración.
        """
        project_root = Path(__file__).resolve().parents[3]
        return Path(
            os.environ.get(
                "CASES_CONFIG_PATH", project_root / "config" / "cases_config.json"
            )
        )

    @classmethod
    def from_file(cls, config_path: str | Path | None = None) -> "CasesConfig":
        """Carga configuración desde disco y crea una instancia ``CasesConfig``.

        Args:
            config_path: Ruta explícita al JSON. Si es ``None``, usa
                :meth:`default_path`.

        Returns:
            Instancia inicializada con contenido validado mínimamente.

        Raises:
            FileNotFoundError: Si el fichero no existe.
            json.JSONDecodeError: Si el contenido no es JSON válido.
            ValueError: Si el JSON raíz no es objeto.
        """
        path = Path(config_path) if config_path is not None else cls.default_path()
        resolved = path.resolve()
        if not resolved.exists():
            raise FileNotFoundError(
                f"No existe el fichero de configuración de casos: {resolved}"
            )
        with resolved.open(encoding="utf-8") as config_file:
            config = json.load(config_file)
        return cls(data=config, source_path=resolved)

    def as_dict(self) -> dict[str, Any]:
        """Devuelve una copia profunda del JSON completo.

        Esta copia permite inspección o transformaciones temporales sin alterar
        el estado interno del singleton ``CASES_CONFIG``.

        Returns:
            Copia profunda del árbol de configuración.
        """
        return copy.deepcopy(self._data)

    @property
    def cases(self) -> dict[str, Any]:
        """Obtiene el nodo ``cases`` con validación de tipo.

        Returns:
            Copia profunda del bloque ``cases``.

        Raises:
            ValueError: Si ``cases`` no existe como objeto JSON.
        """
        cases = self._data.get("cases", {})
        if not isinstance(cases, dict):
            raise ValueError("cases_config.json debe contener un nodo 'cases' tipo objeto")
        return copy.deepcopy(cases)

    @property
    def datasets(self) -> dict[str, Any]:
        """Obtiene el nodo ``datasets`` con validación de tipo.

        Returns:
            Copia profunda del bloque ``datasets``.

        Raises:
            ValueError: Si ``datasets`` no existe como objeto JSON.
        """
        datasets = self._data.get("datasets", {})
        if not isinstance(datasets, dict):
            raise ValueError(
                "cases_config.json debe contener un nodo 'datasets' tipo objeto"
            )
        return copy.deepcopy(datasets)

    @property
    def lakefs_conventions(self) -> dict[str, Any]:
        """Obtiene el nodo ``lakefs_conventions`` con validación de tipo.

        Returns:
            Copia profunda de las convenciones de lakeFS.

        Raises:
            ValueError: Si ``lakefs_conventions`` no existe como objeto JSON.
        """
        conventions = self._data.get("lakefs_conventions", {})
        if not isinstance(conventions, dict):
            raise ValueError(
                "cases_config.json debe contener un nodo 'lakefs_conventions' tipo objeto"
            )
        return copy.deepcopy(conventions)

    @property
    def mlflow_conventions(self) -> dict[str, Any]:
        """Obtiene el nodo ``mlflow_conventions`` con validación de tipo.

        Returns:
            Copia profunda de las convenciones de MLflow.

        Raises:
            ValueError: Si ``mlflow_conventions`` no existe como objeto JSON.
        """
        conventions = self._data.get("mlflow_conventions", {})
        if not isinstance(conventions, dict):
            raise ValueError(
                "cases_config.json debe contener un nodo 'mlflow_conventions' tipo objeto"
            )
        return copy.deepcopy(conventions)

    @property
    def default_branch(self) -> str:
        """Devuelve la rama por defecto de lakeFS de forma estricta.

        Reglas de validación:
        - El campo ``lakefs_conventions.default_branch`` debe existir.
        - Debe ser ``string``.
        - No puede quedar vacío tras ``strip()``.

        Returns:
            Nombre de rama normalizado (sin espacios laterales).

        Raises:
            ValueError: Si el campo no existe, no es string o está vacío.
        """
        conventions = self.lakefs_conventions
        if "default_branch" not in conventions:
            raise ValueError(
                "cases_config.json debe definir lakefs_conventions.default_branch"
            )

        branch = conventions["default_branch"]
        if not isinstance(branch, str):
            raise ValueError(
                "cases_config.json: lakefs_conventions.default_branch debe ser string"
            )

        normalized = branch.strip()
        if not normalized:
            raise ValueError(
                "cases_config.json debe definir lakefs_conventions.default_branch"
            )
        return normalized

    @property
    def tag_pattern(self) -> str:
        """Devuelve el patrón de tags de lakeFS de forma estricta.

        Reglas de validación:
        - El campo ``lakefs_conventions.tag_patterns`` debe existir.
        - Debe ser ``string``.
        - No puede quedar vacío tras ``strip()``.

        Returns:
            Patrón de tag normalizado.

        Raises:
            ValueError: Si el campo no existe, no es string o está vacío.
        """
        conventions = self.lakefs_conventions
        if "tag_patterns" not in conventions:
            raise ValueError(
                "cases_config.json debe definir lakefs_conventions.tag_patterns"
            )

        pattern = conventions["tag_patterns"]
        if not isinstance(pattern, str):
            raise ValueError(
                "cases_config.json: lakefs_conventions.tag_patterns debe ser string"
            )

        normalized = pattern.strip()
        if not normalized:
            raise ValueError(
                "cases_config.json debe definir lakefs_conventions.tag_patterns"
            )
        return normalized

    @property
    def repo_name_pattern(self) -> str:
        """Devuelve el patrón de naming de repositorios en lakeFS.

        Reglas de validación:
        - El campo ``lakefs_conventions.repo_name_pattern`` debe existir.
        - Debe ser ``string``.
        - No puede quedar vacío tras ``strip()``.

        Returns:
            Patrón de repositorio normalizado.

        Raises:
            ValueError: Si el campo no existe, no es string o está vacío.
        """
        conventions = self.lakefs_conventions
        if "repo_name_pattern" not in conventions:
            raise ValueError(
                "cases_config.json debe definir lakefs_conventions.repo_name_pattern"
            )

        pattern = conventions["repo_name_pattern"]
        if not isinstance(pattern, str):
            raise ValueError(
                "cases_config.json: lakefs_conventions.repo_name_pattern debe ser string"
            )

        normalized = pattern.strip()
        if not normalized:
            raise ValueError(
                "cases_config.json debe definir lakefs_conventions.repo_name_pattern"
            )
        return normalized

    def case_for_dataset(self, dataset: str) -> str:
        """Resuelve el ``case`` asociado a un dataset concreto.

        Args:
            dataset: Clave de dataset dentro de ``datasets``.

        Returns:
            Identificador de caso en mayúsculas (por ejemplo ``"B"``).

        Raises:
            KeyError: Si el dataset no existe.
            ValueError: Si el dataset no define campo ``case`` válido.
        """
        dataset_cfg = self.datasets.get(dataset)
        if not isinstance(dataset_cfg, dict):
            raise KeyError(f"Dataset '{dataset}' no existe en cases_config.json")
        case_id = dataset_cfg.get("case")
        if case_id is None or str(case_id).strip() == "":
            raise ValueError(
                f"Dataset '{dataset}' no define el campo obligatorio 'case'"
            )
        return str(case_id).strip().upper()

    def resolve_experiment_name(self, case_id: str) -> str:
        """Resuelve el nombre de experimento MLflow para un caso.

        Construye el nombre con el patrón estricto
        ``mlflow_conventions.experiment_pattern`` aplicando placeholders:
        - ``{case}``: identificador del caso (por ejemplo ``"B"``).
        - ``{name}``: campo ``cases.<case>.name``.

        Args:
            case_id: Identificador del caso de uso.

        Returns:
            Nombre de experimento renderizado.

        Raises:
            KeyError: Si el caso no existe.
            ValueError: Si faltan datos obligatorios o el patrón no se puede renderizar.
        """
        normalized_case = str(case_id).strip().upper()
        if not normalized_case:
            raise ValueError("Debe informarse un case_id no vacío")

        case_cfg = self.cases.get(normalized_case)
        if not isinstance(case_cfg, dict):
            raise KeyError(f"Case '{normalized_case}' no existe en cases_config.json")

        case_name = case_cfg.get("name")
        if not isinstance(case_name, str) or not case_name.strip():
            raise ValueError(
                f"Case '{normalized_case}' debe definir 'name' como string no vacío"
            )

        conventions = self.mlflow_conventions
        if "experiment_pattern" not in conventions:
            raise ValueError(
                "cases_config.json debe definir mlflow_conventions.experiment_pattern"
            )

        pattern = conventions["experiment_pattern"]
        if not isinstance(pattern, str):
            raise ValueError(
                "cases_config.json: mlflow_conventions.experiment_pattern debe ser string"
            )
        pattern = pattern.strip()
        if not pattern:
            raise ValueError(
                "cases_config.json debe definir mlflow_conventions.experiment_pattern"
            )

        try:
            experiment_name = pattern.format(
                case=normalized_case,
                name=case_name.strip(),
            )
        except KeyError as exc:
            missing = exc.args[0]
            raise ValueError(
                "mlflow_conventions.experiment_pattern contiene placeholder no soportado: "
                f"'{missing}'"
            ) from exc

        if not experiment_name.strip():
            raise ValueError("El nombre de experimento resuelto no puede ser vacío")
        return experiment_name

    def resolve_gold_paths(self) -> dict[str, str]:
        """Resuelve rutas `train` y `test` de la capa Gold desde `cases_config`.

        Busca la configuración en:
        - `repository_schema.gold` (formato directo), o
        - `repository_schema.layers.gold` (formato por capas).

        Returns:
            Diccionario con claves `train` y `test` y rutas POSIX normalizadas.

        Raises:
            ValueError: Si falta algún nodo obligatorio o viene con tipo/valor inválido.
        """
        cfg = self.as_dict()
        repository_schema = cfg.get("repository_schema")
        if not isinstance(repository_schema, dict):
            raise ValueError("cases_config.json: falta nodo repository_schema")

        gold_node = repository_schema.get("gold")
        if not isinstance(gold_node, dict):
            layers = repository_schema.get("layers")
            if not isinstance(layers, dict):
                raise ValueError("cases_config.json: falta repository_schema.layers")
            gold_node = layers.get("gold")
            if not isinstance(gold_node, dict):
                raise ValueError("cases_config.json: falta repository_schema.layers.gold")

        gold_path = gold_node.get("path")
        files = gold_node.get("files")
        if not isinstance(gold_path, str) or not gold_path.strip():
            raise ValueError("cases_config.json: falta repository_schema.gold.path")
        if not isinstance(files, dict):
            raise ValueError("cases_config.json: falta repository_schema.gold.files")

        train_name = files.get("train")
        test_name = files.get("test")
        if not isinstance(train_name, str) or not train_name.strip():
            raise ValueError("cases_config.json: falta repository_schema.gold.files.train")
        if not isinstance(test_name, str) or not test_name.strip():
            raise ValueError("cases_config.json: falta repository_schema.gold.files.test")

        base = PurePosixPath(gold_path.strip("/"))
        train_path = str(base / train_name.strip("/"))
        test_path = str(base / test_name.strip("/"))
        return {"train": train_path, "test": test_path}

    def _column_mappings_for_dataset(self, dataset: str) -> dict[str, Any]:
        """Devuelve `column_mappings` para un dataset con validación estricta.

        Args:
            dataset: Nombre del dataset configurado en `cases_config.json`.

        Returns:
            Diccionario `column_mappings` del dataset.

        Raises:
            KeyError: Si el dataset no existe.
            ValueError: Si falta `column_mappings` o no es un objeto no vacío.
        """
        dataset_cfg = self.datasets.get(dataset)
        if not isinstance(dataset_cfg, dict):
            raise KeyError(f"Dataset '{dataset}' no existe en cases_config.json")

        column_mappings = dataset_cfg.get("column_mappings")
        if not isinstance(column_mappings, dict) or not column_mappings:
            raise ValueError(
                f"Dataset '{dataset}' debe definir 'column_mappings' como objeto no vacío"
            )
        return column_mappings

    def resolve_feature_columns(self, dataset: str) -> list[str]:
        """Resuelve columnas de entrada (`role == "feature"`) de un dataset.

        Args:
            dataset: Nombre del dataset configurado en `cases_config.json`.

        Returns:
            Lista de nombres de columnas feature.

        Raises:
            KeyError: Si el dataset no existe.
            ValueError: Si hay mappings inválidos o no hay ninguna feature.
        """
        column_mappings = self._column_mappings_for_dataset(dataset)
        features: list[str] = []

        for column_name, mapping in column_mappings.items():
            if not isinstance(mapping, dict):
                raise ValueError(
                    f"Dataset '{dataset}': mapping inválido para columna '{column_name}'"
                )

            if mapping.get("role") == "feature":
                features.append(column_name)

        if not features:
            raise ValueError(
                f"Dataset '{dataset}' no define columnas con role='feature'"
            )
        return features

    def resolve_target_column(self, dataset: str) -> str:
        """Resuelve columna objetivo (`role == "target"`) de un dataset.

        Nota: algunos datasets pueden no tener `target`. En ese caso este método
        lanza excepción y el flujo llamador decide si esa ausencia es válida.

        Args:
            dataset: Nombre del dataset configurado en `cases_config.json`.

        Returns:
            Nombre de la columna target.

        Raises:
            KeyError: Si el dataset no existe.
            ValueError: Si hay mappings inválidos, si no hay target
                o si hay más de un target.
        """
        column_mappings = self._column_mappings_for_dataset(dataset)
        target: str | None = None

        for column_name, mapping in column_mappings.items():
            if not isinstance(mapping, dict):
                raise ValueError(
                    f"Dataset '{dataset}': mapping inválido para columna '{column_name}'"
                )

            if mapping.get("role") == "target":
                if target is not None:
                    raise ValueError(
                        f"Dataset '{dataset}' define más de una columna con role='target'"
                    )
                target = column_name

        if target is None:
            raise ValueError(
                f"Dataset '{dataset}' no define ninguna columna con role='target'"
            )
        return target

CASES_CONFIG = CasesConfig.from_file()


def get_cases_config() -> CasesConfig:
    """Devuelve el singleton global de configuración.

    Returns:
        La instancia única ``CasesConfig`` inicializada al importar el módulo.
    """
    return CASES_CONFIG
