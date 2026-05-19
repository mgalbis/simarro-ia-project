import re
from typing import Any, Dict, List, Optional

from app.schemas.quality_assessment import ActivityType


VALID_TESTS = {
    "nulls",
    "duplicates",
    "data_types",
    "outliers",
    "balance",
    "model_performance",
    "dataset_split",
}


TEST_KEYWORDS = {
    "nulls": [
        "nulos",
        "nulls",
        "missing",
        "vacíos",
        "vacios",
        "ausentes",
    ],
    "duplicates": [
        "duplicados",
        "duplicates",
        "repetidos",
    ],
    "data_types": [
        "tipos",
        "types",
        "data types",
        "tipo de dato",
        "tipos de dato",
    ],
    "outliers": [
        "outliers",
        "atípicos",
        "atipicos",
        "valores extremos",
    ],
    "balance": [
        "balance",
        "balanceo",
        "desbalanceo",
        "clases",
        "target",
        "objetivo",
    ],
    "model_performance": [
        "modelo",
        "desempeño",
        "rendimiento",
        "accuracy",
        "precision",
        "recall",
        "f1",
        "auc",
        "matriz de confusión",
        "matriz de confusion",
    ],
    "dataset_split": [
        "split",
        "partición",
        "particion",
        "particiones",
        "train",
        "training",
        "entrenamiento",
        "validación",
        "validacion",
        "test",
    ],
}


def interpret_user_intent(message: str) -> Dict[str, Any]:
    """
    Interpretación determinista preliminar del mensaje del usuario.

    No usa LLM real. Funciona mediante reglas simples para mantener trazabilidad
    en la versión mínima viable.
    """
    lower = message.lower()

    if _is_download_request(lower):
        return {
            "intent": "download_report",
            "activity_type": None,
            "requested_tests": [],
        }
        
    has_test_keywords = any(
        keyword in lower
        for tests in TEST_KEYWORDS.values()
        for keyword in tests
    )

    has_action_keywords = any(
        word in lower
        for word in [
            "analiza", "analizar", "revisa", "revisar",
            "valida", "validar", "comprueba", "comprobar",
            "ejecuta", "ejecutar", "verifica", "verificar",
            "prueba", "pruebas", "test", "tests",
            "dataset", "csv", "datos", "modelo",
            "umbral", "threshold", "límite", "limite",
            "punto de corte", "calidad", "quality",
        ]
    )

    has_valid_keywords = has_test_keywords or has_action_keywords

    if not has_valid_keywords:
        return {
            "intent": "unknown",
            "activity_type": None,
            "requested_tests": [],
            "target_column": None,
            "prediction_column": None,
            "split_column": None,
            "id_column": None,
            "threshold": None,
            "critical_columns": [],
            "excluded_columns": [],
        }
        
    activity_type = _detect_activity_type(lower)
    requested_tests = _detect_requested_tests(lower, activity_type)

    target_column = _extract_column_after_patterns(
        message,
        ["target", "objetivo", "variable objetivo", "variable real", "real"],
    )

    prediction_column = _extract_column_after_patterns(
        message,
        [
            "score",
            "probabilidad",
            "predicción",
            "prediccion",
            "prediction",
            "columna de predicción",
            "columna de prediccion",
        ],
    )

    split_column = _extract_column_after_patterns(
        message,
        ["split", "partición", "particion", "conjunto", "dataset", "subset"],
    )

    id_column = _extract_column_after_patterns(
        message,
        ["id", "identificador", "clave"],
    )

    threshold = _extract_threshold(message)

    return {
        "intent": "validate_dataset",
        "activity_type": activity_type,
        "requested_tests": requested_tests,
        "target_column": target_column,
        "prediction_column": prediction_column,
        "split_column": split_column,
        "id_column": id_column,
        "threshold": threshold,
        "critical_columns": [],
        "excluded_columns": [],
    }


def _is_download_request(lower: str) -> bool:
    return any(
        expression in lower
        for expression in [
            "descargar informe",
            "descarga informe",
            "download report",
            "bajar informe",
        ]
    )


def _detect_activity_type(lower: str) -> str:
    mentions_model_performance = (
        any(keyword in lower for keyword in TEST_KEYWORDS["model_performance"])
        or "matriz de confusión" in lower
        or "matriz de confusion" in lower
    )

    mentions_threshold = any(
        word in lower
        for word in [
            "umbral",
            "threshold",
            "límite",
            "limite",
            "punto de corte",
        ]
    )

    mentions_split = any(
        keyword in lower
        for keyword in TEST_KEYWORDS["dataset_split"]
    )

    if mentions_split:
        return ActivityType.DATASET_SPLIT_VALIDATION.value

    if mentions_model_performance:
        return ActivityType.MODEL_PERFORMANCE_EVALUATION.value

    if mentions_threshold:
        return ActivityType.THRESHOLD_QUALITY_EVALUATION.value

    return ActivityType.MINABLE_DATASET_VALIDATION.value


def _detect_requested_tests(lower: str, activity_type: str) -> List[str]:
    if activity_type == ActivityType.DATASET_SPLIT_VALIDATION.value:
        return ["dataset_split"]

    if activity_type in {
        ActivityType.MODEL_PERFORMANCE_EVALUATION.value,
        ActivityType.THRESHOLD_QUALITY_EVALUATION.value,
    }:
        return ["model_performance"]

    requested_tests = []

    for test_name, keywords in TEST_KEYWORDS.items():
        if test_name in {"model_performance", "dataset_split"}:
            continue

        if any(keyword in lower for keyword in keywords):
            requested_tests.append(test_name)

    if not requested_tests:
        requested_tests = [
            "nulls",
            "duplicates",
            "data_types",
            "outliers",
            "balance",
        ]

    return requested_tests


def _extract_column_after_patterns(message: str, patterns: List[str]) -> Optional[str]:
    """
    Extrae nombres de columnas con expresiones simples.

    Ejemplos soportados:
    - target es abandono
    - score es probabilidad_abandono
    - split es conjunto
    - id es cliente_id
    """
    for pattern in patterns:
        regexes = [
            rf"{re.escape(pattern)}\s+es\s+([A-Za-z_][A-Za-z0-9_]*)",
            rf"{re.escape(pattern)}\s*=\s*([A-Za-z_][A-Za-z0-9_]*)",
            rf"{re.escape(pattern)}\s*:\s*([A-Za-z_][A-Za-z0-9_]*)",
            rf"{re.escape(pattern)}\s+([A-Za-z_][A-Za-z0-9_]*)",
        ]

        for regex in regexes:
            match = re.search(regex, message, flags=re.IGNORECASE)
            if match:
                return match.group(1)

    return None


def _extract_threshold(message: str) -> Optional[float]:
    patterns = [
        r"umbral\s+(?:actual\s+)?(?:es\s+)?([0-9]+(?:[.,][0-9]+)?)",
        r"threshold\s+(?:is\s+)?([0-9]+(?:[.,][0-9]+)?)",
        r"punto de corte\s+(?:es\s+)?([0-9]+(?:[.,][0-9]+)?)",
    ]

    for pattern in patterns:
        match = re.search(pattern, message, flags=re.IGNORECASE)
        if match:
            value = match.group(1).replace(",", ".")
            try:
                return float(value)
            except ValueError:
                return None

    return None