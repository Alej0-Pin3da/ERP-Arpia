<script setup lang="ts">
/**
 * Productos create/edit form (PR10, spec MOD-5).
 *
 * Dual-mode ElForm (create -> ProductoCreate / edit -> ProductoUpdate):
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
  <el-form label-position="top" @submit.prevent="onSubmit">
    <el-form-item label="Tipo de producto">
      <el-select
        v-model="form.tipo_producto_id"
        data-test="tipo-producto-select"
        placeholder="Selecciona el tipo"
        style="width: 100%"
      >
        <el-option v-for="t in tipos" :key="t.id" :label="t.nombre" :value="t.id" />
      </el-select>
    </el-form-item>
    <el-form-item label="Nombre del producto">
      <el-input v-model="form.nombre" data-test="nombre-producto-input" placeholder="Ej: Arepa de choclo" />
    </el-form-item>
    <el-form-item label="Requiere fabricación">
      <el-switch v-model="form.requiere_fabricacion" data-test="requiere-fabricacion-switch" />
    </el-form-item>
    <el-form-item label="Costos operativos fijos">
      <el-input-number
        v-model="form.costos_operativos_fijos"
        data-test="costos-fijos-input"
        :min="0"
        :precision="2"
        :step="1000"
        style="width: 100%"
      />
    </el-form-item>
    <el-form-item label="Precio de venta sugerido">
      <el-input-number
        v-model="form.precio_venta_sugerido"
        data-test="precio-venta-input"
        :min="0"
        :precision="2"
        :step="1000"
        style="width: 100%"
      />
    </el-form-item>
    <el-button type="primary" native-type="submit" :loading="saving" data-test="submit-producto">
      {{ submitLabel }}
    </el-button>
  </el-form>
</template>
