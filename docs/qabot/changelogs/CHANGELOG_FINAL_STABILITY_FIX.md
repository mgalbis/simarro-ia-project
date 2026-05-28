# Corrección final de estabilidad - flujo DC + flujo legacy

## Problemas corregidos

1. El selector de dataset podía no relanzar la carga si el usuario elegía el mismo CSV.
   - Se resetea el input file tras cada selección.

2. Las actividades humanas del DC no siempre se resolvían a activity_type canónico.
   - Se añade normalización robusta sin acentos.
   - Se soportan alias como "Validación de tabla minable" y listas de pruebas.

3. El backend podía pedir columnas aunque el CSV ya las contenía.
   - Se infieren target, prediction/score, split e id desde las columnas del dataset.
   - Si el prompt trae una columna no existente generada por texto documental, se ignora y se infiere desde CSV.

4. Etiquetas de estado homogeneizadas en español.
   - PASADA: verde
   - ADVERTENCIA: amarillo
   - FALLIDA: rojo
   - ERROR: rojo

## Validaciones realizadas

- Compilación backend OK.
- Build frontend OK.
- Pruebas directas de QAAgent OK para:
  - MINABLE_DATASET_VALIDATION
  - MODEL_PERFORMANCE_EVALUATION
  - DATASET_SPLIT_VALIDATION
