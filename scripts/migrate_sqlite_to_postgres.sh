#!/bin/sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
COMPOSE_FILE=${COMPOSE_FILE:-"$ROOT_DIR/.docker/ncjm-prod.yml"}
ENV_FILE=${ENV_FILE:-"$ROOT_DIR/.docker/production.env"}
SQLITE_SOURCE=${SQLITE_SOURCE:-"$ROOT_DIR/ncjm/db.sqlite3"}
MIGRATION_MODE=${MIGRATION_MODE:-rehearsal}
TIMESTAMP=$(date -u +%Y%m%dT%H%M%SZ)
ARTIFACT_DIR=${ARTIFACT_DIR:-"$ROOT_DIR/.migration-artifacts/$TIMESTAMP"}

# Compose uses this value both to interpolate service env_file entries and to
# load variables for the Compose model itself.
export NCJM_ENV_FILE="$ENV_FILE"

case "$(uname -s)" in
    MINGW*|MSYS*)
        # Pass Docker explicit Windows host paths while preserving container paths.
        COMPOSE_FILE=$(cygpath -m "$COMPOSE_FILE")
        ENV_FILE=$(cygpath -m "$ENV_FILE")
        SQLITE_SOURCE=$(cygpath -m "$SQLITE_SOURCE")
        ARTIFACT_DIR=$(cygpath -m "$ARTIFACT_DIR")
        NCJM_ENV_FILE=$ENV_FILE
        export NCJM_ENV_FILE MSYS_NO_PATHCONV=1
        ;;
esac

if [ ! -f "$ENV_FILE" ]; then
    echo "Missing production environment file: $ENV_FILE" >&2
    exit 1
fi

if [ ! -f "$SQLITE_SOURCE" ]; then
    echo "Missing SQLite source database: $SQLITE_SOURCE" >&2
    exit 1
fi

case "$MIGRATION_MODE" in
    rehearsal)
        PROJECT_NAME=${COMPOSE_PROJECT_NAME:-ncjm-migration-rehearsal}
        case "$PROJECT_NAME" in
            ncjm-migration-rehearsal*) ;;
            *)
                echo "Rehearsal project names must begin with ncjm-migration-rehearsal." >&2
                exit 1
                ;;
        esac
        ;;
    cutover)
        PROJECT_NAME=${COMPOSE_PROJECT_NAME:-ncjm}
        if [ "${WRITE_FREEZE_CONFIRMED:-}" != "YES" ]; then
            echo "Cutover requires WRITE_FREEZE_CONFIRMED=YES after all SQLite writers are stopped." >&2
            exit 1
        fi
        ;;
    *)
        echo "MIGRATION_MODE must be rehearsal or cutover." >&2
        exit 1
        ;;
esac

mkdir -p "$ARTIFACT_DIR"
chmod 700 "$ARTIFACT_DIR"
cp -p "$SQLITE_SOURCE" "$ARTIFACT_DIR/source.sqlite3"
source_hash=$(sha256sum "$SQLITE_SOURCE" | awk '{print $1}')
snapshot_hash=$(sha256sum "$ARTIFACT_DIR/source.sqlite3" | awk '{print $1}')
if [ "$source_hash" != "$snapshot_hash" ]; then
    echo "SQLite snapshot checksum mismatch; refusing to continue." >&2
    exit 1
fi
printf '%s  source.sqlite3\n' "$snapshot_hash" > "$ARTIFACT_DIR/source.sqlite3.sha256"
cp -p "$ARTIFACT_DIR/source.sqlite3" "$ARTIFACT_DIR/source-migrated.sqlite3"

dc() {
    docker compose \
        --project-name "$PROJECT_NAME" \
        --env-file "$ENV_FILE" \
        --file "$COMPOSE_FILE" \
        "$@"
}

cleanup() {
    status=$?
    trap - EXIT
    if [ "$MIGRATION_MODE" = "rehearsal" ] && [ "${KEEP_REHEARSAL:-}" != "YES" ]; then
        echo "Removing the isolated rehearsal project and PostgreSQL volume..."
        dc --profile ops down --volumes --remove-orphans >/dev/null 2>&1 || true
    fi
    exit "$status"
}

trap cleanup EXIT HUP INT TERM

if [ "$MIGRATION_MODE" = "rehearsal" ]; then
    # This is intentionally destructive only to the explicitly guarded rehearsal project.
    dc --profile ops down --volumes --remove-orphans >/dev/null 2>&1 || true
fi

echo "Building the exact application image used for export and import..."
dc build web

