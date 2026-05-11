def check_nulls(df):

    missing = (
        df.isnull()
        .mean()
        .sort_values(ascending=False) * 100
    )

    critical = []
    warnings = []

    for col, percentage in missing.items():

        if percentage > 5:
            critical.append({
                "column": col,
                "null_percentage": round(percentage, 2)
            })

        elif percentage > 0:
            warnings.append({
                "column": col,
                "null_percentage": round(percentage, 2)
            })

    if critical:
        status = "FAIL"

    elif warnings:
        status = "WARN"

    else:
        status = "PASS"

    return {
        "rule": "QA-NULLS",
        "status": status,
        "critical": critical,
        "warnings": warnings
    }