#!/bin/sh
set -eu

mkdir -p /mlflow/artifacts
chmod -R 775 /mlflow

MLFLOW_ALLOWED_HOSTS="${MLFLOW_ALLOWED_HOSTS:-localhost:*,127.0.0.1:*,mlflow:5000,nginx:80,nginx:443,10.*,192.168.*,172.16-31.*}"

mlflow server \
  --backend-store-uri sqlite:///mlflow/mlflow.db \
  --serve-artifacts \
  --artifacts-destination /mlflow/artifacts \
  --host 0.0.0.0 \
  --port 5000 \
  --allowed-hosts "${MLFLOW_ALLOWED_HOSTS}" \
  --static-prefix /mlflow &
MLFLOW_PID=$!

python /mlflow/init/init_mlflow.py

wait "$MLFLOW_PID"
