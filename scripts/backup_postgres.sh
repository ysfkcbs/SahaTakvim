#!/usr/bin/env bash
# Daily PostgreSQL backup. Dumps to backups/ (kept out of git), prunes anything
# older than RETENTION_DAYS. Run manually or via the launchd job installed by
# scripts/install_backup_schedule.sh.
set -euo pipefail

cd "$(dirname "$0")/.."

set -a
source .env
set +a

: "${DATABASE_URL:?DATABASE_URL must be set in .env}"

RETENTION_DAYS=14
BACKUP_DIR="backups"
TIMESTAMP="$(date +%Y-%m-%d_%H%M%S)"
DEST="$BACKUP_DIR/sahatakvim_${TIMESTAMP}.dump"

# host.docker.internal only resolves from inside containers; this script runs
# directly on the host (Postgres is a native install), so talk to it via localhost.
HOST_DATABASE_URL="${DATABASE_URL/host.docker.internal/localhost}"

mkdir -p "$BACKUP_DIR"

echo "==> Dumping database to $DEST"
pg_dump "$HOST_DATABASE_URL" -F c -f "$DEST"

echo "==> Pruning backups older than $RETENTION_DAYS days"
find "$BACKUP_DIR" -name "sahatakvim_*.dump" -mtime "+${RETENTION_DAYS}" -delete

# Optional offsite copy hook: once you've configured `rclone` with a remote
# (e.g. `rclone config`), uncomment the line below to also push each dump
# off this machine — protects against losing backups if the Mac itself is
# lost, replaced, or damaged.
# rclone copy "$DEST" remote:sahatakvim-backups/

echo "==> Backup complete: $DEST"
