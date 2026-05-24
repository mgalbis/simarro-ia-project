#!/bin/sh
set -eu

# =============================================================================
# init_lakefs.sh
# -----------------------------------------------------------------------------
# Objetivo:
#   1) Esperar a que lakeFS arranque y completar setup inicial (si falta).
#   2) Crear/actualizar usuarios "casoX" con credenciales fijas.
#   3) Aplicar permisos:
#      - Lectura global (pueden ver todos los repos).
#      - Escritura solo en repos con prefijo propio: "<user>--*".
#   4) Crear repos de cada caso (desde cases_config.json) con formato:
#      "<user>--<repo_base>", rama main y hook-retrain.yml.
#
# Nota:
#   El nombre de repositorio en lakeFS no admite "/". Por eso se usa "--".
# =============================================================================

# -----------------------------------------------------------------------------
# 1) Configuración por variables de entorno
# -----------------------------------------------------------------------------
CASES_CONFIG_PATH="${CASES_CONFIG_PATH:-/init/cases_config.json}"
HOOK_FILE_PATH="${HOOK_FILE_PATH:-/init/hook-retrain.yml}"
HOOK_TARGET_PATH="${HOOK_TARGET_PATH:-_lakefs_actions/hook-retrain.yml}"

LAKEFS_ENDPOINT="${LAKEFS_ENDPOINT:-http://127.0.0.1:8000}"
LAKEFS_AUTHZ_ENDPOINT="${LAKEFS_AUTH_API_ENDPOINT:-$LAKEFS_ENDPOINT/api/v1}"

LAKEFS_INSTALLATION_USER_NAME="${LAKEFS_INSTALLATION_USER_NAME:-admin}"
LAKEFS_INSTALLATION_ACCESS_KEY_ID="${LAKEFS_INSTALLATION_ACCESS_KEY_ID:-${LAKEFS_ACCESS_KEY_ID:-}}"
LAKEFS_INSTALLATION_SECRET_ACCESS_KEY="${LAKEFS_INSTALLATION_SECRET_ACCESS_KEY:-${LAKEFS_SECRET_ACCESS_KEY:-}}"
LAKEFS_BOOTSTRAP_CREDS_FILE="${LAKEFS_BOOTSTRAP_CREDS_FILE:-/data/.lakefs_bootstrap_credentials}"

LAKEFS_SETUP_COMM_PREFS_SKIP="${LAKEFS_SETUP_COMM_PREFS_SKIP:-false}"
LAKEFS_SETUP_COMM_PREFS_EMAIL="${LAKEFS_SETUP_COMM_PREFS_EMAIL:-}"
LAKEFS_SETUP_COMM_PREFS_FEATURE_UPDATES="${LAKEFS_SETUP_COMM_PREFS_FEATURE_UPDATES:-false}"
LAKEFS_SETUP_COMM_PREFS_SECURITY_UPDATES="${LAKEFS_SETUP_COMM_PREFS_SECURITY_UPDATES:-false}"

LAKEFS_CASE_USERS_ENABLE="${LAKEFS_CASE_USERS_ENABLE:-true}"
LAKEFS_CASE_USERS_STRICT="${LAKEFS_CASE_USERS_STRICT:-false}"
LAKEFS_CASE_USERS_SECRET_KEY="${LAKEFS_CASE_USERS_SECRET_KEY:-${DEFAULT_USER_PASSWORD:-}}"

# Credenciales admin usadas por lakectl/curl en este script.
export LAKECTL_SERVER_ENDPOINT_URL="$LAKEFS_ENDPOINT"
export LAKECTL_CREDENTIALS_ACCESS_KEY_ID="${LAKEFS_ACCESS_KEY_ID:-$LAKEFS_INSTALLATION_ACCESS_KEY_ID}"
export LAKECTL_CREDENTIALS_SECRET_ACCESS_KEY="${LAKEFS_SECRET_ACCESS_KEY:-$LAKEFS_INSTALLATION_SECRET_ACCESS_KEY}"

