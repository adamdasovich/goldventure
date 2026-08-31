#!/usr/bin/env bash
#
# Deploy the Next.js frontend without taking the live site down while it builds.
#
# The problem this solves: `next start` serves out of .next, and `npm run build`
# rewrites that directory in place. For the two to four minutes a build takes,
# the running server hands out chunk URLs it is about to delete and then fails
# to require them — MODULE_NOT_FOUND, a 500 for every visitor, on every deploy.
#
# So: build into .next-build, then move it into place and restart. The live
# directory is untouched until the build has succeeded, and the only exposure is
# the pm2 restart itself, which is about a second.
#
# Usage, from /var/www/goldventure/frontend:
#     ./deploy.sh              # build, swap, restart, verify
#     ./deploy.sh --install    # same, but npm install first (package.json changed)
#
# Anything that goes wrong after the swap — a failed restart, a page or asset
# that is not a 200, an interrupted run — puts the previous build back and
# restarts. A broken deploy costs a restart rather than an outage.

set -euo pipefail

APP="goldventure-frontend"
SITE="https://juniorminingintelligence.com"
BUILD_DIR=".next-build"
LIVE_DIR=".next"
PREV_DIR=".next-previous"
LOCK_FILE="/tmp/goldventure-frontend-deploy.lock"

cd "$(dirname "$0")"

log() { printf '\n\033[1m==> %s\033[0m\n' "$*"; }
fail() { printf '\n\033[31mFAILED: %s\033[0m\n' "$*" >&2; exit 1; }

# One deploy at a time. More than one agent works in this repo, and two runs
# overlapping would have each moving the other's directories mid-flight.
exec 9>"$LOCK_FILE"
flock -n 9 || fail "another deploy is already running (lock: $LOCK_FILE)"

SWAPPED=0
BUILD_LOG=""

cleanup() {
  [ -n "$BUILD_LOG" ] && rm -f "$BUILD_LOG"
  return 0
}

rollback() {
  local status=$?
  cleanup
  # Nothing swapped yet means the live build was never touched.
  [ "$SWAPPED" = "1" ] || exit "$status"

  if [ ! -d "$PREV_DIR" ]; then
    printf '\n\033[31mCannot roll back: %s is gone. The site is serving the new build.\033[0m\n' \
      "$PREV_DIR" >&2
    exit "$status"
  fi

  printf '\n\033[1m==> Rolling back to the previous build\033[0m\n'
  rm -rf "$LIVE_DIR"
  mv "$PREV_DIR" "$LIVE_DIR"
  pm2 restart "$APP" >/dev/null || true
  printf '\033[31mRolled back — the previous build is live again.\033[0m\n' >&2
  exit "$status"
}

# ERR covers a failing command under set -e; INT/TERM cover someone pressing
# Ctrl+C between the swap and the verification, which would otherwise leave an
# unverified build serving.
trap rollback ERR INT TERM

if [ "${1:-}" = "--install" ]; then
  log "npm install"
  # Never --omit=optional here: Tailwind 4 compiles through lightningcss, whose
  # platform binary ships as an optional dependency, and dropping it breaks
  # every build with an error that points at globals.css.
  npm install
fi

log "Building into $BUILD_DIR (live site still served from $LIVE_DIR)"
rm -rf "$BUILD_DIR"

# Log the build and filter for display afterwards, rather than piping into
# grep: piped, the pipeline's status is grep's, so a build that printed only
# filtered lines would look like a failure and a failed build could look fine.
# This way npm's exit status is npm's alone.
BUILD_LOG="$(mktemp)"
if ! NEXT_DIST_DIR="$BUILD_DIR" npm run build >"$BUILD_LOG" 2>&1; then
  grep -v baseline-browser-mapping "$BUILD_LOG" | tail -40
  fail "build failed — $LIVE_DIR untouched, site still serving the old build"
fi
grep -v baseline-browser-mapping "$BUILD_LOG" | tail -12 || true

[ -f "$BUILD_DIR/BUILD_ID" ] || fail "no BUILD_ID in $BUILD_DIR — build produced nothing usable"

log "Swapping $BUILD_DIR into place"
rm -rf "$PREV_DIR"
mv "$LIVE_DIR" "$PREV_DIR"
mv "$BUILD_DIR" "$LIVE_DIR"
SWAPPED=1

log "Restarting $APP"
pm2 restart "$APP" >/dev/null

# Give the server a moment to bind before asking it anything. Written as an if
# rather than `curl ... && break`: under `set -e` a failing curl in an && list
# ends the script, so the first attempt — which almost always fails, the server
# having just restarted — would abort the deploy it is meant to be waiting for.
ready=0
for _ in $(seq 1 30); do
  sleep 1
  if curl -sf -o /dev/null "$SITE/"; then ready=1; break; fi
done
[ "$ready" = "1" ] || fail "site did not answer within 30s of the restart"

log "Verifying assets (a 200 on / proves nothing — chunks are what break)"
bad=""
for path in / /pricing /companies /open-financings /investor-tools; do
  page_status=$(curl -s -o /dev/null -w '%{http_code}' "$SITE$path")
  [ "$page_status" = "200" ] || bad="$bad\n  $page_status $path"
  assets=$(curl -s "$SITE$path" | grep -oE '/_next/static/[a-zA-Z0-9/._-]+\.(js|css)' | sort -u || true)
  # A page that references no chunks at all is a build that produced nothing
  # usable for it, which is exactly the failure this check exists to catch.
  [ -n "$assets" ] || bad="$bad\n  no /_next/static assets referenced by $path"
  while read -r asset; do
    [ -n "$asset" ] || continue
    asset_status=$(curl -s -o /dev/null -w '%{http_code}' "$SITE$asset")
    [ "$asset_status" = "200" ] || bad="$bad\n  $asset_status $asset"
  done <<< "$assets"
done

if [ -n "$bad" ]; then
  printf '\n\033[31mBroken after deploy:%b\033[0m\n' "$bad"
  false   # hands over to the rollback trap
fi

trap - ERR INT TERM
cleanup
log "Deployed. Every page and asset checked returned 200."
echo "Previous build kept at $PREV_DIR until the next deploy."
pm2 list | grep "$APP" || true
