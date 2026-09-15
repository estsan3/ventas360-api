#!/bin/sh
# Corre Flyway migrate contra el schema ventas.
# No corre dentro del proceso de la API: Pre-Deploy / CI / local.
#
# Opciones:
#   FLYWAY_CMD   binario local (ej. flyway). CWD efectivo: flyway/
#   si no: Docker (imagen FLYWAY_IMAGE, default flyway/flyway:11)
#
# Env requeridas contra Postgres (secrets, no commitear):
#   FLYWAY_URL   jdbc:postgresql://host:5432/appdb   (sin schema)
#   FLYWAY_USER  ventas_migrator
#   FLYWAY_PASSWORD
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
FLYWAY_DIR="$ROOT_DIR/flyway"
FLYWAY_IMAGE="${FLYWAY_IMAGE:-flyway/flyway:11}"

FLYWAY_URL="${FLYWAY_URL:-jdbc:postgresql://host.docker.internal:5433/appdb}"
FLYWAY_USER="${FLYWAY_USER:-ventas_migrator}"
FLYWAY_PASSWORD="${FLYWAY_PASSWORD:-ventas_migrator}"
export FLYWAY_URL FLYWAY_USER FLYWAY_PASSWORD

if [ ! -d "$FLYWAY_DIR/sql" ] || [ ! -f "$FLYWAY_DIR/conf/flyway.conf" ]; then
  echo "No se encontró flyway/sql o flyway/conf/flyway.conf en $ROOT_DIR" >&2
  exit 1
fi

echo "Flyway migrate: url=$FLYWAY_URL user=$FLYWAY_USER"

if [ -n "${FLYWAY_CMD:-}" ]; then
  (cd "$FLYWAY_DIR" && "$FLYWAY_CMD" -configFiles=conf/flyway.conf migrate)
  exit 0
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "No hay FLYWAY_CMD ni docker. Instalá Flyway CLI o Docker." >&2
  exit 1
fi

docker_network_args=""
jdbc_url="$FLYWAY_URL"
if [ -z "${FLYWAY_DOCKER_NETWORK:-}" ] && command -v docker >/dev/null 2>&1; then
  if (cd "$ROOT_DIR" && docker compose ps -q db >/dev/null 2>&1); then
    db_id=$(cd "$ROOT_DIR" && docker compose ps -q db || true)
    if [ -n "$db_id" ]; then
      FLYWAY_DOCKER_NETWORK=$(docker inspect --format '{{range $k, $v := .NetworkSettings.Networks}}{{println $k}}{{end}}' "$db_id" | head -n 1)
    fi
  fi
fi

if [ -n "${FLYWAY_DOCKER_NETWORK:-}" ]; then
  docker_network_args="--network $FLYWAY_DOCKER_NETWORK"
  case "$jdbc_url" in
    *host.docker.internal*|*localhost*|*127.0.0.1*)
      jdbc_url="jdbc:postgresql://db:5432/appdb"
      ;;
  esac
  echo "Docker network: $FLYWAY_DOCKER_NETWORK → $jdbc_url"
else
  docker_network_args="--add-host=host.docker.internal:host-gateway"
fi

# shellcheck disable=SC2086
docker run --rm \
  $docker_network_args \
  -v "$FLYWAY_DIR/sql:/flyway/sql" \
  -v "$FLYWAY_DIR/conf:/flyway/conf" \
  -e "FLYWAY_URL=$jdbc_url" \
  -e "FLYWAY_USER=$FLYWAY_USER" \
  -e "FLYWAY_PASSWORD=$FLYWAY_PASSWORD" \
  "$FLYWAY_IMAGE" \
  -connectRetries=60 \
  migrate
