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
# Deliberately outside /var/www/goldventure: a backup of an env file is a full
# copy of every live secret and must never sit in a git working tree.
BACKUP_DIR=/root/.secret-rotation-backups

red(){ printf '\033[31m%s\033[0m\n' "$*"; }
grn(){ printf '\033[32m%s\033[0m\n' "$*"; }
fp(){ printf '%s' "$1" | sha256sum | cut -c1-12; }

# `set -u` turns a missing option argument into an "unbound variable" abort with
# no indication of which flag was at fault.
need_arg(){ [ "$#" -ge 2 ] && [ -n "${2:-}" ] || { red "option $1 requires a value"; exit 1; }; }

while [ $# -gt 0 ]; do
  case "$1" in
    --generate) GENERATE=1 ;;
    --files) need_arg "$@"; FILES="$(printf '%s' "$2" | tr ',' ' ')"; shift ;;
    --prefix) need_arg "$@"; PREFIX="$2"; shift ;;
    --min-len) need_arg "$@"; MINLEN="$2"; shift ;;
    --no-restart) RESTART=0 ;;
    --restart) need_arg "$@"; UNITS="$2"; shift ;;
    *) echo "unknown option: $1"; exit 1 ;;
  esac
  shift
done

# The shell matches the variable with a regex while the Python writer matches it
# literally with startswith(). A name containing regex metacharacters would make
# those two disagree about which lines are affected, so reject it outright.
printf '%s' "$VAR" | grep -qE '^[A-Za-z_][A-Za-z0-9_]*$' \
  || { red "'$VAR' is not a valid environment variable name"; exit 1; }
printf '%s' "$MINLEN" | grep -qE '^[0-9]+$' \
  || { red "--min-len must be a whole number, got '$MINLEN'"; exit 1; }

declare -A BACKUP
restore_all(){ for f in $FILES; do [ -n "${BACKUP[$f]:-}" ] && [ -f "${BACKUP[$f]}" ] && cp -p "${BACKUP[$f]}" "$f"; done; }
cleanup_backups(){ for f in $FILES; do [ -n "${BACKUP[$f]:-}" ] && [ -f "${BACKUP[$f]}" ] && { shred -u "${BACKUP[$f]}" 2>/dev/null || rm -f "${BACKUP[$f]}"; }; done; }

# Used for both the post-write restart and the rollback, so a rollback always
# cycles exactly what the rotation cycled. gunicorn is reloaded rather than
# restarted: ExecStart has no --preload, so each worker re-imports settings and
# re-runs load_dotenv() on HUP, which picks up the new value with no downtime.
restart_units(){
  for u in $UNITS; do
    if ! systemctl cat "$u" >/dev/null 2>&1; then
      red "  unknown unit '$u' -- NOT restarted (typo?)"
      continue
    fi
    if [ "$u" = "gunicorn" ]; then systemctl reload "$u"; else systemctl restart "$u"; fi
    printf "  %-22s %s\n" "$u" "$(systemctl is-active "$u")"
  done
}

echo "=== rotating $VAR in: $FILES ==="
NFILES=0; PRESENT=0; OLD=""
for f in $FILES; do
  NFILES=$((NFILES+1))
  [ -f "$f" ] || { red "  missing file: $f"; exit 1; }
  if grep -qE "^${VAR}=" "$f"; then
    PRESENT=$((PRESENT+1))
    v=$(grep -E "^${VAR}=" "$f" | head -1 | cut -d= -f2-)
    if [ -n "$v" ]; then
      printf "  %-58s present  sha256:%s\n" "$f" "$(fp "$v")"
      [ -z "$OLD" ] && OLD="$v"
      [ "$v" = "$OLD" ] || red "  NOTE: value differs between files (drift)"
    else
      # Distinct from "no line at all": the variable is declared but unset, which
      # is a perfectly normal thing to be filling in for the first time.
      printf "  %-58s present but EMPTY\n" "$f"
    fi
  else
    printf "  %-58s no %s line\n" "$f" "$VAR"
  fi
