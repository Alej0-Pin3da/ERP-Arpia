<script setup lang="ts">
/**
 * Socios form (PR8, spec MOD-3) — dual mode:
 *  - create: nombre + porcentaje_participacion -> POST /finanzas/socios
 *    (the server enforces an EXACT-100 global sum; otherwise 422).
 *  - edit: percentage ONLY — the backend SocioConfiguracionUpdate schema has
 *    no `nombre` field, so the partner name is not updatable; the current
 *    name is shown read-only. Updates may rebalance below 100 but never
 *    above (server 422, surfaced by the view).
 *
 * The view owns the POST/PATCH, the 422 surfacing and the refresh.
 */
import { ref, watch } from 'vue'
import Button from 'primevue/button'
import InputNumber from 'primevue/inputnumber'
import InputText from 'primevue/inputtext'

import {
  buildSocioPayload,
  buildSocioUpdatePayload,
  type SocioConfiguracionCreate,
  type SocioConfiguracionUpdate,
} from '@/utils/finanzas'
import { showToast } from '@/utils/toast'
import type { SocioConfiguracionRead } from '@/types/api.d'

const props = withDefaults(
  defineProps<{
    /** 'create' shows nombre + porcentaje; 'edit' edits the percentage only. */
    mode?: 'create' | 'edit'
    /** The row being edited (prefills the percentage in edit mode). */
    initial?: SocioConfiguracionRead | null
    /** True while the parent is POST/PATCHing — disables the submit button. */
    saving?: boolean
  }>(),
  { mode: 'create', initial: null, saving: false },
)

const emit = defineEmits<{
  submit: [payload: SocioConfiguracionCreate | SocioConfiguracionUpdate]
}>()

const nombre = ref('')
const porcentaje = ref<number | null>(null)

watch(
  () => props.initial,
  (socio) => {
    if (socio) {
      porcentaje.value = Number.parseFloat(socio.porcentaje_participacion)
    }
  },
  { immediate: true },
)

/** MOD-3: client gates — create requires nombre; every mode requires a share. */
function submit(): void {
  if (props.mode === 'create' && nombre.value.trim() === '') {
    showToast('warn', 'Escribe el nombre del socio.')
    return
  }
  if (porcentaje.value === null || porcentaje.value <= 0) {
    showToast('warn', 'El porcentaje debe ser mayor a cero.')
    return
  }
  if (props.mode === 'edit') {
    emit('submit', buildSocioUpdatePayload(porcentaje.value))
    return
  }
  emit('submit', buildSocioPayload({ nombre: nombre.value, porcentaje_participacion: porcentaje.value }))
}
</script>

<template>
  <form class="socio-form" @submit.prevent="submit">
    <div class="form-grid">
      <div class="form-col" style="--md: 12">
        <template v-if="mode === 'create'">
          <div class="form-item">
            <label class="form-label">Nombre del socio</label>
            <InputText v-model="nombre" placeholder="Ej: Ana María" data-test="nombre-socio-input" />
          </div>
        </template>
        <div v-else class="form-item">
          <label class="form-label">Socio</label>
          <span class="socio-name-static" data-test="socio-name-static">{{ initial?.nombre }}</span>
        </div>
      </div>
      <div class="form-col" style="--md: 12">
        <div class="form-item">
          <label class="form-label">Porcentaje de participación</label>
          <InputNumber
            v-model="porcentaje"
            :min="0.01"
            :max="100"
            :min-fraction-digits="2"
            :max-fraction-digits="2"
            :step="5"
            :use-grouping="false"
            class="socio-field"
            data-test="porcentaje-socio-input"
          />
        </div>
      </div>
    </div>

    <div class="form-footer">
      <span class="form-hint">
        {{ mode === 'edit' ? 'Solo se puede ajustar el porcentaje.' : 'La suma de participaciones debe ser exactamente 100%.' }}
      </span>
      <Button type="submit" :loading="saving" data-test="submit-socio">
        {{ mode === 'edit' ? 'Guardar cambios' : 'Crear socio' }}
      </Button>
    </div>
  </form>
</template>

<style scoped>
.socio-form {
  max-width: 40rem;
}

.socio-field {
  width: 100%;
}

.socio-name-static {
  line-height: 2rem;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(24, 1fr);
  gap: 0.5rem 1rem;
}

.form-col {
  grid-column: span 24;
}

@media (min-width: 768px) {
  .form-col {
    grid-column: span var(--md, 24);
  }
}

.form-item {
  display: flex;
  flex-direction: column;
}

.form-label {
  margin-bottom: 0.25rem;
  font-size: 0.875rem;
  color: var(--arpia-text-primary);
}

.form-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 0.5rem;
  gap: 1rem;
}

.form-hint {
  color: var(--arpia-text-muted);
  font-size: 0.85rem;
}
</style>