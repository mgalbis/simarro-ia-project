def check_duplicates(df):

    duplicated_count = df.duplicated().sum()

    duplicate_ratio = duplicated_count / len(df)

    if duplicate_ratio > 0.05:
        status = "FAIL"

    elif duplicated_count > 0:
        status = "WARN"

    else:
        status = "PASS"

    return {
        "rule": "QA-DUPLICATES",
        "status": status,
        "duplicated_count": int(duplicated_count),
        "duplicate_ratio": round(duplicate_ratio, 4)
    }