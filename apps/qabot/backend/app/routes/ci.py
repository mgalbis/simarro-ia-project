"""Endpoints CI/CD para ejecutar quality gates de QABot."""

import json
import uuid
from io import StringIO
from typing import Optional

import pandas as pd
from app.schemas.quality_assessment import (
    ActivityType,
    ArtifactDescriptor,
    AssessmentStatus,
    QualityAssessmentOrder,
)
from app.services.activity_catalog import ACTIVITY_OBJECTIVES, DEFAULT_TESTS_BY_ACTIVITY
from app.services.qa_specialist_agent import QASpecialistAgent
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/ci", tags=["CI/CD Quality Gate"])
specialist = QASpecialistAgent()


class QualityGateResponse(BaseModel):
    """Respuesta estructurada para integración con pipelines CI/CD."""

    execution_id: str
    pipeline_status: str
    should_fail_pipeline: bool
    exit_code: int
    activity_type: str
    assessment_status: str
    quality_gate: dict = Field(default_factory=dict)
    report: dict = Field(default_factory=dict)


def _parse_csv_upload(file: UploadFile, content: bytes) -> pd.DataFrame:
    try:
        decoded = content.decode("utf-8")
        return pd.read_csv(StringIO(decoded))
    except UnicodeDecodeError:
        try:
            decoded = content.decode("latin-1")
            return pd.read_csv(StringIO(decoded))
        except Exception as exc:
            raise HTTPException(
                status_code=400,
                detail=f"No se pudo leer el CSV {file.filename}: {exc}",
            ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"No se pudo leer el CSV {file.filename}: {exc}",
        ) from exc


def _parse_json_list(value: Optional[str], field_name: str) -> Optional[list[str]]:
    if not value:
        return None

    value = value.strip()

    if not value:
        return None

    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        # Also accept comma-separated values for simple CI/CD calls.
        parsed = [item.strip() for item in value.split(",") if item.strip()]

    if not isinstance(parsed, list) or not all(
        isinstance(item, str) for item in parsed
    ):
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} debe ser una lista JSON de strings o una lista separada por comas.",
        )

    return parsed


def _parse_failure_statuses(value: Optional[str]) -> set[str]:
    statuses = _parse_json_list(value, "fail_on_status") or ["FAIL", "ERROR"]
    normalized = {status.upper() for status in statuses}

    valid = {item.value for item in AssessmentStatus}
    invalid = normalized - valid

    if invalid:
        raise HTTPException(
            status_code=400,
            detail=f"Estados no válidos en fail_on_status: {sorted(invalid)}. Valores permitidos: {sorted(valid)}.",
        )

    return normalized


def _build_order(
    *,
    activity_type: ActivityType,
    filename: str,
    requested_tests: Optional[list[str]],
    target_column: Optional[str],
    prediction_column: Optional[str],
    split_column: Optional[str],
    id_column: Optional[str],
    threshold: Optional[float],
    pipeline_id: Optional[str],
    stage_name: Optional[str],
) -> QualityAssessmentOrder:
    tests = requested_tests or DEFAULT_TESTS_BY_ACTIVITY.get(activity_type, [])

    artifacts = {
        "dataset": ArtifactDescriptor(
            required=True,
            provided=True,
            name=filename,
            access_mode="read_only",
            description="Dataset uploaded by CI/CD quality gate.",
        )
    }

    missing_information: list[str] = []

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

    if missing_information:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Faltan parámetros obligatorios para ejecutar la etapa de pruebas.",
                "missing_information": missing_information,
            },
        )

    parameters = {
        "requested_tests": tests,
        "target_column": target_column,
        "prediction_column": prediction_column,
        "split_column": split_column,
        "id_column": id_column,
        "threshold": threshold if threshold is not None else 0.5,
        "pipeline_id": pipeline_id,
        "stage_name": stage_name,
    }

    return QualityAssessmentOrder(
        request_id=f"REQ-CI-{uuid.uuid4().hex[:8].upper()}",
        activity_type=activity_type,
        objective=ACTIVITY_OBJECTIVES.get(
            activity_type,
            "Execute read-only quality assessment from CI/CD pipeline.",
        ),
        user_message=(
            f"CI/CD predefined quality gate for {activity_type.value}. "
            f"pipeline_id={pipeline_id or 'N/A'}, stage_name={stage_name or 'N/A'}"
        ),
        artifacts=artifacts,
        parameters=parameters,
        missing_information=[],
        expected_outputs=[
            "quality_gate_status",
            "assessment_result",
            "test_results",
            "evidence",
            "recommendations_for_next_iteration",
            "non_modification_statement",
        ],
    )