# -----------------------------------------------------------------------------
# 2) Utilidades genéricas
# -----------------------------------------------------------------------------
require_file() {
  [ -f "$1" ] || { echo "No existe fichero requerido: $1" >&2; exit 1; }
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || { echo "Comando requerido no disponible: $1" >&2; exit 1; }
}

warn_or_fail() {
  msg="$1"
  if [ "$LAKEFS_CASE_USERS_STRICT" = "true" ]; then
    echo "$msg" >&2
    exit 1
  fi
  echo "[WARN] $msg"
}

already_exists() {
  file_path="$1"
  grep -Eqi "already exists|not unique|409 conflict" "$file_path"
}

normalize_name() {
  value="$1"
  norm="$(
    printf '%s' "$value" \
      | tr '[:upper:]' '[:lower:]' \
      | sed -E 's/[^a-z0-9]+/-/g; s/^-+//; s/-+$//; s/-+/-/g'
  )"
  [ -n "$norm" ] || norm="repo"
  printf '%s' "$norm"
}

repo_prefix_for_user() {
  user_id="$1"
  prefix="$(normalize_name "$user_id" | cut -c1-30)"
  [ -n "$prefix" ] || prefix="user"
  printf '%s' "$prefix"
}

owned_repo_name() {
  user_id="$1"
  repo_base="$2"

  prefix="$(repo_prefix_for_user "$user_id")"
  base="$(normalize_name "$repo_base")"

  # lakeFS: nombre repo max 63 chars -> "<prefix>--<base>"
  max_base_len=$((63 - ${#prefix} - 2))
  [ "$max_base_len" -ge 1 ] || max_base_len=1
  base="$(printf '%s' "$base" | cut -c1-"$max_base_len")"

  printf '%s--%s' "$prefix" "$base"
}

api_get_auth() {
  curl -fsS -u "${LAKECTL_CREDENTIALS_ACCESS_KEY_ID}:${LAKECTL_CREDENTIALS_SECRET_ACCESS_KEY}" "$1"
}

api_delete_auth() {
  curl -fsS -X DELETE -u "${LAKECTL_CREDENTIALS_ACCESS_KEY_ID}:${LAKECTL_CREDENTIALS_SECRET_ACCESS_KEY}" "$1" >/dev/null
}

api_current_user_id() {
  api_get_auth "$LAKEFS_ENDPOINT/api/v1/user" | jq -r '.user.id // empty'
}

save_admin_credentials() {
  [ -n "${LAKECTL_CREDENTIALS_ACCESS_KEY_ID:-}" ] || return 0
  [ -n "${LAKECTL_CREDENTIALS_SECRET_ACCESS_KEY:-}" ] || return 0
  cat > "$LAKEFS_BOOTSTRAP_CREDS_FILE" <<EOF
LAKECTL_CREDENTIALS_ACCESS_KEY_ID=${LAKECTL_CREDENTIALS_ACCESS_KEY_ID}
LAKECTL_CREDENTIALS_SECRET_ACCESS_KEY=${LAKECTL_CREDENTIALS_SECRET_ACCESS_KEY}
EOF
  chmod 600 "$LAKEFS_BOOTSTRAP_CREDS_FILE" 2>/dev/null || true
}

load_admin_credentials() {
  [ -f "$LAKEFS_BOOTSTRAP_CREDS_FILE" ] || return 1
  # shellcheck disable=SC1090
  . "$LAKEFS_BOOTSTRAP_CREDS_FILE"
  export LAKECTL_CREDENTIALS_ACCESS_KEY_ID
  export LAKECTL_CREDENTIALS_SECRET_ACCESS_KEY
  return 0
}

# -----------------------------------------------------------------------------
# 3) Arranque inicial de lakeFS (healthcheck + setup + comm prefs)
# -----------------------------------------------------------------------------
wait_lakefs_http() {
  echo "Esperando a que lakeFS HTTP este disponible..."
  tries=0
  until curl -fsS "$LAKEFS_ENDPOINT/api/v1/healthcheck" >/dev/null 2>&1; do
    tries=$((tries + 1))
    [ "$tries" -lt 60 ] || { echo "Timeout esperando lakeFS HTTP." >&2; exit 1; }
    sleep 2
  done
}

setup_state_json() {
  curl -fsS "$LAKEFS_ENDPOINT/api/v1/setup_lakefs" 2>/dev/null || true
}

setup_is_initialized() {
  state_json="$1"
  [ -n "$state_json" ] || return 1
  state="$(echo "$state_json" | jq -r '.state // empty' 2>/dev/null || true)"
  [ "$state" = "initialized" ]
}

ensure_lakefs_setup() {
  # Si ya está inicializado, reutilizamos credenciales guardadas (si existen).
  current="$(setup_state_json)"
  if setup_is_initialized "$current"; then
    echo "[OK] setup_lakefs ya estaba completado."
    load_admin_credentials || true
    return 0
  fi

  [ -n "$LAKEFS_INSTALLATION_USER_NAME" ] || { echo "Falta LAKEFS_INSTALLATION_USER_NAME." >&2; exit 1; }

  # Primer intento: usar credenciales predefinidas (si vienen por env).
  # Segundo intento: dejar que lakeFS genere credenciales.
  setup_response="$(mktemp)"
  setup_ok=false

  if [ -n "$LAKEFS_INSTALLATION_ACCESS_KEY_ID" ] && [ -n "$LAKEFS_INSTALLATION_SECRET_ACCESS_KEY" ]; then
    body="{\"username\":\"$LAKEFS_INSTALLATION_USER_NAME\",\"key\":{\"access_key_id\":\"$LAKEFS_INSTALLATION_ACCESS_KEY_ID\",\"secret_access_key\":\"$LAKEFS_INSTALLATION_SECRET_ACCESS_KEY\"}}"
    if curl -fsS -X POST -H "Content-Type: application/json" -H "Accept: application/json" -d "$body" "$LAKEFS_ENDPOINT/api/v1/setup_lakefs" >"$setup_response" 2>/dev/null; then
      setup_ok=true
    fi
  fi

  if [ "$setup_ok" = "false" ]; then
    body="{\"username\":\"$LAKEFS_INSTALLATION_USER_NAME\"}"
    if curl -fsS -X POST -H "Content-Type: application/json" -H "Accept: application/json" -d "$body" "$LAKEFS_ENDPOINT/api/v1/setup_lakefs" >"$setup_response" 2>/dev/null; then
      setup_ok=true
      echo "[WARN] setup_lakefs con credenciales predefinidas no aplicado; se usaron credenciales generadas."
    fi
  fi

  if [ "$setup_ok" = "true" ]; then
    # Si lakeFS devolvió credenciales, las persistimos para próximos reinicios.
    setup_access_key="$(jq -r '.access_key_id // .key.access_key_id // empty' "$setup_response" 2>/dev/null || true)"
    setup_secret_key="$(jq -r '.secret_access_key // .key.secret_access_key // empty' "$setup_response" 2>/dev/null || true)"
    if [ -n "$setup_access_key" ] && [ -n "$setup_secret_key" ]; then
      export LAKECTL_CREDENTIALS_ACCESS_KEY_ID="$setup_access_key"
      export LAKECTL_CREDENTIALS_SECRET_ACCESS_KEY="$setup_secret_key"
      save_admin_credentials
      echo "[OK] Credenciales admin recibidas desde setup_lakefs."
    fi
  fi
  rm -f "$setup_response"

  # Validación final del estado.
  final_state="$(setup_state_json)"
  setup_is_initialized "$final_state" || { echo "No se pudo completar setup_lakefs automaticamente." >&2; exit 1; }
  echo "[OK] setup_lakefs confirmado."
}

ensure_comm_prefs() {
  [ "$LAKEFS_SETUP_COMM_PREFS_SKIP" = "true" ] && { echo "[INFO] Se omite setup_comm_prefs por configuracion."; return 0; }
  [ -n "$LAKEFS_SETUP_COMM_PREFS_EMAIL" ] || { echo "[WARN] LAKEFS_SETUP_COMM_PREFS_EMAIL vacio; se omite comm_prefs."; return 0; }

  state="$(setup_state_json)"
  [ -n "$state" ] || { echo "[WARN] No se pudo consultar setup_lakefs."; return 0; }
  echo "$state" | grep -q '"comm_prefs_missing"[[:space:]]*:[[:space:]]*true' || { echo "[OK] setup_comm_prefs ya estaba completado."; return 0; }

  body="{\"email\":\"$LAKEFS_SETUP_COMM_PREFS_EMAIL\",\"featureUpdates\":$LAKEFS_SETUP_COMM_PREFS_FEATURE_UPDATES,\"securityUpdates\":$LAKEFS_SETUP_COMM_PREFS_SECURITY_UPDATES}"
  if curl -fsS -X POST -H "Content-Type: application/json" -H "Accept: application/json" -d "$body" "$LAKEFS_ENDPOINT/api/v1/setup_comm_prefs" >/dev/null 2>&1; then
    echo "[OK] setup_comm_prefs completado."
  else
    echo "[WARN] No se pudo completar setup_comm_prefs con $LAKEFS_SETUP_COMM_PREFS_EMAIL."
  fi
}

wait_admin_auth() {
  echo "Esperando a que lakeFS acepte credenciales admin..."
  tries=0
  until lakectl --no-color repo list --amount 1 >/dev/null 2>&1; do
    tries=$((tries + 1))
    if [ "$tries" -eq 30 ]; then
      load_admin_credentials && echo "[INFO] Reintentando con credenciales guardadas."
    fi
    [ "$tries" -lt 60 ] || return 1
    sleep 2
  done
  return 0
}

# -----------------------------------------------------------------------------
# 4) Parseo de casos y repos desde config/cases_config.json
# -----------------------------------------------------------------------------
extract_case_repo_pairs() {
  # Salida: "CASE|repo-base" (únicos, normalizados).
  jq -r '
    .. | objects
    | select(has("case") and has("lakefs_repo"))
    | [.case, .lakefs_repo]
    | @tsv
  ' "$CASES_CONFIG_PATH" \
    | awk -F '\t' '
        NF == 2 {
          c = toupper($1); gsub(/^[[:space:]]+|[[:space:]]+$/, "", c)
          r = tolower($2); gsub(/^[[:space:]]+|[[:space:]]+$/, "", r); gsub(/_/, "-", r)
          if (c != "" && r != "") print c "|" r
        }
      ' \
    | sort -u
}

# -----------------------------------------------------------------------------
# 5) Operaciones de repositorio (crear repo/main/hook)
# -----------------------------------------------------------------------------
ensure_repo() {
  repo="$1"
  out="$(mktemp)"

  if lakectl --no-color repo create "lakefs://$repo" "local://$repo" --default-branch main >"$out" 2>&1; then
    echo "[OK] Repositorio creado: $repo"
    rm -f "$out"
    return 0
  fi

  # Fallback si namespace principal ya está ocupado.
  if grep -qi "storage namespace already in use" "$out"; then
    if lakectl --no-color repo create "lakefs://$repo" "local://bootstrap/$repo" --default-branch main >"$out" 2>&1; then
      echo "[OK] Repositorio creado: $repo (namespace local://bootstrap/$repo)"
      rm -f "$out"
      return 0
    fi
  fi

  if already_exists "$out"; then
    echo "[OK] Repositorio ya existe: $repo"
    rm -f "$out"
    return 0
  fi

  cat "$out" >&2
  rm -f "$out"
  return 1
}

ensure_main_branch() {
  repo="$1"
  lakectl --no-color branch show "lakefs://$repo/main" >/dev/null 2>&1 && { echo "[OK] Rama main disponible: $repo"; return 0; }

  src="$(lakectl --no-color branch list "lakefs://$repo" | awk 'NR>2 && $1 != "" {print $1; exit}')"
  [ -n "$src" ] || { echo "No se encontro rama origen para crear main en $repo" >&2; return 1; }

  out="$(mktemp)"
  if lakectl --no-color branch create "lakefs://$repo/main" -s "lakefs://$repo/$src" >"$out" 2>&1 || already_exists "$out"; then
    echo "[OK] Rama main disponible: $repo"
    rm -f "$out"
    return 0
  fi

  cat "$out" >&2
  rm -f "$out"
  return 1
}

ensure_hook_in_main() {
  repo="$1"
  hook_uri="lakefs://$repo/main/$HOOK_TARGET_PATH"
  tmp="$(mktemp)"

  if lakectl --no-color fs cat "$hook_uri" >"$tmp" 2>/dev/null && cmp -s "$HOOK_FILE_PATH" "$tmp"; then
    echo "[OK] Hook ya configurado en $repo/main"
    rm -f "$tmp"
    return 0
  fi
  rm -f "$tmp"

  lakectl --no-color fs upload "$hook_uri" -s "$HOOK_FILE_PATH" >/dev/null
  lakectl --no-color commit "lakefs://$repo/main" -m "ci: configurar hook retrain" --meta managed_by=lakefs-entrypoint >/dev/null
  echo "[OK] Hook configurado en $repo/main"
}

# -----------------------------------------------------------------------------
# 6) Usuarios/políticas (ACL server)
# -----------------------------------------------------------------------------
create_user_credential() {
  user_id="$1"
  access_key_id="$2"
  secret_key="$3"
  enc_key="$(printf '%s' "$access_key_id" | jq -sRr @uri)"
  enc_secret="$(printf '%s' "$secret_key" | jq -sRr @uri)"
  url="$LAKEFS_AUTHZ_ENDPOINT/auth/users/$user_id/credentials?access_key=$enc_key&secret_key=$enc_secret"
  curl -fsS -X POST -u "${LAKECTL_CREDENTIALS_ACCESS_KEY_ID}:${LAKECTL_CREDENTIALS_SECRET_ACCESS_KEY}" "$url" >/dev/null
}

list_user_access_keys() {
  user_id="$1"
  api_get_auth "$LAKEFS_AUTHZ_ENDPOINT/auth/users/$user_id/credentials" | jq -r '.results[]?.access_key_id'
}

reset_user_credentials() {
  user_id="$1"
  desired_access_key_id="$2"
  desired_secret_key="$3"

  keys="$(list_user_access_keys "$user_id" || true)"
  if [ -n "$keys" ]; then
    for key in $keys; do
      [ -n "$key" ] && api_delete_auth "$LAKEFS_AUTHZ_ENDPOINT/auth/users/$user_id/credentials/$key" || true
    done
  fi

  create_user_credential "$user_id" "$desired_access_key_id" "$desired_secret_key"
}

build_case_policy_document() {
  policy_id="$1"
  user_id="$2"
  out_file="$3"
  prefix="$(repo_prefix_for_user "$user_id")"

  # Lectura global + escritura solo en "<prefix>--*".
  cat > "$out_file" <<EOF
{
  "name": "$policy_id",
  "statement": [
    {"action":["fs:ReadConfig"],"effect":"allow","resource":"*"},
    {"action":["fs:ListRepositories"],"effect":"allow","resource":"*"},
    {"action":["fs:ReadRepository","fs:ReadCommit","fs:ListBranches","fs:ListTags","fs:ListObjects"],"effect":"allow","resource":"arn:lakefs:fs:::repository/*"},
    {"action":["fs:ReadBranch"],"effect":"allow","resource":"arn:lakefs:fs:::repository/*/branch/*"},
    {"action":["fs:ReadObject","fs:ListObjects"],"effect":"allow","resource":"arn:lakefs:fs:::repository/*/object/*"},
    {"action":["fs:ReadTag"],"effect":"allow","resource":"arn:lakefs:fs:::repository/*/tag/*"},

    {"action":["fs:CreateRepository","fs:DeleteRepository"],"effect":"allow","resource":"arn:lakefs:fs:::repository/$prefix--*"},
    {"action":["fs:AttachStorageNamespace"],"effect":"allow","resource":"arn:lakefs:fs:::namespace/local://$prefix--*"},
    {"action":["fs:AttachStorageNamespace"],"effect":"allow","resource":"arn:lakefs:fs:::namespace/local://bootstrap/$prefix--*"},
    {"action":["fs:RevertBranch","fs:CreateBranch","fs:DeleteBranch","fs:CreateCommit"],"effect":"allow","resource":"arn:lakefs:fs:::repository/$prefix--*/branch/*"},
    {"action":["fs:WriteObject","fs:DeleteObject"],"effect":"allow","resource":"arn:lakefs:fs:::repository/$prefix--*/object/*"},
    {"action":["fs:CreateTag","fs:DeleteTag"],"effect":"allow","resource":"arn:lakefs:fs:::repository/$prefix--*/tag/*"}
  ]
}
EOF
}

ensure_group_exists() {
  group_id="$1"
  body="$(mktemp)"
  printf '{"id":"%s"}' "$group_id" >"$body"
  code="$(curl -sS -o /dev/null -w "%{http_code}" -X POST -H "Content-Type: application/json" --data-binary "@$body" "$LAKEFS_AUTHZ_ENDPOINT/auth/groups")"
  rm -f "$body"
  case "$code" in 201) echo "[OK] Grupo creado: $group_id" ;; 409) echo "[OK] Grupo ya existe: $group_id" ;; *) return 1 ;; esac
}

