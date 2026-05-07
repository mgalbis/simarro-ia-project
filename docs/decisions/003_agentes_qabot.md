# Decisión 003 — Arquitectura de agentes de QABot

## Estado

Aceptada.

## Contexto

El proyecto incorpora un caso nuevo de testing de calidad con agentes especialistas.

El objetivo no es crear un chatbot genérico, sino un sistema orientado a tareas: analizar requisitos, generar pruebas, ejecutarlas y evaluar resultados.

## Decisión

QABot se estructura mediante un router y agentes especializados:

- Router de intención.
- Agente analista.
- Agente diseñador funcional.
- Agente API.
- Agente de calidad de datos.
- Agente de seguridad básica.
- Agente de rendimiento básico.
- Executor.
- Agente evaluador.
- Reporter.

## Justificación

Separar responsabilidades permite:

- Explicar mejor la arquitectura.
- Evaluar cada agente por separado.
- Reutilizar agentes en futuros casos.
- Demostrar enrutamiento y especialización.
- Evitar un único prompt monolítico difícil de depurar.

## Alcance de seguridad

El agente de seguridad solo genera pruebas no destructivas:

- Autenticación ausente.
- Token inválido.
- Payload malformado.
- Tipos incorrectos.
- Tamaños excesivos controlados.

No se incluyen ataques ofensivos ni pruebas contra sistemas externos.

## Criterios de éxito

- Router con al menos 3 intenciones.
- Mínimo 4 agentes implementados.
- Tests generados en pytest.
- Ejecución real contra API demo.
- Informe final.
- Métricas registradas en MLflow.

## Consecuencias

Positivas:

- Arquitectura clara para la defensa.
- Caso nuevo diferenciador.
- Fácil de demostrar.

Negativas:

- Más módulos que mantener.
- Requiere definir bien esquemas de entrada/salida.
