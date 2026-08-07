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
