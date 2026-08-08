<script setup lang="ts">
/**
 * Socios form (PR8, spec MOD-3) — dual mode:
 *  - create: nombre + porcentaje_participacion -> POST /finanzas/socios
 *    (the server enforces an EXACT-100 global sum; otherwise 422).
 *  - edit: percentage ONLY — the backend SocioConfiguracionUpdate schema has
 *    no `nombre` field, so the partner name is not updatable; the current
 *    name is shown read-only. Updates may rebalance below 100 but never
 *    above (server 422, surfaced by the view).
 *
 * The view owns the POST/PATCH, the 422 surfacing and the refresh.
 */
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'

import {
  buildSocioPayload,
  buildSocioUpdatePayload,
  type SocioConfiguracionCreate,
  type SocioConfiguracionUpdate,
} from '@/utils/finanzas'
import type { SocioConfiguracionRead } from '@/types/api.d'

const props = withDefaults(
  defineProps<{
    /** 'create' shows nombre + porcentaje; 'edit' edits the percentage only. */
    mode?: 'create' | 'edit'
    /** The row being edited (prefills the percentage in edit mode). */
    initial?: SocioConfiguracionRead | null
    /** True while the parent is POST/PATCHing — disables the submit button. */
    saving?: boolean
  }>(),
  { mode: 'create', initial: null, saving: false },
)

const emit = defineEmits<{
  submit: [payload: SocioConfiguracionCreate | SocioConfiguracionUpdate]
}>()

const nombre = ref('')
const porcentaje = ref<number | null>(null)

watch(
  () => props.initial,
  (socio) => {
    if (socio) {
      porcentaje.value = Number.parseFloat(socio.porcentaje_participacion)
    }
  },
  { immediate: true },
)

/** MOD-3: client gates — create requires nombre; every mode requires a share. */
function submit(): void {
  if (props.mode === 'create' && nombre.value.trim() === '') {
    ElMessage.warning('Escribe el nombre del socio.')
    return
  }
  if (porcentaje.value === null || porcentaje.value <= 0) {
    ElMessage.warning('El porcentaje debe ser mayor a cero.')
    return
  }
  if (props.mode === 'edit') {
    emit('submit', buildSocioUpdatePayload(porcentaje.value))
    return
  }
  emit('submit', buildSocioPayload({ nombre: nombre.value, porcentaje_participacion: porcentaje.value }))
}
</script>

<template>
  <el-form label-position="top" class="socio-form" @submit.prevent="submit">
    <el-row :gutter="16">
      <el-col :xs="24" :md="12">
        <template v-if="mode === 'create'">
          <el-form-item label="Nombre del socio">
            <el-input v-model="nombre" placeholder="Ej: Ana María" data-test="nombre-socio-input" />
          </el-form-item>
        </template>
        <el-form-item v-else label="Socio">
          <span class="socio-name-static" data-test="socio-name-static">{{ initial?.nombre }}</span>
        </el-form-item>
      </el-col>
      <el-col :xs="24" :md="12">
        <el-form-item label="Porcentaje de participación">
          <el-input-number
            v-model="porcentaje"
            :min="0.01"
            :max="100"
            :precision="2"
            :step="5"
            class="socio-field"
            data-test="porcentaje-socio-input"
          />
        </el-form-item>
      </el-col>
    </el-row>

    <div class="form-footer">
      <span class="form-hint">
        {{ mode === 'edit' ? 'Solo se puede ajustar el porcentaje.' : 'La suma de participaciones debe ser exactamente 100%.' }}
      </span>
      <el-button type="primary" native-type="submit" :loading="saving" data-test="submit-socio">
        {{ mode === 'edit' ? 'Guardar cambios' : 'Crear socio' }}
      </el-button>
    </div>
  </el-form>
</template>

<style scoped>
.socio-form {
  max-width: 40rem;
}

.socio-field {
  width: 100%;
}

.socio-name-static {
  line-height: 2rem;
}

.form-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 0.5rem;
  gap: 1rem;
}

.form-hint {
  color: var(--el-text-color-secondary);
  font-size: 0.85rem;
}
</style>
