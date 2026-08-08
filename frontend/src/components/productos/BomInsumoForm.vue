<script setup lang="ts">
/**
 * BOM insumo line form (PR10, spec MOD-5).
 *
 * Dual-mode ElForm (create -> BomInsumoCreate / edit -> BomInsumoUpdate):
 * insumo select (insumos prop), cantidad_requerida (> 0) and
 * porcentaje_desperdicio (0..100). Client gates es-CO: insumo and cantidad
 * are required. Edit prefills from the row (the backend PUT schema accepts
 * the full field set).
 *
 * Emits the API-ready payload via buildBomInsumoPayload/Update — variante_id
 * is omitted when null (the base rule row applies to all variants).
 */
import { computed, reactive, watch } from 'vue'
import { ElMessage } from 'element-plus'

import type { components } from '@/types/api.d'
import { parseDecimal } from '@/utils/format'
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
    ElMessage.warning('Selecciona el insumo')
    return
  }
  if (form.cantidad_requerida === null || form.cantidad_requerida <= 0) {
    ElMessage.warning('Indica la cantidad requerida')
    return
  }
  emit('submit', props.mode === 'edit' ? buildBomInsumoUpdatePayload(form) : buildBomInsumoPayload(form))
}
</script>

<template>
  <el-form label-position="top" @submit.prevent="onSubmit">
    <el-form-item label="Insumo">
      <el-select
        v-model="form.insumo_id"
        data-test="bom-insumo-select"
        placeholder="Selecciona el insumo"
        style="width: 100%"
      >
        <el-option v-for="i in insumos" :key="i.id" :label="i.nombre" :value="i.id" />
      </el-select>
    </el-form-item>
    <el-form-item label="Cantidad requerida">
      <el-input-number
        v-model="form.cantidad_requerida"
        data-test="cantidad-bom-insumo-input"
        :min="0.01"
        :precision="2"
        style="width: 100%"
      />
    </el-form-item>
    <el-form-item label="Desperdicio (%)">
      <el-input-number
        v-model="form.porcentaje_desperdicio"
        data-test="desperdicio-bom-insumo-input"
        :min="0"
        :max="100"
        :precision="2"
        style="width: 100%"
      />
    </el-form-item>
    <el-button type="primary" native-type="submit" :loading="saving" data-test="submit-bom-insumo">
      {{ submitLabel }}
    </el-button>
  </el-form>
</template>
