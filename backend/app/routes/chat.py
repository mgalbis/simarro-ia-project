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
    execution_id = f"EXEC-{uuid.uuid4().hex[:6].upper()}"
    df = None

    if file:
        content = await file.read()
        try:
            df = pd.read_csv(StringIO(content.decode("utf-8")))
        except Exception as e:
            return {"assistant_message": f"Error al leer el archivo: {str(e)}", "report": None}

    # Detectar si pide descargar el informe anterior
    lower_msg = user_message.lower()
    if any(w in lower_msg for w in ["descargar", "informe", "reporte", "pdf"]):
        if last_report_cache:
            return {
                "assistant_message": "Aquí tienes el informe del último análisis.",
                "execution_id": last_report_cache["execution_id"],
                "hasReport": True,
                "report": last_report_cache,
            }
        else:
            return {
                "assistant_message": "Todavía no hay ningún análisis realizado. Carga un CSV y ejecuta una validación primero.",
                "hasReport": False,
                "report": None,
            }

    # Ciclo del agente
    perception = agent.perceive(df, user_message)
    decisions = agent.decide(perception)
    response = agent.act(decisions, execution_id, perception["intent"])

    if response.get("report"):
        last_report_cache = response["report"]

    return response

@router.get("/download/{execution_id}")
async def download_report(execution_id: str):
    
    output = io.StringIO()
    output.write(f"Reporte de Calidad QA - ID: {execution_id}\n")
    output.write("Fila,Columna,Error,Gravedad\n")
    output.write("10,temperature,null,High\n")
    output.write("45,co2,outlier,Medium\n")
    
    # Convertimos el texto en un "archivo" binario que el navegador entienda
    stream = io.BytesIO(output.getvalue().encode())
    
    return StreamingResponse(
        stream,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=Reporte_QA_{execution_id}.csv"
        }
    )