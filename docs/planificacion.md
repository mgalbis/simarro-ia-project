# Planificación de 3 semanas

## 1. Resumen

Duración: 3 semanas.  
Equipo: 5 personas.  
Repositorio: `simarro-ia-project`.

Líneas de trabajo:

- Caso F: MLOps.
- Caso D: calidad del aire, confort y ocupación.
- Caso nuevo: QABot, agentes especialistas de testing.

## 2. Semana 1 — Base funcional

Objetivo:

Tener repositorio, entorno, datasets y primer baseline.

| Día | Tarea | Responsable | Resultado |
|---|---|---|---|
| 1 | Crear repositorio, ramas, issues y estructura | P1 | Repo inicial |
| 1 | Crear `.gitignore`, README y licencia MIT | P1 | Base documental |
| 1-2 | Definir arquitectura | P1 + todos | `docs/arquitectura.md` |
| 2 | Configurar Docker Compose base | P1 + P2 | Servicios definidos |
| 2-3 | Levantar MLflow | P2 | MLflow operativo |
| 2-3 | Levantar lakeFS | P2 | lakeFS operativo |
| 3 | Descargar dataset UCI Occupancy | P3 | Datos raw |
| 3-4 | Preparar datos y validarlos | P3 | Datos procesados |
| 4 | Crear baseline ocupación | P3 | Primer run MLflow |
| 4-5 | Diseñar alcance QABot | P5 | `qabot_scope.md` |
| 5 | Crear API demo inicial | P5 | API ejecutable |
| 5 | Revisión semanal | Todos | Demo interna 1 |

## 3. Semana 2 — Desarrollo principal

Objetivo:

Entrenar modelos, construir agentes y crear dashboards.

| Día | Tarea | Responsable | Resultado |
|---|---|---|---|
| 6 | Logistic Regression y métricas | P3 | Run MLflow |
| 6 | Random Forest y métricas | P3 | Run MLflow |
| 7 | XGBoost/SVM | P3 | Comparativa modelos |
| 7 | Integrar tags lakeFS en MLflow | P2 | Trazabilidad |
| 7-8 | Crear índice IAQ | P4 | Módulo IAQ |
| 8 | Escribir datos en InfluxDB | P4 | Series temporales |
| 8-9 | Crear dashboard Grafana | P4 | Paneles visuales |
| 8 | Implementar router QABot | P5 | Router funcional |
| 8-9 | Implementar agentes QABot | P5 | Agentes iniciales |
| 9 | Generar tests pytest | P5 | Tests generados |
| 9-10 | Ejecutar tests y parsear resultados | P5 | Executor funcional |
| 10 | Revisión semanal | Todos | Demo interna 2 |

## 4. Semana 3 — Integración y entrega

Objetivo:

Cerrar integración, documentación, vídeo y revisión final.

| Día | Tarea | Responsable | Resultado |
|---|---|---|---|
| 11 | Integrar UI Streamlit | P1 + P5 | Demo única |
| 11 | Refinar Grafana | P4 | Dashboard final |
| 11-12 | Evaluar QABot con golden set | P5 | Notebook evaluación |
| 12 | Seleccionar modelo ganador | P3 | Modelo final |
| 12 | Revisar MLflow/lakeFS | P2 | Evidencias MLOps |
| 13 | Completar runbook | P1 + P2 | `runbook.md` |
| 13 | Completar distribución tareas | Todos | `distribucion_tareas.md` |
| 13-14 | Limpiar notebooks y outputs | P3 + P4 + P5 | Notebooks finales |
| 14 | Preparar guion del vídeo | Todos | `video_script.md` |
| 14-15 | Grabar y editar vídeo | Todos | MP4 final |
| 15 | Checklist final y tag release | P1 | `v1.0-final` |

## 5. Prioridad de tareas

### Imprescindible

1. Repositorio reproducible.
2. MLflow funcionando.
3. lakeFS funcionando.
4. Dataset D procesado.
5. Baseline y modelos D.
6. Dashboard Grafana.
7. QABot generando y ejecutando pruebas.
8. Runbook.
9. Vídeo.

### Ampliación

1. Evidently para drift.
2. In-Gauge además de UCI.
3. Agente de seguridad ampliado.
4. Agente de rendimiento.
5. CI con GitHub Actions.
6. Reporte HTML avanzado.

## 6. Revisión semanal

Cada revisión debe demostrar algo ejecutable:

| Semana | Demo mínima |
|---|---|
| Semana 1 | MLflow + dataset preparado + baseline + API demo. |
| Semana 2 | Modelos + dashboard + QABot generando tests. |
| Semana 3 | Demo final integrada. |
