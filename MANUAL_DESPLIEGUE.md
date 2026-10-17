# Manual de despliegue — ERP-Arpia a producción (cPanel / Passenger)

Cómo llevar `main` al servidor y dejarlo verificado. Backend (API) y frontend (SPA) se despliegan por separado con dos scripts.

## Ruta rápida

1. En el servidor, correr el deploy de backend:
   `bash scripts/deploy.sh main`
2. Si también hay cambios de frontend, correrlo con frontend incluido:
   `DEPLOY_FRONTEND=1 bash scripts/deploy.sh main`
3. Verificar:
   `curl https://api.arpia.com.co/health`
   `curl https://api.arpia.com.co/health/ready`

Si esos tres pasos dan verde, el deploy está OK. El resto de este manual es detalle y solución de problemas.

## Qué hace cada script

| Script | Qué hace |
|--------|----------|
| `scripts/deploy.sh` | Clona (si falta) en `CLONE`, hace pull de la rama, sincroniza `backend/` a `APP` con rsync, valida configuración de producción, corre `alembic upgrade head`, reinicia Passenger (`touch passenger_wsgi.py`) y chequea readiness. El frontend solo corre si `DEPLOY_FRONTEND=1`. |
| `scripts/deploy-frontend.sh` | Verifica el clon, hace pull, instala dependencias (`npm ci`), compila (`npm run build`), verifica `dist/` y lo sincroniza al docroot. Solo sube archivos estáticos, no reinicia nada. |

## Rutas del servidor (defaults, ajustables por variables de entorno)

| Variable | Default | Qué es |
|----------|---------|--------|
| `CLONE` | `/home/arpiacom/repositories/ERP-Arpia` | Checkout git en el servidor |
| `APP` | `/home/arpiacom/erp_arpia/backend` | Backend que sirve Passenger |
| `VENV` | `/home/arpiacom/virtualenv/erp_arpia/backend/3.11/bin` | Virtualenv del backend |
| `FRONTEND_SRC` | `$CLONE` (raíz del repo) | El frontend vive en la raíz (`package.json` / `src/` / `dist/`), no en `frontend/` |
| `FRONTEND_DOCROOT` | `/home/arpiacom/app.arpia.com.co` | Docroot del subdominio `app.arpia.com.co` |
| `HEALTHCHECK_URL` | `https://api.arpia.com.co/health/ready` | Chequeo post-deploy del backend |
| `FRONTEND_URL` | `https://app.arpia.com.co` | Chequeo post-deploy del frontend |

## Pre-requisitos en el servidor (una sola vez)

