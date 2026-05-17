# Caso D — Calidad del aire, confort interior y ocupación

## Objetivo

Analizar variables ambientales y entrenar modelos de detección de ocupación a partir de sensores de calidad ambiental.

## Variables principales

- CO₂
- Temperatura interior
- Humedad relativa
- Luminosidad
- Nivel de ruido
- Ocupación

## Flujo recomendado

```text
Dataset UCI / In-Gauge
→ capa bronce en lakeFS
→ ETL a schema CAPTIA
→ capa plata en InfluxDB
→ features oro
→ entrenamiento
→ MLflow
→ dashboard
```

## Código relacionado

```text
src/simarro/cases/case_d_iaq/
notebooks/caso_d_iaq_ocupacion/
```

## Entregables esperados

- EDA documentado.
- Validación de calidad.
- Dataset oro de entrenamiento.
- Baseline.
- Comparativa de modelos.
- Registro MLflow.
- Dashboard Grafana.
- Conclusiones.
