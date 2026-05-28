from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import StreamingResponse
import io
import html
import pandas as pd
from io import StringIO
from typing import Optional
import uuid
from app.services.qa_agent import QAAgent
from app.services.assessment_comparison import build_assessment_comparison
from app.services.pdf_report import build_pdf_report
from pydantic import BaseModel
from typing import Optional
from app.services.session_store import (
    add_message,
    add_phase_feedback,
    add_report,
    clear_session,
    create_session,
    get_report,
    get_session,
    list_sessions,
    update_session_metadata,
    update_session_state,
)
from app.services.artifact_store import build_artifacts_zip, save_uploaded_artifact_bytes

router = APIRouter()
# Instanciamos el agente fuera para que mantenga su configuración
agent = QAAgent()

last_report_cache: dict = {}
reports_history: list[dict] = []

class SessionStatePayload(BaseModel):
    session_id: str
    user_id: str
    active_review_prompt: Optional[str] = None
    pending_prompt: Optional[str] = None
    last_processed_file_name: Optional[str] = None

class MessagePayload(BaseModel):
    session_id: str
    user_id: Optional[str] = None
    role: str
    content: str
    timestamp: Optional[str] = None

class ReportStorePayload(BaseModel):
    session_id: str
    user_id: Optional[str] = None
    report: dict
    
class SessionMetadataPayload(BaseModel):
    session_id: str
    user_id: str
    project_label: Optional[str] = None
    test_phase: Optional[str] = None
    review_label: Optional[str] = None

class PhaseFeedbackPayload(BaseModel):
    session_id: str
    user_id: Optional[str] = None
    prompt: Optional[str] = None
    detected_phase: Optional[str] = None
    comment: Optional[str] = None

@router.post("/sessions")
async def create_qabot_session(user_id: str):
    return create_session(user_id=user_id)

@router.get("/sessions")
async def list_qabot_sessions(user_id: str):
    return {
        "sessions": list_sessions(user_id=user_id)
    }

@router.get("/sessions/{session_id}")
async def get_qabot_session(session_id: str, user_id: str):
    session = get_session(session_id, user_id)

    if not session:
        return {
            "found": False,
            "message": "Sesión no encontrada."
        }

    return {
        "found": True,
        "session": session,
    }

@router.put("/sessions/state")
async def update_qabot_session_state(payload: SessionStatePayload):
    update_session_state(
        session_id=payload.session_id,
        user_id=payload.user_id,
        active_review_prompt=payload.active_review_prompt,
        pending_prompt=payload.pending_prompt,
        last_processed_file_name=payload.last_processed_file_name,
    )

    return {
        "ok": True
    }

@router.post("/sessions/messages")
async def store_qabot_message(payload: MessagePayload):
    add_message(
        session_id=payload.session_id,
        role=payload.role,
        content=payload.content,
        timestamp=payload.timestamp,
    )

    return {
        "ok": True
    }

@router.post("/sessions/reports")
async def store_qabot_report(payload: ReportStorePayload):
    add_report(
        session_id=payload.session_id,
        report=payload.report,
    )

    return {
        "ok": True
    }

@router.delete("/sessions/{session_id}")
async def delete_qabot_session(session_id: str, user_id: str):
    clear_session(session_id, user_id)

    return {
        "ok": True
    }

