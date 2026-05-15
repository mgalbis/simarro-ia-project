from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import StreamingResponse
import io
import pandas as pd
from io import StringIO
from typing import Optional
import uuid
from app.services.qa_agent import QAAgent

router = APIRouter()
# Instanciamos el agente fuera para que mantenga su configuración
agent = QAAgent()

last_report_cache: dict = {}

@router.post("/chat")
async def chat(
    user_message: str = Form(...),
    file: Optional[UploadFile] = File(None)
):
    global last_report_cache
    df = None

    if file:
        content = await file.read()
        try:
            df = pd.read_csv(StringIO(content.decode("utf-8")))
        except Exception as e:
            return {"assistant_message": f"Error al leer el archivo: {str(e)}", "report": None}

    perception = agent.perceive(df, user_message)
    intent = perception.get("intent", {})
    is_download_request = intent.get("intent") == "download_report"

    if is_download_request:
        if not last_report_cache:
            return {
                "assistant_message": "Todavía no hay ningún análisis realizado. Carga un CSV y ejecuta una validación primero.",
                "hasReport": False,
                "report": None,
                "execution_id": None
            }
        cached_id = last_report_cache.get("execution_id")
        return {
            "assistant_message": "Aquí tienes el informe del último análisis.",
            "hasReport": True,
            "report": last_report_cache,
            "execution_id": cached_id,
            "addToHistory": False
        }

    execution_id = f"EXEC-{uuid.uuid4().hex[:6].upper()}"
    decision_data = agent.decide(perception)
    response = agent.act(decision_data, execution_id)

    if response.get("report"):
        last_report_cache = response["report"]

    return response

@router.get("/download/{execution_id}")
async def download_report(execution_id: str):

    if not last_report_cache or last_report_cache.get("execution_id") != execution_id:
        return {"error": "Reporte no encontrado. Asegúrate de haber ejecutado un análisis primero."}

    report = last_report_cache
    lines = []

    lines.append("=" * 60)
    lines.append("        INFORME DE CALIDAD DE DATOS — QABot")
    lines.append("=" * 60)
    lines.append(f"ID de ejecución : {report['execution_id']}")
    lines.append(f"Resultado global: {report['global_status']}")
    lines.append(f"Fecha           : {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    lines.append("=" * 60)
    lines.append("")

    TEST_LABELS = {
        "nulls":      "NULOS",
        "duplicates": "DUPLICADOS",
        "data_types": "TIPOS DE DATO",
        "outliers":   "OUTLIERS",
    }

    for result in report.get("results", []):
        name    = result.get("name", "")
        label   = TEST_LABELS.get(name, name.upper())
        status  = result.get("status", "N/A")
        summary = result.get("summary", "")
        metrics = result.get("metrics", {})
        inner   = metrics.get("metrics", metrics)

        lines.append(f"── {label} {'─' * (50 - len(label))}")
        lines.append(f"  Estado  : {status}")
        lines.append(f"  Resumen : {summary}")
        lines.append("")

        # NULOS
        if name == "nulls":
            ratio = inner.get("global_null_ratio", 0)
            lines.append(f"  Ratio global de nulos: {ratio * 100:.2f}%")
            lines.append("")

            critical = metrics.get("critical", [])
            if critical:
                lines.append("  Columnas críticas (>5% nulos):")
                for item in critical:
                    lines.append(f"    · {item['column']:<25} {item['null_ratio'] * 100:.2f}%")
                lines.append("")

            warnings = metrics.get("warnings", [])
            if warnings:
                lines.append("  Columnas con aviso (>0% nulos):")
                for item in warnings:
                    lines.append(f"    · {item['column']:<25} {item['null_ratio'] * 100:.2f}%")
                lines.append("")

        # DUPLICADOS
        elif name == "duplicates":
            dup_count = inner.get("duplicate_count", 0)
            dup_ratio = inner.get("duplicate_ratio", 0)
            lines.append(f"  Filas duplicadas: {dup_count} ({dup_ratio * 100:.2f}%)")
            lines.append("")

        # TIPOS DE DATO
        elif name == "data_types":
            mismatches = metrics.get("mismatches", [])
            if not mismatches:
                lines.append("  Sin columnas con tipos inesperados.")
            else:
                lines.append("  Columnas con tipo incorrecto:")
                for m in mismatches:
                    lines.append(
                        f"    · {m.get('column',''):<20} "
                        f"detectado: {m.get('detected',''):<12} "
                        f"esperado: {m.get('expected','')}"
                    )
            lines.append("")

        # OUTLIERS
        elif name == "outliers":
            total = inner.get("total_outliers", 0)
            lines.append(f"  Total outliers detectados: {total}")
            lines.append("")

            by_col = inner.get("outlier_ratio_by_column", {})
            if by_col:
                lines.append("  Ratio de outliers por columna:")
                for col, ratio in sorted(by_col.items(), key=lambda x: x[1], reverse=True):
                    lines.append(f"    · {col:<25} {ratio * 100:.2f}%")
                lines.append("")
        
        elif name == "balance":
            majority = inner.get("majority_class_ratio",0)
            target = inner.get("target_column","N/A")
            lines.append(f"  Columna objetivo: {target}")
            lines.append(f"  Clase mayoritaria: {majority * 100:.2f}%")
            lines.append("")
            distribution = inner.get("class_distribution",{})
            if distribution:
                lines.append("  Distribución de clases:")
                for cls, ratio in distribution.items():
                    lines.append(
                        f"    · {cls:<20} {ratio * 100:.2f}%"
                    )
                lines.append("")
                recs = result.get("recommendations", [])
                if recs:
                    lines.append("  Recomendaciones:")
                    for rec in recs:
                        lines.append(f"    → {rec}")
                    lines.append("")

    content = "\n".join(lines)
    stream = io.BytesIO(content.encode("utf-8"))

    return StreamingResponse(
        stream,
        media_type="text/plain; charset=utf-8",
        headers={
            "Content-Disposition": f"attachment; filename=Reporte_QA_{execution_id}.txt"
        }
    )