import io
from datetime import datetime
from typing import Any, Dict, List

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


STATUS_COLORS = {
    "PASS": colors.HexColor("#2E7D32"),
    "WARN": colors.HexColor("#F9A825"),
    "WARNING": colors.HexColor("#F9A825"),
    "FAIL": colors.HexColor("#C62828"),
    "ERROR": colors.HexColor("#C62828"),
}


TEST_LABELS = {
    "nulls": "Nulos",
    "duplicates": "Duplicados",
    "data_types": "Tipos de dato",
    "outliers": "Outliers",
    "balance": "Balanceo",
    "model_performance": "Evaluacion de modelo",
    "dataset_split": "Validacion de particiones",
}


def build_pdf_report(report: Dict[str, Any]) -> bytes:
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=1.2 * cm,
        leftMargin=1.2 * cm,
        topMargin=1.0 * cm,
        bottomMargin=1.0 * cm,
    )

    styles = _build_styles()
    elements = []

    _add_cover(elements, styles, report)
    _add_summary(elements, styles, report)
    _add_test_plan(elements, styles, report)
    _add_results(elements, styles, report)
    _add_comparison(elements, styles, report)
    _add_footer_note(elements, styles)

    doc.build(elements)

    pdf = buffer.getvalue()
    buffer.close()

    return pdf


def _build_styles():
    base = getSampleStyleSheet()

    return {
        "title": ParagraphStyle(
            "title",
            parent=base["Title"],
            fontSize=22,
            leading=26,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#1F2937"),
            spaceAfter=12,
        ),
        "subtitle": ParagraphStyle(
            "subtitle",
            parent=base["Normal"],
            fontSize=11,
            leading=15,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#4B5563"),
            spaceAfter=16,
        ),
        "h1": ParagraphStyle(
            "h1",
            parent=base["Heading1"],
            fontSize=15,
            leading=18,
            textColor=colors.HexColor("#111827"),
            spaceBefore=10,
            spaceAfter=8,
        ),
        "h2": ParagraphStyle(
            "h2",
            parent=base["Heading2"],
            fontSize=12,
            leading=15,
            textColor=colors.HexColor("#374151"),
            spaceBefore=8,
            spaceAfter=6,
        ),
        "normal": ParagraphStyle(
            "normal",
            parent=base["Normal"],
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#111827"),
        ),
        "small": ParagraphStyle(
            "small",
            parent=base["Normal"],
            fontSize=7,
            leading=9,
            textColor=colors.HexColor("#374151"),
        ),
        "muted": ParagraphStyle(
            "muted",
            parent=base["Normal"],
            fontSize=7,
            leading=9,
            textColor=colors.HexColor("#6B7280"),
        ),
    }


def _add_cover(elements, styles, report):
    elements.append(Paragraph("Informe de revision QA - QABot", styles["title"]))

    elements.append(
        Paragraph(
            "Revision de calidad de artefactos del ciclo del dato. "
            "El informe recoge defectos, evidencias y recomendaciones para el siguiente ciclo.",
            styles["subtitle"],
        )
    )

    summary_data = [
        ["ID de ejecucion", report.get("execution_id", "N/A")],
        ["Actividad QA", report.get("activity_type", "N/A")],
        ["Resultado global", report.get("global_status", "N/A")],
        ["Fecha de informe", datetime.now().strftime("%d/%m/%Y %H:%M")],
        ["Modo de trabajo", "Revision QA sin correccion automatica"],
    ]

    elements.append(_table(summary_data, [5 * cm, 16 * cm]))
    elements.append(Spacer(1, 0.4 * cm))


def _add_summary(elements, styles, report):
    elements.append(Paragraph("1. Resumen ejecutivo", styles["h1"]))

    assessment = report.get("assessment_result", {})
    summary = assessment.get("summary", {})

    data = [
        ["Indicador", "Valor"],
        ["Resultado global", report.get("global_status", "N/A")],
        ["Pruebas planificadas", summary.get("planned_checks", "N/A")],
        ["Pruebas ejecutadas", summary.get("executed_checks", "N/A")],
        ["Pruebas superadas", summary.get("passed_checks", "N/A")],
        ["Pruebas fallidas", summary.get("failed_checks", "N/A")],
        ["Advertencias", summary.get("warnings", "N/A")],
        ["Errores", summary.get("errors", "N/A")],
    ]

    elements.append(_table(data, [7 * cm, 8 * cm]))
    elements.append(Spacer(1, 0.25 * cm))

    overall = summary.get("overall_result")
    if overall:
        elements.append(Paragraph(f"<b>Resultado:</b> {overall}", styles["normal"]))
        elements.append(Spacer(1, 0.25 * cm))


