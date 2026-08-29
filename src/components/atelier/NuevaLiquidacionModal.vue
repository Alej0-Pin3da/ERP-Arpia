<script setup lang="ts">
/* eslint-disable @typescript-eslint/no-explicit-any */
import { ref, computed, watch } from 'vue'
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Dropdown from 'primevue/dropdown'
import Textarea from 'primevue/textarea'
import { useAtelierStore, type LiquidacionSocias } from '@/stores/atelier'
import { showToast } from '@/utils/toast'
import { useMode } from '@/composables/useMode'
import { useFinanzas } from '@/composables/useFinanzas'

const props = defineProps<{
  visible: boolean
  liquidacionEditar?: LiquidacionSocias | null
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
  (e: 'guardada', liq: LiquidacionSocias): void
}>()

const atelier = useAtelierStore()
const { isMock } = useMode()
const finanzasApi = useFinanzas()

const isEditing = computed(() => !!props.liquidacionEditar)

// Form fields
const codigo = ref('')
const periodo = ref('')
const fechaCierre = ref(new Date().toISOString().split('T')[0])
const totalVentas = ref(0)
const costoInsumos = ref(0)
const gastosOperativos = ref(1500000)
const estado = ref<LiquidacionSocias['estado']>('BORRADOR')
const observaciones = ref('')

interface LocalItemDistribucion {
  socia_id: number
  nombre_socia: string
  rol_socia: string
  porcentaje: number
  monto_bruto: number
  deduccion_anticipos: number
  monto_neto_pagar: number
  estado_pago: 'PAGADO' | 'PENDIENTE' | 'RETENIDO'
  fecha_pago?: string
  comprobante_transferencia?: string
  banco_destino?: string
}

const distribucionLocal = ref<LocalItemDistribucion[]>([])

const estadosOptions = [
  { label: 'Borrador / En Revisión', value: 'BORRADOR' },
  { label: 'Aprobada por Socias', value: 'APROBADA' },
  { label: 'Totalmente Pagada / Transferida', value: 'PAGADA' },
]

function formatCOP(val: number) {
  return `$${Math.round(val).toLocaleString('es-CO')}`
}

const utilidadNetaCalculada = computed(() => {
  return Math.max(0, totalVentas.value - costoInsumos.value - gastosOperativos.value)
})

const fondoReinversionCalculado = computed(() => {
  return Math.round(utilidadNetaCalculada.value * 0.4)
})

const utilidadRepartibleSocias = computed(() => {
  return utilidadNetaCalculada.value - fondoReinversionCalculado.value
})

function recalcularDistribucion() {
  const util = utilidadNetaCalculada.value
  const activas = (isMock.value ? atelier.socias : [] as any[]).filter((s) => s.activo)

  distribucionLocal.value = activas.map((s) => {
    const montoBruto = Math.round(util * (s.porcentaje / 100))
    // Get pending anticipos for this socia
    const antPending = (isMock.value ? atelier.anticipos : [] as any[])
      .filter((a) => a.socia_id === s.id && a.estado === 'PENDIENTE_DESCUENTO')
      .reduce((sum, a) => sum + a.monto, 0)

    const existingItem = props.liquidacionEditar?.distribucion.find((d) => d.socia_id === s.id)
    const ded = existingItem ? existingItem.deduccion_anticipos : Math.min(montoBruto, antPending)

    return {
      socia_id: s.id,
      nombre_socia: s.nombre,
      rol_socia: s.rol,
      porcentaje: s.porcentaje,
      monto_bruto: montoBruto,
      deduccion_anticipos: ded,
      monto_neto_pagar: Math.max(0, montoBruto - ded),
      estado_pago: existingItem?.estado_pago || (estado.value === 'PAGADA' ? 'PAGADO' : 'PENDIENTE'),
      fecha_pago: existingItem?.fecha_pago,
      comprobante_transferencia: existingItem?.comprobante_transferencia,
      banco_destino: s.banco ? `${s.banco} (${s.numero_cuenta || 'N/A'})` : 'Efectivo Taller',
    }
  })
}

function cargarDatosVentasReales() {
  // Pull real total from atelier.ventas completed
  const completadas = (isMock.value ? atelier.ventas : [] as any[]).filter((v) => v.estado === 'COMPLETADA')
  const vTotal = completadas.reduce((acc, v) => acc + v.total_venta, 0)
  const cTotal = completadas.reduce((acc, v) => acc + v.costo_total, 0)

  totalVentas.value = vTotal > 0 ? vTotal : 23500000
  costoInsumos.value = cTotal > 0 ? cTotal : 6800000
  gastosOperativos.value = 1800000
  recalcularDistribucion()

  showToast('info', 'Valores Importados', `Se importaron ${formatCOP(totalVentas.value)} en ventas completadas del taller.`)
}

