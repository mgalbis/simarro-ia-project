"""Orquestador principal para convertir prompts en evaluaciones QA."""

import uuid

import pandas as pd
from app.schemas.quality_assessment import (
    ActivityType,
    ArtifactDescriptor,
    QualityAssessmentOrder,
)
from app.services.activity_catalog import ACTIVITY_OBJECTIVES, DEFAULT_TESTS_BY_ACTIVITY
from app.services.llm_service import interpret_user_intent
from app.services.qa_specialist_agent import QASpecialistAgent


class QAAgent:
    """
    Agente orquestador QA.

    Transforma el prompt del tester en una QualityAssessmentOrder,
    delega la ejecución read-only en el especialista y prepara la respuesta.
    """

    def __init__(self):
        """Inicializa el agente especialista usado para ejecutar pruebas QA."""
        self.specialist = QASpecialistAgent()

    def perceive(self, df: pd.DataFrame, user_message: str):
        """Construye la percepción inicial con intención, dataset y columnas."""
        intent_data = interpret_user_intent(user_message)

        return {
            "intent": intent_data,
            "dataset": df,
            "columns": list(df.columns) if df is not None else [],
            "user_message": user_message,
        }

    def decide(self, perception):
        """Decide la acción a ejecutar según intención y artefactos disponibles."""
        df = perception.get("dataset")
        intent = perception.get("intent", {})
        user_message = perception.get("user_message", "")

        if intent.get("intent") == "unknown":
            return {
                "action": "unknown_action",
            }

        if intent.get("intent") == "download_report":
            return {
                "action": "download_report",
            }

        order = self._build_quality_assessment_order(
            df=df,
            intent=intent,
            user_message=user_message,
        )

        if order.missing_information:
            return {
                "action": "missing_information",
                "order": order,
            }

        if df is None or df.empty:
            return {
                "action": "empty_dataset",
                "order": order,
            }

        assessment_result = self.specialist.run_assessment(order, df)

        return {
            "action": "assessment_completed",
            "order": order,
            "assessment_result": assessment_result,
        }

    def act(self, decision_data, execution_id="EXEC-DEFAULT", intent=None):
        """Construye la respuesta final del asistente para la decisión tomada."""
        action = decision_data.get("action")

        if action == "download_report":
            return {
                "assistant_message": (
                    "Aquí tienes el informe detallado con los últimos resultados obtenidos."
                ),
                "hasReport": True,
                "report": None,
                "addToHistory": False,
                "execution_id": execution_id,
            }

        if action == "empty_dataset":
            return {
                "assistant_message": (
                    "<div class='qa-result-card'>"
                    "<div class='qa-result-header'>"
                    "<span class='qa-strong'>No se ha proporcionado un dataset válido.</span>"
                    f"{self._status_badge('FAIL')}"
                    "</div>"
                    "<div class='qa-note'>"
                    "Aporta un fichero CSV válido para ejecutar las pruebas del ciclo."
                    "</div>"
                    "</div>"
                ),
                "hasReport": False,
                "report": None,
                "addToHistory": False,
                "execution_id": execution_id,
            }

        if action == "missing_information":
            order = decision_data.get("order")
            return {
                "assistant_message": self._build_missing_information_message(order),
                "hasReport": False,
                "report": None,
                "addToHistory": False,
                "execution_id": execution_id,
            }

        if action == "assessment_completed":
            order = decision_data.get("order")
            assessment_result = decision_data.get("assessment_result")
            return self._build_assessment_response(
                order=order,
                assessment_result=assessment_result,
                execution_id=execution_id,
            )

        return {
            "assistant_message": (
                "<div class='qa-result-card'>"
                "<div class='qa-result-header'>"
                "<span class='qa-strong'>No he entendido la acción solicitada.</span>"
                f"{self._status_badge('WARN')}"
                "</div>"
                "</div>"
            ),
            "hasReport": False,
            "report": None,
            "addToHistory": False,
            "execution_id": execution_id,
        }

    def _infer_column_from_dataset(
        self,
        df,
        explicit_name,
        candidates,
        contains_candidates=None,
        suffix_candidates=None,
    ):
        if df is None or df.empty:
            return explicit_name

        columns = list(df.columns)
        by_lower = {str(column).lower(): str(column) for column in columns}

        if explicit_name:
            explicit_lower = str(explicit_name).lower()
            if explicit_lower in by_lower:
                return by_lower[explicit_lower]
            for column in columns:
                if explicit_lower == str(column).lower():
                    return str(column)
            # Si el prompt traía una columna inventada por texto documental
            # (por ejemplo "dataset es documentales"), no bloqueamos la ejecución.
            explicit_name = None

        for candidate in candidates:
            if candidate.lower() in by_lower:
                return by_lower[candidate.lower()]

        contains_candidates = contains_candidates or candidates
        for column in columns:
            column_lower = str(column).lower()
            if any(
                candidate.lower() in column_lower for candidate in contains_candidates
            ):
                return str(column)

        suffix_candidates = suffix_candidates or []
        for column in columns:
            column_lower = str(column).lower()
            if any(
                column_lower.endswith(suffix.lower()) for suffix in suffix_candidates
            ):
                return str(column)

        return explicit_name

    def _build_quality_assessment_order(
        self,
        df,
        intent,
        user_message,
    ) -> QualityAssessmentOrder:
        activity_type_value = intent.get(
            "activity_type",
            ActivityType.MINABLE_DATASET_VALIDATION.value,
        )

        activity_type = ActivityType(activity_type_value)

        requested_tests = intent.get(
            "requested_tests"
        ) or DEFAULT_TESTS_BY_ACTIVITY.get(
            activity_type,
            [],
        )

        target_column = intent.get("target_column")
        prediction_column = intent.get("prediction_column")
        split_column = intent.get("split_column")
        id_column = intent.get("id_column")
        threshold = intent.get("threshold")

        # Compatibilidad legacy + modo documental: si el prompt no indica columnas
        # o trae columnas no existentes por texto del DC, se infieren desde el CSV.
        target_column = self._infer_column_from_dataset(
            df,
            target_column,
            candidates=[
                "target",
                "abandono",
                "churn",
                "y_true",
                "real",
                "label",
                "clase",
            ],
            contains_candidates=[
                "target",
                "abandono",
                "churn",
                "label",
                "clase",
                "real",
            ],
        )
        prediction_column = self._infer_column_from_dataset(
            df,
            prediction_column,
            candidates=[
                "probabilidad_abandono",
                "churn_probability",
                "score",
                "prediction",
                "prediccion",
                "predicción",
                "y_pred",
                "probabilidad",
                "predicted",
            ],
            contains_candidates=[
                "probabilidad",
                "churn_probability",
                "score",
                "pred",
                "prediction",
            ],
        )
        split_column = self._infer_column_from_dataset(
            df,
            split_column,
            candidates=[
                "split",
                "conjunto",
                "partition",
                "particion",
                "partición",
                "subset",
            ],
            contains_candidates=[
                "split",
                "conjunto",
                "partition",
                "particion",
                "subset",
            ],
        )
        id_column = self._infer_column_from_dataset(
            df,
            id_column,
            candidates=["customer_id", "cliente_id", "id", "row_id"],
            contains_candidates=["customer_id", "cliente_id"],
            suffix_candidates=["_id"],
        )

        missing_information = []

        artifacts = {
            "dataset": ArtifactDescriptor(
                required=True,
                provided=df is not None and not df.empty,
                access_mode="read_only",
                description="Dataset uploaded by the user.",
            )
        }

        if df is None or df.empty:
            missing_information.append("dataset")

        if activity_type in {
            ActivityType.MODEL_PERFORMANCE_EVALUATION,
            ActivityType.THRESHOLD_QUALITY_EVALUATION,
        }:
            artifacts.update(
                {
                    "target_column": ArtifactDescriptor(
                        required=True,
                        provided=bool(target_column),
                        name=target_column,
                        access_mode="read_only",
                    ),
                    "prediction_column": ArtifactDescriptor(
                        required=True,
                        provided=bool(prediction_column),
                        name=prediction_column,
                        access_mode="read_only",
                    ),
                    "threshold": ArtifactDescriptor(
                        required=False,
                        provided=threshold is not None,
                        name=str(threshold) if threshold is not None else None,
                        access_mode="read_only",
                    ),
                }
            )

            if not target_column:
                missing_information.append("target_column")

            if not prediction_column:
                missing_information.append("prediction_column")

        if activity_type == ActivityType.DATASET_SPLIT_VALIDATION:
            artifacts.update(
                {
                    "split_column": ArtifactDescriptor(
                        required=True,
                        provided=bool(split_column),
                        name=split_column,
                        access_mode="read_only",
                    ),
                    "target_column": ArtifactDescriptor(
                        required=False,
                        provided=bool(target_column),
                        name=target_column,
                        access_mode="read_only",
                    ),
                    "id_column": ArtifactDescriptor(
                        required=False,
                        provided=bool(id_column),
                        name=id_column,
                        access_mode="read_only",
                    ),
                }
            )

            if not split_column:
                missing_information.append("split_column")

        parameters = {
            "requested_tests": requested_tests,
            "target_column": target_column,
            "prediction_column": prediction_column,
            "split_column": split_column,
            "id_column": id_column,
            "threshold": threshold if threshold is not None else 0.5,
            "critical_columns": intent.get("critical_columns", []),
            "excluded_columns": intent.get("excluded_columns", []),
        }

        return QualityAssessmentOrder(
            request_id=f"REQ-{uuid.uuid4().hex[:8].upper()}",
            activity_type=activity_type,
            objective=ACTIVITY_OBJECTIVES.get(
                activity_type,
                "Execute read-only quality assessment.",
            ),
            user_message=user_message,
            artifacts=artifacts,
            parameters=parameters,
            missing_information=missing_information,
        )

    def _build_missing_information_message(self, order: QualityAssessmentOrder) -> str:
        readable = self._html_escape(", ".join(order.missing_information))

        if order.activity_type == ActivityType.DATASET_SPLIT_VALIDATION:
            return (
                "<div class='qa-result-card'>"
                "<div class='qa-result-header'>"
                "<span class='qa-strong'>Falta información para validar particiones</span>"
                f"{self._status_badge('WARN')}"
                "</div>"
                "<div class='qa-note'>"
                f"Para validar particiones necesito información adicional: <b>{readable}</b>.<br/>"
                "Indica la columna que identifica cada partición, por ejemplo: "
                "<code>split es conjunto</code>. Opcionalmente puedes indicar "
                "<code>target es abandono</code> y <code>id es cliente_id</code>."
                "</div>"
                "</div>"
            )

        if order.activity_type in {
            ActivityType.MODEL_PERFORMANCE_EVALUATION,
            ActivityType.THRESHOLD_QUALITY_EVALUATION,
        }:
            return (
                "<div class='qa-result-card'>"
                "<div class='qa-result-header'>"
                "<span class='qa-strong'>Falta información para evaluar el modelo</span>"
                f"{self._status_badge('WARN')}"
                "</div>"
                "<div class='qa-note'>"
                f"Para evaluar el modelo necesito información adicional: <b>{readable}</b>.<br/>"
                "Indica, por ejemplo: "
                "<code>target es abandono</code>, "
                "<code>score es probabilidad_abandono</code> "
                "y opcionalmente <code>umbral actual es 0.6</code>."
                "</div>"
                "</div>"
            )

        return (
            "<div class='qa-result-card'>"
            "<div class='qa-result-header'>"
            "<span class='qa-strong'>Falta información para ejecutar el ciclo de pruebas</span>"
            f"{self._status_badge('WARN')}"
            "</div>"
            "<div class='qa-note'>"
            f"Necesito información adicional: <b>{readable}</b>."
            "</div>"
            "</div>"
        )

    def _build_assessment_response(
        self,
        order: QualityAssessmentOrder,
        assessment_result,
        execution_id: str,
    ):
        report_data = {
            "execution_id": execution_id,
            "activity_type": order.activity_type.value,
            "execution_mode": order.execution_mode.value,
            "global_status": assessment_result.assessment_status.value,
            "quality_assessment_order": order.model_dump(),
            "assessment_result": assessment_result.model_dump(),
            "results": assessment_result.test_results,
        }

        assistant_message = self._build_assessment_chat_message(
            order=order,
            assessment_result=assessment_result,
        )

        return {
            "assistant_message": assistant_message,
            "execution_id": execution_id,
            "hasReport": True,
            "report": report_data,
            "addToHistory": True,
        }

    def _build_assessment_chat_message(
        self,
        order: QualityAssessmentOrder,
        assessment_result,
    ) -> str:
        global_status = assessment_result.assessment_status.value
        summary = assessment_result.summary or {}

        test_names = [
            result.get("name", "")
            for result in assessment_result.test_results
            if result.get("name")
        ]
        tests_str = ", ".join(test_names)

        defects_html = self._build_defects_html(assessment_result)
        recommendations_html = self._build_recommendations_html(assessment_result)
        comparison_html = self._build_comparison_html(summary)

        overall_result = self._html_escape(summary.get("overall_result", ""))

        return f"""
<div class="qa-result-card">
  <div class="qa-result-header">
    <span class="qa-strong">Pruebas finalizadas</span>
    {self._status_badge(global_status)}
  </div>

  <div>
    <span class="qa-muted-line">Actividad:</span>
    <span class="qa-strong">{self._html_escape(order.activity_type.value)}</span>
  </div>

  <div>
    <span class="qa-muted-line">Pruebas ejecutadas:</span>
    <span class="qa-strong">{self._html_escape(tests_str)}</span>
  </div>

  <div>
    <span class="qa-muted-line">Resultado global:</span>
    {self._status_badge(global_status)}
  </div>

  {f'<div class="qa-muted-line">{overall_result}</div>' if overall_result else ''}

  {defects_html}

  {recommendations_html}

  {comparison_html}

  <div class="qa-note">
    Nota: estas pruebas solo identifican defectos, advertencias y evidencias.
    No se han aplicado correcciones sobre los artefactos evaluados.
  </div>
</div>
"""

    def _build_defects_html(self, assessment_result) -> str:
        findings = assessment_result.findings or []

        if not findings:
            return """
<div class="qa-section-title">Defectos detectados</div>
<div class="qa-muted-line">
  No se han identificado defectos o advertencias relevantes en las pruebas ejecutadas.
</div>
"""

        items = []

        for finding in findings:
            severity = self._get_attr_or_dict(finding, "severity", "UNKNOWN")
            description = self._get_attr_or_dict(finding, "description", "")
            impact = self._get_attr_or_dict(finding, "impact", None)
            recommendation = self._get_attr_or_dict(finding, "recommendation", None)

            description_html = self._html_escape(description)
            impact_html = self._html_escape(impact) if impact else ""
            recommendation_html = (
                self._html_escape(recommendation) if recommendation else ""
            )

            body_parts = []

            if description_html:
                body_parts.append(f"<div>{description_html}</div>")

            if impact_html:
                body_parts.append(f"<div class='qa-muted-line'>{impact_html}</div>")

            if recommendation_html:
                body_parts.append(
                    f"<div class='qa-muted-line'><b>Recomendación:</b> {recommendation_html}</div>"
                )

            body = (
                "".join(body_parts)
                if body_parts
                else "<div>Defecto sin descripción.</div>"
            )

            items.append(
                f"""
<div class="qa-defect-item">
  <div class="qa-defect-title">
    {self._severity_badge(severity)}
  </div>
  <div class="qa-defect-description">
    {body}
  </div>
</div>
"""
            )

        return f"""
<div class="qa-section-title">Defectos detectados</div>
<div class="qa-defect-list">
  {''.join(items)}
</div>
"""

    def _build_recommendations_html(self, assessment_result) -> str:
        recommendations = assessment_result.recommendations or []

        if not recommendations:
            return ""

        items = "".join(
            f"<li>{self._html_escape(recommendation)}</li>"
            for recommendation in recommendations
        )

        return f"""
<div class="qa-section-title">Recomendaciones para una iteración posterior</div>
<div class="qa-recommendations">
  <ul>
    {items}
  </ul>
</div>
"""

    def _build_comparison_html(self, summary: dict) -> str:
        comparison = summary.get("comparison_with_previous")

        if not comparison:
            return ""

        return f"""
<div class="qa-section-title">Comparación con la iteración anterior</div>
<div class="qa-recommendations">
  {self._html_escape(comparison)}
</div>
"""

    @staticmethod
    def _status_badge(status: str) -> str:
        normalized = (status or "").upper()

        if normalized in ("PASS", "SUCCESS", "PASADA"):
            css_class = "qa-badge qa-badge-pass"
            label = "PASADA"
        elif normalized in ("WARN", "WARNING", "ADVERTENCIA"):
            css_class = "qa-badge qa-badge-warn"
            label = "ADVERTENCIA"
        elif normalized in ("FAIL", "FALLIDA"):
            css_class = "qa-badge qa-badge-fail"
            label = "FALLIDA"
        elif normalized in ("ERROR", "ERRORES"):
            css_class = "qa-badge qa-badge-fail"
            label = "ERROR"
        else:
            css_class = "qa-badge"
            label = normalized or "N/A"

        return f'<span class="{css_class}">{label}</span>'

    @staticmethod
    def _severity_badge(severity: str) -> str:
        normalized = (severity or "").upper()

        if normalized in ("HIGH", "CRITICAL", "ERROR"):
            css_class = "qa-badge qa-badge-fail"
            label = "CRÍTICO" if normalized == "CRITICAL" else "ERROR"
        elif normalized in ("MEDIUM", "WARN", "WARNING"):
            css_class = "qa-badge qa-badge-warn"
            label = "ADVERTENCIA"
        elif normalized in ("LOW", "INFO"):
            css_class = "qa-badge"
            label = "INFO"
        else:
            css_class = "qa-badge"
            label = normalized

        return f'<span class="{css_class}">{label}</span>'

    @staticmethod
    def _html_escape(value) -> str:
        import html

        return html.escape(str(value or ""))

    def _get_attr_or_dict(self, source, key: str, default=None):
        if isinstance(source, dict):
            return source.get(key, default)

        return getattr(source, key, default)
