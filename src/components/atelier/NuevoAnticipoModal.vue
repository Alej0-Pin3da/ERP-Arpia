<script setup lang="ts">
/* eslint-disable @typescript-eslint/no-explicit-any */
import { ref, computed, watch } from 'vue'
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Dropdown from 'primevue/dropdown'
import Textarea from 'primevue/textarea'
import { showToast } from '@/utils/toast'
import { useFinanzas } from '@/composables/useFinanzas'
import { useSocios } from '@/composables/useSocios'
import type { AnticipoRead } from '@/services/api/anticipos'

/** Minimal anticipo shape this modal edits (REAL display object from the caller). */
export interface AnticipoEditar {
  id: number
  socia_id: number
  fecha: string
  monto: number
  concepto: string
  metodo_desembolso: string
  estado: 'PENDIENTE_DESCUENTO' | 'DESCONTADO' | 'ANULADO'
  comprobante?: string
  observaciones?: string
}

const props = defineProps<{
  visible: boolean
  anticipoEditar?: AnticipoEditar | null
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
  (e: 'guardado', ant: AnticipoRead): void
}>()

const finanzasApi = useFinanzas()
const sociosApi = useSocios()

const isEditing = computed(() => !!props.anticipoEditar)

// La API solo permite transicionar el estado; el resto de campos
// se deshabilitan al editar para no descartar ediciones en silencio.
const soloLecturaReal = computed(() => isEditing.value)

// Form fields
const sociaId = ref<number | null>(2)
const fecha = ref(new Date().toISOString().split('T')[0])
const monto = ref(300000)
const concepto = ref('')
const metodoDesembolso = ref('Transferencia Nequi')
const estado = ref<'PENDIENTE_DESCUENTO' | 'DESCONTADO' | 'ANULADO'>('PENDIENTE_DESCUENTO')
const comprobante = ref('')
const observaciones = ref('')

const guardando = ref(false)

const socias = ref<any[]>([])

async function cargarSocias() {
  try {
    const r = await sociosApi.list({ limit: 100 })
    socias.value = (r.items as any) ?? []
  } catch { socias.value = [] }
}

const sociasOptions = computed(() => {
  return (socias.value as any[]).map((s) => ({
    label: `${s.nombre} (${s.rol || 'Socia'})`,
    value: s.id,
  }))
})

const estadosOptions = [
  { label: '⏳ Pendiente de Descontar en Liquidación', value: 'PENDIENTE_DESCUENTO' },
  { label: '✅ Ya Descontado en Cierre Oficial', value: 'DESCONTADO' },
  { label: '🚫 Anulado / Cancelado', value: 'ANULADO' },
]

const metodosOptions = [
  { label: 'Transferencia Nequi', value: 'Transferencia Nequi' },
  { label: 'Transferencia Bancolombia', value: 'Transferencia Bancolombia' },
  { label: 'Daviplata', value: 'Daviplata' },
  { label: 'Efectivo Caja Taller', value: 'Efectivo Caja Taller' },
]

function initForm() {
  if (props.anticipoEditar) {
    const a = props.anticipoEditar
    sociaId.value = a.socia_id
    fecha.value = a.fecha
    monto.value = a.monto
    concepto.value = a.concepto
    metodoDesembolso.value = a.metodo_desembolso
    estado.value = a.estado
    comprobante.value = a.comprobante || ''
    observaciones.value = a.observaciones || ''
  } else {
    // Default to first non-fondo socia
    const soc = (socias.value as any[]).find((s) => !s.es_fondo_taller)
    sociaId.value = soc ? soc.id : null
    fecha.value = new Date().toISOString().split('T')[0]
    monto.value = 350000
    concepto.value = 'Adelanto a cuenta de utilidades mensuales'
    metodoDesembolso.value = 'Transferencia Nequi'
    estado.value = 'PENDIENTE_DESCUENTO'
    comprobante.value = `ANT-${Date.now().toString().slice(-4)}`
    observaciones.value = ''
  }
}

watch(
  () => props.visible,
  (val) => {
    if (val) {
      void cargarSocias()
      initForm()
    }
  },
  { immediate: true },
)

function formatCOP(val: number) {
  return `$${Math.round(val).toLocaleString('es-CO')}`
}

async function guardar() {
  if (guardando.value) return
  if (!concepto.value.trim()) {
    showToast('warn', 'Campo requerido', 'Por favor indique el concepto o justificación del anticipo.')
    return
  }

  if (monto.value <= 0) {
    showToast('warn', 'Monto inválido', 'El monto del anticipo debe ser mayor a 0.')
    return
  }

  // Real API
  if (sociaId.value == null) {
    showToast('warn', 'Socia requerida', 'Elegí la socia beneficiaria del anticipo.')
    return
  }
  guardando.value = true
  const apiPayload = {
    socia_id: sociaId.value,
    monto: Number(monto.value) || 0,
    fecha: fecha.value || null,
    concepto: concepto.value.trim() || null,
    metodo_desembolso: metodoDesembolso.value || null,
    comprobante: comprobante.value.trim() || null,
    observaciones: observaciones.value.trim() || null,
  }
  try {
    if (isEditing.value && props.anticipoEditar) {
      // Edit via PATCH estado if estado changed; monto/concepto not patchable via API in real mode
      if (estado.value !== props.anticipoEditar.estado) {
        const updated = await finanzasApi.transitionAnticipo(props.anticipoEditar.id, { estado: estado.value })
        showToast('success', 'Anticipo Actualizado', `Anticipo ${estado.value}.`)
        emit('guardado', updated)
      } else {
        showToast('info', 'Sin cambios', 'No hay cambios de estado para guardar.')
      }
      emit('update:visible', false)
      return
    }
    const creado = await finanzasApi.createAnticipo(apiPayload)
    showToast('success', 'Anticipo Registrado', `Anticipo de ${formatCOP(Number((creado as unknown as Record<string, unknown>).monto ?? apiPayload.monto))} registrado en BD.`)
    emit('guardado', creado)
    emit('update:visible', false)
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? 'Error al guardar anticipo'
    showToast('error', 'Error', String(msg))
  } finally {
    guardando.value = false
  }
}
</script>

