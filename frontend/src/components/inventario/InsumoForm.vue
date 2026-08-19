<script setup lang="ts">
/**
 * Insumo master form (PR9, spec MOD-4) — admin only.
 *
 * Dual-mode PrimeVue form over /insumos:
 *  - create: POST InsumoCreate {categoria_id, nombre, unidad_medida,
 *    stock_actual, stock_minimo, costo_promedio_actual}
 *  - edit: PUT InsumoUpdate with the same full field set — the backend update
 *    schema accepts every field, so nothing is read-only here (unlike socios).
 *  The categoria select is fed by GET /categorias-insumos (the view loads it).
 *  The view owns the POST/PUT, the admin-only gate (backend require_admin),
 *  the success message and the refresh.
 */
import { ref, watch } from 'vue'
import Button from 'primevue/button'
import InputNumber from 'primevue/inputnumber'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'

import {
  buildInsumoPayload,
  buildInsumoUpdatePayload,
  type InsumoCreate,
  type InsumoUpdate,
} from '@/utils/inventario'
import { parseDecimal } from '@/utils/format'
import { showToast } from '@/utils/toast'
import type { CategoriaInsumoRead, InsumoRead } from '@/types/api.d'

const props = defineProps<{
  mode: 'create' | 'edit'
  /** Categoria options for the select (view loads /categorias-insumos). */
  categorias: CategoriaInsumoRead[]
  /** The row being edited — prefills every field in edit mode. */
  initial?: InsumoRead | null
  /** True while the parent is POSTing/PUTting — disables the submit button. */
  saving?: boolean
}>()

const emit = defineEmits<{ submit: [payload: InsumoCreate | InsumoUpdate] }>()

const nombre = ref('')
const categoriaId = ref<number | null>(null)
const unidadMedida = ref('')
const stockActual = ref<number | null>(null)
const stockMinimo = ref<number | null>(null)
const costoPromedio = ref<number | null>(null)

/** Edit mode prefills every field from the row being edited. */
watch(
  () => props.initial,
  (insumo) => {
    if (insumo) {
      nombre.value = insumo.nombre
      categoriaId.value = insumo.categoria_id
      unidadMedida.value = insumo.unidad_medida
      stockActual.value = parseDecimal(insumo.stock_actual)
      stockMinimo.value = parseDecimal(insumo.stock_minimo)
      costoPromedio.value = parseDecimal(insumo.costo_promedio_actual)
    }
  },
  { immediate: true },
)

/** MOD-4: client-side gates — every master field is required. */
function submit(): void {
  if (nombre.value.trim() === '') {
    showToast('warn', 'Escribe el nombre del insumo.')
    return
  }
  if (categoriaId.value === null) {
    showToast('warn', 'Selecciona la categoría.')
    return
  }
  if (unidadMedida.value.trim() === '') {
    showToast('warn', 'Escribe la unidad de medida.')
    return
  }
  if (stockActual.value === null || stockActual.value < 0) {
    showToast('warn', 'Indica el stock actual.')
    return
  }
  if (stockMinimo.value === null || stockMinimo.value < 0) {
    showToast('warn', 'Indica el stock mínimo.')
    return
  }
  if (costoPromedio.value === null || costoPromedio.value < 0) {
    showToast('warn', 'Indica el costo promedio.')
    return
  }

  const form = {
    nombre: nombre.value,
    categoria_id: categoriaId.value,
    unidad_medida: unidadMedida.value,
    stock_actual: stockActual.value,
    stock_minimo: stockMinimo.value,
    costo_promedio_actual: costoPromedio.value,
  }
  emit('submit', props.mode === 'edit' ? buildInsumoUpdatePayload(form) : buildInsumoPayload(form))
}
</script>

<template>
  <form class="insumo-form" @submit.prevent="submit">
    <div class="form-grid">
      <div class="form-col" style="--md: 10">
        <div class="form-item">
          <label class="form-label">Nombre del insumo</label>
          <InputText v-model="nombre" placeholder="Ej: Harina de maíz" data-test="nombre-insumo-input" />
        </div>
      </div>
      <div class="form-col" style="--md: 6">
        <div class="form-item">
          <label class="form-label">Categoría</label>
          <Select
            v-model="categoriaId"
            :options="categorias"
            option-label="nombre"
            option-value="id"
            filter
            placeholder="Selecciona la categoría"
            class="insumo-field"
            data-test="categoria-insumo-select"
          />
        </div>
      </div>
      <div class="form-col" style="--md: 8">
        <div class="form-item">
          <label class="form-label">Unidad de medida</label>
          <InputText v-model="unidadMedida" placeholder="Ej: kg, L, unidad" data-test="unidad-insumo-input" />
        </div>
      </div>
    </div>

    <div class="form-grid">
      <div class="form-col" style="--md: 6">
        <div class="form-item">
          <label class="form-label">Stock actual</label>
          <InputNumber
            v-model="stockActual"
            :min="0"
            :min-fraction-digits="2"
            :max-fraction-digits="2"
            :use-grouping="false"
            class="insumo-field"
            data-test="stock-actual-input"
          />
        </div>
      </div>
      <div class="form-col" style="--md: 6">
        <div class="form-item">
          <label class="form-label">Stock mínimo</label>
          <InputNumber
            v-model="stockMinimo"
            :min="0"
            :min-fraction-digits="2"
            :max-fraction-digits="2"
            :use-grouping="false"
            class="insumo-field"
            data-test="stock-minimo-input"
          />
        </div>
      </div>
      <div class="form-col" style="--md: 6">
        <div class="form-item">
          <label class="form-label">Costo promedio</label>
          <InputNumber
            v-model="costoPromedio"
            :min="0"
            :min-fraction-digits="2"
            :max-fraction-digits="2"
            :use-grouping="false"
            class="insumo-field"
            data-test="costo-promedio-input"
          />
        </div>
      </div>
      <div class="form-col submit-col" style="--md: 6">
        <Button type="submit" :loading="saving" data-test="submit-insumo">
          {{ mode === 'edit' ? 'Guardar cambios' : 'Crear insumo' }}
        </Button>
      </div>
    </div>
  </form>
</template>

<style scoped>
.insumo-form {
  max-width: 56rem;
}

.insumo-field {
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
