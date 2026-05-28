# Corrección subida dataset + modo documental DC

## Problema corregido
- El CSV quedaba seleccionado visualmente, pero el flujo documental podía ejecutar con `dataset=null` o bloquearse por metadatos de ciclo no sincronizados.
- La mejora DC interfería con el flujo legacy de inferencia automática por nombre/cabeceras del dataset.

## Cambios aplicados
- Sincronización inmediata del dataset seleccionado en `App.jsx`.
- Restauración de prioridad legacy para inferencia por dataset cuando no hay actividad DC explícita.
- Autocompletado robusto de proyecto/ciclo/fase antes de ejecutar:
  1. actividad DC elegida,
  2. `activity_type` explícito,
  3. inferencia original por dataset,
  4. inferencia original por texto.
- Eliminado bloqueo falso de “faltan datos obligatorios” cuando la app puede inferirlos.
- El modo DC mantiene la actividad elegida por el usuario y no cambia a otra al subir el dataset.

## Validación técnica
- Frontend: `npm run build` OK.
- Backend: `python3 -m compileall backend/app` OK.
