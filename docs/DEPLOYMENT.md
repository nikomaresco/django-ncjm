# NCJM Production Deployment Runbook

This runbook prepares NCJM to run as an isolated Docker Compose project behind a host-managed reverse proxy. It does not authorize or perform changes to the live server by itself.

## Architecture contract

- Host-level Caddy is the only service that owns public ports 80 and 443.
- NCJM's internal Nginx binds only to `127.0.0.1:8001` by default.
- PostgreSQL has no published host port.
- NCJM has its own Compose project, environment file, networks, volume, images, and release state.
- This repository contains no configuration for unrelated applications.
- Caddy forwards `Host`, `X-Forwarded-For`, and `X-Forwarded-Proto`.
- The apex domain is canonical; `www` redirects at the host proxy.

The loopback port is configurable with `NCJM_HTTP_PORT` if the live audit finds a conflict.

## Mandatory host audit

Before the first deployment, record—not change—the following:

```sh
docker ps --all
docker compose ls
docker network ls
docker volume ls
sudo ss -lntup
sudo systemctl --type=service --state=running
sudo systemctl list-timers
sudo nft list ruleset
free -h
df -h
docker system df
```

Also inspect:

- Existing Caddy, Nginx, Apache, and Certbot configuration.
- DigitalOcean cloud-firewall rules.
- DNS for `nikoscornyjokemachine.com` and `www`.
- Current NCJM checkout, image/container names, environment location, SQLite path, static path, and deploy commands.
- Current TLS certificate issuer and renewal owner.

Do not start the new internal Nginx until the selected loopback port is confirmed free. Do not start another public proxy if one already owns 80/443.

## Production environment

Copy the example without committing the resulting file:

```sh
cp .docker/production.env.example .docker/production.env
chmod 600 .docker/production.env
```

Replace every placeholder. `POSTGRES_PASSWORD` and `DJANGO_SECRET_KEY` should be independent long random values. Django constructs its PostgreSQL connection from the `POSTGRES_*` variables; a password does not need to be duplicated in a URL.

Review these deployment-time variables, which may be placed in the shell or a Compose `.env` file rather than the application environment file:

```sh
NCJM_HTTP_PORT=8001
NCJM_WEB_MEMORY_LIMIT=384m
NCJM_WEB_CPU_LIMIT=0.75
NCJM_DB_MEMORY_LIMIT=512m
NCJM_DB_CPU_LIMIT=0.75
NCJM_NGINX_MEMORY_LIMIT=64m
NCJM_NGINX_CPU_LIMIT=0.25
```

The defaults consume at most roughly 960 MiB of container memory plus host/Caddy overhead. Adjust them only after the host audit. A memory limit is a failure boundary, not a capacity guarantee; observe real usage after rollout.

## Images

The multi-stage Dockerfile produces two immutable release images from the same source tree:

- `app`: non-root Python/Gunicorn runtime with dependencies installed from a wheel stage.
- `nginx`: internal Nginx plus static files collected during the build.

Static files are baked into the Nginx image, eliminating a mutable shared static volume. The application container is read-only except for a small `/tmp` tmpfs. Both images should use the same release tag.

Build without starting services:

```sh
RELEASE=$(git rev-parse --short=12 HEAD)
NCJM_APP_IMAGE="ncjm-app:$RELEASE" \
NCJM_NGINX_IMAGE="ncjm-nginx:$RELEASE" \
docker compose --env-file .docker/production.env -f .docker/ncjm-prod.yml build web nginx
```

## Health checks

- Django/Gunicorn: `GET /health/` returns `{"status":"ok"}` without querying the database or another service.
- Internal Nginx: `GET /nginx-health` returns plain text directly from Nginx.
- PostgreSQL: `pg_isready` checks the configured database and user.

The Django endpoint is a liveness check. Database readiness is represented separately by the PostgreSQL container health and Compose dependency. This prevents a temporary database problem from repeatedly killing otherwise healthy application processes.

After deployment, verify the private upstream before editing Caddy:

```sh
curl --fail --show-error http://127.0.0.1:8001/nginx-health
curl --fail --show-error http://127.0.0.1:8001/health/
curl --fail --show-error -H 'Host: nikoscornyjokemachine.com' -H 'X-Forwarded-Proto: https' http://127.0.0.1:8001/
```

