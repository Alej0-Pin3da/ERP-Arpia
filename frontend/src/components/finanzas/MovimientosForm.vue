<script setup lang="ts">
/**
 * Movimientos form (PR8, spec MOD-3; T9 edit mode).
 *
 * PrimeVue form that maps to POST /finanzas/movimientos
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
 * The DatePicker works on a Date while the payload contract keeps the
 * "YYYY-MM-DDTHH:mm:ss" string (no timezone suffix): `fecha` stays a string
 * and a computed get/set converts to/from Date for the picker.
 *
 * The view owns the POST/PATCH, the success message and the list refresh.
 */
import { computed, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import Button from 'primevue/button'
import DatePicker from 'primevue/datepicker'
import InputNumber from 'primevue/inputnumber'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'

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

const tipoOptions = computed(() => TIPO_MOVIMIENTO.map((t) => ({ label: tipoMovimientoLabel(t), value: t })))

/** T9/FIN-2: liquidacion-born rows freeze monto+socio (UI reinforcement only —
 *  the server 422s any attempt to change them). */
const frozenMontoSocio = computed(
  () => props.mode === 'edit' && props.initial?.liquidacion_id != null,
)

watch(
  () => props.initial,
  (mov) => {
    if (mov) {
      // The payload contract works on "YYYY-MM-DDTHH:mm:ss" (no timezone suffix).
      fecha.value = mov.fecha ? mov.fecha.replace('Z', '') : null
      tipo.value = mov.tipo as MovimientoTipo
      descripcion.value = mov.descripcion
      monto.value = Number.parseFloat(mov.monto)
      socioId.value = mov.socio_id
    }
  },
  { immediate: true },
)

/** "YYYY-MM-DDTHH:mm:ss" -> Date (parsed as UTC so the round-trip is exact). */
function parseFecha(value: string): Date {
  const [datePart, timePart] = value.split('T')
  const [y, m, d] = datePart.split('-').map(Number)
  const [hh, mm, ss] = timePart.split(':').map(Number)
  return new Date(Date.UTC(y, m - 1, d, hh, mm, ss))
}

/** Date -> "YYYY-MM-DDTHH:mm:ss" (UTC components, zero-padded). */
function formatFecha(date: Date): string {
  const pad = (n: number): string => String(n).padStart(2, '0')
  return (
    `${date.getUTCFullYear()}-${pad(date.getUTCMonth() + 1)}-${pad(date.getUTCDate())}` +
    `T${pad(date.getUTCHours())}:${pad(date.getUTCMinutes())}:${pad(date.getUTCSeconds())}`
  )
}

/** Bridge between the string payload contract and the Date-based DatePicker. */
const fechaModel = computed<Date | null>({
  get: () => (fecha.value ? parseFecha(fecha.value) : null),
  set: (date: Date | null) => {
    fecha.value = date ? formatFecha(date) : null
  },
})

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
  <form class="movimiento-form" @submit.prevent="submit">
    <div class="form-grid">
      <div v-if="mode === 'edit'" class="form-col" style="--md: 6">
        <div class="form-item">
          <label class="form-label">Fecha</label>
          <DatePicker
            v-model="fechaModel"
            show-time
            hour-format="24"
            date-format="dd/mm/yy"
            placeholder="Selecciona la fecha"
            class="movimiento-field"
            data-test="fecha-picker"
          />
        </div>
      </div>
      <div class="form-col" style="--md: 6">
        <div class="form-item">
          <label class="form-label">Tipo de movimiento</label>
          <Select
            v-model="tipo"
            :options="tipoOptions"
            option-label="label"
            option-value="value"
            class="movimiento-field"
            data-test="tipo-movimiento-select"
          />
        </div>
      </div>
      <div class="form-col" style="--md: 10">
        <div class="form-item">
          <label class="form-label">Descripción</label>
          <InputText v-model="descripcion" placeholder="Ej: Compra de insumos" data-test="descripcion-input" />
        </div>
      </div>
      <div class="form-col" style="--md: 4">
        <div class="form-item">
          <label class="form-label">Monto</label>
          <InputNumber
            v-model="monto"
            :min="0.01"
            :min-fraction-digits="2"
            :max-fraction-digits="2"
            :step="1000"
            :use-grouping="false"
            :show-buttons="false"
            :disabled="frozenMontoSocio"
            class="movimiento-field"
            data-test="monto-input"
          />
        </div>
      </div>
      <div class="form-col" style="--md: 4">
        <div class="form-item">
          <label class="form-label">Socio (opcional)</label>
          <Select
            v-model="socioId"
            :options="socios"
            option-label="nombre"
            option-value="id"
            show-clear
            filter
            placeholder="Sin socio"
            :disabled="frozenMontoSocio"
            class="movimiento-field"
            data-test="socio-select"
          />
        </div>
      </div>
    </div>

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
      <Button type="submit" :loading="saving" data-test="submit-movimiento">
        {{ mode === 'edit' ? 'Guardar cambios' : 'Registrar movimiento' }}
      </Button>
    </div>
  </form>
</template>

<style scoped>
.movimiento-form {
  max-width: 56rem;
}

.movimiento-field {
  width: 100%;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(24, 1fr);
  gap: 0.5rem 1rem;
}

.form-col {
  grid-column: span 24;
}

@media (min-width: 768px) {
  .form-col {
    grid-column: span var(--md, 24);
  }
}

.form-item {
  display: flex;
  flex-direction: column;
}

.form-label {
  margin-bottom: 0.25rem;
  font-size: 0.875rem;
  color: var(--el-text-color-primary);
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