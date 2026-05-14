# Convención de experimentos MLflow para los Casos de Uso del Proyecto Final del Curso de Especialización en Inteligencia Artificial y Big Data
**Versión 1.0**

Este documento define los estándares que TODOS los equipos deben seguir al registrar experimentos en MLflow. 
El objetivo es garantizar que los experimentos sean comparables, trazables y auditables.

---

## 1. Nomenclatura de experimentos
(Fuente: Anexo_I_Casos_de_Uso.pdf: CASO 6 (F))
TODO: Comentar con los profesores: 
el experimento es un objeto que agrupa muchos runs con distintos algoritmos y fechas
meterlos todos con el nombre del experimento no tiene sentido operacionalmente

### Formato

`Caso[letra]_[descripcion_del_problema]`

El experimento es un **contenedor permanente** que agrupa todas las
ejecuciones de un mismo problema. No incluye dataset, algoritmo ni fecha
(esos datos van en el nombre del run — ver sección 2).

### Tabla de experimentos del proyecto 
Se obtienen del enunciado de los casos de uso

(Fuente: MEDALLION_Arquitectura_Guia_Referencia.md: sección 2.3)

Grupo    Caso    Nombre del experimento      
 G        A      CasoA_Ingenieria_de_datos
 G1       B      CasoB_Prediccion_de_consumo_electrico
 G3       C      CasoC_Deteccion_de_anomalias_HVAC
 G4       D      CasoD_Calidad_del_aire
 G3       E      CasoE_Datos_meteorologicos
 G4       F      CasoF_Tests_mlflow_lakefs_jupyterhub
 G        G      CasoG_Calidad_de_datos
 G1       H      CasoH_Sistema_rag
 G2       I      CasoI_Deteccion_trafico
 G2       J      CasoJ_benchmark_spark_pandas
 G        K      CasoK_Edge_computing

El nombre del experimento lo crea el Caso F (G4). No lo crea cada equipo.
Si se requiere un experimento nuevo, comunicadlo a G4 para que lo podamos crear.

---

## 2. Nomenclatura de runs
(Fuente: Anexo_I_Casos_de_Uso.pdf: CASO 6)

### Formato
[algoritmo][fecha][descripcion_corta]

### Ejemplos de Runs válidos
XGBoost_20260510_baseline
RandomForest_20260512_feature_engineering_v2
IsolationForest_20260515_threshold_0.05

### Reglas
- La **fecha** es obligatoria en formato `YYYYMMDD`.
- La **descripción corta** se indica usando guiones bajos y sin espacios.
- El **algoritmo** usa el nombre exacto de la clase de scikit-learn o del framework (XGBoost, RandomForest, etc).

---

## 3. Tags obligatorios en cada run
(Fuente: MEDALLION_Arquitectura_Guia_Referencia.md: sección 2)

Todo run debe incluir estos tags. Son la trazabilidad mínima exigida.

```python
mlflow.set_tags({
    # Obligatorios
    'caso_uso': 'B', # letra del caso (A, B, C, D, E, etc)
    'grupo': 'G1', # identificador del grupo
    'dataset': 'uci-appliances', # nombre del repositorio en lakeFS (usar siempre guion, no guion bajo)
    'dataset_version': 'abc123def456', # commit hash de lakeFS
    'dataset_branch': 'main', # rama de lakeFS
    'capa_medallion': 'oro', # bronce | plata | oro
    
    # Recomendados
    'ejecutado_por': 'caso_b', # usuario de JupyterHub
    'descripcion': 'baseline con features básicas',
})
```

### Cómo podemos obtener el commit hash de lakeFS

```python
import lakefs_sdk
import os

cfg = lakefs_sdk.Configuration(
    host=os.environ.get('LAKEFS_ENDPOINT', 'http://localhost:8001'),
    username=os.environ.get('LAKEFS_ACCESS_KEY_ID'),
    password=os.environ.get('LAKEFS_SECRET_ACCESS_KEY'),
)

with lakefs_sdk.ApiClient(cfg) as client:
    api = lakefs_sdk.CommitsApi(client)
    # Obtener el último commit de la rama main del dataset
    commits = api.log_branch_commits(
        repository='uci-appliances',  # nombre de tu repositorio
        branch='main',
    )
    commit_hash = commits.results[0].id
    print(f"Commit hash: {commit_hash}")
    # Ejemplo: 'abc123def456789...'
```

---

## 4. Parámetros mínimos a registrar
(Fuente: `Anexo_I_Casos_de_Uso.pdf`, CASO 6 (F) — Aspectos MLOps)

Dependen del tipo de modelo, pero hay un mínimo común:

