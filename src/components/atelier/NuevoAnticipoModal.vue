<script setup lang="ts">
/* eslint-disable @typescript-eslint/no-explicit-any */
import { ref, computed, watch } from 'vue'
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Dropdown from 'primevue/dropdown'
import Textarea from 'primevue/textarea'
import { useAtelierStore, type AnticipoSocia } from '@/stores/atelier'
import { showToast } from '@/utils/toast'
import { useMode } from '@/composables/useMode'
import { useFinanzas } from '@/composables/useFinanzas'

const props = defineProps<{
  visible: boolean
  anticipoEditar?: AnticipoSocia | null
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
  (e: 'guardado', ant: AnticipoSocia): void
}>()

const atelier = useAtelierStore()
const { isMock } = useMode()
const finanzasApi = useFinanzas()

const isEditing = computed(() => !!props.anticipoEditar)

// Form fields
const sociaId = ref(2)
const fecha = ref(new Date().toISOString().split('T')[0])
const monto = ref(300000)
const concepto = ref('')
const metodoDesembolso = ref('Transferencia Nequi')
const estado = ref<AnticipoSocia['estado']>('PENDIENTE_DESCUENTO')
const comprobante = ref('')
const observaciones = ref('')

const sociasOptions = computed(() => {
  return (isMock.value ? atelier.socias : [] as any[]).map((s) => ({
    label: `${s.nombre} (${s.rol})`,
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
    const soc = (isMock.value ? atelier.socias : [] as any[]).find((s) => !s.es_fondo_taller)
    sociaId.value = soc ? soc.id : 2
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
    if (val) initForm()
  },
  { immediate: true },
)

function formatCOP(val: number) {
  return `$${Math.round(val).toLocaleString('es-CO')}`
}

async function guardar() {
  if (!concepto.value.trim()) {
    showToast('warn', 'Campo requerido', 'Por favor indique el concepto o justificación del anticipo.')
    return
  }

  if (monto.value <= 0) {
    showToast('warn', 'Monto inválido', 'El monto del anticipo debe ser mayor a 0.')
    return
  }

  if (isMock.value) {
    const soc = (isMock.value ? atelier.socias : [] as any[]).find((s) => s.id === sociaId.value)
    const payload: Partial<AnticipoSocia> = {
      socia_id: sociaId.value,
      nombre_socia: soc?.nombre || 'Socia Atelier',
      fecha: fecha.value,
      monto: Number(monto.value) || 0,
      concepto: concepto.value.trim(),
      metodo_desembolso: metodoDesembolso.value,
      estado: estado.value,
      comprobante: comprobante.value.trim(),
      observaciones: observaciones.value.trim(),
    }
    if (isEditing.value && props.anticipoEditar) {
      if (!isMock.value) { showToast('info','Modo REAL','Use Finanzas API'); return }
      const act = atelier.actualizarAnticipo(props.anticipoEditar.id, payload)
      if (act) {
        showToast('success', 'Anticipo Actualizado', `Anticipo de ${formatCOP(act.monto)} para ${act.nombre_socia} actualizado.`)
        emit('guardado', act)
      }
    } else {
      if (!isMock.value) { showToast('info','Modo REAL','Use Finanzas API'); return }
      const nuevo = atelier.crearAnticipo(payload)
      showToast('success', 'Anticipo Registrado', `Se registró un anticipo de ${formatCOP(nuevo.monto)} para ${nuevo.nombre_socia}.`)
      emit('guardado', nuevo)
    }
    emit('update:visible', false)
    return
  }

  // Real API
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
        emit('guardado', updated as unknown as AnticipoSocia)
      } else {
        showToast('info', 'Sin cambios', 'No hay cambios de estado para guardar en modo REAL.')
      }
      emit('update:visible', false)
      return
    }
    const creado = await finanzasApi.createAnticipo(apiPayload)
    showToast('success', 'Anticipo Registrado', `Anticipo de ${formatCOP(Number((creado as unknown as Record<string, unknown>).monto ?? apiPayload.monto))} registrado en BD.`)
    emit('guardado', creado as unknown as AnticipoSocia)
    emit('update:visible', false)
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? 'Error al guardar anticipo'
    showToast('error', 'Error', String(msg))
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
            class="w-full text-xs"
          />
        </div>

        <div>
          <label class="block text-[11px] font-bold text-stone-400 uppercase tracking-wider mb-1">
            Fecha de Entrega
          </label>
          <InputText v-model="fecha" type="date" class="w-full text-xs font-mono" />
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
            class="w-full text-xs font-mono"
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
            />
          </div>

          <div>
            <label class="block text-[10px] text-stone-400 uppercase font-bold tracking-wider mb-1">
              Comprobante / N° Transacción
            </label>
            <InputText v-model="comprobante" class="w-full text-xs font-mono" placeholder="NEQ-99120" />
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
          @click="guardar"
        />
      </div>
    </template>
  </Dialog>
</template>