done
[ "$PRESENT" -gt 0 ] || { red "$VAR has no line in any of those files. Nothing changed."; exit 1; }
if [ "$PRESENT" -ne "$NFILES" ]; then
  red "  WARNING: $VAR is missing from $((NFILES - PRESENT)) of $NFILES file(s)."
  red "  Those files will NOT be updated, which leaves them inconsistent."
fi

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
# OLD is empty when every occurrence was blank, in which case there is nothing
# to be identical to and this check does not apply.
if [ -n "$OLD" ] && [ "$(fp "$NEW")" = "$(fp "$OLD")" ]; then
  red "That is the value already installed. Nothing changed."; exit 1
fi

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
  mkdir -p "$BACKUP_DIR" && chmod 700 "$BACKUP_DIR"
  b="$BACKUP_DIR/$(basename "$f").rotbak.$$"; cp -p "$f" "$b"; chmod 600 "$b"; BACKUP[$f]="$b"
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
# The temp file must live in the target directory for os.replace to be atomic,
# which puts a full copy of every secret in the env file inside a git working
# tree until the rename. Prefixed so .gitignore can name it, and removed on any
# failure so it cannot survive a crash between the two.
fd, tmp = tempfile.mkstemp(prefix='.envrot.', dir=os.path.dirname(path))
try:
    with os.fdopen(fd, 'w', encoding='utf-8') as fh:
        fh.writelines(lines)
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)
except BaseException:
    try:
        os.unlink(tmp)
    except OSError:
        pass
    raise
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
  restart_units
  sleep 10
fi

# --- verify ------------------------------------------------------------
echo
echo "=== verifying ==="
cd /var/www/goldventure/backend
# Not every secret is a Django setting. DO_API_TOKEN, DO_SSH_KEY_ID and
# DB_PASSWORD are read straight from os.environ by gpu_orchestrator.py and
# gpu_worker.py, which are standalone processes -- so demanding the value
# appear on `settings` would fail a perfectly good rotation.
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
    print('  %s is not a Django setting -- the file check below is the proof' % var)

# EVERY file is checked, not just when the value is absent from settings.
# `settings` reflects backend/.env alone, so a variable that lives in two files
# -- DB_PASSWORD and DO_API_TOKEN both do -- could pass the settings check while
# the second file still held the old value. That silent drift is exactly what
# broke the 2026-08-13 rotation and what rotate_do_token.sh exists to prevent.
missing = 0
for path in files:
    found = None
    for line in open(path, encoding='utf-8'):
        if line.startswith(var + '='):
            found = line.split('=', 1)[1].strip()
    if found is None:
        print('    %-58s no %s line' % (path, var))
        missing += 1
        continue
    ok = fp(found) == expect
    print('    %-58s sha256:%s %s' % (path, fp(found), 'OK' if ok else 'MISMATCH'))
    if not ok:
        raise SystemExit('  %s does not hold the new value' % path)
if missing:
    print('  NOTE: %d file(s) had no %s line and were left untouched' % (missing, var))

from core.models import Company
print('  DB reachable:', Company.objects.filter(is_deleted=False).count(), 'companies')
PY
)
rc=$?
printf '%s\n' "$OUT" | sed 's/^/ /'
if [ $rc -ne 0 ]; then
  red "Verification FAILED -- restoring and restarting."
  restore_all
  [ "$RESTART" = "1" ] && restart_units
  cleanup_backups
  red "Rolled back. Backups shredded."; exit 1
fi

# Only meaningful when this rotation actually cycled the running services.
if [ "$RESTART" = "1" ]; then
  for path in / /pricing /api/platform-stats/; do
    printf "  %-24s %s\n" "$path" "$(curl -s -o /dev/null -w '%{http_code}' "https://juniorminingintelligence.com$path")"
  done
fi

cleanup_backups
echo
grn "DONE. $VAR is now sha256:$(fp "$NEW")  (backups shredded)"
