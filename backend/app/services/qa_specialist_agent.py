from app.schemas.quality_assessment import (
    AssessmentResult,
    AssessmentStatus,
    Finding,
    TestCase,
    TestPlan,
    TestSeverity,
)
from app.services.rules.qa_balance import check_balance
from app.services.rules.qa_data_types import check_data_types
from app.services.rules.qa_duplicates import check_duplicates
from app.services.rules.qa_model_performance import check_model_performance
from app.services.rules.qa_nulls import check_nulls
from app.services.rules.qa_outliers import check_outliers_iqr
from app.services.rules.qa_split_validation import check_dataset_split


class QASpecialistAgent:
    """
    Agente especialista de verificación QA.

    Ejecuta pruebas read-only sobre los artefactos recibidos.
    No modifica datasets, modelos, umbrales ni otros artefactos de entrada.
    """

    AVAILABLE_TESTS = {
        "nulls": check_nulls,
        "duplicates": check_duplicates,
        "data_types": check_data_types,
        "outliers": check_outliers_iqr,
        "balance": check_balance,
        "model_performance": check_model_performance,
        "dataset_split": check_dataset_split,
    }

    TEST_DESCRIPTIONS = {
        "nulls": (
            "QA-DATA-001",
            "Análisis de valores nulos",
            "Detecta columnas con valores ausentes.",
        ),
        "duplicates": (
            "QA-DATA-002",
            "Detección de duplicados",
            "Identifica filas repetidas en el dataset.",
        ),
        "data_types": (
            "QA-DATA-003",
            "Chequeo de tipos de datos",
            "Resume y revisa la estructura de tipos de las columnas.",
        ),
        "outliers": (
            "QA-DATA-004",
            "Detección de outliers",
            "Identifica valores atípicos en variables numéricas mediante IQR.",
        ),
        "balance": (
            "QA-DATA-005",
            "Balanceo de clases",
            "Revisa la distribución de la variable objetivo si está disponible.",
        ),
        "model_performance": (
            "QA-MODEL-001",
            "Evaluación de desempeño binario",
            "Calcula métricas de clasificación binaria a partir de target y predicción o score.",
        ),
        "dataset_split": (
            "QA-SPLIT-001",
            "Validación de particiones",
            "Revisa particiones train/validation/test representadas mediante una columna de split.",
        ),
    }

    STATUS_PRIORITY = {
        "ERROR": 4,
        "FAIL": 3,
        "WARN": 2,
        "PASS": 1,
    }

    def build_test_plan(self, order) -> TestPlan:
        requested_tests = order.parameters.get("requested_tests", [])
        tests = []

        for test_name in requested_tests:
            if test_name not in self.AVAILABLE_TESTS:
                continue

            test_id, name, description = self.TEST_DESCRIPTIONS.get(
                test_name,
                (
                    f"QA-GEN-{len(tests) + 1:03d}",
                    test_name,
                    "Prueba QA registrada en el catálogo.",
                ),
            )

            severity = (
                TestSeverity.HIGH
                if test_name in {"model_performance", "dataset_split"}
                else TestSeverity.MEDIUM
            )

            tests.append(
                TestCase(
                    test_id=test_id,
                    name=name,
                    description=description,
                    severity=severity,
                    input_artifacts=list(order.artifacts.keys()),
                    expected_evidence=[
                        "status",
                        "metrics",
                        "warnings",
                        "recommendations",
                    ],
                )
            )

        return TestPlan(
            plan_id=f"PLAN-{order.request_id}",
            activity_type=order.activity_type,
            tests=tests,
            notes=[
                "Plan generado en modo read-only a partir de QualityAssessmentOrder."
            ],
        )

    def run_test(self, test_name: str, df, parameters: dict | None = None):
        parameters = parameters or {}

        if test_name not in self.AVAILABLE_TESTS:
            return None

        test_fn = self.AVAILABLE_TESTS[test_name]

        if test_name == "balance":
            target_column = parameters.get("target_column")

            if not target_column:
                return {
                    "name": "balance",
                    "status": "WARN",
                    "summary": "No se ha evaluado el balanceo porque no se ha indicado variable objetivo",
                    "metrics": {
                        "rule": "QA-BALANCE",
                        "status": "WARN",
                        "metrics": {},
                        "warnings": [
                            {
                                "issue": "Missing target column for balance analysis."
                            }
                        ],
                        "recommendations": [
                            "Indicar la variable objetivo si se desea revisar el balanceo de clases. Ejemplo: target es abandono."
                        ],
                    },
                    "recommendations": [
                        "Indicar la variable objetivo si se desea revisar el balanceo de clases. Ejemplo: target es abandono."
                    ],
                }

            result = test_fn(
                df,
                target_column=target_column,
            )

        elif test_name == "model_performance":
            result = test_fn(
                df,
                target_column=parameters.get("target_column"),
                prediction_column=parameters.get("prediction_column"),
                threshold=parameters.get("threshold", 0.5),
                positive_class=parameters.get("positive_class", 1),
            )

        elif test_name == "dataset_split":
            result = test_fn(
                df,
                split_column=parameters.get("split_column"),
                target_column=parameters.get("target_column"),
                id_column=parameters.get("id_column"),
            )

        else:
            result = test_fn(df)

        summary = self._build_summary(test_name, result)

        return {
            "name": test_name,
            "status": result.get("status", "ERROR"),
            "summary": summary,
            "metrics": result,
            "recommendations": result.get("recommendations", []),
        }

    def run_assessment(self, order, df):
        parameters = order.parameters or {}
        test_plan = self.build_test_plan(order)

        requested_tests = [
            self._test_name_from_case(
                test_case.name,
                parameters.get("requested_tests", []),
            )
            for test_case in test_plan.tests
        ]

        requested_tests = [
            name
            for name in requested_tests
            if name
        ]

        test_results = []

        for test_name in requested_tests:
            result = self.run_test(test_name, df, parameters)

            if result:
                test_results.append(result)

        max_priority = max(
            [
                self.STATUS_PRIORITY.get(item.get("status", "PASS"), 1)
                for item in test_results
            ],
            default=1,
        )

        status = {
            4: AssessmentStatus.ERROR,
            3: AssessmentStatus.FAIL,
            2: AssessmentStatus.WARN,
            1: AssessmentStatus.PASS,
        }.get(max_priority, AssessmentStatus.PASS)

        findings = self._build_findings(test_results)

        recommendations = []

        for item in test_results:
            recommendations.extend(item.get("recommendations", []))

        return AssessmentResult(
            assessment_status=status,
            activity_type=order.activity_type,
            summary={
                "overall_result": self._build_overall_result(status),
                "planned_checks": len(test_plan.tests),
                "executed_checks": len(test_results),
                "passed_checks": sum(
                    1 for r in test_results if r.get("status") == "PASS"
                ),
                "failed_checks": sum(
                    1 for r in test_results if r.get("status") == "FAIL"
                ),
                "warnings": sum(
                    1 for r in test_results if r.get("status") == "WARN"
                ),
                "errors": sum(
                    1 for r in test_results if r.get("status") == "ERROR"
                ),
            },
            test_plan=test_plan,
            test_results=test_results,
            findings=findings,
            recommendations=list(dict.fromkeys(recommendations)),
        )

    def _test_name_from_case(
        self,
        case_name: str,
        requested_tests: list[str],
    ) -> str | None:
        for test_name in requested_tests:
            description = self.TEST_DESCRIPTIONS.get(test_name)

            if description and description[1] == case_name:
                return test_name

        return None

    def _build_summary(self, test_name: str, result: dict) -> str:
        if test_name == "nulls":
            return (
                f"{len(result.get('critical', []))} críticos, "
                f"{len(result.get('warnings', []))} avisos"
            )

        if test_name == "duplicates":
            duplicate_count = result.get("duplicated_count", 0)
            duplicate_ratio = result.get("duplicate_ratio", 0)
            return (
                f"{duplicate_count} duplicados "
                f"({round(duplicate_ratio * 100, 2)}%)"
            )

        if test_name == "data_types":
            return (
                f"{len(result.get('mismatches', []))} columnas con tipos inesperados"
            )

        if test_name == "outliers":
            total = (
                len(result.get("critical", []))
                + len(result.get("warnings", []))
            )
            return f"{total} columnas con outliers detectados"

        if test_name == "balance":
            ratio = (
                result.get("metrics", {})
                .get("majority_class_ratio", 0)
            )
            return f"Clase mayoritaria: {round(ratio * 100, 2)}%"

        if test_name == "model_performance":
            metrics = result.get("metrics", {})

            if result.get("status") == "ERROR":
                return (
                    "No se puede evaluar el desempeño con la información proporcionada"
                )

            return (
                f"accuracy={metrics.get('accuracy')}, "
                f"precision={metrics.get('precision')}, "
                f"recall={metrics.get('recall')}, "
                f"f1={metrics.get('f1')}"
            )

        if test_name == "dataset_split":
            metrics = result.get("metrics", {})

            if result.get("status") == "ERROR":
                return (
                    "No se puede validar la partición con la información proporcionada"
                )

            return f"particiones={metrics.get('split_counts', {})}"

        return ""

    def _build_findings(self, test_results):
        findings = []
        counter = 1

        for result in test_results:
            if result.get("status") == "PASS":
                continue

            test_name = result.get("name", "unknown_test")
            metrics = result.get("metrics", {})
            evidence = metrics.get("metrics", metrics)

            severity = {
                "ERROR": "critical",
                "FAIL": "high",
                "WARN": "medium",
            }.get(result.get("status"), "low")

            recommendations = result.get("recommendations", [])

            findings.append(
                Finding(
                    finding_id=f"F-{counter:03d}",
                    severity=severity,
                    description=self._build_finding_description(
                        test_name=test_name,
                        result=result,
                        metrics=metrics,
                    ),
                    evidence=evidence,
                    impact=self._build_finding_impact(test_name),
                    recommended_next_cycle_action=(
                        recommendations[0]
                        if recommendations
                        else "Revisar el artefacto en el siguiente ciclo de desarrollo."
                    ),
                )
            )

            counter += 1

        return findings
    
    def _build_finding_description(self, test_name: str, result: dict, metrics: dict) -> str:
        if test_name == "nulls":
            critical = metrics.get("critical", [])
            warnings = metrics.get("warnings", [])

            affected = critical or warnings
            affected_text = ", ".join(
                f"{item.get('column')} ({round(item.get('null_ratio', 0) * 100, 2)}%)"
                for item in affected
            )

            if critical:
                return (
                    f"Nulos: {len(critical)} columnas con valores nulos críticos: "
                    f"{affected_text}."
                )

            return (
                f"Nulos: {len(warnings)} columnas con valores nulos a revisar: "
                f"{affected_text}."
            )

        if test_name == "duplicates":
            duplicate_count = (
                metrics.get("duplicated_count")
                or metrics.get("duplicate_count")
                or metrics.get("duplicated_rows")
                or 0
            )
            duplicate_ratio = metrics.get("duplicate_ratio", 0)

            return (
                f"Duplicados: se han detectado {duplicate_count} filas duplicadas "
                f"({round(duplicate_ratio * 100, 2)}% del dataset)."
            )

        if test_name == "outliers":
            critical = metrics.get("critical", [])
            warnings = metrics.get("warnings", [])
            affected = critical or warnings

            affected_text = ", ".join(
                f"{item.get('column')} ({round(item.get('outlier_ratio', 0) * 100, 2)}%)"
                for item in affected
            )

            return (
                f"Outliers: se han detectado valores atípicos en "
                f"{len(affected)} columnas: {affected_text}."
            )

        if test_name == "balance":
            inner = metrics.get("metrics", {})
            target = inner.get("target_column", "variable objetivo")
            ratio = inner.get("majority_class_ratio", 0)

            return (
                f"Balanceo: la clase mayoritaria en '{target}' representa "
                f"el {round(ratio * 100, 2)}% de los registros."
            )

        if test_name == "model_performance":
            inner = metrics.get("metrics", {})

            return (
                "Evaluación de modelo: "
                f"accuracy={inner.get('accuracy')}, "
                f"precision={inner.get('precision')}, "
                f"recall={inner.get('recall')}, "
                f"f1={inner.get('f1')}."
            )

        if test_name == "dataset_split":
            inner = metrics.get("metrics", {})

            return (
                "Validación de particiones: "
                f"particiones={inner.get('split_counts', {})}, "
                f"particiones ausentes={inner.get('missing_splits', [])}, "
                f"IDs repetidos entre particiones={inner.get('duplicate_ids_across_splits')}."
            )

        return result.get("summary", "Hallazgo de calidad detectado.")

    def _build_finding_impact(self, test_name: str) -> str:
        impacts = {
            "nulls": (
                "Los valores nulos pueden afectar a la fiabilidad del análisis, "
                "al entrenamiento del modelo o a la interpretación de los resultados."
            ),
            "duplicates": (
                "Los registros duplicados pueden sesgar métricas, distribuciones y modelos "
                "si no se justifican funcionalmente."
            ),
            "outliers": (
                "Los valores atípicos pueden distorsionar estadísticas, entrenamiento de modelos "
                "y umbrales de decisión."
            ),
            "balance": (
                "Un desbalanceo acusado puede afectar a la interpretación de métricas y al comportamiento del modelo."
            ),
            "model_performance": (
                "Un desempeño insuficiente puede comprometer la utilidad del modelo en el caso de uso previsto."
            ),
            "dataset_split": (
                "Una partición incorrecta puede invalidar la evaluación del modelo o introducir fuga de información."
            ),
        }

        return impacts.get(
            test_name,
            "Puede comprometer la calidad, trazabilidad o interpretación del artefacto evaluado.",
        )

    def _build_overall_result(self, status: AssessmentStatus) -> str:
        if status == AssessmentStatus.PASS:
            return "No se han detectado incumplimientos en las pruebas ejecutadas."

        if status == AssessmentStatus.WARN:
            return (
                "Se han detectado advertencias que deberían revisarse en el siguiente ciclo."
            )

        if status == AssessmentStatus.FAIL:
            return "Se han detectado incumplimientos relevantes de calidad."

        return "La evaluación no se ha podido completar correctamente."