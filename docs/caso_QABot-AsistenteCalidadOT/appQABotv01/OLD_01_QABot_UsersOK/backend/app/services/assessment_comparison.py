from typing import Any, Dict, List, Optional


NUMERIC_METRIC_KEYS = {
    "accuracy",
    "precision",
    "recall",
    "f1",
    "roc_auc",
}


FAILURE_STATUSES = {"FAIL", "ERROR"}
WARNING_STATUSES = {"WARN", "WARNING"}


def _assessment(report: Dict[str, Any]) -> Dict[str, Any]:
    return report.get("assessment_result", {}) or {}


def _test_results_by_name(report: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    results = report.get("results") or _assessment(report).get("test_results", [])
    return {
        item.get("name"): item
        for item in results
        if item.get("name")
    }


def _summary_counts(report: Dict[str, Any]) -> Dict[str, Any]:
    return _assessment(report).get("summary", {}) or {}


def _find_model_metrics(report: Dict[str, Any]) -> Dict[str, Any]:
    for item in _test_results_by_name(report).values():
        if item.get("name") == "model_performance":
            return item.get("metrics", {}).get("metrics", {})
    return {}


def _normalise_status(status: Any) -> str:
    return str(status or "UNKNOWN").upper()


def build_assessment_comparison(
    previous_report: Optional[Dict[str, Any]],
    current_report: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    if not previous_report:
        return None

    previous_activity = previous_report.get("activity_type")
    current_activity = current_report.get("activity_type")

    if previous_activity != current_activity:
        return {
            "comparable": False,
            "reason": "La evaluación anterior corresponde a una actividad QA distinta.",
            "previous_activity_type": previous_activity,
            "current_activity_type": current_activity,
        }

    previous_summary = _summary_counts(previous_report)
    current_summary = _summary_counts(current_report)

    count_deltas = _build_count_deltas(previous_summary, current_summary)

    previous_results = _test_results_by_name(previous_report)
    current_results = _test_results_by_name(current_report)

    test_transitions = _build_test_transitions(previous_results, current_results)

    metric_deltas = _build_metric_deltas(previous_report, current_report)

    return {
        "comparable": True,
        "previous_execution_id": previous_report.get("execution_id"),
        "current_execution_id": current_report.get("execution_id"),
        "activity_type": current_activity,
        "status_transition": {
            "previous": previous_report.get("global_status"),
            "current": current_report.get("global_status"),
        },
        "count_deltas": count_deltas,
        "test_transitions": test_transitions,
        "metric_deltas": metric_deltas,
        "interpretation": _build_interpretation(
            count_deltas=count_deltas,
            test_transitions=test_transitions,
            metric_deltas=metric_deltas,
        ),
    }


def _build_count_deltas(
    previous_summary: Dict[str, Any],
    current_summary: Dict[str, Any],
) -> Dict[str, Any]:
    count_deltas = {}

    for key in [
        "passed_checks",
        "failed_checks",
        "warnings",
        "errors",
    ]:
        previous_value = previous_summary.get(key)
        current_value = current_summary.get(key)

        count_deltas[key] = {
            "previous": previous_value,
            "current": current_value,
            "delta": (
                current_value - previous_value
                if previous_value is not None and current_value is not None
                else None
            ),
        }

    return count_deltas


def _build_test_transitions(
    previous_results: Dict[str, Dict[str, Any]],
    current_results: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    all_test_names = sorted(set(previous_results) | set(current_results))

    fixed = []
    new_failures = []
    persistent_failures = []
    persistent_warnings = []
    unchanged_passes = []
    changed = []

    details = []

    for test_name in all_test_names:
        previous_item = previous_results.get(test_name, {})
        current_item = current_results.get(test_name, {})

        previous_status = _normalise_status(previous_item.get("status"))
        current_status = _normalise_status(current_item.get("status"))

        transition = {
            "test_name": test_name,
            "previous_status": previous_status,
            "current_status": current_status,
            "previous_summary": previous_item.get("summary"),
            "current_summary": current_item.get("summary"),
        }

        details.append(transition)

        previous_failed = previous_status in FAILURE_STATUSES
        current_failed = current_status in FAILURE_STATUSES
        previous_warning = previous_status in WARNING_STATUSES
        current_warning = current_status in WARNING_STATUSES

        if previous_failed and current_status == "PASS":
            fixed.append(transition)

        elif previous_status == "PASS" and current_failed:
            new_failures.append(transition)

        elif previous_failed and current_failed:
            persistent_failures.append(transition)

        elif previous_warning and current_warning:
            persistent_warnings.append(transition)

        elif previous_status == "PASS" and current_status == "PASS":
            unchanged_passes.append(transition)

        elif previous_status != current_status:
            changed.append(transition)

    return {
        "fixed": fixed,
        "new_failures": new_failures,
        "persistent_failures": persistent_failures,
        "persistent_warnings": persistent_warnings,
        "unchanged_passes": unchanged_passes,
        "changed": changed,
        "details": details,
    }


def _build_metric_deltas(
    previous_report: Dict[str, Any],
    current_report: Dict[str, Any],
) -> List[Dict[str, Any]]:
    metric_deltas = []

    previous_metrics = _find_model_metrics(previous_report)
    current_metrics = _find_model_metrics(current_report)

    for key in NUMERIC_METRIC_KEYS:
        previous_value = previous_metrics.get(key)
        current_value = current_metrics.get(key)

        if isinstance(previous_value, (int, float)) and isinstance(current_value, (int, float)):
            metric_deltas.append(
                {
                    "metric": key,
                    "previous": previous_value,
                    "current": current_value,
                    "delta": round(current_value - previous_value, 4),
                }
            )

    return metric_deltas

def _count_value(
    count_deltas: Dict[str, Any],
    key: str,
    field: str,
) -> int:
    value = count_deltas.get(key, {}).get(field)

    if isinstance(value, int):
        return value

    if isinstance(value, float):
        return int(value)

    return 0

def _build_interpretation(
    count_deltas: Dict[str, Any],
    test_transitions: Dict[str, Any],
    metric_deltas: List[Dict[str, Any]],
) -> str:
    previous_passed = _count_value(count_deltas, "passed_checks", "previous")
    current_passed = _count_value(count_deltas, "passed_checks", "current")

    previous_failed = _count_value(count_deltas, "failed_checks", "previous")
    current_failed = _count_value(count_deltas, "failed_checks", "current")

    previous_warnings = _count_value(count_deltas, "warnings", "previous")
    current_warnings = _count_value(count_deltas, "warnings", "current")

    previous_errors = _count_value(count_deltas, "errors", "previous")
    current_errors = _count_value(count_deltas, "errors", "current")

    previous_total = (
        previous_passed
        + previous_failed
        + previous_warnings
        + previous_errors
    )

    current_total = (
        current_passed
        + current_failed
        + current_warnings
        + current_errors
    )

    previous_all_success = (
        previous_total > 0
        and previous_passed == previous_total
        and previous_failed == 0
        and previous_warnings == 0
        and previous_errors == 0
    )

    current_all_success = (
        current_total > 0
        and current_passed == current_total
        and current_failed == 0
        and current_warnings == 0
        and current_errors == 0
    )

    previous_all_failed = (
        previous_total > 0
        and previous_passed == 0
        and (previous_failed + previous_errors) == previous_total
    )

    current_all_failed = (
        current_total > 0
        and current_passed == 0
        and (current_failed + current_errors) == current_total
    )

    fragments = []

    fixed = test_transitions.get("fixed", [])
    new_failures = test_transitions.get("new_failures", [])
    persistent_failures = test_transitions.get("persistent_failures", [])
    persistent_warnings = test_transitions.get("persistent_warnings", [])

    if current_all_success and previous_all_success:
        fragments.append("se mantiene que todas las pruebas pasan con éxito")

    elif current_all_success and not previous_all_success:
        fragments.append("en esta versión todas las pruebas son exitosas")

    elif current_all_failed and previous_all_failed:
        fragments.append("siguen fallando todas las pruebas")

    elif current_all_failed and not previous_all_failed:
        fragments.append("fallan todas las pruebas en esta versión")

    else:
        if fixed:
            fragments.append(
                "defectos corregidos: "
                + ", ".join(item["test_name"] for item in fixed)
            )

        if new_failures:
            fragments.append(
                "nuevos defectos detectados: "
                + ", ".join(item["test_name"] for item in new_failures)
            )

        if persistent_failures:
            fragments.append(
                "defectos persistentes: "
                + ", ".join(item["test_name"] for item in persistent_failures)
            )

        if persistent_warnings:
            fragments.append(
                "advertencias persistentes: "
                + ", ".join(item["test_name"] for item in persistent_warnings)
            )

        failed_delta = count_deltas.get("failed_checks", {}).get("delta")

        if failed_delta is not None:
            if failed_delta < 0:
                fragments.append("se reduce el número total de pruebas fallidas")
            elif failed_delta > 0:
                fragments.append("aumenta el número total de pruebas fallidas")
            else:
                if current_failed == 0:
                    fragments.append("no hay pruebas fallidas en esta versión")
                else:
                    fragments.append("se mantiene el número total de pruebas fallidas")

    if metric_deltas:
        improved = [
            m["metric"]
            for m in metric_deltas
            if m["delta"] > 0
        ]
        worsened = [
            m["metric"]
            for m in metric_deltas
            if m["delta"] < 0
        ]

        if improved:
            fragments.append(
                "mejoran métricas: " + ", ".join(sorted(improved))
            )

        if worsened:
            fragments.append(
                "empeoran métricas: " + ", ".join(sorted(worsened))
            )

    return (
        "; ".join(fragments)
        if fragments
        else "No hay cambios comparables relevantes."
    )