<script setup lang="ts">
/**
 * Compras register form (PR9, spec MOD-4) — operador+.
 *
 * Element Plus form that maps to POST /compras-insumos (CompraInsumoCreate):
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
  <el-form label-position="top" class="compra-form" @submit.prevent="submit">
    <el-row :gutter="16">
      <el-col :xs="24" :md="8">
        <el-form-item label="Insumo">
          <el-select
            v-model="insumoId"
            filterable
            placeholder="Selecciona el insumo"
            class="compra-field"
            data-test="compra-insumo-select"
          >
            <el-option v-for="i in insumos" :key="i.id" :label="i.nombre" :value="i.id" />
          </el-select>
        </el-form-item>
      </el-col>
      <el-col :xs="24" :md="4">
        <el-form-item label="Cantidad">
          <el-input-number
            v-model="cantidad"
            :min="0.01"
            :precision="2"
            :controls="false"
            class="compra-field"
            data-test="compra-cantidad-input"
          />
        </el-form-item>
      </el-col>
      <el-col :xs="24" :md="6">
        <el-form-item label="Precio unitario">
          <el-input-number
            v-model="precioUnitario"
            :min="0"
            :precision="2"
            :controls="false"
            class="compra-field"
            data-test="compra-precio-input"
          />
        </el-form-item>
      </el-col>
      <el-col :xs="24" :md="6" class="submit-col">
        <el-button type="primary" native-type="submit" :loading="saving" data-test="submit-compra">
          Registrar compra
        </el-button>
      </el-col>
    </el-row>

    <p class="form-hint">
      El registro actualiza el stock y el costo promedio (WAC) automáticamente.
    </p>
  </el-form>
</template>

<style scoped>
.compra-form {
  max-width: 56rem;
}

.compra-field {
  width: 100%;
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