<template>
  <Dialog
    :visible="visible"
    modal
    :header="isEditing ? '✏️ Editar Anticipo de Socia' : '💸 Registrar Nuevo Anticipo / Adelanto a Socia'"
    :style="{ width: '90vw', maxWidth: '580px' }"
    @update:visible="(v) => emit('update:visible', v)"
  >
    <div class="space-y-4 pt-1 text-xs text-stone-200">
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 bg-stone-900/70 p-3.5 rounded-xl border border-stone-800">
        <div class="sm:col-span-2">
          <label class="block text-[11px] font-bold text-amber-300 uppercase tracking-wider mb-1">
            Socia Beneficiaria *
          </label>
          <Dropdown
            v-model="sociaId"
            :options="sociasOptions"
            option-label="label"
            option-value="value"
            placeholder="Seleccionar socia..."
            class="w-full text-xs"
            :disabled="soloLecturaReal"
          />
        </div>

        <div v-if="soloLecturaReal" class="sm:col-span-2 bg-sky-950/20 border border-sky-500/20 rounded-xl p-3 text-xs text-sky-200/90 flex items-start gap-2">
          <i class="pi pi-info-circle text-sky-400 text-base flex-shrink-0 mt-0.5" />
          <span>La API solo permite <strong>cambiar el estado</strong> del anticipo; monto, concepto y demás datos no son editables.</span>
        </div>

        <div>
          <label class="block text-[11px] font-bold text-stone-400 uppercase tracking-wider mb-1">
            Fecha de Entrega
          </label>
          <InputText v-model="fecha" type="date" class="w-full text-xs font-mono" :disabled="soloLecturaReal" />
        </div>

        <div>
          <label class="block text-[11px] font-bold text-emerald-400 uppercase tracking-wider mb-1 font-mono">
            Monto del Anticipo (COP) *
          </label>
          <InputNumber
            v-model="monto"
            mode="currency"
            currency="COP"
            locale="es-CO"
            :min="1000"
            :min-fraction-digits="0"
            :max-fraction-digits="0"
            class="w-full text-xs font-mono"
            :disabled="soloLecturaReal"
          />
        </div>
      </div>

      <div class="bg-stone-900/60 p-3.5 rounded-xl border border-stone-800 space-y-3">
        <div>
          <label class="block text-[11px] font-bold text-stone-300 uppercase tracking-wider mb-1">
            Concepto / Motivo del Anticipo *
          </label>
          <InputText
            v-model="concepto"
            class="w-full text-xs"
            placeholder="Ej: Adelanto compra de telas en Medellín, honorarios modelos..."
            :disabled="soloLecturaReal"
          />
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label class="block text-[10px] text-stone-400 uppercase font-bold tracking-wider mb-1">
              Método de Desembolso
            </label>
            <Dropdown
              v-model="metodoDesembolso"
              :options="metodosOptions"
              option-label="label"
              option-value="value"
              class="w-full text-xs"
              :disabled="soloLecturaReal"
            />
          </div>

          <div>
            <label class="block text-[10px] text-stone-400 uppercase font-bold tracking-wider mb-1">
              Comprobante / N° Transacción
            </label>
            <InputText v-model="comprobante" class="w-full text-xs font-mono" placeholder="NEQ-99120" :disabled="soloLecturaReal" />
          </div>
        </div>

        <div>
          <label class="block text-[10px] text-stone-400 uppercase font-bold tracking-wider mb-1">
            Estado del Anticipo
          </label>
          <Dropdown
            v-model="estado"
            :options="estadosOptions"
            option-label="label"
            option-value="value"
            class="w-full text-xs"
          />
        </div>

        <div>
          <label class="block text-[10px] text-stone-400 uppercase font-bold tracking-wider mb-1">
            Observaciones Adicionales
          </label>
          <Textarea v-model="observaciones" rows="2" class="w-full text-xs" placeholder="Detalles de liquidación..." />
        </div>
      </div>
    </div>

    <template #footer>
      <div class="flex items-center justify-end gap-2 pt-2 border-t border-stone-800">
        <Button
          label="Cancelar"
          icon="pi pi-times"
          size="small"
          class="p-button-text p-button-secondary text-xs"
          @click="emit('update:visible', false)"
        />
        <Button
          :label="isEditing ? 'Guardar Cambios' : 'Registrar Anticipo'"
          icon="pi pi-check"
          size="small"
          class="p-button-warning text-xs font-semibold px-4"
          :loading="guardando"
          @click="guardar"
        />
      </div>
    </template>
  </Dialog>
</template>
