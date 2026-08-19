<script setup lang="ts">
/**
 * BOM insumo line form (PR10, spec MOD-5).
 *
 * Dual-mode PrimeVue form (create -> BomInsumoCreate / edit ->
 * BomInsumoUpdate): insumo select (insumos prop), cantidad_requerida (> 0)
 * and porcentaje_desperdicio (0..100). Client gates es-CO: insumo and
 * cantidad are required. Edit prefills from the row (the backend PUT schema
 * accepts the full field set).
 *
 * Emits the API-ready payload via buildBomInsumoPayload/Update — variante_id
 * is omitted when null (the base rule row applies to all variants).
 */
import { computed, reactive, watch } from 'vue'
import Button from 'primevue/button'
import InputNumber from 'primevue/inputnumber'
import Select from 'primevue/select'

import type { components } from '@/types/api.d'
import { parseDecimal } from '@/utils/format'
import { showToast } from '@/utils/toast'
import {
  buildBomInsumoPayload,
  buildBomInsumoUpdatePayload,
  type BomInsumoPayloadInput,
  type BomInsumoRow,
} from '@/utils/productos'

type InsumoRead = components['schemas']['InsumoRead']

const props = defineProps<{
  mode: 'create' | 'edit'
  initial?: BomInsumoRow | null
  insumos: InsumoRead[]
  saving: boolean
}>()

const emit = defineEmits<{ submit: [payload: BomInsumoPayloadInput] }>()

const form = reactive<BomInsumoPayloadInput>({
  insumo_id: null,
  variante_id: null,
  cantidad_requerida: null,
  porcentaje_desperdicio: null,
})

// The edit row carries the joined insumo NAME; the form needs its id to
// prefill the select. Map names over the insumos prop (first match wins).
const INSUMO_ID_FROM_ROW = new Map(props.insumos.map((i) => [i.nombre, i.id]))

watch(
  () => props.initial,
  (row) => {
    if (props.mode === 'edit' && row) {
      form.insumo_id = INSUMO_ID_FROM_ROW.get(row.insumo) ?? null
      form.cantidad_requerida = parseDecimal(row.cantidad_requerida)
      form.porcentaje_desperdicio = parseDecimal(row.porcentaje_desperdicio)
    }
  },
  { immediate: true },
)

const submitLabel = computed(() => (props.mode === 'create' ? 'Agregar insumo' : 'Guardar cambios'))

function onSubmit(): void {
  if (form.insumo_id === null) {
    showToast('warn', 'Selecciona el insumo')
    return
  }
  if (form.cantidad_requerida === null || form.cantidad_requerida <= 0) {
    showToast('warn', 'Indica la cantidad requerida')
    return
  }
  emit('submit', props.mode === 'edit' ? buildBomInsumoUpdatePayload(form) : buildBomInsumoPayload(form))
}
</script>

<template>
  <form class="bom-insumo-form" @submit.prevent="onSubmit">
    <div class="form-grid">
      <div class="form-col" style="--md: 10">
        <div class="form-item">
          <label class="form-label">Insumo</label>
          <Select
            v-model="form.insumo_id"
            :options="insumos"
            option-label="nombre"
            option-value="id"
            data-test="bom-insumo-select"
            placeholder="Selecciona el insumo"
            class="bom-insumo-field"
          />
        </div>
      </div>
      <div class="form-col" style="--md: 7">
        <div class="form-item">
          <label class="form-label">Cantidad requerida</label>
          <InputNumber
            v-model="form.cantidad_requerida"
            data-test="cantidad-bom-insumo-input"
            :min="0.01"
            :min-fraction-digits="2"
            :max-fraction-digits="2"
            :use-grouping="false"
            class="bom-insumo-field"
          />
        </div>
      </div>
      <div class="form-col" style="--md: 7">
        <div class="form-item">
          <label class="form-label">Desperdicio (%)</label>
          <InputNumber
            v-model="form.porcentaje_desperdicio"
            data-test="desperdicio-bom-insumo-input"
            :min="0"
            :max="100"
            :min-fraction-digits="2"
            :max-fraction-digits="2"
            :use-grouping="false"
            class="bom-insumo-field"
          />
        </div>
      </div>
      <div class="form-col submit-col" style="--md: 24">
        <Button type="submit" :loading="saving" data-test="submit-bom-insumo">
          {{ submitLabel }}
        </Button>
      </div>
    </div>
  </form>
</template>

<style scoped>
.bom-insumo-form {
  max-width: 56rem;
}

.bom-insumo-field {
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
</style>