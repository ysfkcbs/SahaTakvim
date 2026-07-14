#!/usr/bin/env bash
# One-time bootstrap: obtains the first Let's Encrypt certificate for DOMAIN.
# Safe to re-run — certbot skips issuance if a valid certificate already exists.
#
# Prerequisites before running this:
#   - Router forwards external 80/443 to this machine.
#   - DNS A record for DOMAIN points at this machine's public IP.
#   - docker compose is NOT already running with the full (HTTPS) nginx config,
#     since that config references certificate files that don't exist yet.
set -euo pipefail

cd "$(dirname "$0")/.."

set -a
source .env
set +a

: "${DOMAIN:?DOMAIN must be set in .env}"
: "${CERTBOT_EMAIL:?CERTBOT_EMAIL must be set in .env}"

ACTIVE_CONF="nginx/conf.d/sahatakvim.conf"
BOOTSTRAP_CONF="nginx/bootstrap/sahatakvim-bootstrap.conf"
BACKUP_CONF="nginx/conf.d/sahatakvim.conf.bak"

echo "==> Backing up the full nginx config and switching to HTTP-only bootstrap config"
cp "$ACTIVE_CONF" "$BACKUP_CONF"
cp "$BOOTSTRAP_CONF" "$ACTIVE_CONF"

echo "==> Starting web + nginx with the bootstrap config"
docker compose up -d web nginx

echo "==> Requesting certificate for $DOMAIN"
docker compose run --rm --entrypoint certbot certbot certonly \
  --webroot -w /var/www/certbot \
  -d "$DOMAIN" \
  --email "$CERTBOT_EMAIL" \
  --agree-tos --no-eff-email

echo "==> Restoring the full (HTTPS) nginx config"
mv "$BACKUP_CONF" "$ACTIVE_CONF"

echo "==> Starting certbot's renewal loop and reloading nginx with the HTTPS config"
docker compose up -d certbot
docker compose exec nginx nginx -s reload

echo "==> Done. https://$DOMAIN should now be serving a valid certificate."
