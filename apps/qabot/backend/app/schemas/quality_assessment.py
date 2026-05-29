"""Esquemas y enums del dominio de evaluación de calidad QA."""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ActivityType(str, Enum):
    """Catálogo de actividades QA soportadas por el sistema."""

    MINABLE_DATASET_VALIDATION = "MINABLE_DATASET_VALIDATION"
    DATASET_SPLIT_VALIDATION = "DATASET_SPLIT_VALIDATION"
    DATASET_SPLIT_VALIDATION_3DS = "DATASET_SPLIT_VALIDATION_3DS"
    FEATURE_SET_QUALITY_REVIEW = "FEATURE_SET_QUALITY_REVIEW"
    MODEL_CONFIGURATION_REVIEW = "MODEL_CONFIGURATION_REVIEW"
    MODEL_PERFORMANCE_EVALUATION = "MODEL_PERFORMANCE_EVALUATION"
    THRESHOLD_QUALITY_EVALUATION = "THRESHOLD_QUALITY_EVALUATION"
    DASHBOARD_RESULT_VALIDATION = "DASHBOARD_RESULT_VALIDATION"


class ExecutionMode(str, Enum):
    """Modos de ejecución admitidos para evaluaciones QA."""

    READ_ONLY_QUALITY_ASSESSMENT = "read_only_quality_assessment"


class AssessmentStatus(str, Enum):
    """Estados globales posibles de una evaluación QA."""

    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"
    ERROR = "ERROR"


class TestSeverity(str, Enum):
    """Niveles de severidad para pruebas y hallazgos QA."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ArtifactDescriptor(BaseModel):
    """Describe un artefacto de entrada requerido por una actividad."""

    required: bool = True
    provided: bool = False
    name: Optional[str] = None
    path: Optional[str] = None
    access_mode: str = "read_only"
    description: Optional[str] = None


class ExecutionConstraints(BaseModel):
    """Restricciones operativas de ejecución para mantener modo read-only."""

    modify_artifacts: bool = False
    train_model: bool = False
    update_threshold: bool = False
    write_output_artifacts: bool = False
    publish_results: bool = False


class QualityAssessmentOrder(BaseModel):
    """Orden estructurada de evaluación QA interpretada desde la solicitud."""

    request_id: str
    activity_type: ActivityType
    execution_mode: ExecutionMode = ExecutionMode.READ_ONLY_QUALITY_ASSESSMENT
    objective: str
    user_message: str
    artifacts: Dict[str, ArtifactDescriptor] = Field(default_factory=dict)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    constraints: ExecutionConstraints = Field(default_factory=ExecutionConstraints)
    acceptance_criteria: Dict[str, Any] = Field(default_factory=dict)
    missing_information: List[str] = Field(default_factory=list)
    expected_outputs: List[str] = Field(
        default_factory=lambda: [
            "quality_assessment_summary",
            "test_plan",
            "test_results",
            "evidence",
            "risks",
            "",
            "non_modification_statement",
        ]
    )


class TestCase(BaseModel):
    """Definición de una prueba concreta dentro del plan QA."""

    model_config = ConfigDict(use_enum_values=True)

    test_id: str
    name: str
    description: str
    severity: TestSeverity = TestSeverity.MEDIUM
    input_artifacts: List[str] = Field(default_factory=list)
    expected_evidence: List[str] = Field(default_factory=list)


class TestPlan(BaseModel):
    """Plan de pruebas generado para una orden de evaluación."""

    model_config = ConfigDict(use_enum_values=True)

    plan_id: str
    activity_type: ActivityType
    execution_mode: ExecutionMode = ExecutionMode.READ_ONLY_QUALITY_ASSESSMENT
    tests: List[TestCase] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)


class Finding(BaseModel):
    """Hallazgo detectado durante la ejecución de pruebas QA."""

    finding_id: str
    severity: str
    description: str
    evidence: Dict[str, Any] = Field(default_factory=dict)
    impact: Optional[str] = None
    recommended_next_cycle_action: Optional[str] = None


class NonModificationStatement(BaseModel):
    """Declaración explícita de no modificación de artefactos de entrada."""

    artifacts_modified: bool = False
    message: str = "No input artifact has been modified during this assessment."


class AssessmentResult(BaseModel):
    """Resultado completo de una evaluación de calidad QA."""

    assessment_status: AssessmentStatus
    activity_type: ActivityType
    summary: Dict[str, Any] = Field(default_factory=dict)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    test_plan: Optional[TestPlan] = None
    test_results: List[Dict[str, Any]] = Field(default_factory=list)
    findings: List[Finding] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    non_modification_statement: NonModificationStatement = Field(
        default_factory=NonModificationStatement
    )
