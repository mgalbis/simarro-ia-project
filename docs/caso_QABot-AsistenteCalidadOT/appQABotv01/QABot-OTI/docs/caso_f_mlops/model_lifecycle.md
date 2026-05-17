# Ciclo de vida de modelos

## Objetivo

Definir los estados por los que pasa un modelo desde el desarrollo hasta su posible reutilización futura.

## Estados

```text
dev → candidate → validated → production-ready → archived
```

## Definición de estados

| Estado | Descripción |
|---|---|
| `dev` | Experimento en desarrollo. Puede estar incompleto. |
| `candidate` | Modelo candidato tras obtener métricas razonables. |
| `validated` | Modelo revisado, con dataset y métricas trazables. |
| `production-ready` | Modelo preparado para ser reutilizado con datos reales. |
| `archived` | Modelo descartado o reemplazado. |

## Criterios para pasar a `candidate`

- El run está en MLflow.
- Tiene métricas completas.
- Tiene parámetros.
- Tiene artefactos.
- Tiene referencia a Git y lakeFS.

## Criterios para pasar a `validated`

- Se compara contra baseline.
- Se documenta dataset usado.
- Se documentan limitaciones.
- El script de integridad pasa correctamente.

## Criterios para pasar a `production-ready`

- El modelo puede cargarse desde MLflow.
- El código de inferencia funciona.
- Se documenta cómo sustituir datos públicos por datos reales de CENTINELA+.
- La configuración depende de `.env`, no de valores hardcodeados.
