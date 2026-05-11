from fastapi import APIRouter, UploadFile, File, Form
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

    # 2. EL CICLO DEL AGENTE (Percibir -> Decidir -> Actuar)
    # El agente mira el mensaje y el dataset
    perception = agent.perceive(df, user_message)
    
    # El agente decide qué reglas de /rules usar
    decisions = agent.decide(perception)
    
    # El agente genera la respuesta final estructurada para React
    response = agent.act(decisions, execution_id)

    return response