## Host-level Caddy interface

The Caddyfile is host infrastructure and is not stored in this repository. The NCJM portion is conceptually:

```caddyfile
nikoscornyjokemachine.com {
    reverse_proxy 127.0.0.1:8001
}

www.nikoscornyjokemachine.com {
    redir https://nikoscornyjokemachine.com{uri} permanent
}
```

Confirm the actual loopback port, email, global options, logging, and existing host conventions on the server. Validate with `caddy validate` before reload. Reload Caddy rather than restarting it when possible.

Internal Nginx preserves Caddy's `X-Forwarded-Proto` value. Django trusts that header and performs HTTPS redirects at the public boundary. Never expose internal Nginx directly to the public network, because the forwarded-protocol trust assumes requests first passed through the controlled host proxy.

## Ordinary release deployment

`scripts/deploy.sh`:

1. Builds release-tagged application and Nginx images.
2. Starts PostgreSQL and waits for health.
3. Takes a local `pg_dump` checkpoint before schema migration.
4. Runs Django migrations as a one-shot container.
5. Replaces the application and internal Nginx containers.
6. Requires the loopback `/health/` check to pass.
7. Records current and previous image tags under ignored `.deploy/` state.

Run from the repository checkout:

```sh
sh scripts/deploy.sh
```

Or supply an explicit immutable release label:

```sh
sh scripts/deploy.sh 4361a3e
```

Do not run application migrations automatically in the web container entrypoint. Migrations are an explicit release step so failures stop before traffic is switched.

## Application rollback boundaries

Image rollback is intentionally separate from database rollback:

```sh
ROLLBACK_DATABASE_COMPATIBLE=YES sh scripts/rollback.sh
```

The required acknowledgement means an operator has reviewed the migrations and confirmed that the previous image can run against the current schema. The script swaps the application and Nginx images and checks health. It never reverses migrations or restores a volume automatically.

For safe routine rollback, schema changes must use expand/migrate/contract deployment patterns:

1. Add nullable or backward-compatible schema.
2. Deploy code that can use both old and new forms.
3. Backfill separately.
4. Remove old schema only after the rollback window closes.

If a migration is not backward-compatible, forward recovery is preferred: fix the migration or application and deploy a new release. Restore a PostgreSQL dump only during a declared outage after preserving the failed database for diagnosis. Never delete the PostgreSQL volume as a rollback technique.

## SQLite-to-PostgreSQL migration

The migration tool is `scripts/migrate_sqlite_to_postgres.sh`. It uses Django's serializers so model natural keys and application validation conventions are honored. It excludes generated content types, generated permissions, and ephemeral sessions; PostgreSQL creates those through migrations.

The tool never switches Caddy or starts application traffic. It:

1. Copies the SQLite source into a timestamped, permission-restricted artifact directory, verifies the copy by SHA-256, and requires `PRAGMA integrity_check` to return `ok`.
2. Builds the exact application image used for migration.
3. Creates the PostgreSQL schema from Django migrations.
4. Refuses to import if non-generated destination data already exists.
5. Takes a pre-import PostgreSQL dump.
6. Applies current migrations to a separate writable copy of the frozen SQLite snapshot and removes content types/permissions belonging to models no longer installed; the original remains unchanged.
7. Creates deterministic per-model row counts and canonical SHA-256 fingerprints from SQLite.
8. Exports the portable fixture.
9. Imports it into PostgreSQL.
10. Explicitly resets PostgreSQL sequences after importing primary keys.
11. Produces and compares PostgreSQL fingerprints.
12. Runs Django deployment checks.
13. Creates a post-import PostgreSQL logical dump and validates its archive structure.

### Repeatable rehearsal

Rehearsal uses an isolated Compose project and disposable named volume. It does not touch the production `ncjm` Compose project:

```sh
MIGRATION_MODE=rehearsal \
SQLITE_SOURCE=/absolute/path/to/a-copy-of-production.sqlite3 \
sh scripts/migrate_sqlite_to_postgres.sh
```

By default the rehearsal project and its volume are removed after either success or failure. Artifacts remain under `.migration-artifacts/<UTC timestamp>/`. Set `KEEP_REHEARSAL=YES` to retain the isolated PostgreSQL database for manual inspection.

