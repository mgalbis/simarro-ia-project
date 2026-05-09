# Arquitectura Medallion

## Resumen

La arquitectura Medallion organiza los datos en capas sucesivas de refinamiento:

```text
Bronce → Plata → Oro
```

Cada capa tiene una función diferente.

## Capa bronce

Contiene los datos originales, sin transformar.

Ejemplos:

- CSV originales de UCI Occupancy.
- CSV de In-Gauge/En-Gage.
- Dumps o exports originales.
- Ficheros recibidos antes de limpieza.

Propiedades:

- No se modifican.
- Se versionan en lakeFS.
- Sirven para recomputar capas posteriores.

Ubicación lógica:

```text
data/raw/
src/simarro/bronze/
lakeFS: *_bronze_v*
```

## Capa plata

Contiene los datos normalizados al schema CAPTIA.

Schema objetivo:

```text
measurement: captia_point

tags:
  captia_env
  domain_id
  site_id
  asset_id
  variable

field:
  value
```

Ejemplo conceptual:

```text
captia_point,
captia_env=prod,
domain_id=bms_classrooms,
site_id=ies_simarro,
asset_id=AULA01,
variable=co2
value=712
```

Ubicación lógica:

```text
src/simarro/silver/
InfluxDB local
lakeFS: *_silver_v*
```

## Capa oro

Contiene artefactos derivados para un caso de uso concreto.

Ejemplos:

- Features para modelos de ocupación.
- Datasets de entrenamiento.
- Métricas calculadas.
- Informes de calidad.
- Índices o artefactos preparados para demo.

Ubicación lógica:

```text
data/gold/
src/simarro/gold/
src/simarro/cases/
lakeFS: *_gold_v*
MLflow: runs, modelos y artefactos
```

## Aplicación en el repositorio

```text
src/simarro/bronze/  → registro y versionado inicial
src/simarro/silver/  → normalización a CAPTIA + escritura InfluxDB
src/simarro/gold/    → generación de features y artefactos finales
src/simarro/mlops/   → trazabilidad transversal
```

## Regla de uso

No entrenar modelos directamente sobre CSV como flujo final. El flujo defendible debe ser:

```text
CSV original
→ lakeFS bronze
→ ETL silver
→ InfluxDB CAPTIA
→ query/pivot
→ gold features
→ modelo
→ MLflow
```
