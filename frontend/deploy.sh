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

# Wait for the site to answer after a restart. `next start` takes about a second
# to bind, so anything asked before that gets a 502 from nginx — including the
# rollback's own check, which is how a rollback could otherwise report success
# over a site that never came back up.
wait_for_site() {
  local attempts="${1:-30}"
  local i
  for ((i = 0; i < attempts; i++)); do
    sleep 1
    if curl -sf -o /dev/null "$SITE/"; then return 0; fi
  done
  return 1
}

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
  # restart, not reload: a rolling reload would leave instances running the
  # build being rolled back for as long as the roll takes, and the reason we
  # are here is that that build is broken. Take them all down at once.
  pm2 restart "$APP" >/dev/null || true

  # Check the rollback, rather than announcing it. Returning while the site is
  # still down is how "rolled back" becomes a sentence nobody should trust.
  if wait_for_site 30; then
    printf '\033[31mRolled back — the previous build is live again and answering.\033[0m\n' >&2
  else
    printf '\033[31mROLLED BACK BUT THE SITE IS NOT ANSWERING. Check `pm2 logs %s` now.\033[0m\n' \
      "$APP" >&2
  fi
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

# Carry the previous build's static assets across, without overwriting any of
# the new ones (-n). Chunk filenames are content-hashed, so the two sets barely
# overlap and the old files are simply extra.
#
# Two things need them. A page already open in someone's browser goes on asking
# for the chunks its HTML named, and during a rolling reload the instance not
# yet cycled is still serving that HTML — while the files it refers to have just
# been moved to $PREV_DIR. Without this, both get a 404 on a stylesheet and
# report it as a MIME type error, which is the confusing failure this repo has
# hit before.
if [ -d "$PREV_DIR/static" ]; then
  cp -rn "$PREV_DIR/static/." "$LIVE_DIR/static/" 2>/dev/null || true
fi

# Rolling reload, not restart: pm2 cycles the cluster's instances one at a time,
# so the other keeps answering. A restart takes every instance down together —
# measured at 4 consecutive 502s over ~0.87s, on every single deploy.
log "Reloading $APP (rolling, one instance at a time)"
pm2 reload "$APP" >/dev/null

wait_for_site 30 || fail "site did not answer within 30s of the restart"

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
# The numbers the API publishes must still match the database. Four count bugs
# shipped in one week and every one was a plausible wrong figure with no error.
# check_counts covers three of them: ?status=open returning all 297 financings
# when 21 were open, the homepage counting 1.9k scraped articles instead of
# 17.9k company releases, and a company list that would have kept serving
# soft-deleted rows. None broke a page, so none of the checks above catch them.
#
# It does NOT cover the fourth — "500+ companies" hardcoded in page copy against
# a database of 396. check_counts drives the API through Django's test client and
# never reads the frontend, so no assertion here can see a number typed into a
# component. That is deliberate rather than pending: several pages carry a
# legitimate "500+" about the TSXV market as a whole, so a check that scanned
# rendered copy for company-count claims would fire on true statements. It would
# cry wolf, and a check nobody trusts is worse than no check. Hardcoded copy
# stays a review problem.
#
# Deliberately NOT part of the rollback: a count mismatch means the copy is
# wrong, not that the build is broken. Rolling back would restore an older build
# carrying the same wrong numbers. So this warns loudly and leaves the deploy up.
log "Checking published counts against the database"
if ( cd ../backend && ./venv/bin/python manage.py check_counts ); then
  echo "  counts agree with the database"
else
  echo ""
  echo "WARNING: published counts no longer match the database."
  echo "  The deploy stands - this is a copy/data problem, not a broken build."
  echo "  Run: cd backend && ./venv/bin/python manage.py check_counts"
fi

log "Deployed. Every page and asset checked returned 200."
echo "Previous build kept at $PREV_DIR until the next deploy."
pm2 list | grep "$APP" || true
