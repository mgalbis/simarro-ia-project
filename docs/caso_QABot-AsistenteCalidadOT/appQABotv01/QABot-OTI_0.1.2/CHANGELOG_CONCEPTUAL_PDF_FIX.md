# Corrección PDF y trazabilidad DC

## Cambios aplicados

- El flujo original de revisión/dataset se mantiene intacto.
- La mejora de documento conceptual queda aislada como contexto adicional.
- Se añade envío del contexto DC al backend durante la ejecución de pruebas.
- El informe PDF de iteración ahora incluye:
  - Documento DC usado.
  - Actividad solicitada desde el DC.
  - Resumen de lo que dice el DC.
  - Reglas/criterios funcionales extraídos.
  - Ciclo del dato inferido.
  - Resultado de cada prueba frente al criterio DC.
  - Justificación de PASS/WARN/FAIL y recomendación cuando exista.
- Se mantiene la descarga PDF por botón y por endpoint `/download/{execution_id}`.

## Archivos principales modificados

- `frontend/src/hooks/useQABotChat.js`
- `backend/app/routes/chat.py`
- `backend/app/services/pdf_report.py`
