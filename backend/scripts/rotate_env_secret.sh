#!/bin/bash
# Rotate one secret across one or more env files, safely.
#
#   rotate_env_secret.sh VAR [options]
#     --generate          generate the value (Django SECRET_KEY) instead of prompting
#     --files a,b         env files to update (default: backend/.env)
#     --prefix STR        require the new value to start with STR
#     --min-len N         require at least N characters (default 16)
#     --no-restart        change the files but do not restart services
#     --restart "u1 u2"   units to restart (default: the Django stack)
#
# The value is read with `read -rs`: never echoed, never an argv, so it stays out
# of shell history, the process list and any agent transcript. Every file is
# backed up, rewritten atomically, and restored automatically if verification
# fails. A value is only written once it differs from what is already installed.
set -uo pipefail

VAR="${1:-}"; shift || true
[ -n "$VAR" ] || { echo "usage: rotate_env_secret.sh VAR [--generate] [--files a,b] [--prefix S] [--min-len N] [--no-restart]"; exit 1; }

FILES="/var/www/goldventure/backend/.env"
GENERATE=0; PREFIX=""; MINLEN=16; RESTART=1
UNITS="gunicorn celery-worker celery-scrape celery-interactive celery-beat daphne"
VENV=/var/www/goldventure/backend/venv/bin/python

while [ $# -gt 0 ]; do
  case "$1" in
    --generate) GENERATE=1 ;;
    --files) FILES="$(printf '%s' "$2" | tr ',' ' ')"; shift ;;
    --prefix) PREFIX="$2"; shift ;;
    --min-len) MINLEN="$2"; shift ;;
    --no-restart) RESTART=0 ;;
    --restart) UNITS="$2"; shift ;;
    *) echo "unknown option: $1"; exit 1 ;;
  esac
  shift
done

red(){ printf '\033[31m%s\033[0m\n' "$*"; }
grn(){ printf '\033[32m%s\033[0m\n' "$*"; }
fp(){ printf '%s' "$1" | sha256sum | cut -c1-12; }

declare -A BACKUP
restore_all(){ for f in $FILES; do [ -n "${BACKUP[$f]:-}" ] && [ -f "${BACKUP[$f]}" ] && cp -p "${BACKUP[$f]}" "$f"; done; }
cleanup_backups(){ for f in $FILES; do [ -n "${BACKUP[$f]:-}" ] && [ -f "${BACKUP[$f]}" ] && { shred -u "${BACKUP[$f]}" 2>/dev/null || rm -f "${BACKUP[$f]}"; }; done; }

echo "=== rotating $VAR in: $FILES ==="
FOUND=0; OLD=""
for f in $FILES; do
  [ -f "$f" ] || { red "  missing file: $f"; exit 1; }
  v=$(grep -E "^${VAR}=" "$f" | head -1 | cut -d= -f2-)
  if [ -n "$v" ]; then
    printf "  %-58s present  sha256:%s\n" "$f" "$(fp "$v")"
    [ -z "$OLD" ] && OLD="$v"
    [ "$v" = "$OLD" ] || red "  NOTE: value differs between files (drift)"
    FOUND=$((FOUND+1))
  else
    printf "  %-58s NOT SET\n" "$f"
  fi
done
[ "$FOUND" -gt 0 ] || { red "$VAR not found in any file. Nothing changed."; exit 1; }

# --- obtain the new value ---------------------------------------------
if [ "$GENERATE" = "1" ]; then
  NEW=$($VENV -c 'from django.core.management.utils import get_random_secret_key as g; print(g())')
  echo
  echo "  generated a new $VAR (${#NEW} chars, sha256:$(fp "$NEW"))"
else
  echo
  echo "=== paste the NEW value for $VAR ==="
  echo "  Input is hidden -- nothing appears as you paste. That is normal."
  echo "  A pasted value usually carries a newline and submits itself; if the"
  echo "  prompt moves on, do NOT press Enter again."
  printf "  new value: "
  read -rs NEW; echo
fi

NEW="${NEW#"${NEW%%[![:space:]]*}"}"; NEW="${NEW%"${NEW##*[![:space:]]}"}"
[ -n "$NEW" ] || { red "Empty. Nothing changed."; exit 1; }
[ "${#NEW}" -ge "$MINLEN" ] || { red "Too short (${#NEW} < $MINLEN). Nothing changed."; exit 1; }
if [ -n "$PREFIX" ]; then
  case "$NEW" in "$PREFIX"*) : ;; *) red "Expected it to start with '$PREFIX'. Nothing changed."; exit 1 ;; esac
fi
[ "$(fp "$NEW")" != "$(fp "$OLD")" ] || { red "That is the value already installed. Nothing changed."; exit 1; }

if [ "$GENERATE" != "1" ]; then
  echo
  echo "  entered : ...${NEW: -4}   length ${#NEW}   sha256:$(fp "$NEW")"
  printf "  Correct? [y/N] "
  read -r YN
  case "$YN" in y|Y|yes|YES) ;; *) red "Aborted. Nothing changed."; exit 1 ;; esac
