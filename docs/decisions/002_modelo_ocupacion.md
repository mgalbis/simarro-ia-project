# Decisión 002 — Modelos de ocupación

## Estado

Aceptada.

## Contexto

El caso D requiere detectar ocupación a partir de variables ambientales: temperatura, humedad, luz, CO2 y ratio de humedad.

El dataset base es UCI Occupancy Detection.

## Decisión

Entrenar y comparar:

1. Baseline.
2. Logistic Regression.
3. Random Forest.
4. Gradient Boosting / XGBoost.
5. SVM.

La métrica principal será F1-score.  
La métrica secundaria será recall de la clase ocupada.

## Justificación

- El baseline permite demostrar mejora real.
- Logistic Regression aporta interpretabilidad.
- Random Forest ofrece buen rendimiento y robustez.
- XGBoost/Gradient Boosting suele funcionar bien en datos tabulares.
- SVM sirve como comparación adicional.

## Validación

- Mantener particiones originales del dataset.
- No mezclar test con entrenamiento.
- Registrar todos los experimentos en MLflow.
- Guardar matriz de confusión y curvas ROC.
- Documentar importancia de variables.

## Criterio de selección

El modelo final debe cumplir:

- F1-score alto.
- Buen recall en la clase ocupada.
- Estabilidad entre test1 y test2.
- Complejidad razonable.
- Facilidad de despliegue.

## Consecuencias

Positivas:

- Comparativa clara.
- Métricas defendibles.
- Interpretabilidad suficiente.

Negativas:

- XGBoost añade dependencia adicional.
- SVM puede ser menos interpretable.
