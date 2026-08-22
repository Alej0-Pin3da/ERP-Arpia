<script setup lang="ts">
/**
 * Compras register form (PR2 — REQ-WAC-003 SCN-WAC-004, REQ-CI-001).
 *
 * PrimeVue form that maps to POST /compras-insumos (CompraInsumoCreate):
 * insumo (required), cantidad > 0, and either precio_unitario >=0 (UNIT) or
 * costo_total >0 (TOTAL). TOTAL derives unit = total/qty display-only.
 * Live preview `newStock/newWAC/valuation` mirrors backend
 * `(stock*cost+qty*unit)/newStock` in JS Number for display (backend remains
 * authoritative Decimal). Confirm is disabled when qty<=0||cost<=0||!isFinite.
 */
import { computed, ref } from 'vue'
import Button from 'primevue/button'
import InputNumber from 'primevue/inputnumber'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'

import { buildCompraPayload, type CompraInsumoCreate } from '@/utils/inventario'
import { parseDecimal } from '@/utils/format'
import { showToast } from '@/utils/toast'
import type { InsumoRead } from '@/types/api.d'

const props = defineProps<{
  /** Insumo catalog for the select (view loads GET /insumos). */
  insumos: InsumoRead[]
  /** True while the parent is POSTing — disables the submit button. */
  saving?: boolean
  /** Optional pre-selected insumo id (per-row +Compra, REQ-CI-004). */
  initialInsumoId?: number | null
}>()

const emit = defineEmits<{ submit: [payload: CompraInsumoCreate] }>()

const insumoId = ref<number | null>(props.initialInsumoId ?? null)
const cantidad = ref<number | null>(null)
const modo = ref<'TOTAL' | 'UNIT'>('UNIT')
const precioUnitario = ref<number | null>(null)
const costoTotal = ref<number | null>(null)
const factura = ref<string>('')

const selectedInsumo = computed(() => props.insumos.find((i) => i.id === insumoId.value) ?? null)

// REQ-WAC-003: JS Number display-only preview — backend is authoritative.
const unitForPreview = computed<number | null>(() => {
  if (modo.value === 'TOTAL') {
    if (cantidad.value == null || costoTotal.value == null) return null
    if (cantidad.value <= 0) return null
    return costoTotal.value / cantidad.value
  }
  return precioUnitario.value
})

const costForGate = computed<number | null>(() => {
  if (modo.value === 'TOTAL') return costoTotal.value
  return precioUnitario.value
})

const newStock = computed<number | null>(() => {
  const ins = selectedInsumo.value
  if (!ins || cantidad.value == null || cantidad.value <= 0) return null
  const stock = parseDecimal(ins.stock_actual)
  if (stock == null) return null
  return stock + cantidad.value
})

const newWAC = computed<number | null>(() => {
  const ins = selectedInsumo.value
  const unit = unitForPreview.value
  if (!ins || unit == null || cantidad.value == null || cantidad.value <= 0) return null
  const stock = parseDecimal(ins.stock_actual)
  const cost = parseDecimal(ins.costo_promedio_actual)
  if (stock == null || cost == null) return null
  if (!Number.isFinite(stock) || !Number.isFinite(cost) || !Number.isFinite(unit)) return null
  const ns = stock + cantidad.value
  if (ns <= 0) return null
  return (stock * cost + cantidad.value * unit) / ns
})

const valuation = computed<number | null>(() => {
  if (newStock.value == null || newWAC.value == null) return null
  return newStock.value * newWAC.value
})

const isConfirmDisabled = computed(() => {
  if (props.saving) return true
  if (insumoId.value == null) return true
  const qty = cantidad.value
  const cost = costForGate.value
  if (qty == null || cost == null) return true
  if (qty <= 0 || cost <= 0) return true
  if (!Number.isFinite(qty) || !Number.isFinite(cost)) return true
  const unit = unitForPreview.value
  if (unit == null || !Number.isFinite(unit)) return true
  if (newWAC.value == null || !Number.isFinite(newWAC.value)) return true
  return false
})

