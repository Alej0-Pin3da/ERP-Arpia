<script setup lang="ts">
/**
 * Movimientos create form (PR8, spec MOD-3).
 *
 * Element Plus form that maps to POST /finanzas/movimientos
 * (MovimientoCreate): required tipo (Gasto|Inversion|Retiro), descripcion
 * and monto > 0; the socio select is OPTIONAL for every tipo — the backend
 * does not require socio_id even for a Retiro (schema default None; the
 * service only 400s on a nonexistent id), so there is no per-tipo required
 * rule to enforce client-side.
 *
 * The view owns the POST, the success message and the list refresh.
 */
import { ref } from 'vue'
import { ElMessage } from 'element-plus'

import {
  TIPO_MOVIMIENTO,
  buildMovimientoPayload,
  tipoMovimientoLabel,
  type MovimientoCreate,
  type MovimientoTipo,
} from '@/utils/finanzas'
import type { SocioConfiguracionRead } from '@/types/api.d'

defineProps<{
  /** Partner rows for the optional socio select (view loads /finanzas/socios). */
  socios: SocioConfiguracionRead[]
  /** True while the parent is POSTing — disables the submit button. */
  saving?: boolean
}>()

const emit = defineEmits<{ submit: [payload: MovimientoCreate] }>()

const tipo = ref<MovimientoTipo | null>(null)
const descripcion = ref('')
const monto = ref<number | null>(null)
const socioId = ref<number | null>(null)

/** MOD-3: client-side gates — tipo, descripcion and monto are required. */
function submit(): void {
  if (tipo.value === null) {
    ElMessage.warning('Selecciona el tipo de movimiento.')
    return
  }
  if (descripcion.value.trim() === '') {
    ElMessage.warning('Escribe una descripción del movimiento.')
    return
  }
  if (monto.value === null || monto.value <= 0) {
    ElMessage.warning('El monto debe ser mayor a cero.')
    return
  }
  emit(
    'submit',
    buildMovimientoPayload({
      tipo: tipo.value,
      descripcion: descripcion.value,
      monto: monto.value,
      socio_id: socioId.value,
    }),
  )
}
</script>

<template>
  <el-form label-position="top" class="movimiento-form" @submit.prevent="submit">
    <el-row :gutter="16">
      <el-col :xs="24" :md="6">
        <el-form-item label="Tipo de movimiento">
          <el-select v-model="tipo" class="movimiento-field" data-test="tipo-movimiento-select">
            <el-option
              v-for="t in TIPO_MOVIMIENTO"
              :key="t"
              :label="tipoMovimientoLabel(t)"
              :value="t"
            />
          </el-select>
        </el-form-item>
      </el-col>
      <el-col :xs="24" :md="10">
        <el-form-item label="Descripción">
          <el-input v-model="descripcion" placeholder="Ej: Compra de insumos" data-test="descripcion-input" />
        </el-form-item>
      </el-col>
      <el-col :xs="24" :md="4">
        <el-form-item label="Monto">
          <el-input-number
            v-model="monto"
            :min="0.01"
            :precision="2"
            :step="1000"
            :controls="false"
            class="movimiento-field"
            data-test="monto-input"
          />
        </el-form-item>
      </el-col>
      <el-col :xs="24" :md="4">
        <el-form-item label="Socio (opcional)">
          <el-select
            v-model="socioId"
            clearable
            filterable
            placeholder="Sin socio"
            class="movimiento-field"
            data-test="socio-select"
          >
            <el-option v-for="s in socios" :key="s.id" :label="s.nombre" :value="s.id" />
          </el-select>
        </el-form-item>
      </el-col>
    </el-row>

    <div class="form-footer">
      <span class="form-hint">El socio se asocia a un retiro o gasto puntual; es opcional.</span>
      <el-button type="primary" native-type="submit" :loading="saving" data-test="submit-movimiento">
        Registrar movimiento
      </el-button>
    </div>
  </el-form>
</template>

<style scoped>
.movimiento-form {
  max-width: 56rem;
}

.movimiento-field {
  width: 100%;
}

.form-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 0.5rem;
}

.form-hint {
  color: var(--el-text-color-secondary);
  font-size: 0.85rem;
}
</style>
