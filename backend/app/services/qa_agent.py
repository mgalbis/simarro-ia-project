import pandas as pd
import numpy as np
from app.services.llm_service import interpret_user_intent
from app.services.qa_specialist_agent import QASpecialistAgent

class QAAgent:
    def __init__(self):
        self.specialist = QASpecialistAgent()
        
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

        perception = {
            "intent": intent_data,
            "dataset": df,
            "columns": list(df.columns) if df is not None else []
        }

        return perception

    def decide(self, perception):
        """
        PASO 2: DECISIÓN
        Toma decisiones basadas en la percepción.
        En este caso, delega la ejecución de los tests al especialista.
        """
        
        df = perception.get("dataset")
        intent = perception.get("intent", {})

        print("DEBUG INTENT:", intent)

        intent_type = intent.get("intent")

        # =========================
        # DESCARGA DE INFORME
        # =========================
        if intent_type == "download_report":

            return {
                "action": "download_report"
            }

        # =========================
        # VALIDACIÓN DATASET
        # =========================
        if intent_type == "validate_dataset":

            if df is None or df.empty:
                return {
                    "action": "empty_dataset"
                }

            requested_tests = intent.get("requested_tests", []) or [
                "nulls",
                "duplicates",
                "data_types",
                "outliers",
                "balance"
            ]

            critical_columns = intent.get("critical_columns", [])
            excluded_columns = intent.get("excluded_columns", [])

            valid_excluded = [
                c for c in excluded_columns
                if c in df.columns
            ]

            if valid_excluded:
                df = df.drop(columns=valid_excluded)

            decisions = []

            for test_name in requested_tests:

                result = self.specialist.run_test(
                    test_name,
                    df,
                    critical_columns
                )

                if result:
                    decisions.append(result)

            return {
                "action": "validate_dataset",
                "decisions": decisions
            }

        return {
            "action": "unknown"
        }

    def act(self, decision_data, execution_id="EXEC-DEFAULT", intent=None):
        """
        PASO 3: ACCIÓN
        Construye el JSON final compatible con React.
        """

        action = decision_data.get("action")

        # =========================
        # DESCARGA
        # =========================
        if action == "download_report":

            return {
                "assistant_message": "Aquí tienes el informe detallado con los últimos resultados obtenidos.",
                "hasReport": True,
                "report": None,
                "addToHistory": False,
                "execution_id": execution_id
            }

        # =========================
        # DATASET VACÍO
        # =========================
        if action == "empty_dataset":

            return {
                "assistant_message": "No se ha proporcionado un dataset válido.",
                "hasReport": False,
                "report": None,
                "execution_id": execution_id
            }

        # =========================
        # VALIDACIÓN
        # =========================
        if action == "validate_dataset":

            decisions = decision_data.get("decisions", [])

            if not decisions:

                return {
                    "assistant_message": "No se han podido ejecutar validaciones.",
                    "hasReport": False,
                    "report": None,
                    "execution_id": execution_id
                }

            status_priority = {
                "FAIL": 3,
                "WARN": 2,
                "PASS": 1
            }

            max_severity = max([
                status_priority.get(
                    d.get("status", "PASS"),
                    1
                )
                for d in decisions
            ])

            global_status = {
                3: "FAIL",
                2: "WARN",
                1: "PASS"
            }.get(max_severity, "PASS")

            test_names = [d["name"] for d in decisions]
            tests_str = ", ".join(test_names)

            report_data = {
                "execution_id": execution_id,
                "global_status": global_status,
                "results": decisions
            }

            return {
                "assistant_message": (
                    f"He finalizado el análisis de calidad.<br/>"
                    f"Validaciones realizadas: <b>{tests_str}</b>.<br/>"
                    f"Resultado global: <b>{global_status}</b>."
                ),
                "execution_id": execution_id,
                "hasReport": False,
                "report": report_data,
                "addToHistory": True
            }

        return {
            "assistant_message": "No he entendido la acción solicitada.",
            "hasReport": False,
            "report": None,
            "execution_id": execution_id
        }