- Repo clonable: `https://github.com/Alej0-Pin3da/ERP-Arpia.git` (el script lo clona solo si falta).
- Virtualenv Python 3.11 con dependencias instaladas (`requirements.txt`, incluye `a2wsgi` pineado).
- Archivo `.env` real en `APP` (`/home/arpiacom/erp_arpia/backend/.env`). Nunca se pisa: el rsync excluye `.env`, `.venv/`, `__pycache__/`, `stderr.log`, `tmp/` y `public/`.
- Node.js con `npm` visible (cPanel → Setup Node.js App). El script de frontend busca `npm` en el `PATH` y en `nodevenv/*/bin`; si no lo encuentra, aborta con instrucciones.
- `.htaccess` del SPA: vive versionado en `public/.htaccess`, Vite lo copia a `dist/` y el rsync lo deja en el docroot. No es un archivo "del servidor": si falta en `public/`, el `rsync --delete` borra el del docroot y las rutas del SPA (`/ventas`, `/dashboard`) pasan a dar 404 al recargar.
- Desafíos `.well-known/` (Let's Encrypt): viven solo en el docroot y sobreviven porque el rsync los excluye.

## Variables de entorno de producción

Guía: `.env.example` (versionado en el repo, con los mismos defaults que `backend/app/core/config.py`).

Obligatorias en `production` / `staging` (el deploy aborta si no están):

| Variable | Regla |
|----------|-------|
| `DATABASE_URL` | Distinta de los defaults de desarrollo |
| `JWT_SECRET_KEY` | Secreto seguro (no `dev_secret_change_me` ni `CHANGE_ME_...`) |
| `CORS_ORIGINS` | Orígenes explícitos (no solo `localhost`) |
| `ENVIRONMENT` | `production` o `staging` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Máximo 30 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Máximo 60 |

Opcionales (con default sano, el deploy no las exige):

| Variable | Default | Nota |
|----------|---------|------|
| `REDIS_URL` | `redis://localhost:6379/0` | Cola / caché |
| `WOO_WEBHOOK_SECRET` | vacío | Vacío = endpoint de webhooks deshabilitado |
| `OLLAMA_URL` | `http://localhost:11434` | IA local para copy comercial (V6 M5). En shared hosting normalmente no existe: solo el botón "generar copy" devuelve `503`, el resto funciona |
| `OLLAMA_MODEL` | `llama3.1` | — |
| `OLLAMA_TIMEOUT_S` | `60` | — |

## Deploy de backend (paso a paso)

```bash
bash scripts/deploy.sh main
```

1. Bootstrap: si no existe `$CLONE/.git`, clona el repo.
2. Pull: `git fetch origin`, `checkout main`, `pull --ff-only`.
3. Sync: `rsync -av --delete` de `$CLONE/backend/` a `$APP/` (con las exclusiones de arriba).
4. Migraciones: valida `ENVIRONMENT` y corre `alembic upgrade head`, luego muestra `alembic current`.
5. Reinicio: `touch "$APP/passenger_wsgi.py"`.
6. Readiness: `curl --fail $HEALTHCHECK_URL`. Si falla, el script sale con error aunque Passenger haya reiniciado.

Verificación manual:

```bash
curl https://api.arpia.com.co/health
curl https://api.arpia.com.co/health/ready
curl https://api.arpia.com.co/api/v1/openapi.json | grep -o 'devoluciones' | head -1
```

Migraciones de referencia: 55 archivos en `backend/alembic/versions/`, head `e7f1a2b3c4d5`. Si `alembic current` no muestra ese head después del deploy, algo quedó a mitad de camino (ver solución de problemas).

## Deploy de frontend (paso a paso)

Solo o combinado:

```bash
bash scripts/deploy-frontend.sh main
# o junto con backend:
DEPLOY_FRONTEND=1 bash scripts/deploy.sh main
```

1. Verifica que exista el clon (si no, correr `deploy.sh` una vez).
2. Pull de la rama.
3. `npm ci` + `npm run build` en la raíz del repo. Aborta si no hay `package.json` o si el build no produce `dist/`.
4. `rsync -av --delete` de `dist/` al docroot (excluye `.well-known/`, `.env*`, `*.map`, `.DS_Store`, `__MACOSX/`).
5. `curl` a `https://app.arpia.com.co`: espera HTTP 200; si da otra cosa muestra WARNING (revisar docroot y `.htaccess`).

## Checklist post-deploy

- [ ] `git rev-parse HEAD` en `$CLONE` es el commit esperado (`75adbbd` o posterior)
- [ ] `alembic current` muestra el head `e7f1a2b3c4d5`
- [ ] `/health` y `/health/ready` responden 200
- [ ] El frontend carga en `https://app.arpia.com.co` (HTTP 200)
- [ ] El login funciona y el Dashboard muestra datos (prueba de punta a punta, ver `TutorialPruebas.md`)
- [ ] El botón "generar copy" da `503` solo si no hay Ollama (comportamiento esperado, no es falla del deploy)

## Solución de problemas

| Síntoma | Causa probable | Qué hacer |
|---------|----------------|-----------|
| `syntax error near unexpected token` en `bash` | Script con CRLF (Windows) | Normalizar a LF. Verificado con `bash -n scripts/deploy.sh scripts/deploy-frontend.sh` antes de subir |
| `package.json not found at .../frontend` | Checkout viejo (el front se mudó a la raíz) | Usar rama con el front en raíz; `FRONTEND_SRC` debe ser `$CLONE` |
| `ENVIRONMENT must be production or staging` | `.env` del servidor sin `ENVIRONMENT` | Fijar `ENVIRONMENT=production` en el `.env` de `APP` (no en el repo) |
| Error `JWT_SECRET_KEY / DATABASE_URL / CORS_ORIGINS must be configured` | Secretos de desarrollo en prod | Completar el `.env` del servidor (ver tabla de obligatorias) |
| `npm not found` | Node no está en el `PATH` de SSH | Instalar Node en cPanel (Setup Node.js App) o exportar el `bin` de `nodevenv` al `PATH` |
| `build did not produce dist/` | Falló `npm run build` | Correr el build a mano en el clon y leer el error de Vite/Vue |
| Frontend viejo tras deploy (assets con hash) | Caché o sync incompleto | El rsync usa `--delete`; forzar recarga dura (Ctrl+F5) y confirmar el HEAD del clon |
| Readiness falla tras reinicio | App no levantó (env, migración o import) | Revisar `stderr.log` de Passenger y el `.env`; correr `alembic current` a mano |

## Rollback

- Código: en `$CLONE`, `git checkout <hash-anterior>` y re-correr el deploy correspondiente (backend y/o frontend).
- Base de datos: `alembic downgrade -1` (con cuidado: solo si la migración a revertir no destruye datos; hacer backup antes).

## Notas

- El deploy es solo avance (`--ff-only`): si el clon tiene commits locales, el pull falla a propósito. Resolver en local y pushear, nunca commitear en el servidor.
- `docker-compose.yml` es para desarrollo/local con `env passthrough` al servicio `api`; producción en cPanel usa Passenger, no Docker.
- Ollama es opcional y posterior al primer deploy: entró en V6 M5 para un solo endpoint (`POST /api/v1/ai/copy`). Sin servidor Ollama, ese endpoint responde `503` y nada más se ve afectado.
