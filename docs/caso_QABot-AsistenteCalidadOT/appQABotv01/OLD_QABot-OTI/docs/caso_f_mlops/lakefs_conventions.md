# Convenciones lakeFS

## Objetivo

Versionar datasets, capas Medallion y schema CAPTIA para que los experimentos sean reproducibles.

## Repositorios recomendados

```text
captia_schema
uci_occupancy
ingauge
qabot_eval
```

## Ramas

```text
main
dev
experiment/{case}/{short-description}
```

Ejemplo:

```text
experiment/d/occupancy-cleaning
```

## Tags

Formato:

```text
{dataset}_{layer}_v{version}
```

Ejemplos:

```text
captia_schema_v1
uci_occupancy_bronze_v1
uci_occupancy_silver_v1
uci_occupancy_gold_v1
ingauge_bronze_v1
ingauge_silver_v1
```

## Commits

Los commits deben explicar qué cambia y por qué.

Ejemplos:

```text
Add raw UCI Occupancy files as bronze layer
Normalize UCI Occupancy to CAPTIA silver schema
Create gold features for occupancy classifier
Version CAPTIA schema v1
```

## Relación con MLflow

Cada run MLflow debe guardar:

```text
lakefs_repo
lakefs_branch
lakefs_commit
lakefs_tag
```

Así se puede reconstruir el dataset exacto usado en el entrenamiento.
