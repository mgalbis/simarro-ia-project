"""Análisis funcional de documentos conceptuales para mapear actividades QA."""

import html
import json
import re
import uuid
import zipfile
from io import BytesIO
from typing import Any, Dict, List
from xml.etree import ElementTree

SUPPORTED_EXTENSIONS = {".docx", ".ipynb", ".txt", ".md"}
SUPPORTED_ACTIVITY_CATALOG = {
    "MINABLE_DATASET_VALIDATION": {
        "label": "Validación de tabla minable",
        "tests": [
            "nulls",
            "duplicates",
            "data_types",
            "outliers",
            "balance",
            "skewness",
        ],
        "keywords": [
            "nulos",
            "duplicados",
            "outliers",
            "tipos",
            "balance",
            "tabla minable",
            "dataset",
            "calidad del dato",
        ],
    },
    "DATASET_SPLIT_VALIDATION": {
        "label": "Validación de particiones train/validation/test",
        "tests": ["dataset_split"],
        "keywords": [
            "split",
            "partición",
            "particion",
            "train",
            "training",
            "validation",
            "validación",
            "test",
        ],
    },
    "MODEL_PERFORMANCE_EVALUATION": {
        "label": "Evaluación de desempeño del modelo",
        "tests": ["model_performance"],
        "keywords": [
            "accuracy",
            "precision",
            "recall",
            "f1",
            "auc",
            "roc",
            "matriz de confusión",
            "modelo",
            "predicción",
            "score",
        ],
    },
    "THRESHOLD_QUALITY_EVALUATION": {
        "label": "Evaluación de umbral de clasificación",
        "tests": ["model_performance"],
        "keywords": ["umbral", "threshold", "punto de corte", "score", "probabilidad"],
    },
}
KNOWN_BUT_NOT_EXECUTABLE = {
    "FEATURE_SET_QUALITY_REVIEW": [
        "feature",
        "variable derivada",
        "variables explicativas",
        "feature set",
    ],
    "MODEL_CONFIGURATION_REVIEW": [
        "hiperparámetro",
        "hiperparametro",
        "configuración del modelo",
        "entrenamiento del modelo",
    ],
    "DASHBOARD_RESULT_VALIDATION": [
        "dashboard",
        "cuadro de mando",
        "power bi",
        "tableau",
        "métrica de negocio",
        "kpi",
    ],
}


def analyze_conceptual_document(filename: str, content: bytes) -> Dict[str, Any]:
    """Analiza un documento y devuelve actividades QA detectadas y contexto."""
    text = extract_text(filename, content)
    normalized = _normalize(text)

    entities = _extract_entities(text)
    business_rules = _extract_business_rules(text)
    datasets = _extract_datasets(text)
    metrics = _extract_metrics(text)
    executable = _detect_supported_activities(normalized)
    unsupported = _detect_unsupported_activities(normalized)

    if not executable and any(
        word in normalized
        for word in ["dataset", "dato", "calidad", "validación", "validacion"]
    ):
        executable.append(
            _activity_payload(
                "MINABLE_DATASET_VALIDATION",
                "Actividad inferida por mención genérica a dataset/calidad del dato.",
            )
        )

    suggested_tests = []
    for activity in executable:
        for test_name in activity.get("tests", []):
            if test_name not in suggested_tests:
                suggested_tests.append(test_name)

    analysis = {
        "analysis_id": f"CDA-{uuid.uuid4().hex[:8].upper()}",
        "activity_type": "CONCEPTUAL_DOCUMENT_ANALYSIS",
        "filename": filename,
        "summary": _summarize(text),
        "entities": entities,
        "business_rules": business_rules,
        "datasets": datasets,
        "models": _extract_models(text),
        "dashboards": _extract_dashboards(text),
        "metrics": metrics,
        "supported_activities": executable,
        "unsupported_activities": unsupported,
        "suggested_validation_tests": suggested_tests,
        "data_cycle": {
            "input": datasets
            or [
                "Documento conceptual aportado por el usuario",
                "Dataset pendiente de carga",
            ],
            "transformation": [
                "Interpretación funcional",
                "Mapeo a catálogo QA",
                "Generación de pruebas read-only",
            ],
            "validation": suggested_tests
            or ["Pendiente de selección de actividad ejecutable"],
            "output": [
                "Resultado en pantalla",
                "Informe PDF de ejecución",
                "Evidencias en panel de resultados",
            ],
        },
    }
    analysis["assistant_message"] = build_conceptual_analysis_message(analysis)
    return analysis


