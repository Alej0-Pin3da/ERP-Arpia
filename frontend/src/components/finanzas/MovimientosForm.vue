<script setup lang="ts">
/**
 * Movimientos form (PR8, spec MOD-3; T9 edit mode).
 *
 * Element Plus form that maps to POST /finanzas/movimientos
 * (MovimientoCreate): required tipo (Gasto|Inversion|Retiro), descripcion
 * and monto > 0; the socio select is OPTIONAL for every tipo — the backend
 * does not require socio_id even for a Retiro (schema default None; the
 * service only 400s on a nonexistent id), so there is no per-tipo required
 * rule to enforce client-side.
 *
 * Edit mode (T9): same pattern as SociosForm — `mode: 'edit'` + `initial`
 * prefill via watch, submit emits the MovimientoUpdate PATCH body through
 * `buildMovimientoUpdatePayload`. The Fecha field appears in edit mode only
 * (create rows get the server's now()). For liquidacion-born rows (initial.
 * liquidacion_id != null) monto and socio are DISABLED and never sent — the
 * real protection is the server-side guard (FIN-2 -> 422); the UI is
 * reinforcement only.
 *
 * The view owns the POST/PATCH, the success message and the list refresh.
 */
import { computed, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'

import {
  TIPO_MOVIMIENTO,
  buildMovimientoPayload,
  buildMovimientoUpdatePayload,
  tipoMovimientoLabel,
  type MovimientoCreate,
  type MovimientoTipo,
  type MovimientoUpdate,
} from '@/utils/finanzas'
import type { MovimientoRead, SocioConfiguracionRead } from '@/types/api.d'

const props = withDefaults(
  defineProps<{
    /** Partner rows for the optional socio select (view loads /finanzas/socios). */
    socios: SocioConfiguracionRead[]
    /** 'create' POSTs; 'edit' PATCHes with `initial` as the prefill. */
    mode?: 'create' | 'edit'
    /** The row being edited (prefills every editable field in edit mode). */
    initial?: MovimientoRead | null
    /** True while the parent is POST/PATCHing — disables the submit button. */
    saving?: boolean
  }>(),
  { mode: 'create', initial: null, saving: false },
)

const emit = defineEmits<{
  submit: [payload: MovimientoCreate | MovimientoUpdate]
}>()

const fecha = ref<string | null>(null)
const tipo = ref<MovimientoTipo | null>(null)
const descripcion = ref('')
const monto = ref<number | null>(null)
const socioId = ref<number | null>(null)

/** T9/FIN-2: liquidacion-born rows freeze monto+socio (UI reinforcement only —
 *  the server 422s any attempt to change them). */
const frozenMontoSocio = computed(
  () => props.mode === 'edit' && props.initial?.liquidacion_id != null,
)

watch(
  () => props.initial,
  (mov) => {
    if (mov) {
      // The date picker works on "YYYY-MM-DDTHH:mm:ss" (no timezone suffix).
      fecha.value = mov.fecha ? mov.fecha.replace('Z', '') : null
      tipo.value = mov.tipo as MovimientoTipo
      descripcion.value = mov.descripcion
      monto.value = Number.parseFloat(mov.monto)
      socioId.value = mov.socio_id
    }
  },
  { immediate: true },
)

/** MOD-3/T9: client gates — tipo and descripcion required; monto required
 *  whenever it is part of the payload (create + edit of non-liquidacion rows). */
function submit(): void {
  if (tipo.value === null) {
    ElMessage.warning('Selecciona el tipo de movimiento.')
    return
  }
  if (descripcion.value.trim() === '') {
    ElMessage.warning('Escribe una descripción del movimiento.')
    return
  }
  if (!frozenMontoSocio.value && (monto.value === null || monto.value <= 0)) {
    ElMessage.warning('El monto debe ser mayor a cero.')
    return
  }
  if (props.mode === 'edit') {
    emit(
      'submit',
      buildMovimientoUpdatePayload({
        fecha: fecha.value,
        tipo: tipo.value,
        descripcion: descripcion.value,
        monto: monto.value,
        socio_id: socioId.value,
        frozenMontoSocio: frozenMontoSocio.value,
      }),
    )
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
      <el-col v-if="mode === 'edit'" :xs="24" :md="6">
        <el-form-item label="Fecha">
          <el-date-picker
            v-model="fecha"
            type="datetime"
            value-format="YYYY-MM-DDTHH:mm:ss"
            placeholder="Selecciona la fecha"
            class="movimiento-field"
            data-test="fecha-picker"
          />
        </el-form-item>
      </el-col>
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
            :disabled="frozenMontoSocio"
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
            :disabled="frozenMontoSocio"
            class="movimiento-field"
            data-test="socio-select"
          >
            <el-option v-for="s in socios" :key="s.id" :label="s.nombre" :value="s.id" />
          </el-select>
        </el-form-item>
      </el-col>
    </el-row>

    <div class="form-footer">
      <span class="form-hint">
        {{
          mode === 'edit'
            ? frozenMontoSocio
              ? 'Los movimientos de una liquidación no permiten cambiar monto ni socio.'
              : 'Edita los campos que necesites; la fecha, el tipo y la descripción también son editables.'
            : 'El socio se asocia a un retiro o gasto puntual; es opcional.'
        }}
      </span>
      <el-button type="primary" native-type="submit" :loading="saving" data-test="submit-movimiento">
        {{ mode === 'edit' ? 'Guardar cambios' : 'Registrar movimiento' }}
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