def _add_test_plan(elements, styles, report):
    assessment = report.get("assessment_result", {})
    test_plan = assessment.get("test_plan") or {}

    if not test_plan:
        return

    elements.append(Paragraph("2. Plan de pruebas", styles["h1"]))

    rows = [["ID", "Prueba", "Severidad", "Descripcion"]]

    for test in test_plan.get("tests", []):
        rows.append(
            [
                test.get("test_id", ""),
                test.get("name", ""),
                _enum_value(test.get("severity", "")),
                test.get("description", ""),
            ]
        )

    elements.append(_table(rows, [3 * cm, 6 * cm, 3 * cm, 14 * cm]))
    elements.append(Spacer(1, 0.25 * cm))


def _add_results(elements, styles, report):
    elements.append(Paragraph("3. Resultados y evidencias", styles["h1"]))

    for result in report.get("results", []):
        name = result.get("name", "")
        label = TEST_LABELS.get(name, name)
        status = result.get("status", "N/A")
        summary = result.get("summary", "")

        elements.append(Paragraph(label, styles["h2"]))

        header = [
            ["Estado", status, "Resumen", summary],
        ]
        elements.append(_table(header, [2.3 * cm, 3 * cm, 2.5 * cm, 18 * cm]))
        elements.append(Spacer(1, 0.15 * cm))

        metrics = result.get("metrics", {})
        inner = metrics.get("metrics", metrics)

        _add_metric_block(elements, styles, name, metrics, inner)
        _add_evidence_block(elements, styles, name, metrics)
        _add_recommendations(elements, styles, result)

        elements.append(Spacer(1, 0.25 * cm))


def _add_metric_block(elements, styles, name, metrics, inner):
    if name == "nulls":
        rows = [["Columna", "Ratio nulos", "Nivel"]]

        for item in metrics.get("critical", []):
            rows.append([item.get("column", ""), _pct(item.get("null_ratio", 0)), "Critico"])

        for item in metrics.get("warnings", []):
            rows.append([item.get("column", ""), _pct(item.get("null_ratio", 0)), "Aviso"])

        if len(rows) > 1:
            elements.append(Paragraph("Metricas principales", styles["small"]))
            elements.append(_table(rows, [7 * cm, 4 * cm, 4 * cm]))

    elif name == "duplicates":
        rows = [
            ["Duplicados", metrics.get("duplicated_count", 0)],
            ["Ratio duplicados", _pct(metrics.get("duplicate_ratio", 0))],
        ]
        elements.append(_table(rows, [6 * cm, 5 * cm]))

    elif name == "outliers":
        ratios = inner.get("outlier_ratio_by_column", {})
        rows = [["Columna", "Ratio outliers"]]

        for col, ratio in ratios.items():
            rows.append([col, _pct(ratio)])

        if len(rows) > 1:
            elements.append(_table(rows, [8 * cm, 5 * cm]))

    elif name == "balance":
        rows = [["Clase", "Porcentaje"]]

        for cls, ratio in inner.get("class_distribution", {}).items():
            rows.append([str(cls), _pct(ratio)])

        if len(rows) > 1:
            elements.append(_table(rows, [8 * cm, 5 * cm]))

    elif name == "model_performance":
        rows = [
            ["Accuracy", inner.get("accuracy", "N/A")],
            ["Precision", inner.get("precision", "N/A")],
            ["Recall", inner.get("recall", "N/A")],
            ["F1", inner.get("f1", "N/A")],
            ["ROC AUC", inner.get("roc_auc", "N/A")],
            ["Matriz confusion", str(inner.get("confusion_matrix", {}))],
        ]
        elements.append(_table(rows, [6 * cm, 8 * cm]))

    elif name == "dataset_split":
        rows = [
            ["Columna particion", inner.get("split_column", "N/A")],
            ["Conteo por particion", str(inner.get("split_counts", {}))],
            ["Ratio por particion", str(inner.get("split_ratios", {}))],
            ["Particiones ausentes", str(inner.get("missing_splits", []))],
            ["Particiones desconocidas", str(inner.get("unknown_splits", []))],
            ["IDs repetidos entre particiones", str(inner.get("duplicate_ids_across_splits", None))],
        ]
        elements.append(_table(rows, [7 * cm, 16 * cm]))


