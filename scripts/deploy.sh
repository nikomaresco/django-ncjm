#!/bin/sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
COMPOSE_FILE=${COMPOSE_FILE:-"$ROOT_DIR/.docker/ncjm-prod.yml"}
ENV_FILE=${ENV_FILE:-"$ROOT_DIR/.docker/production.env"}
STATE_DIR=${STATE_DIR:-"$ROOT_DIR/.deploy"}
RELEASE=${1:-$(git -C "$ROOT_DIR" rev-parse --short=12 HEAD)}

if [ ! -f "$ENV_FILE" ]; then
    echo "Missing production environment file: $ENV_FILE" >&2
    exit 1
fi

mkdir -p "$STATE_DIR/backups"
chmod 700 "$STATE_DIR" "$STATE_DIR/backups"

export NCJM_APP_IMAGE="ncjm-app:$RELEASE"
export NCJM_NGINX_IMAGE="ncjm-nginx:$RELEASE"
export NCJM_ENV_FILE="$ENV_FILE"

dc() {
    docker compose --project-name ncjm --env-file "$ENV_FILE" --file "$COMPOSE_FILE" "$@"
}

if [ -f "$STATE_DIR/current-release" ]; then
    cp "$STATE_DIR/current-release" "$STATE_DIR/previous-release"
fi

echo "Building release $RELEASE..."
dc build web nginx

echo "Starting PostgreSQL and waiting for health..."
dc up --detach db

BACKUP_PATH="$STATE_DIR/backups/postgres-before-$RELEASE.dump"
echo "Creating pre-migration PostgreSQL checkpoint: $BACKUP_PATH"
dc exec -T db sh -c 'exec pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' > "$BACKUP_PATH"

echo "Applying forward database migrations..."
dc --profile ops run --rm migrate

echo "Starting application release..."
dc up --detach --no-build web nginx

echo "Waiting for the loopback health endpoint..."
attempt=0
until curl --fail --silent --show-error \
    --header 'Host: nikoscornyjokemachine.com' \
    --header 'X-Forwarded-Proto: https' \
    "http://127.0.0.1:${NCJM_HTTP_PORT:-8001}/health/" >/dev/null; do
    attempt=$((attempt + 1))
    if [ "$attempt" -ge 20 ]; then
        echo "Release health check failed. Run scripts/rollback.sh after reviewing migration compatibility." >&2
        exit 1
    fi
    sleep 3
done

printf '%s\n' "$RELEASE" > "$STATE_DIR/current-release"
dc ps
echo "Release $RELEASE is healthy on the private loopback upstream."
