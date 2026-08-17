<script setup lang="ts">
/**
 * Nested variante create/edit form (PR10, spec MOD-5).
 *
 * Dual-mode PrimeVue form (create -> VarianteProductoCreate / edit ->
 * VarianteProductoUpdate): nombre_variante (required) + optional
 * precio_venta. The backend VarianteProductoRead has NO costo_adicional —
 * only nombre_variante + precio_venta (verified prod OpenAPI + backend
 * schemas/producto.py), so the form maps exactly those two fields.
 * precio_venta is omitted from the payload when null (schema default).
 *
 * Emits the payload; the view owns the POST/PUT, the admin gate and refresh.
 */
import { computed, reactive, watch } from 'vue'
import { ElMessage } from 'element-plus'
import Button from 'primevue/button'
import InputNumber from 'primevue/inputnumber'
import InputText from 'primevue/inputtext'

import type { components } from '@/types/api.d'
import { parseDecimal } from '@/utils/format'
import { buildVariantePayload, buildVarianteUpdatePayload, type VariantePayloadInput } from '@/utils/productos'

type VarianteProductoRead = components['schemas']['VarianteProductoRead']

const props = defineProps<{
  mode: 'create' | 'edit'
  initial?: VarianteProductoRead | null
  saving: boolean
}>()

const emit = defineEmits<{ submit: [payload: VariantePayloadInput] }>()

const form = reactive<VariantePayloadInput>({
  nombre_variante: '',
  precio_venta: null,
})

watch(
  () => props.initial,
  (row) => {
    if (props.mode === 'edit' && row) {
      form.nombre_variante = row.nombre_variante
      form.precio_venta = parseDecimal(row.precio_venta)
    }
  },
  { immediate: true },
)

const submitLabel = computed(() => (props.mode === 'create' ? 'Agregar variante' : 'Guardar cambios'))

function onSubmit(): void {
  if (form.nombre_variante.trim() === '') {
    ElMessage.warning('Escribe el nombre de la variante')
    return
  }
  emit('submit', props.mode === 'edit' ? buildVarianteUpdatePayload(form) : buildVariantePayload(form))
}
</script>

<template>
  <form class="variante-form" @submit.prevent="onSubmit">
    <div class="form-grid">
      <div class="form-col" style="--md: 12">
        <div class="form-item">
          <label class="form-label">Nombre de la variante</label>
          <InputText
            v-model="form.nombre_variante"
            data-test="nombre-variante-input"
            placeholder="Ej: Individual"
          />
        </div>
      </div>
      <div class="form-col" style="--md: 8">
        <div class="form-item">
          <label class="form-label">Precio de venta</label>
          <InputNumber
            v-model="form.precio_venta"
            data-test="precio-variante-input"
            :min="0"
            :min-fraction-digits="2"
            :max-fraction-digits="2"
            :step="1000"
            :use-grouping="false"
            class="variante-field"
          />
        </div>
      </div>
      <div class="form-col submit-col" style="--md: 24">
        <Button type="submit" :loading="saving" data-test="submit-variante">
          {{ submitLabel }}
        </Button>
      </div>
    </div>
  </form>
</template>

<style scoped>
.variante-form {
  max-width: 56rem;
}

.variante-field {
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