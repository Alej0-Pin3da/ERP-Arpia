<script setup lang="ts">
/**
 * ApiModeBadge — Visual indicator for the current API data source.
 *
 * - MOCK: in-memory Express mock (server.ts + vite mockApiPlugin). Data is
 *   ephemeral and resets on server restart.
 * - REAL: external FastAPI + Postgres backend (VITE_API_BASE_URL points to
 *   an absolute host such as http://localhost:8000, :5433 or backend).
 *
 * Detection is read-only: never mutates api client logic.
 */

import { computed } from 'vue'

type ApiMode = 'MOCK' | 'REAL'

const rawBaseUrl = import.meta.env.VITE_API_BASE_URL as string | undefined

const mode = computed<ApiMode>(() => {
  const raw = (rawBaseUrl ?? '').trim()

  // No env or relative /api path => mock in-memory server
  if (!raw || raw.startsWith('/api')) return 'MOCK'

  const lower = raw.toLowerCase()
  const isExternalHost =
    lower.includes('http') ||
    lower.includes(':8000') ||
    lower.includes(':5433') ||
    lower.includes('backend')

  return isExternalHost ? 'REAL' : 'MOCK'
})

const label = computed(() =>
  mode.value === 'MOCK' ? 'MODO MOCK \u2014 Datos en memoria' : 'BACKEND REAL \u2014 Postgres',
)

const shortLabel = computed(() => (mode.value === 'MOCK' ? 'MOCK' : 'REAL'))

const icon = computed(() => (mode.value === 'MOCK' ? 'pi-database' : 'pi-server'))

const tooltip = computed(() =>
  mode.value === 'MOCK'
    ? 'Los datos se pierden al reiniciar. Backend real inactivo.'
    : 'Conectado a FastAPI + Postgres',
)

// PrimeVue Tag severity mapping (kept for programmatic use / tests)
const severity = computed(() => (mode.value === 'MOCK' ? 'warn' : 'success'))
</script>

<template>
  <div
    class="api-mode-badge"
    :class="`api-mode-badge--${mode.toLowerCase()}`"
    :title="tooltip"
    :data-severity="severity"
    role="status"
    :aria-label="`${label}: ${tooltip}`"
  >
    <span class="api-mode-badge__dot" aria-hidden="true" />
    <i :class="['pi', icon, 'api-mode-badge__icon']" aria-hidden="true" />
    <span class="api-mode-badge__label">{{ label }}</span>
    <span class="api-mode-badge__label-short" aria-hidden="true">{{ shortLabel }}</span>
  </div>
</template>

<style scoped>
.api-mode-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.35rem 0.85rem;
  border-radius: 9999px;
  border: 1px solid;
  font-size: 0.74rem;
  font-weight: 700;
  letter-spacing: 0.02em;
  line-height: 1;
  white-space: nowrap;
  backdrop-filter: blur(8px);
  transition:
    background-color 0.2s ease,
    border-color 0.2s ease,
    color 0.2s ease,
    transform 0.2s ease,
    box-shadow 0.2s ease;
  user-select: none;
}

.api-mode-badge:hover {
  transform: translateY(-1px);
}

/* MOCK — amber / orange (in-memory, ephemeral) */
.api-mode-badge--mock {
  background: rgba(245, 158, 11, 0.08);
  border-color: rgba(245, 158, 11, 0.32);
  color: #fcd34d;
  box-shadow: 0 0 0 1px rgba(245, 158, 11, 0.06) inset;
}

.api-mode-badge--mock .api-mode-badge__dot {
  background: #f59e0b;
  box-shadow: 0 0 8px rgba(245, 158, 11, 0.85);
}

.api-mode-badge--mock .api-mode-badge__icon {
  color: #fbbf24;
}

/* REAL — emerald / green (FastAPI + Postgres) */
.api-mode-badge--real {
  background: rgba(16, 185, 129, 0.08);
  border-color: rgba(16, 185, 129, 0.3);
  color: #6ee7b7;
  box-shadow: 0 0 0 1px rgba(16, 185, 129, 0.06) inset;
}

.api-mode-badge--real .api-mode-badge__dot {
  background: #10b981;
  box-shadow: 0 0 8px rgba(16, 185, 129, 0.9);
}

.api-mode-badge--real .api-mode-badge__icon {
  color: #34d399;
}

.api-mode-badge__dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
  animation: api-mode-pulse 2s infinite;
}

@keyframes api-mode-pulse {
  0% {
    transform: scale(0.92);
    opacity: 0.85;
  }
  50% {
    transform: scale(1.2);
    opacity: 1;
  }
  100% {
    transform: scale(0.92);
    opacity: 0.85;
  }
}

.api-mode-badge__icon {
  font-size: 0.8rem;
  flex-shrink: 0;
}

.api-mode-badge__label-short {
  display: none;
}

/* Noir/Gold harmony: subtle gold hairline on hover */
.api-mode-badge--mock:hover {
  border-color: rgba(245, 158, 11, 0.5);
  box-shadow:
    0 0 0 1px rgba(245, 158, 11, 0.08) inset,
    0 2px 12px rgba(245, 158, 11, 0.18);
}

.api-mode-badge--real:hover {
  border-color: rgba(16, 185, 129, 0.5);
  box-shadow:
    0 0 0 1px rgba(16, 185, 129, 0.08) inset,
    0 2px 12px rgba(16, 185, 129, 0.18);
}

/* Responsive: collapse long label on small viewports */
@media (max-width: 640px) {
  .api-mode-badge__label {
    display: none;
  }

  .api-mode-badge__label-short {
    display: inline;
    font-size: 0.7rem;
    letter-spacing: 0.06em;
  }

  .api-mode-badge {
    padding: 0.3rem 0.6rem;
    gap: 0.35rem;
  }
}
</style>
