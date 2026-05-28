# Documentación — simarro-ia-project

Repositorio del proyecto final del Curso de Especialización en Inteligencia Artificial y Big Data del IES Dr. Lluís Simarro.

El repositorio se organiza como un monorepo por capas y módulos. La estructura separa documentación, infraestructura, configuración, notebooks, código fuente, scripts, pruebas, informes y artefactos.

## Índice

- [Arquitectura general](arquitectura.md)
- [Arquitectura Medallion](arquitectura_medallion.md)
- [Runbook general](runbook.md)
- [Distribución de tareas](distribucion_tareas.md)
- [Caso F — MLOps](caso_f_mlops/README.md)
- [Caso D — IAQ y ocupación](caso_d_iaq_ocupacion/README.md)
- [Caso QABot — Agentes de calidad](caso_qabot/README.md)

## Principios del repositorio

1. Un único repositorio para todos los casos de uso.
2. Separación entre código reutilizable y código específico de cada caso.
3. Arquitectura Medallion: bronce, plata y oro.
4. Configuración mediante variables de entorno.
5. Datasets fuera de Git; versionado en lakeFS.
6. Modelos y artefactos pesados fuera de Git; registro en MLflow.
7. Documentación suficiente para reproducir el entorno desde cero.

## Estructura base

```text
simarro-ia-project/
├── docs/
├── infra/
├── config/
├── data/
├── notebooks/
├── src/
├── scripts/
├── tests/
├── reports/
└── artifacts/
```
