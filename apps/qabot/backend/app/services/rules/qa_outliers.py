"""Regla QA para identificar outliers con el método IQR."""

import numpy as np
import pandas as pd


def check_outliers_iqr(df):
    """Evalúa outliers en columnas numéricas y devuelve evidencias acotadas."""
    numeric_df = df.select_dtypes(include=[np.number])

    critical = []
    warnings = []
    outlier_ratios = []
    evidence_rows = []

    for col in numeric_df.columns:
        q1 = numeric_df[col].quantile(0.25)
        q3 = numeric_df[col].quantile(0.75)

        iqr = q3 - q1

        if iqr == 0 or pd.isna(iqr):
            continue

        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr

        outlier_mask = (numeric_df[col] < lower) | (numeric_df[col] > upper)
        outlier_ratio = outlier_mask.mean()

        outlier_ratios.append(outlier_ratio)

        if outlier_ratio > 0.10:
            critical.append({"column": col, "outlier_ratio": round(outlier_ratio, 4)})
        elif outlier_ratio > 0:
            warnings.append({"column": col, "outlier_ratio": round(outlier_ratio, 4)})

        if outlier_ratio > 0 and len(evidence_rows) < 20:
            for idx, value in numeric_df.loc[outlier_mask, col].head(20).items():
                if len(evidence_rows) >= 20:
                    break

                evidence_rows.append(
                    {
                        "__row_number__": int(idx + 1),
                        "column": col,
                        "value": float(value),
                        "lower_bound": round(float(lower), 4),
                        "upper_bound": round(float(upper), 4),
                    }
                )

    if critical:
        status = "FAIL"
    elif warnings:
        status = "WARN"
    else:
        status = "PASS"

    global_outlier_ratio = float(np.mean(outlier_ratios)) if outlier_ratios else 0.0

    return {
        "rule": "QA-OUTLIERS",
        "status": status,
        "critical": critical,
        "warnings": warnings,
        "metrics": {
            "global_outlier_ratio": round(global_outlier_ratio, 4),
            "outlier_ratio_by_column": {
                c["column"]: c["outlier_ratio"] for c in (critical + warnings)
            },
        },
        "evidence": {
            "description": "Primeros valores detectados como outliers mediante IQR.",
            "max_rows": 20,
            "rows": evidence_rows,
        },
        "recommendations": (
            ["Revisar outliers en variables numéricas."] if critical or warnings else []
        ),
    }
