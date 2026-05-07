# Checklist final de entrega

## 1. Repositorio

- [ ] Existe `README.md` completo.
- [ ] El repositorio no contiene `.env` real.
- [ ] El repositorio no contiene credenciales.
- [ ] El repositorio no contiene datasets grandes.
- [ ] El repositorio no contiene modelos pesados.
- [ ] `.gitignore` está configurado.
- [ ] Hay commits descriptivos y atómicos.

## 2. Documentación

- [ ] `docs/runbook.md` completo.
- [ ] `docs/arquitectura.md` completo.
- [ ] `docs/distribucion_tareas.md` completo.
- [ ] `docs/mlflow_conventions.md` completo.
- [ ] `docs/data_dictionary_occupancy.md` completo.
- [ ] `docs/qabot_scope.md` completo.
- [ ] `docs/qabot_architecture.md` completo.
- [ ] `docs/video_script.md` completo.
- [ ] Diagramas incluidos.
- [ ] Comandos copiables.

## 3. Notebooks

- [ ] Notebooks numerados.
- [ ] Tienen Markdown explicativo.
- [ ] Tienen outputs visibles.
- [ ] Referencian runs MLflow.
- [ ] Explican decisiones y problemas encontrados.

## 4. Caso F — MLOps

- [ ] MLflow arranca.
- [ ] Hay experimentos creados.
- [ ] Hay runs de baseline y modelos.
- [ ] Los runs tienen métricas.
- [ ] Los runs tienen artefactos.
- [ ] Los runs tienen tag lakeFS.
- [ ] lakeFS arranca.
- [ ] Hay repositorio de dataset.
- [ ] Hay tags de dataset.

## 5. Caso D — Ocupación e IAQ

- [ ] Dataset descargado y procesado.
- [ ] Auditoría de calidad generada.
- [ ] Baseline entrenado.
- [ ] Al menos 3 modelos entrenados.
- [ ] Métricas comparadas.
- [ ] Modelo ganador justificado.
- [ ] Importancia de variables explicada.
- [ ] Índice IAQ implementado.
- [ ] InfluxDB recibe datos.
- [ ] Grafana muestra paneles.
- [ ] Alertas configuradas o documentadas.

## 6. QABot

- [ ] Router de intención funcional.
- [ ] Mínimo 4 agentes diferenciados.
- [ ] API demo funcionando.
- [ ] Generación de tests pytest.
- [ ] Ejecución de tests.
- [ ] Reporte generado.
- [ ] Al menos 2 defectos detectados en demo.
- [ ] Métricas registradas en MLflow.

## 7. Calidad de código

- [ ] `black` ejecutado.
- [ ] `flake8` ejecutado.
- [ ] `pytest` ejecutado.
- [ ] No hay errores críticos.
- [ ] Código organizado por módulos.

## 8. Vídeo

- [ ] Duración 10-15 minutos.
- [ ] Resolución 1080p.
- [ ] Audio claro.
- [ ] Muestra funcionalidad real.
- [ ] Muestra dashboard.
- [ ] Muestra MLflow/lakeFS.
- [ ] Muestra QABot ejecutando pruebas.
- [ ] No muestra credenciales.
- [ ] No muestra errores internos.
- [ ] Explica impacto y conexión con el proyecto.

## 9. Release final

- [ ] Crear tag Git `v1.0-final`.
- [ ] Revisar README.
- [ ] Revisar enlaces.
- [ ] Revisar que el repositorio puede ser público sin filtrar información sensible.
