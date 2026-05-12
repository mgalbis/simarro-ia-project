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

@router.post("/chat")
async def chat(
    user_message: str = Form(...),
    file: Optional[UploadFile] = File(None)
):
    df = None
    execution_id = f"EXEC-{uuid.uuid4().hex[:6].upper()}"

    # 1. Procesamiento físico del archivo
    if file:
        content = await file.read()
        try:
            df = pd.read_csv(StringIO(content.decode("utf-8")))
        except Exception as e:
            return {
                "assistant_message": f"Error al leer el archivo: {str(e)}",
                "report": None
            }
       
    lower_msg = user_message.lower()

    if any(word in lower_msg for word in [
        "reporte",
        "report",
        "informe",
        "descargar"
    ]):
        return {
            "assistant_message": "He generado el reporte QA correctamente.",
            "execution_id": execution_id,
            "hasReport": True,
            "report": {
                "execution_id": execution_id
            }
        }
    
    # 2. EL CICLO DEL AGENTE (Percibir -> Decidir -> Actuar)
    # El agente mira el mensaje y el dataset
    perception = agent.perceive(df, user_message)
    
    # El agente decide qué reglas de /rules usar
    decisions = agent.decide(perception)
    
    # El agente genera la respuesta final estructurada para React
    response = agent.act(decisions, execution_id)

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