# Decisión 001 — Stack tecnológico

## Estado

Aceptada.

## Contexto

El proyecto necesita integrar aprendizaje automático, trazabilidad, visualización, dashboards y un asistente agéntico de testing.

Debe ser reproducible, compatible con un proyecto académico y fácil de demostrar.

## Decisión

Se adopta el siguiente stack:

| Área | Tecnología |
|---|---|
| Lenguaje | Python |
| Notebooks | Jupyter |
| Modelos ML | scikit-learn / XGBoost |
| Tracking | MLflow |
| Versionado datos | lakeFS |
| Series temporales | InfluxDB |
| Dashboards | Grafana |
| UI | Streamlit |
| API demo | FastAPI |
| Testing generado | pytest + requests |
| Calidad código | black, flake8, pytest |
| Contenedores | Docker Compose |

## Justificación

- Python es el lenguaje principal del ecosistema IA/Big Data.
- scikit-learn permite construir modelos supervisados de forma rápida y explicable.
- MLflow cubre registro de parámetros, métricas, modelos y artefactos.
- lakeFS evita subir datasets grandes a Git y permite versionarlos.
- InfluxDB y Grafana encajan con datos de sensores y series temporales.
- Streamlit permite construir una UI funcional con poco tiempo.
- FastAPI permite crear una API demo clara para QABot.
- pytest + requests evita depender de herramientas específicas de testing.

## Consecuencias

Positivas:

- Stack open-source.
- Fácil de ejecutar localmente.
- Buena integración con Python.
- Suficiente para una demo completa.

Negativas:

- Docker Compose debe mantenerse correctamente.
- MLflow y lakeFS requieren configuración inicial.
- Streamlit no es la mejor opción para una UI compleja, pero sí para MVP.
