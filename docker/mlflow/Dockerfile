FROM ghcr.io/mlflow/mlflow:latest

USER root

ENV MLFLOW_TRACKING_URI=http://127.0.0.1:5000/mlflow
ENV CASES_CONFIG_PATH=/mlflow/init/cases_config.json
ENV MLFLOW_INIT_RETRIES=60
ENV MLFLOW_INIT_RETRY_SECONDS=2

COPY docker/mlflow/init_mlflow.py /mlflow/init/init_mlflow.py
COPY config/cases_config.json /mlflow/init/cases_config.json
COPY docker/mlflow/entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
