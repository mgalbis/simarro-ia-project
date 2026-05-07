# Documentación del proyecto `simarro-ia-project`

Repositorio del proyecto final del Curso de Especialización en Inteligencia Artificial y Big Data del IES Dr. Lluís Simarro.

El proyecto integra tres líneas de trabajo:

1. **Caso F — MLOps y ciclo de vida de modelos**  
   Registro de experimentos con MLflow, versionado de datasets con lakeFS y entorno reproducible.

2. **Caso D — Calidad del aire, confort interior y ocupación**  
   Análisis de variables ambientales, predicción de ocupación e índice IAQ con visualización en Grafana.

3. **Caso nuevo — QABot**  
   Asistente agéntico para generación, ejecución y evaluación de pruebas de calidad software a partir de requisitos o especificaciones API. Las pruebas no usan Wakamiti.

## Índice de documentación

| Documento | Descripción |
|---|---|
| `arquitectura.md` | Arquitectura funcional y técnica del sistema. |
| `runbook.md` | Instalación, configuración, arranque, parada y troubleshooting. |
| `runbook_mlops.md` | Uso específico de MLflow y lakeFS. |
| `distribucion_tareas.md` | Reparto de responsabilidades dentro del equipo. |
| `data_dictionary_occupancy.md` | Diccionario de datos del caso de ocupación. |
| `mlflow_conventions.md` | Convenciones de experimentos, métricas y artefactos. |
| `qabot_scope.md` | Alcance funcional del asistente de testing. |
| `qabot_architecture.md` | Arquitectura de agentes de QABot. |
| `planificacion.md` | Planning de tres semanas. |
| `video_script.md` | Guion recomendado para el vídeo de demostración. |
| `checklist_entrega.md` | Lista final de comprobación antes de entregar. |
| `decisions/` | Decisiones técnicas justificadas. |

## Criterios de calidad documental

- Todo comando debe ser copiable y ejecutable.
- Cada notebook debe tener explicación en Markdown, outputs visibles y referencia a los runs de MLflow.
- Los datasets y modelos grandes no deben subirse al repositorio Git.
- Los datasets se versionan en lakeFS.
- Los modelos y artefactos de entrenamiento se registran en MLflow.
- Las credenciales se documentan mediante `.env.example`, nunca mediante `.env` real.
