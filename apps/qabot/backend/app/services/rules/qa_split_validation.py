"""Regla QA para validar consistencia de particiones train/validation/test."""

from typing import Any, Dict

import pandas as pd

VALIDATION_ALIASES = {"validation", "valid", "val"}


def _normalise_split(value: Any) -> str:
    value = str(value).strip().lower()

    if value in VALIDATION_ALIASES:
        return "validation"

    return value


def _safe_ratio(part: float, total: float) -> float:
    return 0.0 if total == 0 else part / total


def _distribution(series: pd.Series) -> Dict[str, float]:
    total = len(series)

    if total == 0:
        return {}

    counts = series.value_counts(dropna=False)

    return {str(k): round(float(v) / total, 4) for k, v in counts.items()}


def _max_abs_distribution_delta(
    reference: Dict[str, float], candidate: Dict[str, float]
) -> float:
    keys = set(reference) | set(candidate)

    if not keys:
        return 0.0

    return max(abs(reference.get(k, 0.0) - candidate.get(k, 0.0)) for k in keys)


def check_dataset_split(
    df: pd.DataFrame,
    split_column: str | None = None,
    target_column: str | None = None,
    id_column: str | None = None,
):
    """Valida particiones de dataset y detecta riesgos de fuga o sesgo."""
    if split_column is None:
        return {
            "rule": "QA-SPLIT-VALIDATION",
            "status": "ERROR",
            "metrics": {},
            "warnings": [{"issue": "Missing split column."}],
            "recommendations": [
                "Indicar la columna que identifica la partición. Ejemplo: split es conjunto."
            ],
        }

    if split_column not in df.columns:
        return {
            "rule": "QA-SPLIT-VALIDATION",
            "status": "ERROR",
            "metrics": {"available_columns": list(df.columns)},
            "warnings": [{"issue": f"Column not found: {split_column}"}],
            "recommendations": [
                "Revisar el nombre de la columna de partición proporcionada."
            ],
        }

    normalised_split = df[split_column].map(_normalise_split)

    split_counts = normalised_split.value_counts(dropna=False).to_dict()
    split_ratios = {
        str(k): round(_safe_ratio(float(v), len(df)), 4)
        for k, v in split_counts.items()
    }

    present_splits = {str(k) for k in split_counts.keys()}
    expected_splits = {"train", "validation", "test"}

    missing_splits = sorted(expected_splits - present_splits)
    unknown_splits = sorted(present_splits - expected_splits)

    warnings = []
    recommendations = []
    status = "PASS"

    if missing_splits:
        status = "FAIL"
        warnings.append(
            {
                "issue": "Missing expected split partitions.",
                "missing_splits": missing_splits,
            }
        )
        recommendations.append(
            "Revisar en una iteración posterior la estrategia de particionado para asegurar train, validation y test."
        )

    if unknown_splits:
        status = "WARN" if status == "PASS" else status
        warnings.append(
            {
                "issue": "Unexpected split labels detected.",
                "unknown_splits": unknown_splits,
            }
        )
        recommendations.append(
            "Normalizar los valores de la columna de partición para evitar interpretaciones ambiguas."
        )

    if split_ratios.get("test", 0) < 0.05:
        status = "WARN" if status == "PASS" else status
        warnings.append(
            {"issue": "Test partition ratio is below diagnostic reference 5%."}
        )
        recommendations.append(
            "Revisar en una iteración posterior si el conjunto de test tiene tamaño suficiente para una evaluación fiable."
        )

    if "validation" in expected_splits and split_ratios.get("validation", 0) < 0.05:
        status = "WARN" if status == "PASS" else status
        warnings.append(
            {"issue": "Validation partition ratio is below diagnostic reference 5%."}
        )
        recommendations.append(
            "Revisar en una iteración posterior si el conjunto de validación tiene tamaño suficiente."
        )

    target_distribution = {}
    distribution_deltas = {}

    if target_column:
        if target_column not in df.columns:
            status = "ERROR"
            warnings.append({"issue": f"Target column not found: {target_column}"})
            recommendations.append(
                "Revisar el nombre de la variable objetivo proporcionada."
            )
        else:
            global_distribution = _distribution(df[target_column])
            target_distribution["global"] = global_distribution

            for split in sorted(present_splits & expected_splits):
                split_distribution = _distribution(
                    df.loc[normalised_split == split, target_column]
                )
                target_distribution[split] = split_distribution
                distribution_deltas[split] = round(
                    _max_abs_distribution_delta(
                        global_distribution,
                        split_distribution,
                    ),
                    4,
                )

            max_delta = max(distribution_deltas.values(), default=0)

            if max_delta > 0.15:
                status = "WARN" if status == "PASS" else status
                warnings.append(
                    {
                        "issue": "Target distribution differs across partitions.",
                        "max_distribution_delta": max_delta,
                    }
                )
                recommendations.append(
                    "Revisar en una iteración posterior si la partición debería ser estratificada o si existe sesgo de muestreo."
                )

    duplicate_ids_across_splits = None

    if id_column:
        if id_column not in df.columns:
            status = "ERROR"
            warnings.append({"issue": f"ID column not found: {id_column}"})
            recommendations.append(
                "Revisar el nombre de la columna identificadora proporcionada."
            )
        else:
            id_split_counts = (
                df.assign(__split__=normalised_split)
                .groupby(id_column)["__split__"]
                .nunique()
            )
            duplicate_ids_across_splits = int((id_split_counts > 1).sum())

            if duplicate_ids_across_splits > 0:
                status = "FAIL"
                warnings.append(
                    {
                        "issue": "Same identifier appears in more than one partition.",
                        "duplicate_ids_across_splits": duplicate_ids_across_splits,
                    }
                )
                recommendations.append(
                    "Revisar en una iteración posterior la generación de particiones para evitar fuga de información entre conjuntos."
                )

    return {
        "rule": "QA-SPLIT-VALIDATION",
        "status": status,
        "metrics": {
            "split_column": split_column,
            "target_column": target_column,
            "id_column": id_column,
            "rows": int(len(df)),
            "split_counts": {str(k): int(v) for k, v in split_counts.items()},
            "split_ratios": split_ratios,
            "missing_splits": missing_splits,
            "unknown_splits": unknown_splits,
            "target_distribution": target_distribution,
            "target_distribution_deltas": distribution_deltas,
            "duplicate_ids_across_splits": duplicate_ids_across_splits,
        },
        "warnings": warnings,
        "recommendations": recommendations,
    }
