"""Regla QA para validar balance de clases en una variable objetivo."""


def check_balance(df, target_column=None):
    """Evalúa el balance de clases y devuelve estado, métricas y recomendaciones."""
    if target_column is None:

        categorical_cols = df.select_dtypes(
            include=["object", "category"]
        ).columns.tolist()

        if not categorical_cols:
            return {
                "rule": "QA-BALANCE",
                "status": "WARN",
                "metrics": {},
                "warnings": [
                    {
                        "issue": "No se encontró ninguna columna categórica para evaluar balanceo"
                    }
                ],
                "recommendations": ["Especificar una columna objetivo categórica"],
            }

        target_column = categorical_cols[0]

    # Distribución
    distribution = df[target_column].value_counts(normalize=True).to_dict()

    max_ratio = max(distribution.values())
    min_ratio = min(distribution.values())

    imbalance_ratio = max_ratio - min_ratio

    # Reglas simples
    if max_ratio > 0.90:
        status = "FAIL"

    elif max_ratio > 0.75:
        status = "WARN"

    else:
        status = "PASS"

    return {
        "rule": "QA-BALANCE",
        "status": status,
        "metrics": {
            "target_column": target_column,
            "imbalance_ratio": round(imbalance_ratio, 4),
            "class_distribution": distribution,
            "majority_class_ratio": round(max_ratio, 4),
        },
        "warnings": (
            [{"column": target_column, "issue": "Dataset desbalanceado"}]
            if status in ["WARN", "FAIL"]
            else []
        ),
        "recommendations": (
            ["Aplicar técnicas de balanceo como oversampling o undersampling"]
            if status in ["WARN", "FAIL"]
            else []
        ),
    }
