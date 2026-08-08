<script setup lang="ts">
/**
 * Combo-content (BomProducto) form (PR10, spec MOD-5).
 *
 * Dual-mode ElForm (create -> BomProductoCreate / edit -> BomProductoUpdate):
 * producto_incluido select (productos prop) + cantidad (> 0). Client gates
 * es-CO. Edit prefills from the row (name -> id lookup over the productos
 * prop, same pattern as BomInsumoForm).
 *
 * Emits the API-ready payload via buildBomProductoPayload/Update.
 */
import { computed, reactive, watch } from 'vue'
import { ElMessage } from 'element-plus'

import type { components } from '@/types/api.d'
import { parseDecimal } from '@/utils/format'
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
    ElMessage.warning('Selecciona el producto incluido')
    return
  }
  if (form.cantidad === null || form.cantidad <= 0) {
    ElMessage.warning('Indica la cantidad')
    return
  }
  emit('submit', props.mode === 'edit' ? buildBomProductoUpdatePayload(form) : buildBomProductoPayload(form))
}
</script>

<template>
  <el-form label-position="top" @submit.prevent="onSubmit">
    <el-form-item label="Producto incluido">
      <el-select
        v-model="form.producto_incluido_id"
        data-test="bom-producto-select"
        placeholder="Selecciona el producto"
        style="width: 100%"
      >
        <el-option v-for="p in productos" :key="p.id" :label="p.nombre" :value="p.id" />
      </el-select>
    </el-form-item>
    <el-form-item label="Cantidad">
      <el-input-number
        v-model="form.cantidad"
        data-test="cantidad-bom-producto-input"
        :min="0.01"
        :precision="2"
        style="width: 100%"
      />
    </el-form-item>
    <el-button type="primary" native-type="submit" :loading="saving" data-test="submit-bom-producto">
      {{ submitLabel }}
    </el-button>
  </el-form>
</template>