function submit(): void {
  if (insumoId.value === null) {
    showToast('warn', 'Selecciona el insumo.')
    return
  }
  if (cantidad.value === null || cantidad.value <= 0 || !Number.isFinite(cantidad.value)) {
    showToast('warn', 'La cantidad debe ser mayor a cero.')
    return
  }
  if (modo.value === 'TOTAL') {
    if (costoTotal.value === null || costoTotal.value <= 0 || !Number.isFinite(costoTotal.value)) {
      showToast('warn', 'Indica el costo total.')
      return
    }
  } else {
    if (precioUnitario.value === null || precioUnitario.value < 0 || !Number.isFinite(precioUnitario.value)) {
      showToast('warn', 'Indica el precio unitario.')
      return
    }
  }
  emit(
    'submit',
    buildCompraPayload({
      insumo_id: insumoId.value,
      cantidad: cantidad.value,
      // Omit modo when UNIT to preserve MOD-4 payload shape; TOTAL must be explicit.
      modo: modo.value === 'TOTAL' ? 'TOTAL' : undefined,
      precio_unitario: precioUnitario.value,
      costo_total: costoTotal.value,
      factura: factura.value || null,
    }),
  )
}
</script>

<template>
  <form class="compra-form" @submit.prevent="submit">
    <div class="form-grid">
      <div class="form-col" style="--md: 8">
        <div class="form-item">
          <label class="form-label">Insumo</label>
          <Select
            v-model="insumoId"
            :options="insumos"
            option-label="nombre"
            option-value="id"
            filter
            placeholder="Selecciona el insumo"
            class="compra-field"
            data-test="compra-insumo-select"
          />
        </div>
      </div>
      <div class="form-col" style="--md: 4">
        <div class="form-item">
          <label class="form-label">Cantidad</label>
          <InputNumber
            v-model="cantidad"
            :min="0.01"
            :min-fraction-digits="2"
            :max-fraction-digits="2"
            :use-grouping="false"
            :show-buttons="false"
            class="compra-field"
            data-test="compra-cantidad-input"
          />
        </div>
      </div>
      <div class="form-col" style="--md: 4">
        <div class="form-item">
          <label class="form-label">Modo</label>
          <Select
            v-model="modo"
            :options="[{ label: 'UNIT', value: 'UNIT' }, { label: 'TOTAL', value: 'TOTAL' }]"
            option-label="label"
            option-value="value"
            class="compra-field"
            data-test="compra-modo-select"
          />
        </div>
      </div>
      <div class="form-col" style="--md: 8">
        <div class="form-item">
          <label class="form-label">{{ modo === 'TOTAL' ? 'Costo total' : 'Precio unitario' }}</label>
          <InputNumber
            v-if="modo === 'TOTAL'"
            v-model="costoTotal"
            :min="0.01"
            :min-fraction-digits="2"
            :max-fraction-digits="2"
            :use-grouping="false"
            :show-buttons="false"
            class="compra-field"
            data-test="compra-costo-total-input"
          />
          <InputNumber
            v-else
            v-model="precioUnitario"
            :min="0"
            :min-fraction-digits="2"
            :max-fraction-digits="2"
            :use-grouping="false"
            :show-buttons="false"
            class="compra-field"
            data-test="compra-precio-input"
          />
        </div>
      </div>
      <div class="form-col" style="--md: 8">
        <div class="form-item">
          <label class="form-label">Factura (opcional)</label>
          <InputText v-model="factura" maxlength="100" placeholder="F-001" class="compra-field" data-test="compra-factura-input" />
        </div>
      </div>
      <div class="form-col submit-col" style="--md: 16">
        <Button type="submit" :loading="saving" :disabled="isConfirmDisabled" data-test="submit-compra">
          Registrar compra
        </Button>
      </div>
    </div>

    <!-- REQ-WAC-003 live preview (display-only, backend authoritative) -->
    <div v-if="selectedInsumo && newWAC !== null" class="preview" data-test="compra-preview">
      <span>Nuevo stock: <strong>{{ newStock?.toFixed(2) }}</strong></span>
      <span>Nuevo WAC: <strong>{{ newWAC.toFixed(4) }}</strong></span>
      <span>Valorización: <strong>{{ valuation?.toFixed(2) }}</strong></span>
    </div>
    <p class="form-hint">
      El registro actualiza el stock y el costo promedio (WAC) automáticamente.
    </p>
  </form>
</template>

<style scoped>
.compra-form {
  max-width: 56rem;
}
.compra-field {
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
.submit-col {
  display: flex;
  align-items: flex-end;
  padding-bottom: 0.15rem;
}
.preview {
  display: flex;
  gap: 1rem;
  margin-top: 0.75rem;
  padding: 0.5rem 0.75rem;
  background: var(--p-surface-50);
  border: 1px solid var(--p-surface-200);
  border-radius: 6px;
  font-size: 0.85rem;
}
.form-hint {
  color: var(--arpia-text-muted);
  font-size: 0.85rem;
  margin: 0.25rem 0 0;
}
</style>
