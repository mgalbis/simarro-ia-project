# QABot - Asistente QA para Oficina de test en proyectos de Ciclo del Dato

## Descripción

QABot es un agente orquestador orientado al aseguramiento de calidad (QA) en proyectos de datos, IA y Machine Learning.

El sistema guía al usuario durante iteraciones de prueba, validando artefactos, ejecutando controles basados en reglas y generando informes de resultados.

# Objetivo

Desarrollar un agente orquestador de asistencia QA que acompañe al usuario durante iteraciones de prueba de un proyecto de datos/ML, solicitando artefactos, ejecutando validaciones basadas en reglas, reportando defectos, recogiendo feedback, generando informes, etc.

La v1 estará basada en reglas definidas por testers expertos almacenadas en un grafo de conocimiento que relaciona fases del ciclo del dato, riesgos, controles, evidencias y recomendaciones.

---

# Cobertura funcional

El ciclo de pruebas incluye numerosas fases dependiendo del propósito. No se ejecuta igual un plan de pruebas en la primera iteración que en una regresión funcional tras varias iteraciones, al igual que realizar pruebas sobre errores resueltos, pruebas de carga o pruebas de integración.

En este caso vamos a desarrollar la disciplina de prueba de ciclo del dato, que tiene fases específicas ligadas al ciclo de desarrollo de una solución de IA y Big Data.

## Casos de uso generales del agente orquestador

1. Iniciar una sesión de validación.
2. Entender el objetivo del usuario.
3. Solicitar artefactos necesarios.
4. Guiar al usuario cuando falte información.
5. Mantener contexto durante la conversación.
6. Gestionar varias iteraciones de análisis.
7. Presentar resultados de forma comprensible.
8. Permitir profundizar en defectos detectados.
9. Recoger feedback del usuario.
10. Ofrecer generación de informe de pruebas.
11. Cerrar la sesión con trazabilidad.

---

# Ciclo del dato

El ciclo del dato puede incluir distintas tareas dependiendo del objetivo de negocio, la técnica de IA aplicada, el dominio de los datos, etc., especialmente en desarrollos avanzados multimodales y agénticos.

## Tareas habituales del ciclo del dato

1. Ingesta de datos
2. Selección y filtrado
3. Calidad de los datos
4. Limpieza
5. Preparación y transformación
6. División de datasets (train/validation/test)
7. Selección de algoritmos
8. Entrenamiento del modelo
9. Evaluación del modelo
10. Métricas de desempeño
11. Explicabilidad
12. Empaquetado
13. Despliegue en producción

---

# Especialización por dominio

Estas fases pueden especializarse según el dominio de los datos.

Por ejemplo, en soluciones NLP es necesario asegurar la calidad en la transformación de texto a tokens (vectores numéricos) para permitir la aplicación de algoritmos de Machine Learning.

Por ello, se incluirá una subfase específica de validación de codificación del texto dentro del apartado de calidad de los datos.

---

# Alcance de la versión v1

La versión v1 estará limitada a los casos de uso principales y a las tareas del ciclo del dato más asequibles, ya que se trata de un piloto dentro del contexto del proyecto integrador del curso de especialización.

No obstante, el sistema quedará preparado para incorporar posteriormente nuevas pruebas, reglas y tareas de ciclo del dato.

---

# Funcionalidades iniciales del asistente orquestador

1. Iniciar una sesión de pruebas.
2. Entender el objetivo del usuario.
   - Ejemplos:
     - Ejecutar un plan de pruebas.
     - Realizar una regresión.
     - Crear defectos en Azure DevOps.
3. Solicitar artefactos necesarios para el objetivo solicitado.
4. Guiar al usuario cuando falte información.
5. Reportar resultados de las pruebas.
6. Solicitar feedback para mejora continua adaptando el grafo de conocimiento de forma autoincremental.

---

# Tareas iniciales del ciclo del dato contempladas en v1

## 1. Calidad de los datos

### a. Calidad de datos general

- Valores nulos
- Duplicados
- Tipado incorrecto
- Inconsistencias
- Distribuciones anómalas

### b. Calidad de datos en problemas NLP

- Validación de codificación de texto
- Caracteres inválidos
- Tokenización
- Longitud de secuencias
- Normalización

---

## 2. División de datasets

Validación de la correcta separación de los conjuntos:

- Entrenamiento
- Validación
- Pruebas

Se comprobarán aspectos como:

- Proporciones esperadas
- Fuga de datos
- Balance de clases

---

## 3. Evaluación del modelo

Ejemplos de propiedades a evaluar:

- Estabilidad
- Robustez
- Tiempo de ejecución

Las propiedades concretas serán definidas tras validar el alcance definitivo de la v1.

---

## 4. Métricas de evaluación

Ejemplos iniciales:

- Precisión
- Accuracy
- Error cuadrático medio (MSE)

Las métricas definitivas incluidas en v1 se determinarán posteriormente según el tipo de solución ML/NLP objetivo.

---

# Enfoque técnico propuesto para v1

## Arquitectura conceptual

```text
Usuario
   │
   ▼
Agente Orquestador QA
   │
   ├── Gestor de contexto
   ├── Motor de reglas
   ├── Gestor de artefactos
   ├── Generador de informes
   └── Adaptador de feedback
            │
            ▼
    Grafo de conocimiento QA