@router.get("/activities")
async def list_ci_quality_gate_activities():
    """Devuelve el catálogo de actividades QA ejecutables en CI/CD."""
    return {
        "activities": [
            {
                "activity_type": activity_type.value,
                "default_tests": DEFAULT_TESTS_BY_ACTIVITY.get(activity_type, []),
                "objective": ACTIVITY_OBJECTIVES.get(activity_type, ""),
            }
            for activity_type in DEFAULT_TESTS_BY_ACTIVITY.keys()
        ]
    }


@router.post("/quality-gate", response_model=QualityGateResponse)
async def run_ci_quality_gate(
    file: UploadFile = File(...),
    activity_type: ActivityType = Form(...),
    target_column: Optional[str] = Form(None),
    prediction_column: Optional[str] = Form(None),
    split_column: Optional[str] = Form(None),
    id_column: Optional[str] = Form(None),
    threshold: Optional[float] = Form(None),
    requested_tests: Optional[str] = Form(None),
    fail_on_status: Optional[str] = Form(None),
    pipeline_id: Optional[str] = Form(None),
    stage_name: Optional[str] = Form(None),
):
    """
    Ejecuta una etapa de pruebas predefinida para integración CI/CD.

    Este endpoint no usa conversación ni estado de sesión. Recibe un artefacto CSV,
    una actividad de pruebas y los parámetros necesarios para ejecutar el agente
    especialista en modo read-only. Devuelve un resultado estructurado apto para
    que el pipeline decida si continúa o falla la etapa.
    """
    content = await file.read()
    df = _parse_csv_upload(file, content)

    tests = _parse_json_list(requested_tests, "requested_tests")
    failure_statuses = _parse_failure_statuses(fail_on_status)
    execution_id = f"CI-{uuid.uuid4().hex[:8].upper()}"

    order = _build_order(
        activity_type=activity_type,
        filename=file.filename or "uploaded.csv",
        requested_tests=tests,
        target_column=target_column,
        prediction_column=prediction_column,
        split_column=split_column,
        id_column=id_column,
        threshold=threshold,
        pipeline_id=pipeline_id,
        stage_name=stage_name,
    )

    assessment_result = specialist.run_assessment(order, df)
    assessment_status = assessment_result.assessment_status.value
    should_fail_pipeline = assessment_status in failure_statuses

    report = {
        "execution_id": execution_id,
        "activity_type": order.activity_type.value,
        "execution_mode": order.execution_mode.value,
        "global_status": assessment_status,
        "quality_assessment_order": order.model_dump(),
        "assessment_result": assessment_result.model_dump(),
        "results": assessment_result.test_results,
    }

    return QualityGateResponse(
        execution_id=execution_id,
        pipeline_status="FAIL" if should_fail_pipeline else "PASS",
        should_fail_pipeline=should_fail_pipeline,
        exit_code=1 if should_fail_pipeline else 0,
        activity_type=order.activity_type.value,
        assessment_status=assessment_status,
        quality_gate={
            "fail_on_status": sorted(failure_statuses),
            "pipeline_id": pipeline_id,
            "stage_name": stage_name,
            "artifact_name": file.filename,
            "read_only": True,
        },
        report=report,
    )