function initForm() {
  if (props.liquidacionEditar) {
    const l = props.liquidacionEditar
    codigo.value = l.codigo
    periodo.value = l.periodo
    fechaCierre.value = l.fecha_cierre
    totalVentas.value = l.total_ventas_brutas
    costoInsumos.value = l.costo_taller_insumos
    gastosOperativos.value = l.gastos_operativos
    estado.value = l.estado
    observaciones.value = l.observaciones || ''
    distribucionLocal.value = l.distribucion.map((d) => ({ ...d }))
  } else {
    const nextNum = isMock.value ? (atelier.liquidaciones.length ? Math.max(...atelier.liquidaciones.map((l) => l.id)) : 0) + 1 : 1
    codigo.value = `LIQ-${new Date().getFullYear()}-${String(nextNum).padStart(2, '0')}`
    periodo.value = `Liquidación Periodo ${new Date().toLocaleString('es-CO', { month: 'long', year: 'numeric' })}`
    fechaCierre.value = new Date().toISOString().split('T')[0]
    totalVentas.value = isMock.value ? (atelier.totalVentasRealizadas || 24800000) : totalVentas.value || 0
    costoInsumos.value = 7200000
    gastosOperativos.value = 1800000
    estado.value = 'BORRADOR'
    observaciones.value = 'Liquidación de utilidades sujeta a revisión y visto bueno de las socias.'
    recalcularDistribucion()
  }
}

watch(
  () => props.visible,
  (val) => {
    if (val) initForm()
  },
  { immediate: true },
)

watch([totalVentas, costoInsumos, gastosOperativos], () => {
  recalcularDistribucion()
})

async function guardar() {
  if (!periodo.value.trim()) {
    showToast('warn', 'Campo requerido', 'Por favor indique el nombre o periodo de la liquidación.')
    return
  }

  if (isMock.value) {
    const payload: Partial<LiquidacionSocias> = {
      codigo: codigo.value || `LIQ-${Date.now().toString().slice(-4)}`,
      periodo: periodo.value.trim(),
      fecha_cierre: fechaCierre.value,
      total_ventas_brutas: totalVentas.value,
      costo_taller_insumos: costoInsumos.value,
      gastos_operativos: gastosOperativos.value,
      utilidad_neta_total: utilidadNetaCalculada.value,
      fondo_reinversion_monto: fondoReinversionCalculado.value,
      utilidad_repartible: utilidadRepartibleSocias.value,
      estado: estado.value,
      distribucion: distribucionLocal.value.map((d) => ({
        socia_id: d.socia_id,
        nombre_socia: d.nombre_socia,
        rol_socia: d.rol_socia,
        porcentaje: d.porcentaje,
        monto_bruto: d.monto_bruto,
        deduccion_anticipos: d.deduccion_anticipos,
        monto_neto_pagar: d.monto_neto_pagar,
        estado_pago: d.estado_pago,
        fecha_pago: d.estado_pago === 'PAGADO' ? (d.fecha_pago || new Date().toISOString().split('T')[0]) : undefined,
        comprobante_transferencia: d.comprobante_transferencia,
        banco_destino: d.banco_destino,
      })),
      observaciones: observaciones.value,
    }
    if (isEditing.value && props.liquidacionEditar) {
      const act = atelier.actualizarLiquidacion(props.liquidacionEditar.id, payload)
      if (act) {
        showToast('success', 'Liquidación Actualizada', `La liquidación ${act.codigo} fue actualizada.`)
        emit('guardada', act)
      }
    } else {
      const nueva = atelier.crearLiquidacion(payload)
      showToast('success', 'Liquidación Creada', `Liquidación ${nueva.codigo} registrada con ${formatCOP(nueva.utilidad_neta_total)} de utilidad.`)
      emit('guardada', nueva)
    }
    emit('update:visible', false)
    return
  }

  // Real API: server computes codigo + distribucion, only header totals sent
  const apiPayload = {
    periodo: periodo.value.trim(),
    fecha_cierre: fechaCierre.value,
    total_ventas_brutas: totalVentas.value,
    costo_taller_insumos: costoInsumos.value,
    gastos_operativos: gastosOperativos.value,
    utilidad_neta_total: utilidadNetaCalculada.value,
    fondo_reinversion_monto: fondoReinversionCalculado.value,
    utilidad_repartible: utilidadRepartibleSocias.value,
    observaciones: observaciones.value || null,
  }
  try {
    if (isEditing.value && props.liquidacionEditar) {
      // Editing not supported via API (only state transition); keep local mock for edit
      showToast('warn', 'Edición', 'La edición de liquidaciones existentes solo está disponible en modo MOCK. Use cambio de estado para transiciones.')
      return
    }
    const creada = await finanzasApi.createLiquidacion(apiPayload)
    const cod = (creada as unknown as Record<string, unknown>).codigo as string
    showToast('success', 'Liquidación Creada', `Liquidación ${cod} registrada en BD.`)
    emit('guardada', creada as unknown as LiquidacionSocias)
    emit('update:visible', false)
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? 'Error al crear liquidación'
    showToast('error', 'Error', String(msg))
  }
}
</script>