upsert_policy() {
  policy_id="$1"
  doc="$2"
  url="$LAKEFS_AUTHZ_ENDPOINT/auth/policies/$policy_id"
  current="$(curl -sS -o /dev/null -w "%{http_code}" "$url")"

  if [ "$current" = "200" ]; then
    code="$(curl -sS -o /dev/null -w "%{http_code}" -X PUT -H "Content-Type: application/json" --data-binary "@$doc" "$url")"
    [ "$code" = "200" ] || return 1
    echo "[OK] Politica actualizada: $policy_id"
    return 0
  fi

  code="$(curl -sS -o /dev/null -w "%{http_code}" -X POST -H "Content-Type: application/json" --data-binary "@$doc" "$LAKEFS_AUTHZ_ENDPOINT/auth/policies")"
  case "$code" in
    201) echo "[OK] Politica creada: $policy_id" ;;
    409)
      code="$(curl -sS -o /dev/null -w "%{http_code}" -X PUT -H "Content-Type: application/json" --data-binary "@$doc" "$url")"
      [ "$code" = "200" ] || return 1
      echo "[OK] Politica actualizada (post-conflict): $policy_id"
      ;;
    *) return 1 ;;
  esac
}

attach_policy_to_group() {
  group_id="$1"
  policy_id="$2"
  code="$(curl -sS -o /dev/null -w "%{http_code}" -X PUT "$LAKEFS_AUTHZ_ENDPOINT/auth/groups/$group_id/policies/$policy_id")"
  case "$code" in 201|409) return 0 ;; *) return 1 ;; esac
}

