def check_duplicates(df):

    duplicated_count = df.duplicated().sum()

    duplicated_percentage = (
        duplicated_count / len(df)
    ) * 100

    # Estado según cantidad
    if duplicated_percentage > 5:
        status = "FAIL"

    elif duplicated_count > 0:
        status = "WARN"

    else:
        status = "PASS"

    return {
        "rule": "QA-DUPLICATES",
        "status": status,
        "duplicated_count": int(duplicated_count),
        "duplicated_percentage": round(
            duplicated_percentage,
            2
        )
    }