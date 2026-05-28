"""Pruebas unitarias de `CasesConfig` contra el `cases_config.json` real."""

from __future__ import annotations

from pathlib import Path

import pytest

from mlops.config import CASES_CONFIG, get_cases_config
from mlops.config.cases_config_parser import CasesConfig


def _real_config_path() -> Path:
    """Resuelve la ruta real a `config/cases_config.json` del repositorio."""
    return Path(__file__).resolve().parents[4] / "config" / "cases_config.json"


def test_from_file_loads_real_cases_config():
    """Carga correctamente el `cases_config.json` real desde ruta explícita."""
    cfg = CasesConfig.from_file(_real_config_path())

    assert isinstance(cfg, CasesConfig)
    assert cfg.source_path == _real_config_path().resolve()


def test_default_path_points_to_real_config_file():
    """`default_path` debe apuntar a un fichero existente en este proyecto."""
    default = CasesConfig.default_path()

    assert default.name == "cases_config.json"
    assert default.exists()


def test_get_cases_config_returns_global_singleton():
    """`get_cases_config` devuelve la instancia global ya inicializada."""
    assert get_cases_config() is CASES_CONFIG


def test_as_dict_returns_deep_copy_on_real_config():
    """`as_dict` devuelve copia profunda y no modifica estado interno."""
    snapshot = CASES_CONFIG.as_dict()
    snapshot["project"] = "mutated-project-name"

    assert CASES_CONFIG.as_dict()["project"] != "mutated-project-name"


def test_lakefs_conventions_values_from_real_config():
    """Valida convenciones de lakeFS definidas en el fichero real."""
    assert CASES_CONFIG.default_branch == "main"
    assert CASES_CONFIG.tag_pattern == "{dataset}_v{version}"
    assert CASES_CONFIG.repo_name_pattern == "caso{case}--{dataset}"


def test_case_for_dataset_returns_expected_real_mappings():
    """Resuelve correctamente el `case` para varios datasets reales."""
    assert CASES_CONFIG.case_for_dataset("uci-appliances") == "B"
    assert CASES_CONFIG.case_for_dataset("bdg2") == "B"
    assert CASES_CONFIG.case_for_dataset("lbnl-fdd") == "C"
    assert CASES_CONFIG.case_for_dataset("uci-occupancy") == "D"
    assert CASES_CONFIG.case_for_dataset("ingauge") == "D"
    assert CASES_CONFIG.case_for_dataset("era5") == "E"


def test_case_for_dataset_raises_for_unknown_dataset():
    """Lanza `KeyError` para datasets inexistentes."""
    with pytest.raises(KeyError):
        CASES_CONFIG.case_for_dataset("dataset-que-no-existe")


def test_resolve_gold_paths_matches_real_repository_schema():
    """Resuelve rutas Gold reales de train/test desde el esquema del repo."""
    assert CASES_CONFIG.resolve_gold_paths() == {
        "train": "gold/train.parquet",
        "test": "gold/test.parquet",
    }


def test_resolve_feature_columns_matches_real_column_mappings():
    """Devuelve features reales para datasets con target configurado."""
    assert CASES_CONFIG.resolve_feature_columns("uci-occupancy") == [
        "Temperature",
        "Humidity",
        "Light",
        "CO2",
        "HumidityRatio",
    ]
    assert CASES_CONFIG.resolve_feature_columns("uci-appliances") == [
        "lights",
        "T_out",
        "T1",
    ]


def test_resolve_target_column_matches_real_column_mappings():
    """Devuelve target real para datasets que sí definen `role=target`."""
    assert CASES_CONFIG.resolve_target_column("uci-occupancy") == "Occupancy"
    assert CASES_CONFIG.resolve_target_column("uci-appliances") == "Appliances"


def test_resolve_target_column_raises_for_dataset_without_target():
    """En el real config, `era5` no define target y debe lanzar error."""
    with pytest.raises(ValueError) as exc:
        CASES_CONFIG.resolve_target_column("era5")

    assert "role='target'" in str(exc.value)


def test_resolve_experiment_name_renders_expected_real_names():
    """Renderiza nombres de experimento reales según patrón MLflow."""
    assert (
        CASES_CONFIG.resolve_experiment_name("B")
        == "CasoB_Prediccion_consumo_electrico"
    )
    assert CASES_CONFIG.resolve_experiment_name("C") == "CasoC_Deteccion_anomalias_HVAC"
    assert (
        CASES_CONFIG.resolve_experiment_name("D")
        == "CasoD_Prediccion_ocupacion_espacios"
    )
    assert CASES_CONFIG.resolve_experiment_name("E") == "CasoE_Meteorologia_integracion"


def test_resolve_experiment_name_normalizes_case_id_input():
    """Normaliza espacios y mayúsculas del `case_id` antes de resolver."""
    assert (
        CASES_CONFIG.resolve_experiment_name("  b ")
        == "CasoB_Prediccion_consumo_electrico"
    )


def test_resolve_experiment_name_raises_for_unknown_case():
    """Lanza `KeyError` cuando el caso solicitado no existe en config real."""
    with pytest.raises(KeyError):
        CASES_CONFIG.resolve_experiment_name("Z")
