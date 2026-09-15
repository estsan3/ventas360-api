#!/bin/sh
# Crea DB appdb (si falta), roles ventas_migrator / ventas_app, search_path y privilegios.
# Uso local:
#   PGHOST=localhost PGPORT=5433 PGUSER=ventas360 PGPASSWORD=ventas360 ./scripts/bootstrap-roles.sh
# En Compose (profile flyway) las variables las inyecta el servicio flyway-bootstrap.
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
SQL_FILE="${BOOTSTRAP_SQL:-$SCRIPT_DIR/sql/bootstrap-roles.sql}"

PGHOST="${PGHOST:-localhost}"
PGPORT="${PGPORT:-5433}"
PGUSER="${PGUSER:-ventas360}"
PGPASSWORD="${PGPASSWORD:-ventas360}"
ADMIN_DB="${ADMIN_DB:-postgres}"
APP_DB="${APP_DB:-appdb}"
VENTAS_MIGRATOR_PASSWORD="${VENTAS_MIGRATOR_PASSWORD:-ventas_migrator}"
VENTAS_APP_PASSWORD="${VENTAS_APP_PASSWORD:-ventas_app}"
export PGHOST PGPORT PGUSER PGPASSWORD

case "$APP_DB" in
  *[!a-zA-Z0-9_]*)
    echo "APP_DB inválido: $APP_DB" >&2
    exit 1
    ;;
esac

if [ ! -f "$SQL_FILE" ]; then
  echo "No se encontró $SQL_FILE" >&2
  exit 1
fi

if ! command -v psql >/dev/null 2>&1; then
  echo "psql no está en PATH. Instalá el cliente de Postgres o corré el profile compose flyway." >&2
  exit 1
fi

run_psql() {
  target_db=$1
  shift
  psql -v ON_ERROR_STOP=1 -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$target_db" "$@"
}

echo "Bootstrap Flyway: host=$PGHOST port=$PGPORT db=$APP_DB"

exists=$(run_psql "$ADMIN_DB" -tAc "SELECT 1 FROM pg_database WHERE datname = '${APP_DB}'")
if [ "$exists" != "1" ]; then
  echo "Creando database ${APP_DB}"
  run_psql "$ADMIN_DB" -c "CREATE DATABASE ${APP_DB}"
else
  echo "Database ${APP_DB} ya existe"
fi

ensure_role() {
  role_name=$1
  role_pwd=$2
  # stdout a /dev/null: el SELECT format() no debe imprimir el password.
  run_psql "$ADMIN_DB" \
    --set=role_name="$role_name" \
    --set=role_pwd="$role_pwd" <<'SQL' >/dev/null
SELECT format('CREATE ROLE %I LOGIN PASSWORD %L', :'role_name', :'role_pwd')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :'role_name');
\gexec
SELECT format('ALTER ROLE %I LOGIN PASSWORD %L', :'role_name', :'role_pwd');
\gexec
SELECT format('ALTER ROLE %I SET search_path = ventas', :'role_name');
\gexec
SQL
  echo "Rol $role_name OK"
}

ensure_role ventas_migrator "$VENTAS_MIGRATOR_PASSWORD"
ensure_role ventas_app "$VENTAS_APP_PASSWORD"

run_psql "$ADMIN_DB" --set=app_db="$APP_DB" <<'SQL' >/dev/null
SELECT format('GRANT CONNECT ON DATABASE %I TO ventas_migrator', :'app_db');
\gexec
SELECT format('GRANT CONNECT ON DATABASE %I TO ventas_app', :'app_db');
\gexec
SQL

run_psql "$APP_DB" -f "$SQL_FILE"

echo "Bootstrap OK: schema ventas, roles ventas_migrator / ventas_app, search_path y default privileges."