add_user_to_group() {
  group_id="$1"
  user_id="$2"
  code="$(curl -sS -o /dev/null -w "%{http_code}" -X PUT "$LAKEFS_AUTHZ_ENDPOINT/auth/groups/$group_id/members/$user_id")"
  case "$code" in 201|409) return 0 ;; *) return 1 ;; esac
}

ensure_case_permissions() {
  case_id="$1"
  user_id="$2"
  group_id="case-$case_id"
  policy_id="case-${case_id}-repos-rw"
  doc="$(mktemp)"

  build_case_policy_document "$policy_id" "$user_id" "$doc"
  ensure_group_exists "$group_id" || { rm -f "$doc"; return 1; }
  upsert_policy "$policy_id" "$doc" || { rm -f "$doc"; return 1; }
  attach_policy_to_group "$group_id" "$policy_id" || { rm -f "$doc"; return 1; }
  add_user_to_group "$group_id" "$user_id" || { rm -f "$doc"; return 1; }
  rm -f "$doc"

  echo "[OK] Permisos aplicados: $user_id -> $group_id -> $policy_id"
}

# -----------------------------------------------------------------------------
# 7) Bootstrap por caso
# -----------------------------------------------------------------------------
bootstrap_case_repos_as_user() {
  user_id="$1"
  repos_file="$2"

  # Guardamos credenciales admin y cambiamos temporalmente a credenciales del caso.
  admin_key="$LAKECTL_CREDENTIALS_ACCESS_KEY_ID"
  admin_secret="$LAKECTL_CREDENTIALS_SECRET_ACCESS_KEY"
  export LAKECTL_CREDENTIALS_ACCESS_KEY_ID="$user_id"
  export LAKECTL_CREDENTIALS_SECRET_ACCESS_KEY="$LAKEFS_CASE_USERS_SECRET_KEY"

  # Verificación explícita: evitar crear repos con otra identidad por error.
  current_user="$(api_current_user_id 2>/dev/null || true)"
  if [ "$current_user" != "$user_id" ]; then
    export LAKECTL_CREDENTIALS_ACCESS_KEY_ID="$admin_key"
    export LAKECTL_CREDENTIALS_SECRET_ACCESS_KEY="$admin_secret"
    echo "Credenciales inesperadas al bootstrap. Esperado=$user_id, recibido=${current_user:-<vacio>}" >&2
    return 1
  fi
  echo "[OK] Autenticado como $current_user para crear repos del caso."

  while IFS= read -r repo_base; do
    [ -n "$repo_base" ] || continue
    repo="$(owned_repo_name "$user_id" "$repo_base")"
    echo "Procesando repo como $user_id: $repo (base: $repo_base)"
    ensure_repo "$repo" || { export LAKECTL_CREDENTIALS_ACCESS_KEY_ID="$admin_key"; export LAKECTL_CREDENTIALS_SECRET_ACCESS_KEY="$admin_secret"; return 1; }
    ensure_main_branch "$repo" || { export LAKECTL_CREDENTIALS_ACCESS_KEY_ID="$admin_key"; export LAKECTL_CREDENTIALS_SECRET_ACCESS_KEY="$admin_secret"; return 1; }
    ensure_hook_in_main "$repo" || { export LAKECTL_CREDENTIALS_ACCESS_KEY_ID="$admin_key"; export LAKECTL_CREDENTIALS_SECRET_ACCESS_KEY="$admin_secret"; return 1; }
  done < "$repos_file"

  # Restauramos credenciales admin para seguir con el siguiente caso.
  export LAKECTL_CREDENTIALS_ACCESS_KEY_ID="$admin_key"
  export LAKECTL_CREDENTIALS_SECRET_ACCESS_KEY="$admin_secret"
}

