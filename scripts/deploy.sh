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
#   4) Install backend dependencies from requirements.txt into the venv
#   5) Validate production configuration and run alembic migrations
#   6) Restart the Passenger app
#   7) Verify readiness
#   8) (Optional) Deploy the frontend — enabled with DEPLOY_FRONTEND=1
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

echo "==> [3b/6] Installing backend dependencies"
if [ ! -x "$VENV/python" ]; then
  echo "ERROR: no venv python at $VENV — create the Python app in cPanel first." >&2
  exit 1
fi
# A fresh venv, or a package added to requirements.txt, used to reach runtime as an
# ImportError: that is how a missing slowapi put a 500 on every endpoint. Install
# here — after the code sync, before migrations and before Passenger restarts — so
# the restart picks up the new code with its dependencies already in place. Without
# --upgrade, pip only installs what is missing or does not satisfy the pins, so an
# unchanged requirements.txt is a no-op.
"$VENV/python" -m pip install --no-input --disable-pip-version-check \
  -r "$APP/requirements.txt"

echo "==> [4/6] Running migrations"
cd "$APP"
source "$VENV/activate"

echo "    Validating production configuration"
python -c "from app.core.config import settings; raise SystemExit(0 if settings.ENVIRONMENT in ('production', 'staging') else 'ENVIRONMENT must be production or staging');"
echo "    production configuration accepted"
alembic upgrade head

echo "==> [5/6] Migration state"
alembic current

echo "==> [6/6] Restarting Passenger app"
touch "$APP/passenger_wsgi.py"

HEALTHCHECK_URL="${HEALTHCHECK_URL:-https://api.arpia.com.co/health/ready}"
echo "==> Readiness check: $HEALTHCHECK_URL"
if ! curl --fail --silent --show-error "$HEALTHCHECK_URL" >/dev/null; then
  echo "ERROR: Passenger restarted but readiness check failed." >&2
  exit 1
fi

# =============================================================================
# Optional step 8: frontend deploy (static SPA -> app.arpia.com.co docroot).
# Disabled by default so backend deploys behave exactly as before.
# Enable with:  DEPLOY_FRONTEND=1 bash scripts/deploy.sh [branch]
# The frontend is a static bundle (no Passenger restart needed); this just
# builds frontend/ and syncs dist/ to FRONTEND_DOCROOT in deploy-frontend.sh.
# =============================================================================
if [ "${DEPLOY_FRONTEND:-0}" = "1" ]; then
  echo "==> [8/8] Deploying frontend"
  bash "$CLONE/scripts/deploy-frontend.sh" "$BRANCH"
else
  echo "==> [8/8] Skipping frontend deploy (set DEPLOY_FRONTEND=1 to enable)"
fi

echo ""
echo "==> Deploy complete. Verify:"
echo "    curl https://api.arpia.com.co/health"
echo "    curl https://api.arpia.com.co/api/v1/openapi.json | grep -o 'devoluciones' | head -1"
