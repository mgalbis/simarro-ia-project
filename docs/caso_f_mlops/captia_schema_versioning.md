# Versionado del schema CAPTIA

## Objetivo

El schema CAPTIA define cómo se representan los datos en la capa plata. Debe versionarse porque los modelos dependen
directamente de los nombres de variables, tags, unidades y tipos.

## Schema base

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

## Fichero de configuración

Ubicación recomendada:

```text
config/captia_schema.json
```

Contenido mínimo:

```json
{
  "schema_id": "captia_canonical_schema",
  "version": "1.0",
  "silver_layer": {
    "logical_schema": {
      "measurement": "captia_point",
      "field": "value",
      "tags": ["captia_env", "domain_id", "site_id", "asset_id", "variable"]
    }
  }
}
```

## Versionado en lakeFS

Repositorio:

```text
captia_schema
```

Tag inicial:

```text
captia_schema_v1
```

## Uso desde MLflow

Todo experimento debe registrar:

```text
captia_schema_version=captia_schema_v1
```

## Motivo

Si cambia el nombre de una variable o el tipo de una señal, los modelos antiguos pueden dejar de ser reproducibles.
Versionar el schema evita esa pérdida de trazabilidad.