fi

# --- write -------------------------------------------------------------
echo
echo "=== writing ==="
for f in $FILES; do
  grep -qE "^${VAR}=" "$f" || { echo "  $f: no $VAR line, skipping"; continue; }
  b="${f}.rotbak.$$"; cp -p "$f" "$b"; chmod 600 "$b"; BACKUP[$f]="$b"
  VAR_NAME="$VAR" NEW_VALUE="$NEW" $VENV - "$f" <<'PY'
import os, sys, tempfile
path = sys.argv[1]; var = os.environ['VAR_NAME']; new = os.environ['NEW_VALUE']
lines = open(path, encoding='utf-8').readlines()
hits = 0
for i, l in enumerate(lines):
    if l.startswith(var + '='):
        hits += 1; lines[i] = '%s=%s\n' % (var, new)
if hits != 1:
    sys.exit('expected exactly 1 %s line, found %d' % (var, hits))
fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path))
with os.fdopen(fd, 'w', encoding='utf-8') as fh: fh.writelines(lines)
os.chmod(tmp, 0o600); os.replace(tmp, path)
PY
  if [ $? -ne 0 ]; then red "  rewrite failed for $f -- restoring"; restore_all; cleanup_backups; exit 1; fi
  d=$(diff "$b" "$f" | grep -cE '^[<>]'); dv=$(diff "$b" "$f" | grep -E '^[<>]' | grep -cE "^[<>] ${VAR}=")
  if [ "$d" != "2" ] || [ "$dv" != "2" ]; then red "  unexpected diff in $f ($d lines) -- restoring"; restore_all; cleanup_backups; exit 1; fi
  printf "  %-58s updated (1 line, perms %s)\n" "$f" "$(stat -c %a "$f")"
done

# --- restart -----------------------------------------------------------
if [ "$RESTART" = "1" ]; then
  echo
  echo "=== restarting: $UNITS ==="
  for u in $UNITS; do
    systemctl is-enabled "$u" >/dev/null 2>&1 || continue
    if [ "$u" = "gunicorn" ]; then systemctl reload "$u"; else systemctl restart "$u"; fi
    printf "  %-22s %s\n" "$u" "$(systemctl is-active "$u")"
  done
  sleep 10
fi

# --- verify ------------------------------------------------------------
echo
echo "=== verifying ==="
cd /var/www/goldventure/backend
# Not every secret is a Django setting. DO_API_TOKEN, DO_SSH_KEY_ID and
# DB_PASSWORD are read straight from os.environ by gpu_orchestrator.py and
# gpu_worker.py, which are standalone processes -- so demanding the value
# appear on `settings` would fail a perfectly good rotation. Verify against
# settings when the name IS a setting, and against the files themselves when
# it is not.
OUT=$(DJANGO_SETTINGS_MODULE=config.settings VAR_NAME="$VAR" EXPECT_FP="$(fp "$NEW")" TARGET_FILES="$FILES" $VENV - <<'PY' 2>&1
import hashlib, os, django
django.setup()
from django.conf import settings

var    = os.environ['VAR_NAME']
expect = os.environ['EXPECT_FP']
files  = os.environ['TARGET_FILES'].split()
fp     = lambda s: hashlib.sha256((s or '').encode()).hexdigest()[:12]

val = getattr(settings, var, None)
if not val and var == 'DB_PASSWORD':
    val = (settings.DATABASES.get('default') or {}).get('PASSWORD')

if val:
    print('  settings.%s -> sha256:%s' % (var, fp(val)))
    if fp(val) != expect:
        raise SystemExit('  settings holds a DIFFERENT value than was just written')
else:
    print('  %s is not a Django setting -- verifying the files directly' % var)
    for path in files:
        found = None
        for line in open(path, encoding='utf-8'):
            if line.startswith(var + '='):
                found = line.split('=', 1)[1].strip()
        if found is None:
            print('    %-58s no %s line' % (path, var))
            continue
        ok = fp(found) == expect
        print('    %-58s sha256:%s %s' % (path, fp(found), 'OK' if ok else 'MISMATCH'))
        if not ok:
            raise SystemExit('  %s does not hold the new value' % path)

from core.models import Company
print('  DB reachable:', Company.objects.filter(is_deleted=False).count(), 'companies')
PY
)
rc=$?
printf '%s\n' "$OUT" | sed 's/^/ /'
if [ $rc -ne 0 ]; then
  red "Verification FAILED -- restoring and restarting."
  restore_all
  [ "$RESTART" = "1" ] && { systemctl reload gunicorn; systemctl restart celery-worker celery-scrape celery-interactive celery-beat; }
  cleanup_backups
  red "Rolled back. Backups shredded."; exit 1
fi

for u in / /pricing /api/platform-stats/; do
  printf "  %-24s %s\n" "$u" "$(curl -s -o /dev/null -w '%{http_code}' https://juniorminingintelligence.com$u)"
done

cleanup_backups
echo
grn "DONE. $VAR is now sha256:$(fp "$NEW")  (backups shredded)"
