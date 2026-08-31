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
# On failure the previous build is put back and the process restarted, so a
# broken deploy costs a restart rather than an outage.

set -euo pipefail

APP="goldventure-frontend"
SITE="https://juniorminingintelligence.com"
BUILD_DIR=".next-build"
LIVE_DIR=".next"
PREV_DIR=".next-previous"

cd "$(dirname "$0")"

log() { printf '\n\033[1m==> %s\033[0m\n' "$*"; }
fail() { printf '\n\033[31mFAILED: %s\033[0m\n' "$*" >&2; exit 1; }

if [ "${1:-}" = "--install" ]; then
  log "npm install"
  # Never --omit=optional here: Tailwind 4 compiles through lightningcss, whose
  # platform binary ships as an optional dependency, and dropping it breaks
  # every build with an error that points at globals.css.
  npm install
fi

log "Building into $BUILD_DIR (live site still served from $LIVE_DIR)"
rm -rf "$BUILD_DIR"
# The grep filters an unsuppressable warning from Next's vendored browserslist;
# set -o pipefail (from set -e above plus this) keeps a failed build fatal.
set -o pipefail
NEXT_DIST_DIR="$BUILD_DIR" npm run build 2>&1 | grep -v baseline-browser-mapping

[ -f "$BUILD_DIR/BUILD_ID" ] || fail "no BUILD_ID in $BUILD_DIR — build produced nothing usable"

log "Swapping $BUILD_DIR into place"
rm -rf "$PREV_DIR"
mv "$LIVE_DIR" "$PREV_DIR"
mv "$BUILD_DIR" "$LIVE_DIR"

log "Restarting $APP"
pm2 restart "$APP" >/dev/null

# Give the server a moment to bind before asking it anything.
for _ in $(seq 1 20); do
  sleep 1
  curl -sf -o /dev/null "$SITE/" && break
done

log "Verifying assets (a 200 on / proves nothing — chunks are what break)"
bad=""
for path in / /pricing /companies /open-financings /investor-tools; do
  page_status=$(curl -s -o /dev/null -w '%{http_code}' "$SITE$path")
  [ "$page_status" = "200" ] || bad="$bad\n  $page_status $path"
  while read -r asset; do
    [ -n "$asset" ] || continue
    asset_status=$(curl -s -o /dev/null -w '%{http_code}' "$SITE$asset")
    [ "$asset_status" = "200" ] || bad="$bad\n  $asset_status $asset"
  done < <(curl -s "$SITE$path" | grep -oE '/_next/static/[a-zA-Z0-9/._-]+\.(js|css)' | sort -u)
done

if [ -n "$bad" ]; then
  printf '\n\033[31mBroken after deploy:%b\033[0m\n' "$bad"
  log "Rolling back to the previous build"
  rm -rf "$LIVE_DIR"
  mv "$PREV_DIR" "$LIVE_DIR"
  pm2 restart "$APP" >/dev/null
  fail "rolled back — the previous build is live again"
fi

log "Deployed. Every page and asset checked returned 200."
pm2 list | grep "$APP" || true
