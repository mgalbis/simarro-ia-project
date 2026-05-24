FROM ghcr.io/mlflow/mlflow:latest

USER root

ENV MLFLOW_TRACKING_URI=http://127.0.0.1:5000/mlflow
ENV CASES_CONFIG_PATH=/mlflow/init/cases_config.json
ENV MLFLOW_INIT_RETRIES=60
ENV MLFLOW_INIT_RETRY_SECONDS=2

COPY docker/mlflow/bootstrap_mlflow_metadata.py /mlflow/init/bootstrap_mlflow_metadata.py
COPY config/cases_config.json /mlflow/init/cases_config.json
COPY docker/mlflow/entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
