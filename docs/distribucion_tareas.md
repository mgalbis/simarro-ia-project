# Distribución de tareas del equipo

## 1. Composición del equipo

| Persona | Nombre | Rol principal | Caso de uso principal |
|---|---|---|---|
| P1 | Pendiente | Coordinación técnica e integración | Transversal |
| P2 | Pendiente | MLOps | F |
| P3 | Pendiente | Datos y modelos | D |
| P4 | Pendiente | Visualización e ingesta | D |
| P5 | Pendiente | QABot y agentes | Caso nuevo |

## 2. Responsabilidades por persona

### P1 — Coordinación técnica e integración

Responsabilidades:

- Mantener la estructura del repositorio.
- Revisar ramas y merges.
- Coordinar integración entre módulos.
- Mantener `README.md` actualizado.
- Validar que la demo final arranca desde cero.
- Preparar el checklist final de entrega.

Complejidad estimada: alta.

Justificación:

La integración afecta a todos los módulos y determina que la solución funcione de extremo a extremo.

### P2 — Caso F: MLOps

Responsabilidades:

- Desplegar MLflow.
- Configurar lakeFS.
- Crear convenciones de experimentos.
- Implementar utilidades de logging.
- Asegurar trazabilidad dataset-modelo-código.
- Documentar el runbook MLOps.

Complejidad estimada: alta.

Justificación:

MLflow y lakeFS son componentes transversales. Un error aquí impide justificar resultados y reproducibilidad.

### P3 — Caso D: datos y modelos

Responsabilidades:

- Descargar y preparar UCI Occupancy.
- Crear EDA.
- Auditar calidad del dataset.
- Entrenar baseline y modelos supervisados.
- Comparar métricas.
- Seleccionar el modelo ganador.
- Documentar interpretabilidad.

Complejidad estimada: alta.

Justificación:

Esta parte contiene la aplicación principal de aprendizaje automático y requiere validación rigurosa.

### P4 — Caso D: visualización, IAQ e integración

Responsabilidades:

- Crear índice IAQ.
- Escribir datos y predicciones en InfluxDB.
- Crear dashboards de Grafana.
- Configurar alertas.
- Preparar capturas y demo visual.

Complejidad estimada: media-alta.

Justificación:

Convierte los modelos en una solución comprensible y demostrable para usuarios no técnicos.

### P5 — QABot: agentes especialistas de testing

Responsabilidades:

- Diseñar arquitectura de agentes.
- Crear router de intención.
- Implementar agentes de análisis, diseño, API, datos, seguridad, rendimiento y evaluación.
- Generar tests pytest.
- Ejecutar pruebas contra API demo.
- Generar informe final.
- Registrar métricas en MLflow.

Complejidad estimada: alta.

Justificación:

Es el caso nuevo y combina agentes, generación de pruebas, ejecución automática y evaluación de resultados.

## 3. Distribución por bloques

| Bloque | Responsable principal | Apoyo | Complejidad |
|---|---|---|---|
| Arquitectura | P1 | Todos | Alta |
| Repositorio y CI básica | P1 | P2 | Media |
| MLflow | P2 | P1 | Alta |
| lakeFS | P2 | P3 | Alta |
| Preparación dataset D | P3 | P4 | Media |
| Modelos ocupación | P3 | P2 | Alta |
| IAQ | P4 | P3 | Media |
| InfluxDB/Grafana | P4 | P1 | Media-alta |
| QABot router/agentes | P5 | P1 | Alta |
| API demo | P5 | P1 | Media |
| Evaluación QABot | P5 | P2 | Alta |
| Documentación final | Todos | P1 coordina | Media |
| Vídeo demo | Todos | P1 coordina | Media |

## 4. Evidencias esperadas por persona

| Persona | Evidencias mínimas |
|---|---|
| P1 | Pull requests, README, arquitectura, integración final, checklist. |
| P2 | Runs MLflow, tags lakeFS, scripts MLOps, runbook MLOps. |
| P3 | Notebooks EDA/modelos, métricas, modelo ganador, interpretación. |
| P4 | IAQ, InfluxDB, Grafana, alertas, capturas demo. |
| P5 | Código QABot, agentes, tests generados, informe, evaluación. |

## 5. Contribución al benchmark Big Data

Aunque este equipo no sea responsable principal del benchmark Spark vs pandas, cada integrante debe conocer:

- Qué se compara.
- Por qué Spark es útil con datos grandes.
- Qué limitaciones tiene pandas.
- Qué conclusiones generales se obtuvieron.

Responsable de preparar una síntesis interna: P1.

## 6. Criterio de reparto equilibrado

El reparto se considera equilibrado si:

- Cada persona tiene al menos una responsabilidad crítica.
- Cada persona deja evidencias en Git.
- Cada persona puede explicar su parte en la defensa.
- Cada persona entiende la arquitectura global.
