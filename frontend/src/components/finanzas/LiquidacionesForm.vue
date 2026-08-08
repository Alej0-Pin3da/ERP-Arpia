<script setup lang="ts">
/**
 * Liquidaciones form (PR8, spec MOD-3).
 *
 * Element Plus form that maps to POST /finanzas/liquidaciones
 * (LiquidacionCreate): monto > 0 and optional notas. The settlement is
 * ONE-TIME — the backend rejects a replay of the same liquidacion_id with
 * 409 — so the form carries an explicit warning. The view owns the POST, the
 * per-socio result table and the 409 surfacing.
 */
import { ref } from 'vue'
import { ElMessage } from 'element-plus'

import { buildLiquidacionPayload, type LiquidacionCreate } from '@/utils/finanzas'

defineProps<{
  /** True while the parent is POSTing — disables the submit button. */
  saving?: boolean
}>()

const emit = defineEmits<{ submit: [payload: LiquidacionCreate] }>()

const monto = ref<number | null>(null)
const notas = ref('')

/** MOD-3: client gate — monto is required (> 0). */
function submit(): void {
  if (monto.value === null || monto.value <= 0) {
    ElMessage.warning('Indica el monto a liquidar.')
    return
  }
  emit(
    'submit',
    buildLiquidacionPayload({ monto: monto.value, notas: notas.value }),
  )
}
</script>

<template>
  <el-form label-position="top" class="liquidacion-form" @submit.prevent="submit">
    <el-row :gutter="16">
      <el-col :xs="24" :md="8">
        <el-form-item label="Monto a liquidar">
          <el-input-number
            v-model="monto"
            :min="0.01"
            :precision="2"
            :step="100000"
            :controls="false"
            class="liquidacion-field"
            data-test="monto-liquidacion-input"
          />
        </el-form-item>
      </el-col>
      <el-col :xs="24" :md="16">
        <el-form-item label="Notas">
          <el-input
            v-model="notas"
            type="textarea"
            :rows="2"
            placeholder="Opcional"
            data-test="notas-input"
          />
        </el-form-item>
      </el-col>
    </el-row>

    <div class="form-footer">
      <span class="form-hint">
        La liquidación se procesa una sola vez y genera un Retiro por socio según su participación.
      </span>
      <el-button type="primary" native-type="submit" :loading="saving" data-test="submit-liquidacion">
        Procesar liquidación
      </el-button>
    </div>
  </el-form>
</template>

<style scoped>
.liquidacion-form {
  max-width: 48rem;
}

.liquidacion-field {
  width: 100%;
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
