import pandas as pd
import numpy as np
from app.services.rules.qa_nulls import check_nulls
from app.services.rules.qa_duplicates import check_duplicates
from app.services.llm_service import interpret_user_intent

class QAAgent:
    def __init__(self):
        """
        Agente Orquestador QA.
        Estructura basada en Percibir -> Decidir -> Actuar.
        """
        pass

    def perceive(self, df: pd.DataFrame, user_message: str):
        """
        PASO 1: PERCEPCIÓN
        Recopila la información del entorno (dataset y mensaje).
        """
        intent_data = interpret_user_intent(user_message)
        
        return {
            "intent": intent_data.get("intent", "unknown"),
            "actions": intent_data.get("actions", []),
            "dataset": df,
            "message": user_message
        }

    def decide(self, perception):
        """
        PASO 2: DECISIÓN
        Llama a las funciones de la carpeta /rules según el objetivo.
        """
        df = perception["dataset"]
        actions = perception["actions"]
        
        if df is None or df.empty:
            return []

        results = []
        # Ejecutamos las reglas basadas en lo que el LLM decidió
        if "check_nulls" in actions:
            # 1. Ejecutamos la lógica
            res = check_nulls(df) 
            
            # 2. Inyectamos las métricas que el Frontend espera para las barras
            null_ratio = float(df.isnull().mean().mean())
            res.update({
                "name": "Nulos",
                "details": f"Detección de {df.isnull().sum().sum()} valores vacíos",
                "metrics": {
                    "global_null_ratio": null_ratio
                }
            })
            results.append(res)
            
        if "check_duplicates" in actions:
            res = check_duplicates(df)
            # Calculamos ratio de duplicados para la barra de "Unicidad"
            dup_ratio = float(df.duplicated().mean())
            res.update({
                "name": "Duplicados",
                "details": "Análisis de filas repetidas",
                "metrics": {
                    "duplicate_ratio": dup_ratio
                }
            })
            results.append(res)
            
        return results

    def act(self, decisions, execution_id="EXEC-DEFAULT"):
        """
        PASO 3: ACCIÓN
        Construye el JSON final compatible con la interfaz React.
        """
        if not decisions:
            return {
                "assistant_message": "He recibido tu mensaje, pero no he identificado una acción clara. Por favor, reformula tu solicitud o proporciona más detalles.",
                "report": None,
                "hasReport": False,
                "execution_id": execution_id
            }

        # Cálculo de severidad
        status_priority = {"FAIL": 3, "WARN": 2, "PASS": 1}
        max_severity = max([status_priority.get(d.get("status", "PASS"), 1) for d in decisions])
        
        global_status = "PASS"
        if max_severity == 3: global_status = "FAIL"
        elif max_severity == 2: global_status = "WARN"

        msg = f"Análisis finalizado con éxito. Estado global: **{global_status}**. "

        return {
            "assistant_message": msg,
            "execution_id": execution_id,
            "report": {
                "execution_id": execution_id,
                "global_status": global_status,
                "hasReport": True,
                "results": decisions
            }
        }