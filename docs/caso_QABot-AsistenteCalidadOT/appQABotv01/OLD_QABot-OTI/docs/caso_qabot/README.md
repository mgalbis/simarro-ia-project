# Caso QABot — Agentes especialistas de calidad

## Objetivo

Construir un sistema de agentes orientado a pruebas y auditoría de calidad.

## Enfoque

El caso puede cubrir:

1. Calidad de datos.
2. Calidad de experimentos MLflow.
3. Calidad de respuestas del chatbot de otro equipo mediante golden set.
4. Generación y ejecución de pruebas software.

## Agentes previstos

| Agente | Función |
|---|---|
| Router | Decide qué agente debe actuar. |
| Agente de calidad de datos | Revisa nulos, rangos, timestamps y schema. |
| Agente auditor MLflow | Comprueba baseline, métricas, tags y artefactos. |
| Agente evaluador de chatbot | Evalúa respuestas frente a golden set. |
| Agente reporter | Genera informe final. |

## Flujo general

```text
Entrada
→ router
→ agente especialista
→ validación o prueba
→ resultado estructurado
→ informe
```

## Código relacionado

```text
src/simarro/cases/qabot/
notebooks/caso_qabot/
```
