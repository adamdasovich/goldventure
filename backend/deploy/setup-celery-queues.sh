#!/bin/bash
# Split the single Celery worker into three queue-dedicated workers.
#
# Pairs with CELERY_TASK_ROUTES in backend/config/settings.py. Run this BEFORE
# deploying that setting — the moment those routes are live, nothing publishes
# to the legacy `celery` queue any more, and any queue without a consumer
# silently swallows every task routed to it.
#
#   scrape       bulk crawling. Browser-heavy. Also drains the legacy `celery`
#                queue, which still holds ~400 mixed tasks from before the split.
#                Drop `,celery` from -Q once that backlog is gone.
#   interactive  user-triggered onboarding. Browser-heavy but usually idle;
#                must never queue behind `scrape`.
#   default      health checks, cleanups, prices, emails, reports. Light.
#
# Memory: the box is 7.8 GB with ~2.4 GB free and has OOM-killed Celery twice
# (2026-08-03, 2026-08-10). The old single unit capped at MemoryMax=3G; these
# three sum to 3.2G rather than tripling it. Chromium children live in the
# spawning unit's cgroup, so the scrape worker gets the biggest share.
#
# Node names MUST be distinct — two workers sharing one produces
# DuplicateNodenameWarning and silently breaks `celery inspect` (cost a day on
# 2026-08-14).

set -euo pipefail

VENV=/var/www/goldventure/backend/venv/bin/celery
WORKDIR=/var/www/goldventure/backend

echo "==> Writing generic cgroup reaper"
cat > /usr/local/sbin/celery-reap.sh <<'REAPER'
#!/bin/bash
# ExecStopPost reaper. Takes the unit name as $1 and kills only what is left in
# THAT unit's own cgroup — never a bare `pkill -f celery`, which cross-kills
# sibling units and, with Restart=always on both, causes restart storms.
# systemd's KillMode=control-group already handles the normal path; this is the
# belt-and-braces net for Playwright/Chromium children outliving the pool.
set -u
UNIT="${1:-}"
[ -n "$UNIT" ] || exit 0

CG="/sys/fs/cgroup/system.slice/${UNIT}/cgroup.procs"
[ -r "$CG" ] || exit 0

SELF=$$
PARENT=${PPID:-0}

# Snapshot first: the file shrinks as we kill, which would truncate a live read.
mapfile -t PIDS < "$CG" 2>/dev/null || exit 0

for pid in "${PIDS[@]}"; do
    [ -z "$pid" ] && continue
    [ "$pid" = "$SELF" ] && continue
    [ "$pid" = "$PARENT" ] && continue
    kill -9 "$pid" 2>/dev/null
done
exit 0
REAPER
chmod 0755 /usr/local/sbin/celery-reap.sh

# Emit one unit file.
#   $1 unit name  $2 description  $3 -Q value  $4 node name
#   $5 concurrency  $6 MemoryHigh  $7 MemoryMax
write_unit() {
  local unit="$1" desc="$2" queues="$3" node="$4" conc="$5" high="$6" max="$7"
  echo "==> Writing /etc/systemd/system/${unit}"
  cat > "/etc/systemd/system/${unit}" <<UNIT
[Unit]
Description=${desc}
After=network.target redis.service postgresql.service

[Service]
Type=simple
User=root
WorkingDirectory=${WORKDIR}
Environment=DJANGO_SETTINGS_MODULE=config.settings
EnvironmentFile=/etc/goldventure/ga4.env
ExecStart=${VENV} -A config worker \\
    -Q ${queues} \\
    -n ${node} \\
    --concurrency=${conc} \\
    --logfile=/var/log/${unit%.service}.log

# Graceful shutdown - let running tasks finish. CELERY_TASK_ACKS_LATE=True, so
# anything killed mid-flight is redelivered rather than lost.
ExecStop=/bin/bash -c '${VENV} -A config control shutdown 2>/dev/null || true'
TimeoutStopSec=35

ExecStopPost=/usr/local/sbin/celery-reap.sh ${unit}

Restart=always
RestartSec=10

KillMode=control-group
KillSignal=SIGTERM

MemoryHigh=${high}
MemoryMax=${max}

[Install]
WantedBy=multi-user.target
UNIT
}

write_unit celery-scrape.service \
  "Celery Worker (scrape queue) for GoldVenture" \
  "scrape,celery" "scrape@%%h" 2 "1500M" "1800M"

write_unit celery-interactive.service \
  "Celery Worker (interactive queue) for GoldVenture" \
  "interactive" "interactive@%%h" 2 "700M" "900M"

write_unit celery-worker.service \
  "Celery Worker (default queue) for GoldVenture" \
  "default" "default@%%h" 2 "400M" "500M"

echo "==> daemon-reload"
systemctl daemon-reload

echo "==> Enabling + starting"
systemctl enable celery-scrape celery-interactive >/dev/null 2>&1
systemctl restart celery-worker
systemctl start celery-scrape celery-interactive

sleep 12

echo
echo "==> Unit states"
for u in celery-worker celery-scrape celery-interactive celery-beat; do
  printf "  %-22s enabled=%-9s active=%s\n" \
    "$u" "$(systemctl is-enabled $u 2>&1)" "$(systemctl is-active $u 2>&1)"
done

echo
echo "==> Queues with a live consumer"
cd "$WORKDIR"
# shellcheck disable=SC1091
source venv/bin/activate
timeout 45 celery -A config inspect active_queues 2>/dev/null \
  | grep -oE "'name': '[a-z]+'" | sort -u || echo "  (inspect timed out)"

echo
echo "==> Queue depths"
for q in celery default scrape interactive; do
  printf "  %-14s %s\n" "$q" "$(redis-cli llen "$q" 2>/dev/null)"
done
