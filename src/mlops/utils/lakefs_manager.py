"""Gestión de operaciones lakeFS apoyadas en convenciones de `CASES_CONFIG`."""

from __future__ import annotations

import os
from io import BytesIO
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
