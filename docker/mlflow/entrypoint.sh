#!/bin/sh
set -eu

mkdir -p /mlflow/artifacts
chmod -R 775 /mlflow

mlflow server \
  --backend-store-uri sqlite:///mlflow/mlflow.db \
  --serve-artifacts \
  --artifacts-destination /mlflow/artifacts \
  --host 0.0.0.0 \
  --port 5000 \
  --static-prefix /mlflow &
MLFLOW_PID=$!

python /mlflow/init/bootstrap_mlflow_metadata.py

wait "$MLFLOW_PID"
