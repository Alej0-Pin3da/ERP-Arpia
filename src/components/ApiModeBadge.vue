<script setup lang="ts">
/**
 * ApiModeBadge — Visual indicator for the current API data source.
 *
 * REAL-only: the app always talks to the FastAPI + Postgres backend.
 * The badge statically shows REAL (kept for layout compat).
 */

import { computed } from 'vue'

type ApiMode = 'MOCK' | 'REAL'

const mode = computed<ApiMode>(() => 'REAL')

const label = computed(() => 'BACKEND REAL — Postgres')

const shortLabel = computed(() => 'REAL')

const icon = computed(() => 'pi-server')

const tooltip = computed(() => 'Conectado a FastAPI + Postgres')

// PrimeVue Tag severity mapping (kept for programmatic use / tests)
const severity = computed(() => 'success')
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