```python
mlflow.log_params({
    # Para todos
    'random_state': 42, # para reproducibilidad
    'test_size': 0.2, # proporción del split
    
    # Para modelos de árboles (RandomForest, XGBoost, etc)
    'n_estimators': 200,
    'max_depth': 6,
    'learning_rate': 0.05,
    
    # Para redes neuronales
    'epochs': 300,
    'batch_size': 32,
    'learning_rate': 0.1,
})
```

---

## 5. Métricas mínimas a registrar
(Fuente: Anexo_I_Casos_de_Uso.pdf`: CASO 2, CASO 3 y CASO 4)

### Regresión (Casos B, E)
```python
mlflow.log_metrics({
    'rmse': ...,
    'mae': ...,
    'mape': ...,  # error porcentual absoluto medio — objetivo < 10% (Caso B)
    'r2': ...,
})
```

### Clasificación / Detección de anomalías (Casos C, D)
```python
mlflow.log_metrics({
    'accuracy': ...,
    'precision': ...,
    'recall': ...,
    'f1': ...,
    'roc_auc': ...,
})
```

---

## 6. Registro en el Model Registry
(Fuente: `Anexo_I_Casos_de_Uso.pdf`, CASO 6)

El nombre del modelo en el registry sigue este formato:
simarro-[caso]-[descripcion]

 Caso   Nombre en el registry
  B     simarro-caso-b-consumo
  C     simarro-caso-c-hvac
  D     simarro-caso-d-ocupacion
  E     simarro-caso-e-meteorologia

Los nombres se reservan en el arranque del proyecto
No crear nombres propios en el registry.
---

## 7. Plantilla de código lista para usar
(Fuente: fichero mlflow_template.py)

Copiad este bloque al inicio de cada notebook de entrenamiento y hay que rellenar los valores marcados por los TODO

```python
import os
import mlflow

# Configuración (no tocar)
mlflow.set_tracking_uri(os.environ.get('MLFLOW_TRACKING_URI', 'http://localhost:5000'))

# Identificación del experimento
EXPERIMENT_NAME    = 'CasoB_UCI_consumo' # TODO: indicar el experimento
CASO_USO           = 'B' # TODO: letra del caso de uso
GRUPO              = 'G1' # TODO indicad el grupo al que pertenece el experimento
DATASET_REPO       = 'uci-appliances' # TODO: repo en lakeFS
REGISTERED_MODEL   = 'simarro-caso-b-consumo' # TODO: modelo (siguiendo la nomenclatura indicada al principio de este documento)

# Obtener commit hash de lakeFS (no tocar)
def get_lakefs_commit(repo: str, branch: str = 'main') -> str:
    import lakefs_sdk
    cfg = lakefs_sdk.Configuration(
        host=os.environ.get('LAKEFS_ENDPOINT'),
        username=os.environ.get('LAKEFS_ACCESS_KEY_ID'),
        password=os.environ.get('LAKEFS_SECRET_ACCESS_KEY'),
    )
    with lakefs_sdk.ApiClient(cfg) as client:
        api = lakefs_sdk.CommitsApi(client)
        commits = api.log_branch_commits(repository=repo, branch=branch)
        return commits.results[0].id

# Entrenamiento
mlflow.set_experiment(EXPERIMENT_NAME)

with mlflow.start_run(run_name=f"XGBoost_{date.today():%Y%m%d}_baseline"):
    
    # Tags obligatorios
    mlflow.set_tags({
        'caso_uso': CASO_USO,
        'grupo': GRUPO,
        'dataset': DATASET_REPO,
        'dataset_version': get_lakefs_commit(DATASET_REPO),
        'dataset_branch': 'main',
        'capa_medallion': 'plata',  # bronce | plata | oro
    })
    
    # Aquí va el código del entrenamiento
    mlflow.log_params({...})
    mlflow.log_metrics({...})
    mlflow.sklearn.log_model(
        sk_model=modelo,
        artifact_path='model',
        registered_model_name=REGISTERED_MODEL,
    )
```

---

## 8. Acceso a los servicios
(Fuente: `README.md`)

Servicio    URL local                   Uso
MLflow      http://localhost:5000       Ver experimentos y modelos
lakeFS      http://localhost:8001       Ver datasets y commits
JupyterHub  http://localhost:8000       Entorno de notebooks

TODO: Cuando tengamos la infra de ITI preparada tendremos que camiar .env 

---

## 9. Checklist antes de hacer merge a `main` en lakeFS
(Fuente: MEDALLION_Arquitectura_Guia_Referencia.md, sección 4 — variante híbrida)

Antes de aprobar un merge de datos a `main`, hay que comprobar los siguiente puntos:

- El experimento existe en MLflow con el nombre correcto
- El run referencia el commit hash del dataset
- Los 5 tags obligatorios están presentes
- Las métricas mínimas están registradas
- El modelo está registrado en el Model Registry
- Los artefactos (modelo + CSV de predicciones) están guardados

---

* Cualquier dudas o propuesta de cambio consultar con el equipo G4 *