ensure_case_users_and_repos() {
  pairs="$1"
  [ "$LAKEFS_CASE_USERS_ENABLE" = "true" ] || { echo "[INFO] Bootstrap de usuarios por caso desactivado."; return 0; }

  cases="$(printf '%s\n' "$pairs" | cut -d '|' -f 1 | sort -u)"
  for case_id in $cases; do
    [ -n "$case_id" ] || continue
    user_id="caso$case_id"

    repos_file="$(mktemp)"
    printf '%s\n' "$pairs" | awk -F '|' -v c="$case_id" '$1 == c {print $2}' | sort -u > "$repos_file"
    if [ ! -s "$repos_file" ]; then
      rm -f "$repos_file"
      continue
    fi

    # 1) Crear usuario (o reutilizar si ya existe).
    out="$(mktemp)"
    if lakectl --no-color auth users create --id "$user_id" >"$out" 2>&1; then
      echo "[OK] Usuario creado: $user_id"
    elif already_exists "$out"; then
      echo "[OK] Usuario ya existe: $user_id"
    else
      cat "$out" >&2
      rm -f "$out" "$repos_file"
      warn_or_fail "No se pudo crear usuario $user_id."
      continue
    fi
    rm -f "$out"

    # 2) Fijar credenciales del caso: access_key=user_id, secret=DEFAULT_USER_PASSWORD.
    out="$(mktemp)"
    if reset_user_credentials "$user_id" "$user_id" "$LAKEFS_CASE_USERS_SECRET_KEY" >"$out" 2>&1; then
      echo "[OK] Credenciales actualizadas para $user_id"
    else
      cat "$out" >&2
      rm -f "$out" "$repos_file"
      warn_or_fail "No se pudo fijar credenciales para $user_id."
      continue
    fi
    rm -f "$out"

    # 3) Aplicar permisos del caso (lectura global + escritura en prefijo propio).
    if ! ensure_case_permissions "$case_id" "$user_id"; then
      rm -f "$repos_file"
      warn_or_fail "No se pudieron aplicar permisos para $user_id."
      continue
    fi

    # 4) Crear/asegurar repos del caso con credenciales del propio usuario.
    if ! bootstrap_case_repos_as_user "$user_id" "$repos_file"; then
      rm -f "$repos_file"
      warn_or_fail "No se pudieron crear/configurar repos de $user_id con sus credenciales."
      continue
    fi

    repos_log="$(tr '\n' ' ' < "$repos_file")"
    rm -f "$repos_file"
    echo "[INFO] Caso $case_id -> usuario $user_id -> repos base: $repos_log"
  done
}