def extract_text(filename: str, content: bytes) -> str:
    """Extrae texto plano de documentos `.docx`, `.ipynb`, `.txt` o `.md`."""
    lower = filename.lower()
    if lower.endswith(".docx"):
        return _extract_docx_text(content)
    if lower.endswith(".ipynb"):
        return _extract_ipynb_text(content)
    if lower.endswith(".txt") or lower.endswith(".md"):
        return content.decode("utf-8", errors="ignore")
    raise ValueError(
        "Formato no soportado. Sube un documento .docx, .ipynb, .txt o .md."
    )


def build_conceptual_analysis_message(analysis: Dict[str, Any]) -> str:
    """Construye el mensaje HTML de resumen del análisis conceptual."""
    supported = analysis.get("supported_activities", [])
    unsupported = analysis.get("unsupported_activities", [])
    entities = analysis.get("entities", [])
    rules = analysis.get("business_rules", [])

    supported_items = (
        "".join(
            f"<li><b>{html.escape(item['activity_type'])}</b> — {html.escape(item['label'])}. Pruebas: <code>{html.escape(', '.join(item.get('tests', [])))}</code></li>"
            for item in supported
        )
        or "<li>No he identificado una actividad ejecutable con las reglas actuales.</li>"
    )

    unsupported_items = (
        "".join(
            f"<li><b>{html.escape(item['activity_type'])}</b> — detectada, pero todavía no está preparada para ejecución automática en esta versión.</li>"
            for item in unsupported
        )
        or "<li>No se han detectado actividades fuera del catálogo ejecutable actual.</li>"
    )

    entity_items = (
        "".join(f"<li>{html.escape(entity)}</li>" for entity in entities[:8])
        or "<li>No se han detectado entidades explícitas.</li>"
    )
    rule_items = (
        "".join(f"<li>{html.escape(rule)}</li>" for rule in rules[:8])
        or "<li>No se han detectado reglas textuales explícitas; se ha inferido el flujo por palabras clave.</li>"
    )

    return f"""
<div class="qa-result-card">
  <div class="qa-result-header">
    <span class="qa-strong">Documento conceptual analizado</span>
    <span class="qa-badge qa-badge-pass">CONCEPTUAL_DOCUMENT_ANALYSIS</span>
  </div>
  <div class="qa-note">
    He revisado el documento <b>{html.escape(analysis.get('filename', 'documento'))}</b> y he preparado un mapa funcional para el ciclo de pruebas.
  </div>
  <div class="qa-section-title">Actividades ejecutables detectadas</div>
  <ul>{supported_items}</ul>
  <div class="qa-section-title">Actividades en mejora continua</div>
  <ul>{unsupported_items}</ul>
  <div class="qa-section-title">Entidades funcionales detectadas</div>
  <ul>{entity_items}</ul>
  <div class="qa-section-title">Reglas de negocio candidatas</div>
  <ul>{rule_items}</ul>
  <div class="qa-note">
    Indica qué actividad quieres ejecutar. Después completarás los campos obligatorios del proyecto y subirás el dataset para lanzar las pruebas y generar el PDF.
  </div>
</div>
"""


def _extract_docx_text(content: bytes) -> str:
    with zipfile.ZipFile(BytesIO(content)) as docx:
        xml_content = docx.read("word/document.xml")
    root = ElementTree.fromstring(xml_content)
    namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    texts = [node.text for node in root.findall(".//w:t", namespace) if node.text]
    return "\n".join(texts)


