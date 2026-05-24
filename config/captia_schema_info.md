# Contenido de `schema_captia.json`

## Propósito

`schema_captia.json` define el contrato estructural común de la capa Silver compatible con CAPTIA.

El fichero contiene únicamente información común a todos los casos de uso. Su objetivo es fijar la forma que debe tener
cualquier observación normalizada, sin depender del dataset original, del caso de uso, del modelo entrenado ni del
repositorio lakeFS donde se versionen los datos.

## Metadatos

Los campos `schema_id`, `version`, `project` y `description` identifican el contrato usado por el proyecto.

Esta información permite referenciar una versión concreta del schema desde notebooks, validaciones y documentación.

## `silver_layer.logical_schema`

Esta sección define la estructura lógica de un punto CAPTIA.

Incluye:

- `measurement`: el measurement común `captia_point`.
- `field`: el field único `value`.
- `tags`: los cinco tags obligatorios que identifican entorno, dominio, sitio, activo y variable.

Estos elementos son comunes a todos los casos de uso.

## `silver_layer.file_schema`

Esta sección define la representación equivalente cuando la capa Silver se materializa como fichero Parquet o CSV.

Incluye las columnas necesarias para conservar la misma semántica que un punto CAPTIA:

- `timestamp`
- `captia_env`
- `domain_id`
- `site_id`
- `asset_id`
- `variable`
- `value`
- `metric_kind`
- `unit`

Cada columna incluye su tipo esperado para que la capa Silver pueda validarse antes de construir datasets Gold o
entrenar modelos.

## `metric_kinds`

Esta sección define los tipos de señal admitidos en la capa Silver.

Cada `metric_kind` indica cómo se interpreta la señal y qué estadísticas son válidas para ella. Esta información es
común a todos los casos de uso porque forma parte del contrato de datos normalizados.