echo "Running SQLite integrity_check against the frozen snapshot..."
dc --profile ops run --rm --no-deps \
    -v "$ARTIFACT_DIR/source.sqlite3:/migration/source.sqlite3:ro" \
    migrate python -c \
    "import sqlite3; c=sqlite3.connect('file:/migration/source.sqlite3?mode=ro', uri=True); r=c.execute('PRAGMA integrity_check').fetchall(); print(r); raise SystemExit(0 if r == [('ok',)] else 1)" \
    > "$ARTIFACT_DIR/sqlite-integrity-check.txt"

echo "Starting an isolated PostgreSQL destination..."
dc up --detach db

echo "Creating the destination schema..."
dc --profile ops run --rm migrate

echo "Refusing to merge into a destination that already contains importable data..."
dc --profile ops run --rm migrate \
    python manage.py database_fingerprint --assert-import-target-empty \
    > "$ARTIFACT_DIR/destination-empty.json"

echo "Saving a pre-import PostgreSQL rollback checkpoint..."
dc exec -T db sh -c 'exec pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' \
    > "$ARTIFACT_DIR/postgres-before-import.dump"

echo "Applying current Django migrations to a working copy of the SQLite snapshot..."
dc --profile ops run --rm --no-deps \
    -e DATABASE_URL=sqlite:////migration/out/source-migrated.sqlite3 \
    -v "$ARTIFACT_DIR:/migration/out" \
    migrate python manage.py migrate --noinput

echo "Removing content types and generated permissions for models no longer installed..."
dc --profile ops run --rm --no-deps \
    -e DATABASE_URL=sqlite:////migration/out/source-migrated.sqlite3 \
    -v "$ARTIFACT_DIR:/migration/out" \
    migrate python manage.py remove_stale_contenttypes --noinput

echo "Fingerprinting the migrated SQLite working copy..."
dc --profile ops run --rm --no-deps \
    -e DATABASE_URL=sqlite:////migration/out/source-migrated.sqlite3 \
    -v "$ARTIFACT_DIR:/migration/out:ro" \
    migrate python manage.py database_fingerprint \
    > "$ARTIFACT_DIR/sqlite-fingerprint.json"

echo "Exporting portable Django data from SQLite..."
dc --profile ops run --rm --no-deps \
    -e DATABASE_URL=sqlite:////migration/out/source-migrated.sqlite3 \
    -v "$ARTIFACT_DIR:/migration/out" \
    migrate python manage.py dumpdata \
    --natural-foreign \
    --natural-primary \
    --exclude contenttypes \
    --exclude auth.permission \
    --exclude sessions \
    --indent 2 \
    --output /migration/out/ncjm-data.json

echo "Importing into PostgreSQL..."
dc --profile ops run --rm \
    -v "$ARTIFACT_DIR:/migration/out:ro" \
    migrate python manage.py loaddata /migration/out/ncjm-data.json

echo "Resetting PostgreSQL sequences after explicit primary-key import..."
dc --profile ops run --rm migrate \
    python manage.py sqlsequencereset admin auth ncjm oauth2_provider \
    | dc exec -T db sh -c 'exec psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"'

echo "Fingerprinting PostgreSQL and comparing every imported model..."
dc --profile ops run --rm migrate python manage.py database_fingerprint \
    > "$ARTIFACT_DIR/postgres-fingerprint.json"

if ! cmp -s "$ARTIFACT_DIR/sqlite-fingerprint.json" "$ARTIFACT_DIR/postgres-fingerprint.json"; then
    echo "Migration verification failed. Fingerprints differ; do not cut over." >&2
    diff -u "$ARTIFACT_DIR/sqlite-fingerprint.json" "$ARTIFACT_DIR/postgres-fingerprint.json" || true
    exit 1
fi

echo "Running Django deployment checks against PostgreSQL..."
dc --profile ops run --rm migrate python manage.py check --deploy

echo "Creating and validating a post-import PostgreSQL logical dump..."
dc exec -T db sh -c 'exec pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' \
    > "$ARTIFACT_DIR/postgres-after-import.dump"
dc exec -T db pg_restore --list < "$ARTIFACT_DIR/postgres-after-import.dump" >/dev/null

echo "Migration verified successfully. Artifacts: $ARTIFACT_DIR"

if [ "$MIGRATION_MODE" = "cutover" ]; then
    echo "PostgreSQL is verified but application traffic has not been switched by this script."
    echo "Keep the SQLite source and migration artifacts until the forward-recovery window closes."
fi
