<script setup lang="ts">
/**
 * Compras register form (PR9, spec MOD-4) — operador+.
 *
 * PrimeVue form that maps to POST /compras-insumos (CompraInsumoCreate):
 * required insumo (select over the insumos catalog), cantidad > 0 and
 * precio_unitario >= 0. The schema field names are `cantidad_comprada` /
 * `precio_unitario_compra`. The backend runs the WAC service on POST
 * (updating stock_actual and costo_promedio_actual server-side), so a
 * successful compra refreshes BOTH the compras list and the insumos list.
 *
 * The view owns the POST, the success message and the two-tab refresh.
 */
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import Button from 'primevue/button'
import InputNumber from 'primevue/inputnumber'
import Select from 'primevue/select'

import { buildCompraPayload, type CompraInsumoCreate } from '@/utils/inventario'
import type { InsumoRead } from '@/types/api.d'

defineProps<{
  /** Insumo catalog for the select (view loads GET /insumos). */
  insumos: InsumoRead[]
  /** True while the parent is POSTing — disables the submit button. */
  saving?: boolean
}>()

const emit = defineEmits<{ submit: [payload: CompraInsumoCreate] }>()

const insumoId = ref<number | null>(null)
const cantidad = ref<number | null>(null)
const precioUnitario = ref<number | null>(null)

/** MOD-4: client-side gates — insumo, cantidad > 0 and precio >= 0 required. */
function submit(): void {
  if (insumoId.value === null) {
    ElMessage.warning('Selecciona el insumo.')
    return
  }
  if (cantidad.value === null || cantidad.value <= 0) {
    ElMessage.warning('La cantidad debe ser mayor a cero.')
    return
  }
  if (precioUnitario.value === null || precioUnitario.value < 0) {
    ElMessage.warning('Indica el precio unitario.')
    return
  }
  emit(
    'submit',
    buildCompraPayload({
      insumo_id: insumoId.value,
      cantidad: cantidad.value,
      precio_unitario: precioUnitario.value,
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
      <div class="form-col" style="--md: 6">
        <div class="form-item">
          <label class="form-label">Precio unitario</label>
          <InputNumber
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
      <div class="form-col submit-col" style="--md: 6">
        <Button type="submit" :loading="saving" data-test="submit-compra">
          Registrar compra
        </Button>
      </div>
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
  color: var(--el-text-color-primary);
}

.submit-col {
  display: flex;
  align-items: flex-end;
  padding-bottom: 0.15rem;
}

.form-hint {
  color: var(--el-text-color-secondary);
  font-size: 0.85rem;
  margin: 0.25rem 0 0;
}
</style>