"""Gestión de operaciones lakeFS apoyadas en convenciones de `CASES_CONFIG`."""

from __future__ import annotations

import os
import re
from io import BytesIO
from pathlib import Path, PurePosixPath
from typing import Any

import lakefs_sdk
import pandas as pd
from lakefs_sdk.client import LakeFSClient

from mlops.config import CASES_CONFIG, CasesConfig


class LakeFSManager:
    """Encapsula operaciones de lectura en lakeFS con convenciones de proyecto.

    Esta clase centraliza:
    - resolución de rutas Gold desde `CASES_CONFIG`,
    - lectura robusta de respuestas binaras lakeFS,
    - descarga de splits train/test a DataFrames,
    - helpers de nomenclatura (repo/tag/branch) basados en convenciones.
    """

    def __init__(
        self,
        client: Any | None = None,
        cases_config: CasesConfig = CASES_CONFIG,
        *,
        endpoint: str | None = None,
        access_key_id: str | None = None,
        secret_access_key: str | None = None,
    ):
        """Construye el manager.

        Args:
            client: Cliente lakeFS ya construido. Si no se informa, se crea
                automáticamente desde entorno.
            cases_config: Configuración de casos/convenios.
            endpoint: Endpoint explícito para lakeFS (opcional).
            access_key_id: Access key explícita (opcional).
            secret_access_key: Secret key explícita (opcional).
        """
        self.client = client or self._create_client(
            endpoint=endpoint,
            access_key_id=access_key_id,
            secret_access_key=secret_access_key,
        )
        self.cases_config = cases_config

    @staticmethod
    def _create_client(
        *,
        endpoint: str | None = None,
        access_key_id: str | None = None,
        secret_access_key: str | None = None,
    ) -> LakeFSClient:
        """Crea cliente lakeFS desde argumentos explícitos o variables de entorno."""
        resolved_endpoint = endpoint or os.environ.get(
            "LAKEFS_ENDPOINT", "http://localhost:8001"
        )
        resolved_access_key = access_key_id or os.environ.get("LAKEFS_ACCESS_KEY_ID")
        resolved_secret_key = secret_access_key or os.environ.get(
            "LAKEFS_SECRET_ACCESS_KEY"
        )

        configuration = lakefs_sdk.Configuration(
            host=resolved_endpoint,
            username=resolved_access_key,
            password=resolved_secret_key,
        )
        return LakeFSClient(configuration=configuration)

    @property
    def default_branch(self) -> str:
        """Devuelve la rama por defecto definida en `cases_config.json`."""
        return self.cases_config.default_branch

    def resolve_repository_name(self, dataset: str, case_id: str | None = None) -> str:
        """Resuelve el nombre de repositorio siguiendo `repo_name_pattern`.

        Si `case_id` no se informa, se obtiene desde el mapeo de datasets de
        `CASES_CONFIG`.
        """
        resolved_case = (
            str(case_id).strip().upper()
            if case_id is not None
            else self.cases_config.case_for_dataset(dataset)
        )
        pattern = self.cases_config.repo_name_pattern
        return pattern.format(case=resolved_case.lower(), dataset=dataset)

    def new_transform_branch(
        self,
        repository: str | None = None,
        *,
        dataset: str | None = None,
        case_id: str | None = None,
    ) -> str:
        """Crea (si no existe) una rama de transformación y devuelve su nombre."""
        if repository is None:
            if dataset is None:
                raise ValueError(
                    "Debes informar `repository` o bien `dataset` para resolverlo."
                )
            repository = self.resolve_repository_name(dataset=dataset, case_id=case_id)
        elif dataset is None:
            dataset = self._dataset_from_repository_name(repository)

        branch = self.resolve_transform_branch(repository=repository, dataset=dataset)

        if not hasattr(self.client, "branches_api"):
            raise RuntimeError("El cliente lakeFS no expone branches_api")

        try:
            self.client.branches_api.get_branch(repository=repository, branch=branch)
            return branch
        except Exception:
            pass

        self.client.branches_api.create_branch(
            repository=repository,
            branch_creation=lakefs_sdk.BranchCreation(
                name=branch,
                source=self.default_branch,
            ),
        )
        return branch

    def resolve_transform_branch(
        self,
        repository: str,
        *,
        dataset: str | None = None,
        case_id: str | None = None,
    ) -> str:
        """Resuelve nombre de rama transform usando el patrón y la próxima versión.

        La versión se obtiene a partir del mayor sufijo numérico encontrado en
        los tags del repositorio (según `tag_pattern`) y se incrementa en 1.
        Si no hay tags compatibles, usa versión 1.
        """
        _ = case_id
        conventions = self.cases_config.lakefs_conventions
        if not isinstance(conventions, dict):
            raise ValueError(
                "cases_config.json no contiene 'lakefs_conventions' válido"
            )

        pattern = conventions.get("branch_pattern")
        if not isinstance(pattern, str) or not pattern.strip():
            raise ValueError(
                "cases_config.json debe definir lakefs_conventions.branch_pattern"
            )

        branch_pattern = pattern.strip()
        if "{version}" not in branch_pattern and "[version]" not in branch_pattern:
            raise ValueError(
                "lakefs_conventions.branch_pattern debe incluir "
                "placeholder '{version}' o '[version]'"
            )

        next_version = self._resolve_next_version_from_tags(
            repository=repository,
            dataset=dataset,
        )
        return (
            branch_pattern.replace("{version}", str(next_version))
            .replace("[version]", str(next_version))
            .strip()
        )

    def _list_tags(self, repository: str) -> list[str]:
        """Lista tags de un repositorio con paginación."""
        if not hasattr(self.client, "tags_api"):
            return []

        after: str | None = None
        tags: list[str] = []
        while True:
            response = self.client.tags_api.list_tags(
                repository=repository,
                after=after,
                amount=1000,
            )
            results = getattr(response, "results", None) or []
            if not results:
                break

            for item in results:
                tag_id = getattr(item, "id", None)
                if tag_id:
                    tags.append(str(tag_id))

            pagination = getattr(response, "pagination", None)
            has_more = bool(getattr(pagination, "has_more", False))
            next_offset = getattr(pagination, "next_offset", None)
            if not has_more or not next_offset:
                break
            after = str(next_offset)

        return tags

    def _resolve_next_version_from_tags(
        self,
        *,
        repository: str,
        dataset: str | None = None,
    ) -> int:
        """Devuelve la siguiente versión a partir de los tags del repositorio."""
        tags = self._list_tags(repository)
        if not tags:
            return 1

        tag_pattern = self.cases_config.tag_pattern.strip()
        escaped = re.escape(tag_pattern)
        if dataset is not None:
            escaped = escaped.replace(r"\{dataset\}", re.escape(dataset))
        else:
            escaped = escaped.replace(r"\{dataset\}", r"[A-Za-z0-9][A-Za-z0-9._-]*")
        escaped = escaped.replace(r"\{version\}", r"(?P<version>\d+)")
        escaped = escaped.replace(r"\[version\]", r"(?P<version>\d+)")

        regex = re.compile(f"^{escaped}$")
        max_version = 0
        for tag in tags:
            match = regex.fullmatch(tag)
            if not match:
                continue
            try:
                version = int(match.group("version"))
            except (TypeError, ValueError):
                continue
            if version > max_version:
                max_version = version

        return max_version + 1 if max_version > 0 else 1

    def _dataset_from_repository_name(self, repository: str) -> str:
        """Extrae dataset desde `repository` usando `repo_name_pattern`."""
        pattern = self.cases_config.repo_name_pattern.strip()
        if not pattern:
            raise ValueError(
                "cases_config.json debe definir lakefs_conventions.repo_name_pattern"
            )

        escaped = re.escape(pattern)
        escaped = escaped.replace(
            r"\{dataset\}", r"(?P<dataset>[A-Za-z0-9][A-Za-z0-9._-]*)"
        )
        token_pattern = r"[A-Za-z0-9][A-Za-z0-9._-]*"
        escaped = escaped.replace(r"\{case\}", token_pattern)
        escaped = escaped.replace(r"\{case_id\}", token_pattern)
        regex = re.compile(f"^{escaped}$")

        match = regex.fullmatch(str(repository).strip())
        if not match:
            raise ValueError(
                f"No se pudo extraer dataset desde repository '{repository}'"
            )

        dataset = match.group("dataset").strip()
        if not dataset:
            raise ValueError(
                f"No se pudo extraer dataset desde repository '{repository}'"
            )
        return dataset

    def build_tag(
        self, dataset: str, version: int | str, case_id: str | None = None
    ) -> str:
        """Construye un tag desde `tag_pattern` de `CASES_CONFIG`.

        Soporta plantillas que incluyan `{dataset}`, `{version}` y opcionalmente
        `{case}`.
        """
        pattern = self.cases_config.tag_pattern
        resolved_case = (
            str(case_id).strip().upper()
            if case_id is not None
            else self.cases_config.case_for_dataset(dataset)
        )
        return pattern.format(
            dataset=dataset,
            version=version,
            case=resolved_case.lower(),
        )

    def commit_bronze(
        self,
        files: str | Path | list[str | Path] | tuple[str | Path, ...],
        repository: str | None = None,
        *,
        dataset: str | None = None,
        case_id: str | None = None,
        branch: str | None = None,
        message: str | None = None,
    ) -> str:
        """Sube ficheros a la ruta Bronze configurada y crea commit Medallion.

        Args:
            files: Fichero local único o colección de ficheros locales.
            repository: Repositorio lakeFS. Si no se informa, se resuelve desde
                `dataset` + `case_id`.
            dataset: Dataset para resolver repositorio y metadata de commit.
            case_id: Identificador de caso para resolver repositorio si aplica.
            branch: Rama destino. Si no se informa, crea/usa una nueva rama
                transform con `new_transform_branch`.
            message: Mensaje de commit opcional.

        Returns:
            Identificador del commit creado.
        """
        if repository is None:
            if dataset is None:
                raise ValueError(
                    "Debes informar `repository` o bien `dataset` para resolverlo."
                )
            repository = self.resolve_repository_name(dataset=dataset, case_id=case_id)
        elif dataset is None:
            dataset = self._dataset_from_repository_name(repository)

        branch_name = branch or self.new_transform_branch(
            repository=repository,
            dataset=dataset,
            case_id=case_id,
        )
        bronze_base_path = self.resolve_bronze_path()
        local_files = self._normalize_local_files(files)

        if not hasattr(self.client, "objects_api"):
            raise RuntimeError("El cliente lakeFS no expone objects_api")
        if not hasattr(self.client, "commits_api"):
            raise RuntimeError("El cliente lakeFS no expone commits_api")

        uploaded_paths: list[str] = []
        for local_file in local_files:
            lakefs_path = str(PurePosixPath(bronze_base_path) / local_file.name)
            with local_file.open("rb") as file_obj:
                self.client.objects_api.upload_object(
                    repository=repository,
                    branch=branch_name,
                    path=lakefs_path,
                    content=file_obj,
                )
            uploaded_paths.append(lakefs_path)

        commit_message = message or "add bronze datasets"
        commit_metadata = {
            "layer": "bronze",
            "files_count": str(len(uploaded_paths)),
            "paths": ",".join(uploaded_paths),
        }
        if dataset:
            commit_metadata["dataset"] = dataset
        if case_id:
            commit_metadata["case"] = str(case_id).strip().upper()

        commit = self.client.commits_api.commit(
            repository=repository,
            branch=branch_name,
            commit_creation=lakefs_sdk.CommitCreation(
                message=commit_message,
                metadata=commit_metadata,
                allow_empty=False,
            ),
        )
        return str(getattr(commit, "id", "unknown"))

    def resolve_bronze_path(self) -> str:
        """Resuelve la ruta base de Bronze desde `repository_schema` en config."""
        if not hasattr(self.cases_config, "as_dict"):
            raise ValueError(
                "No se puede resolver ruta Bronze: `cases_config` no expone as_dict()."
            )

        cfg = self.cases_config.as_dict()
        repository_schema = cfg.get("repository_schema")
        if not isinstance(repository_schema, dict):
            raise ValueError("cases_config.json: falta nodo repository_schema")

        bronze_node = repository_schema.get("bronze")
        if not isinstance(bronze_node, dict):
            layers = repository_schema.get("layers")
            if not isinstance(layers, dict):
                raise ValueError("cases_config.json: falta repository_schema.layers")
            bronze_node = layers.get("bronze")
            if not isinstance(bronze_node, dict):
                raise ValueError(
                    "cases_config.json: falta repository_schema.layers.bronze"
                )

        bronze_path = bronze_node.get("path")
        if not isinstance(bronze_path, str) or not bronze_path.strip():
            raise ValueError("cases_config.json: falta repository_schema.bronze.path")

        normalized = bronze_path.strip().strip("/")
        if not normalized:
            raise ValueError("cases_config.json: ruta Bronze inválida")
        return normalized

    @staticmethod
    def _normalize_local_files(
        files: str | Path | list[str | Path] | tuple[str | Path, ...]
    ) -> list[Path]:
        """Normaliza entradas de ficheros locales y valida existencia."""
        if isinstance(files, (str, Path)):
            items = [files]
        else:
            items = list(files)

        paths: list[Path] = []
        for item in items:
            path = Path(item)
            if not path.exists() or not path.is_file():
                raise FileNotFoundError(f"No existe fichero local: {path}")
            paths.append(path)

        if not paths:
            raise ValueError("Debes informar al menos un fichero para capa bronze.")
        return paths

    @staticmethod
    def _normalize_object_bytes(response: Any) -> bytes:
        """Normaliza respuestas de lakeFS a bytes crudos."""
        if hasattr(response, "read"):
            content = response.read()
        elif isinstance(response, (bytes, bytearray, memoryview)):
            content = bytes(response)
        elif hasattr(response, "data"):
            content = response.data
        else:
            raise TypeError(
                "Respuesta lakeFS inválida: se esperaba read(), data o bytes crudos"
            )

        if isinstance(content, (bytearray, memoryview)):
            return bytes(content)
        if isinstance(content, bytes):
            return content
        raise TypeError(
            "Contenido lakeFS inválido: se esperaba bytes/bytearray/memoryview"
        )

    def read_object_bytes(self, repository: str, ref: str, path: str) -> bytes:
        """Lee un objeto lakeFS y devuelve su contenido binario."""
        response = self.client.objects_api.get_object(
            repository=repository,
            ref=ref,
            path=path,
        )
        return self._normalize_object_bytes(response)

    def read_parquet(self, repository: str, ref: str, path: str) -> pd.DataFrame:
        """Lee un parquet desde lakeFS y devuelve DataFrame."""
        content = self.read_object_bytes(repository=repository, ref=ref, path=path)
        return pd.read_parquet(BytesIO(content))

    def resolve_gold_paths(self) -> dict[str, str]:
        """Obtiene rutas Gold (`train`/`test`) desde `CASES_CONFIG`."""
        return self.cases_config.resolve_gold_paths()

    def download_gold_data(
        self, repository: str, ref: str
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Descarga `train` y `test` de Gold para un repo/ref concretos."""
        gold_paths = self.resolve_gold_paths()
        train_df = self.read_parquet(
            repository=repository,
            ref=ref,
            path=gold_paths["train"],
        )
        test_df = self.read_parquet(
            repository=repository,
            ref=ref,
            path=gold_paths["test"],
        )
        return train_df, test_df
