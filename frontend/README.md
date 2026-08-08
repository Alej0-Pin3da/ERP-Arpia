# ERP Arpia — Frontend

Vue 3 + TypeScript single-page application for ERP Arpia (Phase 6). Built with
[Vite](https://vite.dev), consumes the FastAPI backend at
`VITE_API_BASE_URL`.

## Stack

- **Framework**: Vue 3 (`<script setup>`) + TypeScript
- **Build tool**: Vite (`base: '/'`, alias `@/ → src/`)
- **UI**: Element Plus (es locale) + ECharts / vue-echarts
- **State**: Pinia
- **Routing**: Vue Router (added in a later slice)
- **API client**: Axios wrapper with single-flight refresh (later slice)
- **Tests**: Vitest + Vue Test Utils + jsdom

## Prerequisites

- Node.js >= 20 (`node --version`)
- npm >= 10 (`npm --version`)

## Setup

```bash
npm install
```

## Development

```bash
npm run dev
```

Serves on `http://localhost:5173` and targets the local backend
(`http://localhost:8000/api/v1`, see `.env.development`). The backend must be
running locally, and its CORS config must allow the `localhost:5173` origin.

## Build

```bash
npm run build
```

Produces a fully static bundle in `frontend/dist/` (deployable to a cPanel
subdomain docroot). The production build targets
`https://api.arpia.com.co/api/v1` (see `.env.production`).

Preview the production build locally:

```bash
npm run preview
```

## Deploy

The frontend is a **static SPA** (no server runtime) served from the
`app.arpia.com.co` cPanel subdomain docroot. Build output goes to `frontend/dist/`
and is uploaded as-is.

### Build + deploy

```bash
# Local development
npm run dev

# Production build (output: frontend/dist/)
npm run build

# Deploy: build + sync dist/ to the server docroot
bash scripts/deploy-frontend.sh            # latest main
bash scripts/deploy-frontend.sh feature/x  # a specific branch
```

`scripts/deploy-frontend.sh` runs `npm ci && npm run build` and rsyncs
`frontend/dist/` to `FRONTEND_DOCROOT` (default
`/home/arpiacom/erp_arpia_frontend`, the app.arpia.com.co docroot — adjust the
variable at the top of the script if the server layout differs). It then curls
`FRONTEND_URL` (default `https://app.arpia.com.co`) as a post-deploy check.

The backend `scripts/deploy.sh` can also deploy the frontend afterwards: set
`DEPLOY_FRONTEND=1 bash scripts/deploy.sh`. It is off by default so backend
deploys keep their exact previous behavior.

### SPA routing (.htaccess)

Vue Router uses history mode (`base: '/'`), so deep links (`/ventas`, `/usuarios`,
...) must fall back to `index.html`. The file `frontend/public/.htaccess` is
copied verbatim by Vite into `dist/` (public assets land at the dist root) and
is deployed with the bundle. It rewrites every non-file, non-directory request
to `index.html`. No extra server config is required for routing; the docroot
must allow `.htaccess` overrides (cPanel default).

### CORS (operational, not code)

The SPA runs on `app.arpia.com.co` but calls the API on `api.arpia.com.co`, so
the **production backend** must include `https://app.arpia.com.co` in its
`CORS_ORIGINS` env var (and be restarted). This is a server-side env change —
do it once after the first deploy, before relying on live API calls. Local dev
uses `http://localhost:5173` (see `.env.development`).

## Tests

```bash
npm run test        # run once
npm run test:watch  # watch mode
```

## Lint & format

```bash
npm run lint    # ESLint (flat config, eslint.config.js)
npm run format  # Prettier
```

## Generate API types

Regenerates `src/types/api.d.ts` from the backend OpenAPI schema. The script
sources the **production** schema (`https://api.arpia.com.co/api/v1/openapi.json`)
so a local backend instance is not required. To generate from a local backend
instead, pass its URL explicitly:

```bash
npm run gen:api
npx openapi-typescript http://localhost:8000/api/v1/openapi.json -o src/types/api.d.ts
```

## Environment variables

| Variable            | Description            | Dev                          | Prod                              |
| ------------------- | ---------------------- | ---------------------------- | --------------------------------- |
| `VITE_API_BASE_URL` | Backend API base URL   | `http://localhost:8000/api/v1` | `https://api.arpia.com.co/api/v1` |

- `.env.development` — used by `npm run dev`
- `.env.production` — used by `npm run build`
- `.env.example` — documented template; copy to `.env.local` for local overrides

## Project layout

```
frontend/
├── src/
│   ├── styles/main.css   # global styles
│   ├── App.vue           # root component (placeholder shell)
│   ├── main.ts           # app bootstrap (Pinia + Element Plus es locale)
│   └── env.d.ts          # Vite client + env typing
├── tests/                # Vitest specs + setup
├── vite.config.ts        # Vite + Vitest config (alias, base, jsdom)
├── tsconfig.json
├── eslint.config.js      # ESLint flat config
├── .prettierrc
├── .env.development
├── .env.production
└── .env.example
```
