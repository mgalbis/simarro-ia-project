#!/bin/sh
set -eu

cleanup() {
  if [ -n "${LAKEFS_PID:-}" ] && kill -0 "$LAKEFS_PID" 2>/dev/null; then
    kill "$LAKEFS_PID"
    wait "$LAKEFS_PID" || true
  fi
}

trap cleanup INT TERM

echo "Arrancando lakeFS..."
/app/lakefs run &
LAKEFS_PID=$!

echo "Inicializando repositorios y hooks de lakeFS..."
/init_lakefs.sh
echo "Inicializacion de lakeFS completada."

wait "$LAKEFS_PID"
