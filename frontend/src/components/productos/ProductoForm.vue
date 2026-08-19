<script setup lang="ts">
/**
 * Productos create/edit form (PR10, spec MOD-5).
 *
 * Dual-mode PrimeVue form (create -> ProductoCreate / edit -> ProductoUpdate):
 * tipo_producto_id select (from GET /tipos-producto), nombre,
 * requiere_fabricacion switch (default ON), costos_operativos_fijos +
 * precio_venta_sugerido number fields. Client gates es-CO: nombre and tipo
 * are required. Edit prefills every field from the row (the backend PUT
 * schema accepts the full set, like inventario's InsumoForm).
 *
 * Emits the payload; the view owns the POST/PUT, the admin-only gate and the
 * refresh.
 */
import { computed, reactive, watch } from 'vue'
import { ElMessage } from 'element-plus'
import Button from 'primevue/button'
import InputNumber from 'primevue/inputnumber'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import ToggleSwitch from 'primevue/toggleswitch'

import type { components } from '@/types/api.d'
import { parseDecimal } from '@/utils/format'
import { buildProductoPayload, buildProductoUpdatePayload, type ProductoPayloadInput } from '@/utils/productos'

type ProductoRead = components['schemas']['ProductoRead']
type TipoProductoRead = components['schemas']['TipoProductoRead']

const props = defineProps<{
  mode: 'create' | 'edit'
  initial?: ProductoRead | null
  tipos: TipoProductoRead[]
  saving: boolean
}>()

const emit = defineEmits<{ submit: [payload: ProductoPayloadInput] }>()

const form = reactive<ProductoPayloadInput>({
  tipo_producto_id: null,
  nombre: '',
  requiere_fabricacion: true,
  costos_operativos_fijos: null,
  precio_venta_sugerido: null,
})

watch(
  () => props.initial,
  (row) => {
    if (props.mode === 'edit' && row) {
      form.tipo_producto_id = row.tipo_producto_id
      form.nombre = row.nombre
      form.requiere_fabricacion = row.requiere_fabricacion
      form.costos_operativos_fijos = parseDecimal(row.costos_operativos_fijos)
      form.precio_venta_sugerido = parseDecimal(row.precio_venta_sugerido)
    }
  },
  { immediate: true },
)

const submitLabel = computed(() => (props.mode === 'create' ? 'Crear producto' : 'Guardar cambios'))

function onSubmit(): void {
  if (form.nombre.trim() === '') {
    ElMessage.warning('Escribe el nombre del producto')
    return
  }
  if (form.tipo_producto_id === null) {
    ElMessage.warning('Selecciona el tipo de producto')
    return
  }
  emit('submit', props.mode === 'edit' ? buildProductoUpdatePayload(form) : buildProductoPayload(form))
}
</script>

<template>
  <form class="producto-form" @submit.prevent="onSubmit">
    <div class="form-grid">
      <div class="form-col" style="--md: 12">
        <div class="form-item">
          <label class="form-label">Tipo de producto</label>
          <Select
            v-model="form.tipo_producto_id"
            :options="tipos"
            option-label="nombre"
            option-value="id"
            data-test="tipo-producto-select"
            placeholder="Selecciona el tipo"
            class="producto-field"
          />
        </div>
      </div>
      <div class="form-col" style="--md: 12">
        <div class="form-item">
          <label class="form-label">Nombre del producto</label>
          <InputText
            v-model="form.nombre"
            data-test="nombre-producto-input"
            placeholder="Ej: Arepa de choclo"
          />
        </div>
      </div>
      <div class="form-col" style="--md: 8">
        <div class="form-item">
          <label class="form-label">Requiere fabricación</label>
          <ToggleSwitch v-model="form.requiere_fabricacion" data-test="requiere-fabricacion-switch" />
        </div>
      </div>
      <div class="form-col" style="--md: 8">
        <div class="form-item">
          <label class="form-label">Costos operativos fijos</label>
          <InputNumber
            v-model="form.costos_operativos_fijos"
            data-test="costos-fijos-input"
            :min="0"
            :min-fraction-digits="2"
            :max-fraction-digits="2"
            :step="1000"
            :use-grouping="false"
            class="producto-field"
          />
        </div>
      </div>
      <div class="form-col" style="--md: 8">
        <div class="form-item">
          <label class="form-label">Precio de venta sugerido</label>
          <InputNumber
            v-model="form.precio_venta_sugerido"
            data-test="precio-venta-input"
            :min="0"
            :min-fraction-digits="2"
            :max-fraction-digits="2"
            :step="1000"
            :use-grouping="false"
            class="producto-field"
          />
        </div>
      </div>
      <div class="form-col submit-col" style="--md: 24">
        <Button type="submit" :loading="saving" data-test="submit-producto">
          {{ submitLabel }}
        </Button>
      </div>
    </div>
  </form>
</template>

<style scoped>
.producto-form {
  max-width: 56rem;
}

.producto-field {
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