# -----------------------------------------------------------------------------
# 8) Main
# -----------------------------------------------------------------------------
# Validaciones básicas de entorno/archivos.
require_file "$CASES_CONFIG_PATH"
require_file "$HOOK_FILE_PATH"
require_cmd jq
require_cmd curl
require_cmd lakectl

[ -n "${LAKECTL_CREDENTIALS_ACCESS_KEY_ID}" ] || { echo "Faltan credenciales admin (access key)." >&2; exit 1; }
[ -n "${LAKECTL_CREDENTIALS_SECRET_ACCESS_KEY}" ] || { echo "Faltan credenciales admin (secret key)." >&2; exit 1; }
[ "$LAKEFS_CASE_USERS_ENABLE" = "false" ] || [ -n "$LAKEFS_CASE_USERS_SECRET_KEY" ] || { echo "Falta contraseña de usuarios de caso. Configura DEFAULT_USER_PASSWORD (o LAKEFS_CASE_USERS_SECRET_KEY)." >&2; exit 1; }

# Arranque/setup base de lakeFS.
wait_lakefs_http
ensure_lakefs_setup
ensure_comm_prefs

# Si no hay auth admin, dejamos el servicio vivo pero omitimos bootstrap.
if ! wait_admin_auth; then
  warn_or_fail "No se pudo autenticar con credenciales admin. Se omite bootstrap de repos/usuarios."
  exit 0
fi

# Parseo de casos/repos.
pairs="$(extract_case_repo_pairs)"
[ -n "$pairs" ] || { echo "No se han encontrado pares case/lakefs_repo en $CASES_CONFIG_PATH" >&2; exit 1; }
repos="$(printf '%s\n' "$pairs" | cut -d '|' -f 2 | sort -u)"
[ -n "$repos" ] || { echo "No se han encontrado repositorios en $CASES_CONFIG_PATH" >&2; exit 1; }
echo "Repos base detectados: $(echo "$repos" | tr '\n' ' ')"

# Bootstrap completo por caso.
ensure_case_users_and_repos "$pairs"

echo "Bootstrap de lakeFS completado."
