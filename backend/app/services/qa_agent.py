import pandas as pd
import numpy as np
from app.services.rules.qa_nulls import check_nulls
from app.services.rules.qa_duplicates import check_duplicates
from app.services.rules.qa_data_types import check_data_types
from app.services.rules.qa_outliers import check_outliers_iqr
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

        perception = {
            "intent": intent_data,
            "dataset": df,
            "columns": list(df.columns) if df is not None else []
        }

        return perception

    def decide(self, perception):
        """
        PASO 2: DECISIÓN
        Llama a las funciones de la carpeta /rules según el objetivo.
        """
        df = perception.get("dataset")
        intent = perception.get("intent", {})
        print("DEBUG INTENT:", intent)

        if df is None or df.empty:
            return []

        decisions = []

        requested_tests = intent.get("requested_tests", [])
        excluded_columns = intent.get("excluded_columns", [])
        critical_columns = intent.get("critical_columns", [])

        # Si no especifica tests → ejecutar todos
        if not requested_tests:
            requested_tests = [
                "nulls",
                "duplicates",
                "data_types",
                "outliers"
            ]

        valid_excluded = [c for c in excluded_columns if c in df.columns]

        if valid_excluded:
            df = df.drop(columns=valid_excluded)

        available_tests = {
            "nulls": {
                "function": check_nulls,
                "name": "nulls"
            },
            "duplicates": {
                "function": check_duplicates,
                "name": "duplicates"
            },
            "data_types": {
                "function": check_data_types,
                "name": "data_types"
            },
            "outliers": {
                "function": check_outliers_iqr,
                "name": "outliers"
            }
        }


        for test_name in requested_tests:

            if test_name not in available_tests:
                continue

            test_config = available_tests[test_name]
            test_function = test_config["function"]

            # Ejecutar regla
            result = test_function(df)

            result["critical_columns"] = critical_columns


            decision = {
                "name": test_config["name"],
                "status": result.get("status", "unknown"),
                "summary": "",
                "metrics": result,
                "recommendations": result.get("recommendations", [])
            }

            # Resumen personalizado por tipo
            if test_name == "nulls":
                decision["summary"] = (
                    f"{len(result.get('critical', []))} críticos, "
                    f"{len(result.get('warnings', []))} avisos"
                )

            elif test_name == "duplicates":
                decision["summary"] = (
                    f"{len(result.get('critical', []))} críticos, "
                    f"{len(result.get('warnings', []))} duplicados"
                )

            elif test_name == "data_types":
                decision["summary"] = (
                    f"{len(result.get('mismatches', []))} columnas con tipos inesperados"
                )

            elif test_name == "outliers":
                total_outliers = result.get("metrics", {}).get("total_outliers", 0)

                decision["summary"] = (
                    f"{total_outliers} outliers detectados"
                )

            decisions.append(decision)

        return decisions

    def act(self, decisions, execution_id="EXEC-DEFAULT", intent=None):
        """
        PASO 3: ACCIÓN
        Construye el JSON final compatible con React.
        """

        if not decisions:
            return {
                "assistant_message": "He recibido tu mensaje, pero no he identificado una acción clara.",
                "report": None,
                "hasReport": False,
                "execution_id": execution_id
            }

        # 1. Severidad global
        status_priority = {"FAIL": 3, "WARN": 2, "PASS": 1}
        max_severity = max([status_priority.get(d.get("status", "PASS"), 1) for d in decisions])
        global_status = "PASS"
        if max_severity == 3: global_status = "FAIL"
        elif max_severity == 2: global_status = "WARN"

        # 2. LISTAR TESTS PARA EL MENSAJE
        test_names = [d["name"] for d in decisions]
        tests_str = ", ".join(test_names)

        should_show_download_button = intent.get("download_report", False) if intent else False

        # 3. PREPARAR MÉTRICAS PARA EL RIGHT PANEL
        panel_metrics = []
        for d in decisions:
            val = 100 if d["status"] == "PASS" else (70 if d["status"] == "WARN" else 30)
            panel_metrics.append({"label": d["name"], "value": val})

        # 4. REPORTE
        report_data = {
            "execution_id": execution_id,
            "global_status": global_status,
            "results": decisions,
            "metrics": panel_metrics
        }

        # 5. CONSTRUIR EL MENSAJE DEL BOT
        msg = (
            f"He finalizado el análisis de calidad.<br/>"
            f"Validaciones realizadas: <b>{tests_str}</b>.<br/>"
            f"Resultado global: <b style='color: white'>{global_status}</b>.<br/><br/>"
        )
        
        if should_show_download_button:
            msg += "He preparado el informe detallado para su descarga."
        else:
            msg += "Si necesitas el informe en PDF, puedes pedírmelo."

        return {
            "assistant_message": msg,
            "execution_id": execution_id,
            "hasReport": should_show_download_button,
            "report": report_data
        }