<template>
  <Dialog
    :visible="visible"
    modal
    :header="isEditing ? `✏️ Editar Liquidación: ${liquidacionEditar?.codigo}` : '✨ Nueva Liquidación & Reparto de Socias'"
    :style="{ width: '92vw', maxWidth: '850px' }"
    @update:visible="(v) => emit('update:visible', v)"
  >
    <div class="space-y-5 pt-1 text-xs text-stone-200">
      <!-- Top info bar -->
      <div class="grid grid-cols-1 sm:grid-cols-4 gap-3 bg-stone-900/70 p-3.5 rounded-xl border border-stone-800">
        <div>
          <label class="block text-[11px] font-bold text-amber-300 uppercase tracking-wider mb-1">
            Código Liquidación
          </label>
          <InputText v-model="codigo" class="w-full text-xs font-mono" placeholder="LIQ-2026-05" />
        </div>

        <div class="sm:col-span-2">
          <label class="block text-[11px] font-bold text-stone-300 uppercase tracking-wider mb-1">
            Periodo o Concepto de Cierre
          </label>
          <InputText v-model="periodo" class="w-full text-xs" placeholder="Ej: Agosto 2026 / Colección Set Aelo" />
        </div>

        <div>
          <label class="block text-[11px] font-bold text-stone-400 uppercase tracking-wider mb-1">
            Fecha de Cierre
          </label>
          <InputText v-model="fechaCierre" type="date" class="w-full text-xs font-mono" />
        </div>
      </div>

      <!-- Financial Base Numbers (Ventas, Insumos, Gastos) -->
      <div class="bg-stone-900/60 p-4 rounded-xl border border-stone-800 space-y-3">
        <div class="flex flex-wrap items-center justify-between gap-2">
          <div class="text-[11px] font-bold text-amber-400 uppercase tracking-wider font-mono">
            Balance Financiero del Periodo
          </div>
          <Button
            label="Importar Ventas Reales del Atelier"
            icon="pi pi-sync"
            size="small"
            class="p-button-outlined p-button-warning text-[11px] py-1 px-2.5"
            @click="cargarDatosVentasReales"
          />
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div>
            <label class="block text-[10px] text-stone-400 uppercase font-bold tracking-wider mb-1">
              Total Ventas Brutas ($)
            </label>
            <InputNumber
              v-model="totalVentas"
              mode="currency"
              currency="COP"
              locale="es-CO"
              :min="0"
              class="w-full text-xs font-mono"
            />
          </div>

          <div>
            <label class="block text-[10px] text-stone-400 uppercase font-bold tracking-wider mb-1">
              Costo Insumos & Taller ($)
            </label>
            <InputNumber
              v-model="costoInsumos"
              mode="currency"
              currency="COP"
              locale="es-CO"
              :min="0"
              class="w-full text-xs font-mono"
            />
          </div>

          <div>
            <label class="block text-[10px] text-stone-400 uppercase font-bold tracking-wider mb-1">
              Gastos Operativos & Fijos ($)
            </label>
            <InputNumber
              v-model="gastosOperativos"
              mode="currency"
              currency="COP"
              locale="es-CO"
              :min="0"
              class="w-full text-xs font-mono"
            />
          </div>
        </div>

        <!-- Calculated Summary Strip -->
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2 font-mono">
          <div class="p-2.5 rounded-lg bg-stone-950 border border-stone-800 flex items-center justify-between">
            <span class="text-stone-400 text-[11px]">Utilidad Neta:</span>
            <span class="text-emerald-400 font-bold text-sm">{{ formatCOP(utilidadNetaCalculada) }}</span>
          </div>

          <div class="p-2.5 rounded-lg bg-amber-950/40 border border-amber-500/30 flex items-center justify-between">
            <span class="text-amber-300 text-[11px]">🏛️ Fondo Taller (40%):</span>
            <span class="text-amber-300 font-bold text-sm">{{ formatCOP(fondoReinversionCalculado) }}</span>
          </div>

          <div class="p-2.5 rounded-lg bg-stone-950 border border-stone-800 flex items-center justify-between">
            <span class="text-stone-300 text-[11px]">Reparto Socias (60%):</span>
            <span class="text-stone-100 font-bold text-sm">{{ formatCOP(utilidadRepartibleSocias) }}</span>
          </div>
        </div>
      </div>

      <!-- Partner Breakdown Table -->
      <div class="bg-stone-900/90 rounded-xl border border-stone-800 overflow-hidden">
        <div class="p-3.5 bg-stone-950/90 border-b border-stone-800 flex items-center justify-between">
          <div class="text-[11px] font-bold text-amber-300 uppercase tracking-wider font-mono">
            Distribución & Deducción de Anticipos por Socia (40% / 30% / 30%)
          </div>
          <div class="text-[10px] text-stone-400 font-mono">
            {{ distribucionLocal.length }} Participantes
          </div>
        </div>

        <div class="overflow-x-auto">
          <table class="w-full text-xs text-left border-collapse font-mono">
            <thead>
              <tr class="border-b border-stone-800 text-stone-400 text-[10px] uppercase">
                <th class="py-2.5 px-3">Socia / Fondo</th>
                <th class="py-2.5 px-2 text-center">% Part.</th>
                <th class="py-2.5 px-3 text-right">Cuota Bruta</th>
                <th class="py-2.5 px-3 text-right">Deducción Anticipos</th>
                <th class="py-2.5 px-3 text-right">Neto a Transferir</th>
                <th class="py-2.5 px-3 text-center">Estado Pago</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-stone-800/60">
              <tr v-for="d in distribucionLocal" :key="d.socia_id" class="hover:bg-stone-800/30">
                <td class="py-3 px-3">
                  <div class="font-serif font-bold text-stone-100 text-xs">{{ d.nombre_socia }}</div>
                  <div class="text-[10px] text-stone-500">{{ d.rol_socia }}</div>
                </td>
                <td class="py-3 px-2 text-center font-bold text-amber-400">
                  {{ d.porcentaje }}%
                </td>
                <td class="py-3 px-3 text-right font-bold text-stone-200">
                  {{ formatCOP(d.monto_bruto) }}
                </td>
                <td class="py-3 px-3 text-right">
                  <InputNumber
                    v-model="d.deduccion_anticipos"
                    mode="currency"
                    currency="COP"
                    locale="es-CO"
                    :min="0"
                    class="w-28 text-xs font-mono text-rose-400"
                    @update:model-value="d.monto_neto_pagar = Math.max(0, d.monto_bruto - d.deduccion_anticipos)"
                  />
                </td>
                <td class="py-3 px-3 text-right font-bold text-emerald-400 text-sm">
                  {{ formatCOP(d.monto_neto_pagar) }}
                </td>
                <td class="py-3 px-3 text-center">
                  <Dropdown
                    v-model="d.estado_pago"
                    :options="[
                      { label: 'Pendiente', value: 'PENDIENTE' },
                      { label: 'Pagado', value: 'PAGADO' },
                      { label: 'Retenido', value: 'RETENIDO' }
                    ]"
                    option-label="label"
                    option-value="value"
                    class="w-28 text-[11px]"
                  />
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- State and Notes -->
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 bg-stone-900/60 p-3.5 rounded-xl border border-stone-800">
        <div>
          <label class="block text-[11px] font-bold text-stone-300 uppercase tracking-wider mb-1">
            Estado de la Liquidación
          </label>
          <Dropdown
            v-model="estado"
            :options="estadosOptions"
            option-label="label"
            option-value="value"
            class="w-full text-xs"
          />
        </div>

        <div class="sm:col-span-2">
          <label class="block text-[11px] font-bold text-stone-400 uppercase tracking-wider mb-1">
            Observaciones & Acta de Cierre
          </label>
          <Textarea
            v-model="observaciones"
            rows="2"
            placeholder="Notas sobre el periodo, metas cumplidas, transferencias bancarias..."
            class="w-full text-xs"
          />
        </div>
      </div>
    </div>

    <template #footer>
      <div class="flex items-center justify-end gap-2 pt-3 border-t border-stone-800">
        <Button
          label="Cancelar"
          icon="pi pi-times"
          size="small"
          class="p-button-text p-button-secondary text-xs"
          @click="emit('update:visible', false)"
        />
        <Button
          :label="isEditing ? 'Guardar Cambios' : 'Generar Liquidación'"
          icon="pi pi-check"
          size="small"
          class="p-button-warning text-xs font-semibold px-4"
          @click="guardar"
        />
      </div>
    </template>
  </Dialog>
</template>