@router.post("/chat")
async def chat(
    user_message: str = Form(...),
    file: Optional[UploadFile] = File(None),
    session_id: Optional[str] = Form(None),
    user_id: Optional[str] = Form(None),
):
    global last_report_cache, reports_history
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
        user_cache_matches = (
            last_report_cache
            and user_id
            and str(last_report_cache.get("user_id")) == str(user_id)
        )

        if not user_cache_matches:
            return {
                "assistant_message": "Todavía no hay ningún análisis realizado en esta sesión de usuario. Carga un CSV y ejecuta una validación primero.",
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
    response = agent.act(decision_data, execution_id, intent=intent)

    if response.get("report") and response.get("addToHistory", False):
        previous_report = last_report_cache

        if session_id:
            stored_session = get_session(session_id, user_id) if user_id else None
            if stored_session and stored_session.get("last_report"):
                previous_report = stored_session.get("last_report")

        comparison = build_assessment_comparison(
            previous_report,
            response["report"],
        )

        if comparison:
            response["report"]["comparison_vs_previous"] = comparison

            if comparison.get("comparable"):
                response["assistant_message"] += (
                    "<br/><br/>"
                    + _build_comparison_html(comparison)
                )
            else:
                response["assistant_message"] += (
                    "<br/><br/><b>Comparación con ejecución anterior:</b> "
                    + comparison.get("reason", "No comparable.")
                )

        reports_history.append(response["report"])
        last_report_cache = response["report"]

        if session_id:
            response["report"]["session_id"] = session_id
        if user_id:
            response["report"]["user_id"] = user_id

        if session_id and file and content:
            save_uploaded_artifact_bytes(
                session_id=session_id,
                execution_id=response["report"]["execution_id"],
                filename=file.filename,
                content=content,
            )

        if session_id:
            add_message(
                session_id=session_id,
                role="user",
                content=user_message,
            )

            add_message(
                session_id=session_id,
                role="assistant",
                content=response.get("assistant_message", ""),
            )

            add_report(
                session_id=session_id,
                report=response["report"],
            )

            update_session_state(
                session_id=session_id,
                user_id=user_id,
                active_review_prompt=user_message,
                pending_prompt=None,
                last_processed_file_name=file.filename if file else None,
            )

    return response

@router.put("/sessions/metadata")
async def update_qabot_session_metadata(payload: SessionMetadataPayload):
    update_session_metadata(
        session_id=payload.session_id,
        user_id=payload.user_id,
        project_label=payload.project_label,
        test_phase=payload.test_phase,
        review_label=payload.review_label,
    )

    return {"ok": True}

def _build_comparison_html(comparison: dict) -> str:
    transitions = comparison.get("test_transitions", {})

    fixed = transitions.get("fixed", [])
    new_failures = transitions.get("new_failures", [])
    persistent_failures = transitions.get("persistent_failures", [])

    interpretation = comparison.get("interpretation", "Comparación generada.")

    html_output = """
<div class="qa-section-title">Comparación con la ejecución anterior</div>
<div class="qa-comparison-card">
"""

    if fixed:
        html_output += """
  <div class="qa-comparison-block">
    <div class="qa-comparison-title qa-comparison-title-success">
      Defectos corregidos
    </div>
"""
        for item in fixed:
            html_output += _build_transition_row(item)
        html_output += "  </div>"

    if new_failures:
        html_output += """
  <div class="qa-comparison-block">
    <div class="qa-comparison-title qa-comparison-title-fail">
      Nuevos defectos detectados
    </div>
"""
        for item in new_failures:
            html_output += _build_transition_row(item)
        html_output += "  </div>"

    if persistent_failures:
        html_output += """
  <div class="qa-comparison-block">
    <div class="qa-comparison-title qa-comparison-title-warn">
      Defectos persistentes
    </div>
"""
        for item in persistent_failures:
            html_output += _build_transition_row(item)
        html_output += "  </div>"

    html_output += f"""
  <div class="qa-comparison-summary">
    <b>Resumen:</b> {_html_escape(interpretation)}
  </div>
</div>
"""

    return html_output


def _build_transition_row(item: dict) -> str:
    test_name = _html_escape(item.get("test_name", "Prueba"))
    previous_status = item.get("previous_status", "")
    current_status = item.get("current_status", "")

    return f"""
    <div class="qa-comparison-row">
      <span class="qa-comparison-test">{test_name}</span>
      {_status_badge(previous_status)}
      <span class="qa-transition-arrow">→</span>
      {_status_badge(current_status)}
    </div>
"""


def _status_badge(status: str) -> str:
    normalized = (status or "").upper()

    if normalized in ("PASS", "SUCCESS"):
        css_class = "qa-badge qa-badge-pass"
    elif normalized in ("WARN", "WARNING"):
        css_class = "qa-badge qa-badge-warn"
    elif normalized in ("FAIL", "ERROR"):
        css_class = "qa-badge qa-badge-fail"
    else:
        css_class = "qa-badge"

    return f'<span class="{css_class}">{_html_escape(normalized or "N/A")}</span>'


def _html_escape(value) -> str:
    return html.escape(str(value or ""))

@router.get("/download/{execution_id}")
async def download_report(execution_id: str, user_id: str):
    report = None

    if execution_id == "latest" and str(last_report_cache.get("user_id")) == str(user_id):
        report = last_report_cache

    if not report and last_report_cache and last_report_cache.get("execution_id") == execution_id and str(last_report_cache.get("user_id")) == str(user_id):
        report = last_report_cache

    if not report:
        report = get_report(execution_id, user_id)

    if not report:
        return {
            "error": "Reporte no encontrado."
        }

    pdf_content = build_pdf_report(report)
    stream = io.BytesIO(pdf_content)

    return StreamingResponse(
        stream,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f"attachment; filename=Reporte_QA_{report.get('execution_id', execution_id)}.pdf"
            )
        },
    )

@router.get("/download/artifacts/{session_id}/{execution_id}")
async def download_artifacts(session_id: str, execution_id: str, user_id: str):
    session = get_session(session_id, user_id)

    if not session:
        return {
            "error": "Sesión no encontrada."
        }

    zip_path = build_artifacts_zip(session_id, execution_id)

    if not zip_path:
        return {
            "error": "No se han encontrado artefactos para esta iteración."
        }

    return StreamingResponse(
        open(zip_path, "rb"),
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename=Artefactos_QA_{execution_id}.zip"
        },
    )

@router.post("/sessions/phase-feedback")
async def create_phase_feedback(payload: PhaseFeedbackPayload):
    add_phase_feedback(
        session_id=payload.session_id,
        prompt=payload.prompt,
        detected_phase=payload.detected_phase,
        comment=payload.comment,
    )

    return {"ok": True}