The source must belong to the migration lineage present in the checked-out release. A database that records migrations from another branch must fail rather than be coerced. In particular, the repository's current developer `db.sqlite3` was created on the experimental long-joke branch and cannot be imported into the one-liner schema without an explicit rich-joke preservation design. It is not evidence of the production database's lineage. Confirm the production snapshot's migration history during the host audit.

Repeat the rehearsal from the latest production SQLite copy until it succeeds without manual database edits. Review:

- `sqlite-fingerprint.json`
- `postgres-fingerprint.json`
- `ncjm-data.json`
- `postgres-before-import.dump`
- `postgres-after-import.dump`
- `sqlite-integrity-check.txt`
- command output and elapsed time

Perform application-level checks against a retained rehearsal: random joke, stable ID/slug, search, tags, reaction totals, admin login, approval queue, API reads if enabled, and record counts visible in admin.

### Production cutover prerequisites

Before cutover:

- A rehearsal from a recent production copy has passed.
- The exact release image has passed application tests and deployment checks.
- The new PostgreSQL destination contains no application data.
- The SQLite file path and current writers are known.
- A maintenance window and rollback decision owner are established.
- The old SQLite deployment remains intact and startable.
- The host has enough disk for SQLite copies, the fixture, PostgreSQL data, and dumps.

### Write freeze

The migration is not an online replication system. Every process that can write SQLite must be stopped before the final source copy: old web containers, admin workers, shell/import jobs, scheduled jobs, and any second checkout. Merely putting Caddy into maintenance mode is insufficient if background writers remain.

After stopping writers, copy SQLite and verify that no process has it open. Set the confirmation only after this is true:

```sh
MIGRATION_MODE=cutover \
WRITE_FREEZE_CONFIRMED=YES \
SQLITE_SOURCE=/absolute/path/to/frozen-production.sqlite3 \
sh scripts/migrate_sqlite_to_postgres.sh
```

The tool leaves PostgreSQL running and verified but does not start the new web stack or change routing. Review the artifacts and retained source before running the normal release deployment and switching Caddy.

### Integrity verification

Fingerprint comparison covers every imported Django model, including user/admin/OAuth data and NCJM jokes, tags, join records, and reaction trackers. For each model it compares the row count and a deterministic hash of serialized records and relationships.

Before opening writes, also verify these domain invariants in PostgreSQL:

- Every `JokeTag` references an existing joke and tag.
- Every `ReactionTracker` references an existing joke.
- Joke slugs remain unique and unchanged.
- Reaction JSON values and totals match the SQLite source.
- Approved, queued, and soft-deleted joke counts match.
- Admin authentication succeeds.
- Newly inserted records receive IDs above existing maxima.

The first post-import insert should be performed only in rehearsal. Production remains write-frozen until cutover verification is accepted.

### Migration rollback and forward recovery

Before PostgreSQL accepts any production write, rollback is simple: route traffic back to the unchanged SQLite deployment. Preserve the failed PostgreSQL volume and artifacts for diagnosis.

Once PostgreSQL accepts a write, SQLite is stale. Do not route back to it without a deliberate data reconciliation plan; doing so can lose submissions, reactions, approvals, or administrative changes. After that boundary, prefer forward recovery on PostgreSQL or restore the pre-failure PostgreSQL dump during an outage.

Keep the frozen SQLite source, export fixture, fingerprints, and PostgreSQL checkpoints until the migration has been stable for an explicitly accepted retention window. Removing old data is a separate, reviewed operation.

## First production cutover sequence

1. Complete the host audit and choose a free loopback port.
2. Rehearse SQLite migration from a fresh production copy.
3. Build and retain immutable release images.
4. Enter maintenance mode and freeze every SQLite writer.
5. Run the cutover-mode migration and review integrity artifacts.
6. Start the new web/internal-Nginx stack and test through loopback.
7. Add or update only NCJM's host-level Caddy route and validate it.
8. Reload Caddy and smoke-test HTTPS, redirects, static files, admin, CSRF, absolute URLs, and Analytics configuration.
9. Monitor health, logs, memory, CPU, PostgreSQL connections, and disk.
10. End the write freeze only after the rollback boundary is explicitly accepted.
11. Retain the old SQLite deployment stopped but intact until the recovery window closes.
