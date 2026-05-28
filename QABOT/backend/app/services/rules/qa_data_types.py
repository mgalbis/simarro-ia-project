def check_data_types(df):

    mismatches = []

    for col, dtype in df.dtypes.items():

        if dtype == "object":
            mismatches.append({
                "column": col,
                "dtype": str(dtype)
            })

    if mismatches:
        status = "WARN"
    else:
        status = "PASS"

    return {
        "rule": "QA-DATATYPES",
        "status": status,
        "mismatches": mismatches,
        "metrics": {
            "object_columns_ratio": round(len(mismatches) / len(df.columns), 4)
        },
        "recommendations": (
            ["Revisar columnas en formato object (posibles strings sucios)"]
            if mismatches else []
        )
    }