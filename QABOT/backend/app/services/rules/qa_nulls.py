def check_nulls(df):
    missing_ratio = (
        df.isnull()
        .mean()
        .sort_values(ascending=False)
    )

    critical = []
    warnings = []

    for col, ratio in missing_ratio.items():
        if ratio > 0.05:
            critical.append({
                "column": col,
                "null_ratio": round(ratio, 4)
            })
        elif ratio > 0:
            warnings.append({
                "column": col,
                "null_ratio": round(ratio, 4)
            })

    if critical:
        status = "FAIL"
    elif warnings:
        status = "WARN"
    else:
        status = "PASS"

    global_null_ratio = float(missing_ratio.mean()) if len(missing_ratio) > 0 else 0.0

    affected_columns = [item["column"] for item in critical + warnings]
    evidence_rows = []

    if affected_columns:
        null_mask = df[affected_columns].isnull().any(axis=1)
        evidence_df = df.loc[null_mask].head(20).copy()
        evidence_df.insert(0, "__row_number__", evidence_df.index + 1)

        for _, row in evidence_df.iterrows():
            null_columns = [
                col for col in affected_columns
                if col in df.columns and row[col] != row[col]
            ]

            evidence_rows.append({
                "__row_number__": int(row["__row_number__"]),
                "null_columns": null_columns,
                "row": {
                    key: (None if value != value else value)
                    for key, value in row.drop(labels=["__row_number__"]).to_dict().items()
                }
            })

    return {
        "rule": "QA-NULLS",
        "status": status,
        "critical": critical,
        "warnings": warnings,
        "metrics": {
            "global_null_ratio": round(global_null_ratio, 4),
            "null_ratio_by_column": missing_ratio.to_dict()
        },
        "evidence": {
            "description": "Primeras filas que contienen valores nulos en columnas críticas o con aviso.",
            "max_rows": 20,
            "rows": evidence_rows,
        },
        "recommendations": (
            ["Tratar valores nulos en columnas críticas."]
            if critical else []
        )
    }