def _add_evidence_block(elements, styles, name, metrics):
    evidence = metrics.get("evidence") or {}
    rows = evidence.get("rows") or []

    if not rows:
        return

    elements.append(Paragraph("Evidencias detectadas", styles["small"]))
    elements.append(Paragraph(evidence.get("description", ""), styles["muted"]))

    if name == "nulls":
        table_rows = [["Fila", "Columnas con nulo", "Valores de la fila"]]
        for row in rows:
            table_rows.append(
                [
                    row.get("__row_number__", ""),
                    ", ".join(row.get("null_columns", [])),
                    _short_dict(row.get("row", {}), max_chars=160),
                ]
            )
        elements.append(_table(table_rows, [2 * cm, 7 * cm, 17 * cm]))

    elif name in {"duplicates", "model_performance", "dataset_split"}:
        elements.append(_dict_rows_table(rows, max_columns=8))

    elif name == "outliers":
        table_rows = [["Fila", "Columna", "Valor", "Limite inf.", "Limite sup."]]

        for row in rows:
            table_rows.append(
                [
                    row.get("__row_number__", ""),
                    row.get("column", ""),
                    row.get("value", ""),
                    row.get("lower_bound", ""),
                    row.get("upper_bound", ""),
                ]
            )

        elements.append(_table(table_rows, [2 * cm, 6 * cm, 4 * cm, 5 * cm, 5 * cm]))


def _add_recommendations(elements, styles, result):
    recommendations = result.get("recommendations", [])

    if not recommendations:
        return

    elements.append(Paragraph("Recomendaciones para el siguiente ciclo", styles["small"]))

    rows = [["#", "Recomendacion"]]
    for index, rec in enumerate(recommendations, start=1):
        rows.append([index, rec])

    elements.append(_table(rows, [1.5 * cm, 22 * cm]))


def _add_comparison(elements, styles, report):
    comparison = report.get("comparison_vs_previous")

    if not comparison:
        return

    elements.append(Paragraph("4. Comparacion con revision anterior", styles["h1"]))

    if not comparison.get("comparable"):
        elements.append(
            Paragraph(
                comparison.get("reason", "La comparación no es aplicable."),
                styles["normal"],
            )
        )
        return

    elements.append(
        Paragraph(
            comparison.get("interpretation", "Comparación generada."),
            styles["normal"],
        )
    )
    elements.append(Spacer(1, 0.2 * cm))

    transitions = comparison.get("test_transitions", {})
    rows = [["Tipo", "Prueba", "Estado anterior", "Estado actual"]]

    for label, key in [
        ("Defecto corregido", "fixed"),
        ("Nuevo defecto", "new_failures"),
        ("Defecto persistente", "persistent_failures"),
        ("Advertencia persistente", "persistent_warnings"),
    ]:
        for item in transitions.get(key, []):
            rows.append(
                [
                    label,
                    item.get("test_name", ""),
                    item.get("previous_status", ""),
                    item.get("current_status", ""),
                ]
            )

    if len(rows) > 1:
        elements.append(_table(rows, [5 * cm, 7 * cm, 5 * cm, 5 * cm]))
    else:
        elements.append(
            Paragraph(
                "No hay transiciones relevantes entre ambas revisiones.",
                styles["normal"],
            )
        )


def _add_footer_note(elements, styles):
    elements.append(Spacer(1, 0.4 * cm))
    elements.append(
        Paragraph(
            "<b>Nota QA:</b> este informe documenta defectos, advertencias y evidencias. "
            "El sistema no aplica correcciones sobre los artefactos evaluados; los ajustes corresponden "
            "al equipo responsable en un nuevo ciclo de desarrollo.",
            styles["muted"],
        )
    )


def _table(data: List[List[Any]], col_widths: List[float]) -> Table:
    wrapped = []
    for row in data:
        wrapped.append([_cell(value) for value in row])

    table = Table(wrapped, colWidths=col_widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E5E7EB")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#111827")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#D1D5DB")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONTSIZE", (0, 0), (-1, -1), 7),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FAFAFA")]),
            ]
        )
    )

    return table


def _dict_rows_table(rows: List[Dict[str, Any]], max_columns: int = 8) -> Table:
    if not rows:
        return _table([["Sin evidencias"]], [10 * cm])

    keys = list(rows[0].keys())[:max_columns]
    table_rows = [keys]

    for row in rows[:20]:
        table_rows.append([row.get(key, "") for key in keys])

    width = 26 * cm / max(1, len(keys))

    return _table(table_rows, [width] * len(keys))


def _cell(value: Any) -> Paragraph:
    text = "" if value is None else str(value)
    text = (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )

    return Paragraph(text, ParagraphStyle("cell", fontSize=7, leading=8))


def _pct(value: Any) -> str:
    try:
        return f"{float(value) * 100:.2f}%"
    except Exception:
        return "N/A"


def _short_dict(value: Dict[str, Any], max_chars: int = 120) -> str:
    text = str(value)
    return text if len(text) <= max_chars else text[:max_chars] + "..."


def _enum_value(value: Any) -> str:
    text = str(value)
    return text.split(".")[-1].lower() if "." in text else text