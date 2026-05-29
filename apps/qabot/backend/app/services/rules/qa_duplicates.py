"""Regla QA para detectar registros duplicados en el dataset."""


def check_duplicates(df):
    """Calcula ratio de duplicados y devuelve evidencias de filas repetidas."""
    duplicated_mask = df.duplicated(keep=False)
    duplicated_rows = df.loc[duplicated_mask].copy()

    duplicated_count = int(df.duplicated().sum())
    duplicate_ratio = duplicated_count / len(df) if len(df) else 0

    if duplicate_ratio > 0.05:
        status = "FAIL"
    elif duplicated_count > 0:
        status = "WARN"
    else:
        status = "PASS"

    evidence_rows = []

    if not duplicated_rows.empty:
        evidence_df = duplicated_rows.head(20).copy()
        evidence_df.insert(0, "__row_number__", evidence_df.index + 1)
        evidence_rows = (
            evidence_df.astype(object)
            .where(evidence_df.notna(), None)
            .to_dict(orient="records")
        )

    return {
        "rule": "QA-DUPLICATES",
        "status": status,
        "duplicated_count": duplicated_count,
        "duplicate_ratio": round(duplicate_ratio, 4),
        "evidence": {
            "description": "Primeras filas implicadas en duplicados exactos.",
            "max_rows": 20,
            "rows": evidence_rows,
        },
        "recommendations": (
            [
                "Revisar las filas duplicadas antes de utilizar el dataset en fases posteriores."
            ]
            if duplicated_count > 0
            else []
        ),
    }
