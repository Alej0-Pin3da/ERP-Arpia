#!/usr/bin/env bash
# =============================================================================
# deploy-frontend.sh — ERP-Arpia frontend deploy (static SPA → cPanel docroot)
#
# Builds the Vue 3 SPA and syncs the static bundle to the app.arpia.com.co
# document root. Static upload only — no server runtime, no Passenger restart.
#
#   bash scripts/deploy-frontend.sh            # deploy latest main
#   bash scripts/deploy-frontend.sh feature/x  # deploy a specific branch
#
# Requires an existing server checkout (scripts/deploy.sh bootstraps CLONE).
# Steps:
#   1) Verify the server clone exists ($CLONE/.git)
#   2) Pull latest code in the clone
#   3) Install frontend deps + build (npm ci / npm run build)
#   4) Verify the build produced dist/
#   5) Sync dist/ to the frontend docroot (FRONTEND_DOCROOT)
#   6) Verification curl against the live URL (FRONTEND_URL)
#
# Adjust CLONE / FRONTEND_DOCROOT / FRONTEND_URL if the server layout changes.
# =============================================================================
set -euo pipefail

REPO_URL="https://github.com/Alej0-Pin3da/ERP-Arpia.git"
# Server checkout — env-overridable (see deploy.sh). Fails fast if missing.
CLONE="${CLONE:-/home/arpiacom/repositories/ERP-Arpia}"
FRONTEND_SRC="$CLONE/frontend"
# app.arpia.com.co document root — ADJUST to the cPanel subdomain docroot.
FRONTEND_DOCROOT="${FRONTEND_DOCROOT:-/home/arpiacom/erp_arpia_frontend}"
# Live URL used for the post-deploy verification curl.
FRONTEND_URL="${FRONTEND_URL:-https://app.arpia.com.co}"
BRANCH="${1:-main}"

echo "==> [1/6] Verifying server clone exists"
if [ ! -d "$CLONE/.git" ]; then
  echo "ERROR: clone not found at $CLONE" >&2
  echo "       Run scripts/deploy.sh once to bootstrap it, or set CLONE." >&2
  exit 1
fi

echo "==> [2/6] Pulling latest code (branch: $BRANCH)"
cd "$CLONE"
git fetch origin
git checkout "$BRANCH"
git pull --ff-only origin "$BRANCH"

echo "==> [3/6] Verifying frontend source and building"
if [ ! -f "$FRONTEND_SRC/package.json" ]; then
  echo "ERROR: frontend/ not found at $FRONTEND_SRC" >&2
  echo "       This branch may predate Phase 6 — checkout a branch that has frontend/." >&2
  exit 1
fi
cd "$FRONTEND_SRC"
npm ci
npm run build

echo "==> [4/6] Verifying build output"
if [ ! -d "$FRONTEND_SRC/dist" ]; then
  echo "ERROR: build did not produce dist/ — aborting sync" >&2
  exit 1
fi

echo "==> [5/6] Syncing dist/ to docroot ($FRONTEND_DOCROOT)"
mkdir -p "$FRONTEND_DOCROOT"
# Clean mirror of dist/: --delete removes stale hashed assets from old builds.
# Keep server-side tweaks in frontend/public/ (e.g. .htaccess) so they survive.
rsync -av --delete \
  --exclude='.env*' \
  --exclude='*.map' \
  --exclude='.DS_Store' \
  --exclude='__MACOSX/' \
  "$FRONTEND_SRC/dist/" "$FRONTEND_DOCROOT/"

echo "==> [6/6] Verification curl"
code="$(curl -s -o /dev/null -w '%{http_code}' "$FRONTEND_URL" || echo 000)"
echo "    $FRONTEND_URL → HTTP $code"
if [ "$code" != "200" ]; then
  echo "    WARNING: expected HTTP 200 — check the docroot and .htaccess" >&2
fi

echo ""
echo "==> Deploy complete. Verify:"
echo "    curl -s -o /dev/null -w '%{http_code}' $FRONTEND_URL"
echo "    curl -s $FRONTEND_URL/ventas | grep -o '<title>[^<]*' | head -1"
