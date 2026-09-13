#!/bin/sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
COMPOSE_FILE=${COMPOSE_FILE:-"$ROOT_DIR/.docker/ncjm-prod.yml"}
ENV_FILE=${ENV_FILE:-"$ROOT_DIR/.docker/production.env"}
STATE_DIR=${STATE_DIR:-"$ROOT_DIR/.deploy"}

if [ ! -f "$ENV_FILE" ]; then
    echo "Missing production environment file: $ENV_FILE" >&2
    exit 1
fi

if [ ! -f "$STATE_DIR/previous-release" ]; then
    echo "No previous release is recorded." >&2
    exit 1
fi

if [ "${ROLLBACK_DATABASE_COMPATIBLE:-}" != "YES" ]; then
    echo "Refusing image rollback without ROLLBACK_DATABASE_COMPATIBLE=YES." >&2
    echo "Confirm the previous image can run against the current forward-migrated schema." >&2
    exit 1
fi

PREVIOUS_RELEASE=$(cat "$STATE_DIR/previous-release")
CURRENT_RELEASE=$(cat "$STATE_DIR/current-release")
export NCJM_APP_IMAGE="ncjm-app:$PREVIOUS_RELEASE"
export NCJM_NGINX_IMAGE="ncjm-nginx:$PREVIOUS_RELEASE"
export NCJM_ENV_FILE="$ENV_FILE"

dc() {
    docker compose --project-name ncjm --env-file "$ENV_FILE" --file "$COMPOSE_FILE" "$@"
}

echo "Rolling application images back from $CURRENT_RELEASE to $PREVIOUS_RELEASE..."
dc up --detach --no-build web nginx

attempt=0
until curl --fail --silent --show-error \
    --header 'Host: nikoscornyjokemachine.com' \
    --header 'X-Forwarded-Proto: https' \
    "http://127.0.0.1:${NCJM_HTTP_PORT:-8001}/health/" >/dev/null; do
    attempt=$((attempt + 1))
    if [ "$attempt" -ge 20 ]; then
        echo "Rollback image health check failed. Preserve data and investigate; do not delete volumes." >&2
        exit 1
    fi
    sleep 3
done

printf '%s\n' "$PREVIOUS_RELEASE" > "$STATE_DIR/current-release"
printf '%s\n' "$CURRENT_RELEASE" > "$STATE_DIR/previous-release"
dc ps
echo "Application images rolled back. The database was not reversed."
