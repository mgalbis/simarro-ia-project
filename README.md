# simarro-ia-project

Proyecto integrador del Curso de Especialización en Inteligencia Artificial y Big Data del IES Dr. Lluís Simarro.

El repositorio agrupa los desarrollos principales del equipo en analítica de datos, MLOps y herramientas de calidad para
proyectos de IA.

## Resúmen

El proyecto se estructura en tres líneas de trabajo complementarias:

- **Caso D:** analítica de datos ambientales y modelos de ocupación de aulas, con ejecución en batch y servicio
API/frontend de demostración.
- **Caso F (MLOps):** infraestructura de versionado, trazabilidad y operación de modelos con lakeFS, MLflow, JupyterHub
y automatización de pipelines.
- **QABot:** asistente QA para validación de datasets y resultados de modelos, con backend FastAPI y frontend web.

Para ampliar información sobre la arquitectura y los detalles de cada caso, explorar la carpeta `docs`.

## Guía rápida de comandos

Consultar ayuda:

```shell
make help
```

Inicializar entorno (requirements + certificados TLS):

```shell
make init
```

Construir imágenes MLOps:

```shell
make build
```

Arrancar stack MLOps:

```shell
make start
```

Parar stack MLOps (manteniendo volúmenes):

```shell
make stop
```

Parar stack MLOps y eliminar volúmenes:

```shell
make destroy
```

Arrancar y parar QABot:

```shell
make qabot-up
make qabot-down
make qabot-logs
```

Arrancar y parar In-Gauge and En-Gage:

```shell
make ingauge-up
make ingauge-down
make ingauge-logs
```

## Reparto de tareas del equipo

### FEDE B. (Caso D)

- Preparación y estructuración de datasets.
- Definición de variables (señales físicas del entorno).
- Entrenamiento y evaluación de modelos.
- Análisis de resultados e interpretación.
- Registro de experimentos en MLflow.

### Mª JESÚS G. (QABot)

- Definir métricas de calidad de datos.
- Diseñar validaciones (completitud, consistencia).
- Diseñar lógica de desarrollo de planes de pruebas.
- Diseño de pruebas de validación del modelo.
- Definir criterios de aceptación/rechazo.
- Definir reglas del sistema asistido.

### LUCIA F. (QABot)

- Implementar backend agéntico.
- Implementar lógica de planes de prueba.
- Construir interfaz conversacional.
- Orquestar interacción usuario-sistema.
- Integrar reglas de negocio definidas.
- Generar planes ejecutables.

### JOSE V. (Caso F)

- Despliegue de MLflow, lakeFS y JupyterHub.
- Configuración de entornos.
- Desarrollo notebook demo.
- Desarrollo de pipelines (CI/CD de modelos).

### MARIA G. (Caso F)

- Despliegue de MLflow, lakeFS y JupyterHub.
- Configuración de entornos.
- Definición de estándares y convenciones.
- Garantizar coherencia end-to-end del sistema.
- Gestión del repositorio.
