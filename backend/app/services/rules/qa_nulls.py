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

    return {
        "rule": "QA-NULLS",
        "status": status,
        "critical": critical,
        "warnings": warnings,
        "metrics": {
            "global_null_ratio": round(global_null_ratio, 4),
            "null_ratio_by_column": missing_ratio.to_dict()
        },
        "recommendations": (
            ["Tratar valores nulos en columnas críticas"]
            if critical else []
        )
    }