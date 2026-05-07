# Alcance de QABot

## 1. Objetivo

QABot es un asistente agéntico especializado en pruebas de calidad software.

Recibe requisitos funcionales o especificaciones API y genera pruebas ejecutables, las ejecuta contra una aplicación demo y produce un informe de resultados.

No usa Wakamiti.

## 2. Entradas soportadas

### 2.1 Requisito en lenguaje natural

Ejemplo:

```text
El sistema debe permitir consultar el índice IAQ de un aula mediante su identificador.
Si el aula no existe, debe devolver un error 404.
```

### 2.2 Especificación OpenAPI

Ejemplo:

```yaml
paths:
  /rooms/{id}/iaq:
    get:
      parameters:
        - name: id
          in: path
          required: true
```

### 2.3 Historia de usuario

Ejemplo:

```text
Como gestor del edificio quiero consultar la ocupación prevista de un aula para optimizar la climatización.
```

## 3. Salidas generadas

QABot debe generar:

- Matriz de casos de prueba.
- Tests ejecutables en `pytest`.
- Resultado de ejecución.
- Informe Markdown/HTML.
- Métricas registradas en MLflow.

## 4. Tipos de pruebas

| Tipo | Descripción |
|---|---|
| Funcionales positivas | Validan comportamiento esperado. |
| Funcionales negativas | Validan errores controlados. |
| Frontera | Valores límite. |
| Calidad de datos | Nulos, tipos, rangos, duplicados. |
| API | Status codes, payloads, headers básicos. |
| Seguridad básica | Falta de autenticación, payload inválido, entradas malformadas. |
| Rendimiento básico | Latencia media y percentiles simples. |

## 5. Fuera de alcance

No se incluyen:

- Testing destructivo.
- Ataques ofensivos reales.
- Fuzzing agresivo.
- Pruebas de carga intensiva.
- Ejecución sobre sistemas externos no autorizados.
- Sustitución de herramientas profesionales de QA.

## 6. API demo bajo prueba

Endpoints previstos:

| Endpoint | Método | Descripción |
|---|---|---|
| `/health` | GET | Estado de la API. |
| `/login` | POST | Login simulado. |
| `/rooms` | GET | Lista de aulas. |
| `/rooms/{id}/iaq` | GET | Índice IAQ de un aula. |
| `/rooms/{id}/measurements` | POST | Inserción de medición ambiental. |
| `/occupancy/predict` | POST | Predicción de ocupación. |

## 7. Defectos controlados para demo

La API demo puede incluir fallos intencionados para demostrar la utilidad de QABot:

- Acepta CO₂ negativo.
- Acepta humedad superior a 100%.
- Devuelve 200 para un aula inexistente.
- No valida payload vacío.
- No controla tipos incorrectos.
- Presenta latencia artificial en un endpoint.

## 8. Métricas de evaluación

| Métrica | Descripción |
|---|---|
| `tests_generated` | Número de pruebas generadas. |
| `tests_executable` | Pruebas que pueden ejecutarse sin error sintáctico. |
| `tests_passed` | Pruebas superadas. |
| `tests_failed` | Pruebas fallidas. |
| `detected_defects` | Defectos reales detectados. |
| `valid_test_ratio` | Porcentaje de pruebas útiles. |
| `generation_time_seconds` | Tiempo de generación. |
| `execution_time_seconds` | Tiempo de ejecución. |

## 9. Criterio de aceptación

QABot se considera MVP funcional si:

- Clasifica la intención del usuario.
- Genera al menos 8 pruebas para una API demo.
- Exporta pruebas en formato pytest.
- Ejecuta las pruebas.
- Detecta al menos 2 defectos controlados.
- Genera informe final.
- Registra métricas en MLflow.
