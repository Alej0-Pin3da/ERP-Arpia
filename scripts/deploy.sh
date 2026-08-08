#!/usr/bin/env bash
# =============================================================================
# deploy.sh — ERP-Arpia production deploy (cPanel / Passenger)
#
# Bootstraps the server clone if missing, then runs the full deploy:
#   bash deploy.sh            # deploy latest main
#   bash deploy.sh feature/x  # deploy a specific branch
#
# Steps:
#   1) Clone the repo if the clone dir does not exist (bootstrap)
#   2) Pull latest code in the clone
#   3) Sync backend to the app dir
#   4) Run alembic migrations
#   5) Restart the Passenger app
#   6) (Optional) Deploy the frontend — enabled with DEPLOY_FRONTEND=1
#
# Adjust CLONE / APP / VENV / REPO_URL if the server layout changes.
# Frontend docroot / URL live in scripts/deploy-frontend.sh.
# =============================================================================
set -euo pipefail

REPO_URL="https://github.com/Alej0-Pin3da/ERP-Arpia.git"
CLONE="/home/arpiacom/repositories/ERP-Arpia"
APP="/home/arpiacom/erp_arpia/backend"
VENV="/home/arpiacom/virtualenv/erp_arpia/backend/3.11/bin"
BRANCH="${1:-main}"

echo "==> [1/6] Bootstrap: ensuring clone exists"
if [ ! -d "$CLONE/.git" ]; then
  echo "    Clone not found, creating $CLONE"
  mkdir -p "$(dirname "$CLONE")"
  git clone "$REPO_URL" "$CLONE"
else
  echo "    Clone already exists at $CLONE"
fi

echo "==> [2/6] Pulling latest code (branch: $BRANCH)"
cd "$CLONE"
git fetch origin
git checkout "$BRANCH"
git pull --ff-only origin "$BRANCH"

echo "==> [3/6] Syncing backend to app dir"
# rsync contents of the repo backend/ into the app dir.
# Excludes keep local server state (venv, .env, logs, cache, tmp).
mkdir -p "$APP"
rsync -av --delete \
  --exclude='.venv/' \
  --exclude='__pycache__/' \
  --exclude='.env' \
  --exclude='stderr.log' \
  --exclude='tmp/' \
  --exclude='public/' \
  "$CLONE/backend/" "$APP/"

echo "==> [4/6] Running migrations"
cd "$APP"
source "$VENV/activate"
alembic upgrade head

echo "==> [5/6] Migration state"
alembic current

echo "==> [6/6] Restarting Passenger app"
touch "$APP/passenger_wsgi.py"

# =============================================================================
# Optional step 7: frontend deploy (static SPA -> app.arpia.com.co docroot).
# Disabled by default so backend deploys behave exactly as before.
# Enable with:  DEPLOY_FRONTEND=1 bash scripts/deploy.sh [branch]
# The frontend is a static bundle (no Passenger restart needed); this just
# builds frontend/ and syncs dist/ to FRONTEND_DOCROOT in deploy-frontend.sh.
# =============================================================================
if [ "${DEPLOY_FRONTEND:-0}" = "1" ]; then
  echo "==> [7/7] Deploying frontend"
  bash "$CLONE/scripts/deploy-frontend.sh" "$BRANCH"
else
  echo "==> [7/7] Skipping frontend deploy (set DEPLOY_FRONTEND=1 to enable)"
fi

echo ""
echo "==> Deploy complete. Verify:"
echo "    curl https://api.arpia.com.co/health"
echo "    curl https://api.arpia.com.co/api/v1/openapi.json | grep -o 'devoluciones' | head -1"
