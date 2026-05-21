# Caso F — MLOps y ciclo de vida de modelos

## Objetivo

Implementar la capa MLOps del proyecto para que los modelos sean reproducibles, trazables, comparables y auditables.

El Caso F no entrega un modelo principal. Entrega la infraestructura y las convenciones que permiten saber:

```text
qué código
+ qué dataset
+ qué versión del schema
+ qué parámetros
+ qué métricas
+ qué artefactos
+ qué modelo
```

se usaron en cada experimento.

## Componentes

| Componente | Función |
|---|---|
| MLflow | Registro de experimentos, modelos, métricas, parámetros y artefactos. |
| lakeFS | Versionado de datasets y schema CAPTIA. |
| Git | Versionado del código. |
| Scripts MLOps | Inicialización, demo y validación de integridad. |
| Runbook | Reproducción del entorno. |

## MVP del Caso F

El MVP está completo cuando se demuestra:

1. MLflow arranca.
2. lakeFS arranca.
3. Hay repositorios lakeFS creados.
4. El schema CAPTIA está versionado.
5. Existe una convención MLflow documentada.
6. Existe una convención lakeFS documentada.
7. Se ejecuta un experimento de prueba.
8. El experimento guarda parámetros, métricas, artefactos y modelo.
9. El experimento referencia commit Git, repo lakeFS, tag lakeFS y schema CAPTIA.
10. Un script valida la integridad del run.

## Estructura relacionada

```text
docs/caso_f_mlops/
src/simarro/mlops/
scripts/mlops/
tests/mlops/
notebooks/caso_f_mlops/
```
