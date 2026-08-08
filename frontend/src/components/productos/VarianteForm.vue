<script setup lang="ts">
/**
 * Nested variante create/edit form (PR10, spec MOD-5).
 *
 * Dual-mode ElForm (create -> VarianteProductoCreate / edit ->
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
  <el-form label-position="top" @submit.prevent="onSubmit">
    <el-form-item label="Nombre de la variante">
      <el-input v-model="form.nombre_variante" data-test="nombre-variante-input" placeholder="Ej: Individual" />
    </el-form-item>
    <el-form-item label="Precio de venta">
      <el-input-number
        v-model="form.precio_venta"
        data-test="precio-variante-input"
        :min="0"
        :precision="2"
        :step="1000"
        style="width: 100%"
      />
    </el-form-item>
    <el-button type="primary" native-type="submit" :loading="saving" data-test="submit-variante">
      {{ submitLabel }}
    </el-button>
  </el-form>
</template>
