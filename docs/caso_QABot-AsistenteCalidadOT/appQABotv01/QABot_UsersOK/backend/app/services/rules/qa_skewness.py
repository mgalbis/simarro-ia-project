def check_skewness(df, target_column=None):

    if target_column is None:

        numerical_cols = df.select_dtypes(
            include=["int64", "float64"]
        ).columns.tolist()

        if not numerical_cols:
            return {
                "rule": "QA-SKEWNESS",
                "status": "WARN",
                "metrics": {},
                "warnings": [
                    {
                        "issue": "No se encontró ninguna columna numérica para evaluar asimetria"
                    }
                ],
                "recommendations": [
                    "Especificar una columna objetivo numérica"
                ]
            }

        target_column = numerical_cols[0]

    # Skewness
    skewness = df[target_column].skew()

    # Reglas simples
    if abs(skewness) > 1:
        status = "FAIL"

    elif abs(skewness) > 0.5:
        status = "WARN"

    else:
        status = "PASS"

    return {
        "rule": "QA-SKEWNESS",
        "status": status,
        "metrics": {
            "target_column": target_column,
            "skewness": round(skewness, 4)
        },
        "warnings": (
            [{
                "column": target_column,
                "issue": "Dataset con asimetria significativa"
            }]
            if status in ["WARN", "FAIL"] else []
        ),
        "recommendations": (
            ["Considerar transformaciones de datos para reducir la asimetria"]
            if status in ["WARN", "FAIL"] else []
        )
    }
