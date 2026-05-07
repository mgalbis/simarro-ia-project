# Guion del vídeo de demostración

Duración objetivo: 10-15 minutos.  
Audiencia: público no técnico en Big Data e IA.

## 1. Estructura general

| Bloque | Duración | Contenido |
|---|---:|---|
| Contexto | 1-2 min | Problema real y objetivo del proyecto. |
| Arquitectura | 1-2 min | Componentes principales y flujo. |
| Caso D | 3-4 min | Ocupación, IAQ, modelos y dashboard. |
| Caso F | 2 min | MLflow, lakeFS y trazabilidad. |
| QABot | 3-4 min | Generación y ejecución de pruebas. |
| Cierre | 1 min | Resultados, impacto y mejoras. |

## 2. Bloque 1 — Contexto

Mensaje clave:

Los edificios inteligentes necesitan datos fiables, modelos trazables y sistemas de calidad para poder tomar decisiones útiles sobre confort, ocupación y eficiencia.

Texto orientativo:

```text
Este proyecto aborda tres necesidades complementarias: predecir la ocupación de espacios a partir de variables ambientales, asegurar que los modelos son reproducibles mediante MLOps y construir un asistente agéntico capaz de generar y ejecutar pruebas de calidad software.
```

## 3. Bloque 2 — Arquitectura

Mostrar:

- Diagrama general.
- Flujo de datos.
- Relación entre Caso D, Caso F y QABot.

Puntos a explicar:

- Los datos se preparan y versionan.
- Los modelos se entrenan y registran.
- Las predicciones se visualizan.
- QABot prueba una API demo.

## 4. Bloque 3 — Caso D

Mostrar:

1. Dataset UCI Occupancy.
2. Variables principales: temperatura, humedad, luz, CO₂, ocupación.
3. Notebook de EDA con gráficos.
4. Comparativa de modelos.
5. Modelo ganador.
6. Dashboard Grafana.

Texto orientativo:

```text
El modelo aprende a detectar si una estancia está ocupada usando señales ambientales. Esto permite optimizar climatización e iluminación sin usar cámaras ni sensores explícitos de presencia.
```

Métricas a enseñar:

- Accuracy.
- Precision.
- Recall.
- F1-score.
- Matriz de confusión.

## 5. Bloque 4 — Caso F

Mostrar:

1. UI de MLflow con runs.
2. Detalle del modelo ganador.
3. Métricas y artefactos.
4. lakeFS con tags de dataset.

Texto orientativo:

```text
Cada resultado del proyecto queda trazado. Sabemos qué versión del dataset se usó, qué código generó el modelo, qué parámetros se aplicaron y qué métricas produjo.
```

## 6. Bloque 5 — QABot

Mostrar:

1. UI de QABot.
2. Entrada: requisito u OpenAPI.
3. Router clasificando intención.
4. Agentes generando pruebas.
5. Tests pytest generados.
6. Ejecución contra API demo.
7. Fallos detectados.
8. Reporte final.
9. Registro en MLflow.

Texto orientativo:

```text
QABot actúa como un asistente de calidad. Analiza requisitos, propone casos de prueba, genera código ejecutable, lanza las pruebas y resume los errores encontrados.
```

Fallos demo recomendados:

- CO₂ negativo aceptado.
- Humedad superior a 100 aceptada.
- Aula inexistente devuelve código incorrecto.

## 7. Bloque 6 — Cierre

Mensaje final:

```text
El resultado es una solución integrada: modelos de IA medibles, trazabilidad MLOps y agentes de testing que ayudan a validar software. El sistema es reproducible y puede evolucionar con nuevos datos y nuevos casos de uso.
```

## 8. Qué no mostrar

Evitar:

- Código fuente largo.
- Errores internos.
- Configuración irrelevante.
- Credenciales.
- Ficheros `.env`.
- Discusiones técnicas demasiado detalladas.

## 9. Checklist antes de grabar

- Servicios arrancados.
- Dashboard con datos.
- MLflow con runs visibles.
- lakeFS con tags visibles.
- API demo funcionando.
- QABot probado.
- Informe QABot generado.
- Navegador limpio con pestañas preparadas.
- Resolución 1080p.
- Audio claro.