def _extract_ipynb_text(content: bytes) -> str:
    notebook = json.loads(content.decode("utf-8", errors="ignore"))
    chunks = []
    for cell in notebook.get("cells", []):
        source = cell.get("source", [])
        if isinstance(source, list):
            chunks.append("".join(source))
        elif isinstance(source, str):
            chunks.append(source)
    return "\n".join(chunks)


def _normalize(text: str) -> str:
    return (text or "").lower()


def _summarize(text: str) -> str:
    clean = re.sub(r"\s+", " ", text or "").strip()
    return clean[:700] + ("..." if len(clean) > 700 else "")


def _extract_entities(text: str) -> List[str]:
    candidates = set()
    patterns = [
        r"(?:entidad|tabla|dataset|modelo|dashboard|métrica|metrica|kpi)\s+([A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9_ -]{3,60})",
        r"`([^`]{3,60})`",
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, text or "", flags=re.IGNORECASE):
            value = match.group(1).strip(" .:-\n\t")
            if value:
                candidates.add(value)
    return sorted(candidates)[:20]


def _extract_business_rules(text: str) -> List[str]:
    rules = []
    for raw in re.split(r"[\n\.;]", text or ""):
        sentence = raw.strip()
        lower = sentence.lower()
        if len(sentence) < 12:
            continue
        if any(
            marker in lower
            for marker in [
                "debe",
                "deberá",
                "obligatorio",
                "regla",
                "validar",
                "no puede",
                "umbral",
                "mínimo",
                "maximo",
                "máximo",
            ]
        ):
            rules.append(sentence[:240])
    return rules[:20]


def _extract_datasets(text: str) -> List[str]:
    datasets = []
    for match in re.finditer(
        r"(?:dataset|tabla|fichero|csv)\s+([A-Za-z0-9_ -]{3,60})",
        text or "",
        flags=re.IGNORECASE,
    ):
        datasets.append(match.group(0).strip())
    return list(dict.fromkeys(datasets))[:12]


def _extract_models(text: str) -> List[str]:
    models = []
    for match in re.finditer(
        r"(?:modelo|model)\s+([A-Za-z0-9_ -]{3,60})", text or "", flags=re.IGNORECASE
    ):
        models.append(match.group(0).strip())
    return list(dict.fromkeys(models))[:12]


def _extract_dashboards(text: str) -> List[str]:
    dashboards = []
    for match in re.finditer(
        r"(?:dashboard|cuadro de mando|informe)\s+([A-Za-z0-9_ -]{3,60})",
        text or "",
        flags=re.IGNORECASE,
    ):
        dashboards.append(match.group(0).strip())
    return list(dict.fromkeys(dashboards))[:12]


def _extract_metrics(text: str) -> List[str]:
    known = [
        "accuracy",
        "precision",
        "recall",
        "f1",
        "auc",
        "roc",
        "nulos",
        "duplicados",
        "outliers",
        "skewness",
        "balance",
        "umbral",
    ]
    normalized = _normalize(text)
    return [metric for metric in known if metric in normalized]


def _detect_supported_activities(normalized: str) -> List[Dict[str, Any]]:
    activities = []
    for activity_type, config in SUPPORTED_ACTIVITY_CATALOG.items():
        hits = [kw for kw in config["keywords"] if kw in normalized]
        if hits:
            payload = _activity_payload(
                activity_type, f"Coincidencias detectadas: {', '.join(hits[:6])}."
            )
            activities.append(payload)
    return activities


def _detect_unsupported_activities(normalized: str) -> List[Dict[str, str]]:
    unsupported = []
    for activity_type, keywords in KNOWN_BUT_NOT_EXECUTABLE.items():
        if any(keyword in normalized for keyword in keywords):
            unsupported.append(
                {
                    "activity_type": activity_type,
                    "reason": "Actividad reconocida pero no ejecutable en el catálogo actual.",
                }
            )
    return unsupported


def _activity_payload(activity_type: str, reason: str) -> Dict[str, Any]:
    config = SUPPORTED_ACTIVITY_CATALOG[activity_type]
    return {
        "activity_type": activity_type,
        "label": config["label"],
        "tests": config["tests"],
        "reason": reason,
    }
