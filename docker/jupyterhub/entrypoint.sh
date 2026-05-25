#!/bin/sh
set -eu

# Script de inicialización del contenedor JupyterHub.
# Se ejecuta cada vez que arranca el contenedor y crea usuarios locales.

# Configuración:
# - CASES_CONFIG_PATH: JSON con el bloque "cases" (por defecto /init/cases_config.json)
# - JUPYTERHUB_CASE_USERS_PASSWORD: contraseña para usuarios de caso
# - JUPYTERHUB_ADMIN: usuario admin de JupyterHub
CASES_CONFIG_PATH="${CASES_CONFIG_PATH:-/init/cases_config.json}"
JUPYTERHUB_ADMIN="$(printf '%s' "${JUPYTERHUB_ADMIN:-admin}" | tr '[:upper:]' '[:lower:]')"
CASE_USERS_PASSWORD="${JUPYTERHUB_CASE_USERS_PASSWORD:-${DEFAULT_USER_PASSWORD:-}}"

if [ -z "$CASE_USERS_PASSWORD" ]; then
    echo "[ERROR] Falta contraseña por defecto. Configura DEFAULT_USER_PASSWORD (o JUPYTERHUB_CASE_USERS_PASSWORD)." >&2
    exit 1
fi

if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
else
    echo "[WARN] No hay python disponible en la imagen. Solo se creará el usuario admin."
    PYTHON_BIN=""
fi

if [ -z "$PYTHON_BIN" ] || [ ! -f "$CASES_CONFIG_PATH" ]; then
    [ -f "$CASES_CONFIG_PATH" ] || echo "[WARN] No existe $CASES_CONFIG_PATH. Solo se creará el usuario admin."
    CASE_USERS_FILE="$(mktemp)"
else
    # Extraemos "casox" a partir de las claves de "cases" en el JSON.
    # Si hay error de parseo, no abortamos el arranque de JupyterHub.
    CASE_USERS_FILE="$(mktemp)"
    "$PYTHON_BIN" - "$CASES_CONFIG_PATH" > "$CASE_USERS_FILE" <<'PY'
import json
import sys

path = sys.argv[1]
users = set()
try:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    cases = data.get("cases", {})
    if isinstance(cases, dict):
        for key in cases.keys():
            case_id = str(key).strip().lower()
            if case_id:
                users.add(f"caso{case_id}")
    else:
        print(f"[WARN] Campo 'cases' no es un objeto en {path}", file=sys.stderr)
except Exception as exc:
    print(f"[WARN] No se pudo leer {path}: {exc}", file=sys.stderr)

for user in sorted(users):
    print(user)
PY
fi

echo "Creando usuarios locales de JupyterHub..."
# Deduplicamos admin + casos y asignamos la misma contraseña a todos.
ALL_USERS_FILE="$(mktemp)"
{
    printf '%s\n' "$JUPYTERHUB_ADMIN"
    cat "$CASE_USERS_FILE"
} | sed '/^$/d' | sort -u > "$ALL_USERS_FILE"

while IFS= read -r user; do
    [ -n "$user" ] || continue
    if id -u "$user" >/dev/null 2>&1; then
        echo "Usuario $user ya existe"
    else
        useradd -m -s /bin/bash "$user"
        echo "Usuario $user creado"
    fi
    echo "$user:$CASE_USERS_PASSWORD" | chpasswd
done < "$ALL_USERS_FILE"

rm -f "$CASE_USERS_FILE" "$ALL_USERS_FILE"

echo "Arrancando JupyterHub..."
exec jupyterhub -f /app/jupyterhub_config.py
