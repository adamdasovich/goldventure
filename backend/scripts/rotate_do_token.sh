#!/bin/bash
# Rotate the DigitalOcean API token across every place that holds it.
#
# The token lives in TWO files, which is what broke the 2026-08-13 rotation:
# Django/Celery read backend/.env, but gpu-orchestrator.service reads
# backend/gpu_orchestrator.env via EnvironmentFile. Updating only .env leaves
# the orchestrator authenticating with a revoked token, and it fails at the
# point it tries to create a droplet — not at startup, so nothing looks wrong
# until a GPU job is queued.
#
# The token is read from a hidden prompt rather than an argument so it never
# reaches shell history, process listings, or a chat transcript. It is
# validated against the DO API before anything is written, so a typo cannot
# leave the box half-rotated.
#
#   bash scripts/rotate_do_token.sh

set -euo pipefail

ENV_FILE=/var/www/goldventure/backend/.env
ORCH_FILE=/var/www/goldventure/backend/gpu_orchestrator.env

for f in "$ENV_FILE" "$ORCH_FILE"; do
    [ -f "$f" ] || { echo "missing: $f" >&2; exit 1; }
    grep -q '^DO_API_TOKEN=' "$f" || { echo "no DO_API_TOKEN line in $f" >&2; exit 1; }
done

printf 'Paste the NEW DigitalOcean token (input hidden), then press Enter: '
read -rs NEW_TOKEN
printf '\n'

[ -n "$NEW_TOKEN" ] || { echo "empty token, aborting" >&2; exit 1; }
case "$NEW_TOKEN" in
    dop_v1_*) ;;
    *) echo "that does not look like a DO token (expected dop_v1_...), aborting" >&2; exit 1 ;;
esac

echo "Validating against the DigitalOcean API..."
code=$(curl -s -o /dev/null -w '%{http_code}' \
    -H "Authorization: Bearer $NEW_TOKEN" \
    'https://api.digitalocean.com/v2/droplets?per_page=1')
if [ "$code" != "200" ]; then
    echo "token rejected by DO (HTTP $code) — nothing written" >&2
    exit 1
fi
echo "  token is valid and can read droplets"

# Write via a 600 temp file in the same directory so the replace is atomic and
# the secret is never briefly world-readable.
update() {
    local file="$1" tmp
    tmp=$(mktemp "$(dirname "$file")/.rotate.XXXXXX")
    chmod 600 "$tmp"
    NEW_TOKEN="$NEW_TOKEN" awk '
        /^DO_API_TOKEN=/ { print "DO_API_TOKEN=" ENVIRON["NEW_TOKEN"]; next }
        { print }
    ' "$file" > "$tmp"
    chown --reference="$file" "$tmp" 2>/dev/null || true
    chmod --reference="$file" "$tmp" 2>/dev/null || true
    mv "$tmp" "$file"
    echo "  updated $file"
}

update "$ENV_FILE"
update "$ORCH_FILE"

a=$(grep '^DO_API_TOKEN=' "$ENV_FILE")
b=$(grep '^DO_API_TOKEN=' "$ORCH_FILE")
[ "$a" = "$b" ] || { echo "files disagree after write — investigate" >&2; exit 1; }
echo "  both files agree"

echo "Restarting services that hold the token..."
systemctl restart gpu-orchestrator
systemctl reload gunicorn || true
systemctl restart celery-worker celery-scrape celery-interactive celery-beat

sleep 8
systemctl is-active --quiet gpu-orchestrator \
    && echo "  gpu-orchestrator is active" \
    || { echo "  gpu-orchestrator FAILED to start" >&2; journalctl -u gpu-orchestrator -n 20 --no-pager >&2; exit 1; }

unset NEW_TOKEN
echo
echo "Rotation complete. Remaining manual step:"
echo "  Revoke the OLD token at https://cloud.digitalocean.com/account/api/tokens"
