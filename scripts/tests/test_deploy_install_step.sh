#!/usr/bin/env bash
# Regression tests for the backend dependency install step of scripts/deploy.sh.
#
# Covers: install ordering against the rsync, migrations and the Passenger
# restart; the exact pip argv; abort-on-pip-failure; the missing-venv guard; the
# LF-only git blob; and bash syntax. No network, no pytest, no server access.
#
#   bash scripts/tests/test_deploy_install_step.sh
#
# Why it exists: the deploy script never installed requirements.txt in the venv,
# so a new dependency reached production as an ImportError (a missing slowapi put
# a 500 on every endpoint). This pins that step and where it runs.
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
DEPLOY="$REPO_ROOT/scripts/deploy.sh"
SCRATCH="$(mktemp -d)"
trap 'rm -rf "$SCRATCH"' EXIT
export HOME="$SCRATCH/home" TMPDIR="$SCRATCH/tmp"
mkdir -p "$HOME" "$TMPDIR" "$SCRATCH/bin" "$SCRATCH/app" "$SCRATCH/venv/bin" "$SCRATCH/clone"

fail() { echo "FAIL: $1" >&2; exit 1; }
pass() { echo "ok - $1"; }

# --- stubs: every external command the deploy window calls, recorded in order ---
for c in rsync alembic touch; do
  printf '#!/usr/bin/env bash\nprintf "%%s [%%s]\\n" "%s" "$*" >> "$ORDER_LOG"\nexit 0\n' "$c" > "$SCRATCH/bin/$c"
  chmod +x "$SCRATCH/bin/$c"
done
cat > "$SCRATCH/venv/bin/python" <<'EOS'
#!/usr/bin/env bash
printf 'python [%s]\n' "$*" >> "$ORDER_LOG"
[ "${PIP_FAIL:-0}" = "1" ] && exit 3
exit 0
EOS
chmod +x "$SCRATCH/venv/bin/python"
printf 'export PATH="%s/venv/bin:$PATH"\n' "$SCRATCH" > "$SCRATCH/venv/bin/activate"
printf 'slowapi>=0.1.9\n' > "$SCRATCH/app/requirements.txt"

# --- the deploy windows, extracted by ANCHOR (line numbers would rot) ----------
line_of() { grep -n -F -- "$1" "$DEPLOY" | head -1 | cut -d: -f1; }
window() { # ancla-inicio ancla-fin salida
  local a b
  a="$(line_of "$1")"; b="$(line_of "$2")"
  [ -n "$a" ] && [ -n "$b" ] \
    || fail "no encontre las anclas '$1' / '$2' en scripts/deploy.sh"
  sed -n "${a},${b}p" "$DEPLOY" > "$3"
}
run_window() { # archivo   (env: APP VENV CLONE PATH ORDER_LOG PIP_FAIL)
  bash -c 'set -euo pipefail; source "$1"' _ "$1"
}

window 'mkdir -p "$APP"' 'touch "$APP/passenger_wsgi.py"' "$SCRATCH/order.sh"
window 'Installing backend dependencies' '-r "$APP/requirements.txt"' "$SCRATCH/guard.sh"

lineno() { grep -nF -- "$1" "$SCRATCH/order.log" | head -1 | cut -d: -f1; }

# --- S1 + S2: happy path order and exact command line -------------------------
: > "$SCRATCH/order.log"
ORDER_LOG="$SCRATCH/order.log" APP="$SCRATCH/app" VENV="$SCRATCH/venv/bin" \
  CLONE="$SCRATCH/clone" PATH="$SCRATCH/bin:$PATH" \
  run_window "$SCRATCH/order.sh" || fail "el camino feliz aborto (S1)"

grep -qxF "python [-m pip install --no-input --disable-pip-version-check -r $SCRATCH/app/requirements.txt]" \
  "$SCRATCH/order.log" || fail "la invocacion de pip no es la esperada (S2)"

r="$(lineno 'rsync [')"; p="$(lineno 'pip install')"
m="$(lineno 'alembic [upgrade')"; t="$(lineno 'passenger_wsgi.py')"
[ -n "$r" ] && [ -n "$p" ] && [ -n "$m" ] && [ -n "$t" ] || fail "falta un paso en el log (S1)"
[ "$r" -lt "$p" ] && [ "$p" -lt "$m" ] && [ "$p" -lt "$t" ] \
  || fail "las dependencias no se instalan despues del rsync y antes de migrar/reiniciar (S1)"
pass "S1: instala despues del rsync y antes de migraciones + restart"
pass "S2: linea exacta de pip"

# --- S3a: pip fallando aborta antes de migrar y antes de reiniciar -----------
: > "$SCRATCH/order.log"
ORDER_LOG="$SCRATCH/order.log" APP="$SCRATCH/app" VENV="$SCRATCH/venv/bin" \
  CLONE="$SCRATCH/clone" PIP_FAIL=1 PATH="$SCRATCH/bin:$PATH" \
  run_window "$SCRATCH/order.sh" && fail "pip fallando no aborto el deploy (S3)"
grep -qF 'alembic' "$SCRATCH/order.log" && fail "corrieron migraciones tras fallar pip (S3)"
grep -qF 'passenger_wsgi.py' "$SCRATCH/order.log" && fail "se reinicio Passenger tras fallar pip (S3)"
pass "S3: pip fallando aborta antes de migraciones y del restart"

# --- S3b: venv ausente: mensaje claro, exit != 0, y no corre nada mas --------
: > "$SCRATCH/order.log"
ORDER_LOG="$SCRATCH/order.log" APP="$SCRATCH/app" VENV="$SCRATCH/no-venv/bin" \
  CLONE="$SCRATCH/clone" PATH="$SCRATCH/bin:$PATH" \
  run_window "$SCRATCH/guard.sh" 2> "$SCRATCH/guard.err" \
  && fail "el venv ausente no aborto el deploy (S3)"
grep -qF 'no venv python at' "$SCRATCH/guard.err" || fail "no aparece el mensaje del guard (S3)"
[ ! -s "$SCRATCH/order.log" ] || fail "el guard corrio algo antes de fallar (S3)"
pass "S3: venv ausente aborta con su mensaje y sin tocar nada"

# --- S4: lo que git guarda debe ser LF (bytes, no un patron de grep) ---------
cr="$(git -C "$REPO_ROOT" cat-file blob :scripts/deploy.sh | tr -cd '\r' | wc -c | tr -d ' ')"
[ "$cr" = "0" ] || fail "el blob de git tiene $cr bytes CR: bash moriria en el servidor (S4)"
bash -n "$DEPLOY" || fail "deploy.sh no pasa bash -n (S4)"
pass "S4: el blob de git es solo LF y pasa bash -n"

echo "ALL PASS"
