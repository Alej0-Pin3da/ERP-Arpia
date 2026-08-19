<script setup lang="ts">
/**
 * Liquidaciones form (PR8, spec MOD-3).
 *
 * PrimeVue form that maps to POST /finanzas/liquidaciones
 * (LiquidacionCreate): monto > 0 and optional notas. The settlement is
 * ONE-TIME — the backend rejects a replay of the same liquidacion_id with
 * 409 — so the form carries an explicit warning. The view owns the POST, the
 * per-socio result table and the 409 surfacing.
 */
import { ref } from 'vue'
import Button from 'primevue/button'
import InputNumber from 'primevue/inputnumber'
import Textarea from 'primevue/textarea'

import { buildLiquidacionPayload, type LiquidacionCreate } from '@/utils/finanzas'
import { showToast } from '@/utils/toast'

defineProps<{
  /** True while the parent is POSTing — disables the submit button. */
  saving?: boolean
}>()

const emit = defineEmits<{ submit: [payload: LiquidacionCreate] }>()

const monto = ref<number | null>(null)
const notas = ref('')

/** MOD-3: client gate — monto is required (> 0). */
function submit(): void {
  if (monto.value === null || monto.value <= 0) {
    showToast('warn', 'Indica el monto a liquidar.')
    return
  }
  emit(
    'submit',
    buildLiquidacionPayload({ monto: monto.value, notas: notas.value }),
  )
}
</script>

<template>
  <form class="liquidacion-form" @submit.prevent="submit">
    <div class="form-grid">
      <div class="form-col" style="--md: 8">
        <div class="form-item">
          <label class="form-label">Monto a liquidar</label>
          <InputNumber
            v-model="monto"
            :min="0.01"
            :min-fraction-digits="2"
            :max-fraction-digits="2"
            :step="100000"
            :use-grouping="false"
            :show-buttons="false"
            class="liquidacion-field"
            data-test="monto-liquidacion-input"
          />
        </div>
      </div>
      <div class="form-col" style="--md: 16">
        <div class="form-item">
          <label class="form-label">Notas</label>
          <Textarea
            v-model="notas"
            :rows="2"
            placeholder="Opcional"
            data-test="notas-input"
          />
        </div>
      </div>
    </div>

    <div class="form-footer">
      <span class="form-hint">
        La liquidación se procesa una sola vez y genera un Retiro por socio según su participación.
      </span>
      <Button type="submit" :loading="saving" data-test="submit-liquidacion">
        Procesar liquidación
      </Button>
    </div>
  </form>
</template>

<style scoped>
.liquidacion-form {
  max-width: 48rem;
}

.liquidacion-field {
  width: 100%;
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