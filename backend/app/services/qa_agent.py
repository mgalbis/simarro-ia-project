import pandas as pd
import numpy as np
from app.services.rules.qa_nulls import check_nulls
from app.services.rules.qa_duplicates import check_duplicates

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
        perception = {
            "goal": user_message.lower(),
            "dataset": df,
            "columns": list(df.columns) if df is not None else []
        }
        return perception

    def decide(self, perception):
        """
        PASO 2: DECISIÓN
        Llama a las funciones de la carpeta /rules según el objetivo.
        """
        goal = perception["goal"]
        df = perception["dataset"]
        
        if df is None or df.empty:
            return []

        decisions = []

        # Lógica de disparo de reglas (Orquestación básica)
        # Si el usuario menciona 'calidad', 'analiza' o términos generales, ejecutamos todo.
        is_general_query = any(word in goal for word in ["analiza", "calidad", "test", "prueba", "informe"])

        if is_general_query or "nulo" in goal:
            res_nulls = check_nulls(df)
            # Añadimos metadata necesaria para el RightPanel de React
            res_nulls["name"] = "Nulos"
            res_nulls["details"] = f"{len(res_nulls.get('critical', []))} críticos, {len(res_nulls.get('warnings', []))} avisos"
            # Calculamos métrica para la barra de progreso (0-1)
            res_nulls["metrics"] = {"global_null_ratio": float(df.isnull().mean().mean())}
            decisions.append(res_nulls)

        if is_general_query or "duplicado" in goal:
            res_dups = check_duplicates(df)
            res_dups["name"] = "Duplicados"
            # Aseguramos que existan métricas para el frontend
            if "metrics" not in res_dups:
                res_dups["metrics"] = {"duplicate_ratio": float(df.duplicated().sum() / len(df)) if len(df) > 0 else 0}
            decisions.append(res_dups)

        return decisions

    def act(self, decisions, execution_id="EXEC-DEFAULT"):
        """
        PASO 3: ACCIÓN
        Construye el JSON final compatible con la interfaz React.
        """
        if not decisions:
            return {
                "assistant_message": "He recibido el archivo, pero no sé qué validación quieres que haga. Prueba con 'Analiza la calidad'.",
                "report": None
            }

        # Cálculo del estado global para el encabezado del RightPanel
        status_priority = {"FAIL": 3, "WARN": 2, "PASS": 1}
        max_severity = max([status_priority.get(d["status"], 1) for d in decisions])
        
        global_status = "PASS"
        if max_severity == 3: global_status = "FAIL"
        elif max_severity == 2: global_status = "WARN"

        report = {
            "execution_id": execution_id,
            "global_status": global_status,
            "results": decisions
        }

        return {
            "assistant_message": f"Análisis finalizado. Estado global: **{global_status}**. Se han aplicado {len(decisions)} reglas de validación.",
            "report": report
        }