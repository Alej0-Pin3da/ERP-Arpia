<script setup lang="ts">
/**
 * Combo-content (BomProducto) form (PR10, spec MOD-5).
 *
 * Dual-mode PrimeVue form (create -> BomProductoCreate / edit ->
 * BomProductoUpdate): producto_incluido select (productos prop) + cantidad
 * (> 0). Client gates es-CO. Edit prefills from the row (name -> id lookup
 * over the productos prop, same pattern as BomInsumoForm).
 *
 * Emits the API-ready payload via buildBomProductoPayload/Update.
 */
import { computed, reactive, watch } from 'vue'
import Button from 'primevue/button'
import InputNumber from 'primevue/inputnumber'
import Select from 'primevue/select'

import type { components } from '@/types/api.d'
import { parseDecimal } from '@/utils/format'
import { showToast } from '@/utils/toast'
import {
  buildBomProductoPayload,
  buildBomProductoUpdatePayload,
  type BomProductoPayloadInput,
  type BomProductoRow,
} from '@/utils/productos'

type ProductoRead = components['schemas']['ProductoRead']

const props = defineProps<{
  mode: 'create' | 'edit'
  initial?: BomProductoRow | null
  productos: ProductoRead[]
  saving: boolean
}>()

const emit = defineEmits<{ submit: [payload: BomProductoPayloadInput] }>()

const form = reactive<BomProductoPayloadInput>({
  producto_incluido_id: null,
  cantidad: null,
})

// The edit row carries the joined product NAME; map names over the productos
// prop to prefill the select.
const PRODUCTO_ID_FROM_ROW = new Map(props.productos.map((p) => [p.nombre, p.id]))

watch(
  () => props.initial,
  (row) => {
    if (props.mode === 'edit' && row) {
      form.producto_incluido_id = PRODUCTO_ID_FROM_ROW.get(row.producto) ?? null
      form.cantidad = parseDecimal(row.cantidad)
    }
  },
  { immediate: true },
)

const submitLabel = computed(() => (props.mode === 'create' ? 'Agregar producto' : 'Guardar cambios'))

function onSubmit(): void {
  if (form.producto_incluido_id === null) {
    showToast('warn', 'Selecciona el producto incluido')
    return
  }
  if (form.cantidad === null || form.cantidad <= 0) {
    showToast('warn', 'Indica la cantidad')
    return
  }
  emit('submit', props.mode === 'edit' ? buildBomProductoUpdatePayload(form) : buildBomProductoPayload(form))
}
</script>

<template>
  <form class="bom-producto-form" @submit.prevent="onSubmit">
    <div class="form-grid">
      <div class="form-col" style="--md: 12">
        <div class="form-item">
          <label class="form-label">Producto incluido</label>
          <Select
            v-model="form.producto_incluido_id"
            :options="productos"
            option-label="nombre"
            option-value="id"
            data-test="bom-producto-select"
            placeholder="Selecciona el producto"
            class="bom-producto-field"
          />
        </div>
      </div>
      <div class="form-col" style="--md: 6">
        <div class="form-item">
          <label class="form-label">Cantidad</label>
          <InputNumber
            v-model="form.cantidad"
            data-test="cantidad-bom-producto-input"
            :min="0.01"
            :min-fraction-digits="2"
            :max-fraction-digits="2"
            :use-grouping="false"
            class="bom-producto-field"
          />
        </div>
      </div>
      <div class="form-col submit-col" style="--md: 24">
        <Button type="submit" :loading="saving" data-test="submit-bom-producto">
          {{ submitLabel }}
        </Button>
      </div>
    </div>
  </form>
</template>

<style scoped>
.bom-producto-form {
  max-width: 56rem;
}

.bom-producto-field {
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
</style>