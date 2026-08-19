#!/bin/bash
# Cap journald.
#
# All Celery worker output goes to the journal (the units' --logfile stays
# near-empty; Django's LOGGING sends to stdout, which systemd captures). The
# scrape worker is verbose — every URL pattern it tries logs a line — so the
# journal reached 2.6 GB with no ceiling configured, growing without bound.
#
# SystemMaxUse caps total on-disk journal. SystemMaxFileSize keeps individual
# files small enough that rotation reclaims space in usable increments rather
# than dropping one enormous file at a time. MaxRetentionSec bounds age as well
# as size, so a quiet month does not preserve stale logs indefinitely.
#
# 800M keeps roughly a fortnight of current volume, which comfortably covers
# the debugging window for a nightly batch, on a box with 53 GB free.

set -euo pipefail

CONF=/etc/systemd/journald.conf

cp "$CONF" "/root/journald.conf.bak-$(date +%Y%m%d-%H%M%S)"

# Idempotent: replace the keys if present (commented or not), else append.
set_key() {
  local key="$1" val="$2"
  if grep -qE "^\s*#?\s*${key}=" "$CONF"; then
    sed -i -E "s|^\s*#?\s*${key}=.*|${key}=${val}|" "$CONF"
  else
    printf '%s=%s\n' "$key" "$val" >> "$CONF"
  fi
}

set_key SystemMaxUse 800M
set_key SystemMaxFileSize 100M
set_key MaxRetentionSec 3week

echo "==> journald.conf now:"
grep -vE '^\s*#|^\s*$' "$CONF"

echo
echo "==> restarting journald"
systemctl restart systemd-journald

echo "==> vacuuming to the new ceiling"
journalctl --vacuum-size=800M 2>&1 | tail -3

echo
echo "==> after:"
journalctl --disk-usage
df -h / | tail -1
