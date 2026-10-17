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
# Frontend vive en la RAIZ del repo (package.json / src/ / dist/), no en frontend/.
FRONTEND_SRC="$CLONE"
# app.arpia.com.co document root — ADJUST to the cPanel subdomain docroot.
FRONTEND_DOCROOT="${FRONTEND_DOCROOT:-/home/arpiacom/app.arpia.com.co}"
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

# npm is often NOT on the SSH PATH on cPanel. Probe common locations and, if
# needed, prepend the first found nodevenv bin dir so `npm` resolves below.
if ! command -v npm >/dev/null 2>&1; then
  for cand in /home/*/nodevenv/*/*/bin /opt/cpanel/ea-nodejs*/bin; do
    if [ -x "$cand/npm" ]; then
      export PATH="$cand:$PATH"
      echo "    npm not on PATH — using $cand"
      break
    fi
  done
fi
if ! command -v npm >/dev/null 2>&1; then
  echo "ERROR: npm not found. Install Node.js in cPanel (Setup Node.js App)" >&2
  echo "       or add npm to PATH." >&2
  exit 1
fi

if [ ! -f "$FRONTEND_SRC/package.json" ]; then
  echo "ERROR: package.json not found at $FRONTEND_SRC" >&2
  echo "       Expected frontend at repo root — checkout a branch that has package.json at root." >&2
  exit 1
fi
cd "$FRONTEND_SRC"
npm ci

# Platform-native binaries. package-lock.json is generated on Windows, so it
# only pins the win32 builds of rollup / esbuild / tailwind-oxide /
# lightningcss; `npm ci` installs exactly what the lock lists, so on Linux
# those packages cannot load their native module at build time
# ("Cannot find module @rollup/rollup-linux-x64-gnu"). Install the Linux x64
# binaries at the very versions `npm ci` just installed, then restore the
# lockfile so the clone stays clean for the next `git pull --ff-only`.
restore_lockfile() {
  if ! git -C "$FRONTEND_SRC" diff --quiet -- package-lock.json; then
    git -C "$FRONTEND_SRC" checkout -- package-lock.json
    echo "    package-lock.json restaurado - el clon queda limpio"
  fi
}
trap restore_lockfile EXIT

native_missing=""
require_native() {
  # $1 = package, $2 = parent package whose installed version we mirror
  local pkg="$1" parent="$2" version
  if [ -d "node_modules/$pkg" ]; then
    return 0
  fi
  version="$(node -p "require('./node_modules/$parent/package.json').version" 2>/dev/null || true)"
  if [ -z "$version" ]; then
    echo "ERROR: cannot read $parent version from node_modules" >&2
    exit 1
  fi
  native_missing="$native_missing $pkg@$version"
}

if [ "$(uname -s)" = "Linux" ]; then
  require_native "@rollup/rollup-linux-x64-gnu" "rollup"
  require_native "@esbuild/linux-x64" "esbuild"
  require_native "@tailwindcss/oxide-linux-x64-gnu" "@tailwindcss/oxide"
  require_native "lightningcss-linux-x64-gnu" "lightningcss"

  if [ -n "$native_missing" ]; then
    echo "    native Linux binaries missing from the lock:$native_missing"
    # shellcheck disable=SC2086  # the space-separated list is intentional
    npm install --no-save --no-audit --no-fund $native_missing
  fi
fi

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
# .well-known/ is excluded so Let's Encrypt HTTP-01 challenges survive redeploys.
rsync -av --delete \
  --exclude='.well-known/' \
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
