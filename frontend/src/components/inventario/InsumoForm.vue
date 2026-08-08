<script setup lang="ts">
/**
 * Insumo master form (PR9, spec MOD-4) — admin only.
 *
 * Dual-mode Element Plus form over /insumos:
 *  - create: POST InsumoCreate {categoria_id, nombre, unidad_medida,
 *    stock_actual, stock_minimo, costo_promedio_actual}
 *  - edit: PUT InsumoUpdate with the same full field set — the backend update
 *    schema accepts every field, so nothing is read-only here (unlike socios).
 *  The categoria select is fed by GET /categorias-insumos (the view loads it).
 *  The view owns the POST/PUT, the admin-only gate (backend require_admin),
 *  the success message and the refresh.
 */
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'

import {
  buildInsumoPayload,
  buildInsumoUpdatePayload,
  type InsumoCreate,
  type InsumoUpdate,
} from '@/utils/inventario'
import { parseDecimal } from '@/utils/format'
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
    ElMessage.warning('Escribe el nombre del insumo.')
    return
  }
  if (categoriaId.value === null) {
    ElMessage.warning('Selecciona la categoría.')
    return
  }
  if (unidadMedida.value.trim() === '') {
    ElMessage.warning('Escribe la unidad de medida.')
    return
  }
  if (stockActual.value === null || stockActual.value < 0) {
    ElMessage.warning('Indica el stock actual.')
    return
  }
  if (stockMinimo.value === null || stockMinimo.value < 0) {
    ElMessage.warning('Indica el stock mínimo.')
    return
  }
  if (costoPromedio.value === null || costoPromedio.value < 0) {
    ElMessage.warning('Indica el costo promedio.')
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
  <el-form label-position="top" class="insumo-form" @submit.prevent="submit">
    <el-row :gutter="16">
      <el-col :xs="24" :md="10">
        <el-form-item label="Nombre del insumo">
          <el-input v-model="nombre" placeholder="Ej: Harina de maíz" data-test="nombre-insumo-input" />
        </el-form-item>
      </el-col>
      <el-col :xs="24" :md="6">
        <el-form-item label="Categoría">
          <el-select
            v-model="categoriaId"
            filterable
            placeholder="Selecciona la categoría"
            class="insumo-field"
            data-test="categoria-insumo-select"
          >
            <el-option v-for="c in categorias" :key="c.id" :label="c.nombre" :value="c.id" />
          </el-select>
        </el-form-item>
      </el-col>
      <el-col :xs="24" :md="8">
        <el-form-item label="Unidad de medida">
          <el-input v-model="unidadMedida" placeholder="Ej: kg, L, unidad" data-test="unidad-insumo-input" />
        </el-form-item>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <el-col :xs="24" :md="6">
        <el-form-item label="Stock actual">
          <el-input-number
            v-model="stockActual"
            :min="0"
            :precision="2"
            :controls="false"
            class="insumo-field"
            data-test="stock-actual-input"
          />
        </el-form-item>
      </el-col>
      <el-col :xs="24" :md="6">
        <el-form-item label="Stock mínimo">
          <el-input-number
            v-model="stockMinimo"
            :min="0"
            :precision="2"
            :controls="false"
            class="insumo-field"
            data-test="stock-minimo-input"
          />
        </el-form-item>
      </el-col>
      <el-col :xs="24" :md="6">
        <el-form-item label="Costo promedio">
          <el-input-number
            v-model="costoPromedio"
            :min="0"
            :precision="2"
            :controls="false"
            class="insumo-field"
            data-test="costo-promedio-input"
          />
        </el-form-item>
      </el-col>
      <el-col :xs="24" :md="6" class="submit-col">
        <el-button type="primary" native-type="submit" :loading="saving" data-test="submit-insumo">
          {{ mode === 'edit' ? 'Guardar cambios' : 'Crear insumo' }}
        </el-button>
      </el-col>
    </el-row>
  </el-form>
</template>

<style scoped>
.insumo-form {
  max-width: 56rem;
}

.insumo-field {
  width: 100%;
}

.submit-col {
  display: flex;
  align-items: flex-end;
  padding-bottom: 0.15rem;
}
</style>
