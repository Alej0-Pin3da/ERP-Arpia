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
import { useVentas } from '@/composables/useVentas'
import { getParametros } from '@/services/api/maestros'
import type { LiquidacionRead } from '@/services/api/liquidaciones'

/** Minimal liquidación shape this modal edits (REAL display object from the caller). */
export interface LiquidacionEditarItem {
  socia_id: number
  deduccion_anticipos: number
  estado_pago: string
  fecha_pago?: string
  comprobante_transferencia?: string
  banco_destino?: string
}
export interface LiquidacionEditar {
  id: number
  codigo: string
  periodo: string
  fecha_cierre: string
  total_ventas_brutas: number
  costo_taller_insumos: number
  gastos_operativos: number
  estado: string
  observaciones?: string
  distribucion: LiquidacionEditarItem[]
}

const props = defineProps<{
  visible: boolean
  liquidacionEditar?: LiquidacionEditar | null
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
  (e: 'guardada', liq: LiquidacionRead): void
}>()

const finanzasApi = useFinanzas()
const sociosApi = useSocios()
const ventasApi = useVentas()

const isEditing = computed(() => !!props.liquidacionEditar)

// Form fields
const codigo = ref('')
const periodo = ref('')
const fechaCierre = ref(new Date().toISOString().split('T')[0])
const totalVentas = ref(0)
const costoInsumos = ref(0)
const gastosOperativos = ref(1500000)
const estado = ref<'BORRADOR' | 'APROBADA' | 'PAGADA'>('BORRADOR')
const observaciones = ref('')
const guardando = ref(false)

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

// Ventas elegibles para liquidar (confirmed + sin liquidar).
const ventasElegibles = ref<{ id: number; codigo: string; fecha: string; cliente: string; total: number; costo: number }[]>([])

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
  return Math.round(utilidadNetaCalculada.value * (fondoPct.value / 100))
})

const utilidadRepartibleSocias = computed(() => {
  return utilidadNetaCalculada.value - fondoReinversionCalculado.value
})

// Socias + anticipos para la vista previa del reparto (el servidor calcula
// la distribución oficial al crear; esto solo previsualiza).
const sociasPreview = ref<{ id: number; nombre: string; rol: string; porcentaje: number; banco?: string; numero_cuenta?: string; activo: boolean }[]>([])
const anticiposPreview = ref<{ socia_id: number; monto: number; estado: string }[]>([])

async function cargarPreview() {
  try {
    const [s, a] = await Promise.all([
      sociosApi.list({ limit: 100 }),
      finanzasApi.listAnticipos({ limit: 100 }),
    ])
    sociasPreview.value = ((s as any).items ?? []).map((x: any) => ({
      id: x.id,
      nombre: x.nombre,
      rol: x.rol ?? 'Socia',
      porcentaje: Number(x.porcentaje_participacion ?? x.porcentaje ?? 0),
      banco: x.banco,
      numero_cuenta: x.numero_cuenta,
      activo: x.activo !== false,
    }))
    anticiposPreview.value = ((a as any).items ?? []).map((x: any) => ({
      socia_id: x.socia_id,
      monto: Number(x.monto ?? 0),
      estado: x.estado,
    }))
  } catch {
    sociasPreview.value = []
    anticiposPreview.value = []
  }
}

function recalcularDistribucion() {
  // Preview must mirror the server (crear_liquidacion): bruto over the
  // REPARTIBLE (neta - fondo del estatuto), ded = full pending sum (no cap),
  // neto = bruto - ded (may go negative, same as the server).
  const util = utilidadRepartibleSocias.value
  const activas = sociasPreview.value.filter((s) => s.activo)

  distribucionLocal.value = activas.map((s) => {
    const montoBruto = Math.round(util * (s.porcentaje / 100))
    // Get pending anticipos for this socia
    const antPending = anticiposPreview.value
      .filter((a) => a.socia_id === s.id && a.estado === 'PENDIENTE_DESCUENTO')
      .reduce((sum, a) => sum + a.monto, 0)

    const existingItem = props.liquidacionEditar?.distribucion.find((d) => d.socia_id === s.id)
    const ded = existingItem ? existingItem.deduccion_anticipos : antPending

    return {
      socia_id: s.id,
      nombre_socia: s.nombre,
      rol_socia: s.rol,
      porcentaje: s.porcentaje,
      monto_bruto: montoBruto,
      deduccion_anticipos: ded,
      monto_neto_pagar: montoBruto - ded,
      estado_pago: existingItem?.estado_pago || (estado.value === 'PAGADA' ? 'PAGADO' : 'PENDIENTE'),
      fecha_pago: existingItem?.fecha_pago,
      comprobante_transferencia: existingItem?.comprobante_transferencia,
      banco_destino: s.banco ? `${s.banco} (${s.numero_cuenta || 'N/A'})` : 'Efectivo Taller',
    }
  })
}

async function cargarTotalesVentas() {
  // Ventas elegibles: confirmed y sin liquidar (el servidor valida igual).
  try {
    const r = await ventasApi.list({ estado: 'confirmed', sin_liquidar: true, limit: 100 } as any)
    ventasElegibles.value = ((r as any).items ?? []).map((v: any) => ({
      id: v.id,
      codigo: v.codigo ?? `VEN-${v.id}`,
      fecha: String(v.fecha ?? '').slice(0, 10),
      cliente: v.cliente_nombre ?? '—',
      total: Number(v.total_venta ?? 0),
      costo: Number(v.costo_total ?? 0),
    }))
    if (!ventasElegibles.value.length) {
      showToast('info', 'Sin ventas', 'No hay ventas confirmadas sin liquidar.')
    }
  } catch {
    ventasElegibles.value = []
    showToast('error', 'No se pudo cargar', 'Revisá la conexión con el backend.')
  }
}

// % fondo del estatuto de Maestros (manda Maestros; 40 si no carga).
const fondoPct = ref(40)
async function cargarFondoEstatuto() {
  try {
    const p = await getParametros()
    fondoPct.value = Number((p as any).distribucion_reinversion_pct ?? 40)
  } catch {
    fondoPct.value = 40
  }
}

// Selección: con ventas elegidas los totales se calculan y se bloquean.
const ventasSel = ref<number[]>([])
const haySeleccion = computed(() => ventasSel.value.length > 0)
function toggleVenta(id: number) {
  ventasSel.value = ventasSel.value.includes(id)
    ? ventasSel.value.filter((x) => x !== id)
    : [...ventasSel.value, id]
  aplicarSeleccion()
}
function aplicarSeleccion() {
  const sel = new Set(ventasSel.value)
  const elegidas = ventasElegibles.value.filter((v) => sel.has(v.id))
  totalVentas.value = elegidas.reduce((acc, v) => acc + v.total, 0)
  costoInsumos.value = elegidas.reduce((acc, v) => acc + v.costo, 0)
  recalcularDistribucion()
}
function limpiarSeleccion() {
  ventasSel.value = []
  recalcularDistribucion()
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
    estado.value = (l.estado as 'BORRADOR' | 'APROBADA' | 'PAGADA') ?? 'BORRADOR'
    observaciones.value = l.observaciones || ''
    distribucionLocal.value = l.distribucion.map((d) => ({ ...d }))
  } else {
    const nextNum = 1
    codigo.value = `LIQ-${new Date().getFullYear()}-${String(nextNum).padStart(2, '0')}`
    // El backend exige periodo de 1..20 chars: default corto YYYY-MM.
    periodo.value = new Date().toISOString().slice(0, 7)
    fechaCierre.value = new Date().toISOString().split('T')[0]
    totalVentas.value = totalVentas.value || 0
    costoInsumos.value = 7200000
    gastosOperativos.value = 1800000
    ventasSel.value = []
    estado.value = 'BORRADOR'
    observaciones.value = 'Liquidación de utilidades sujeta a revisión y visto bueno de las socias.'
    void cargarTotalesVentas()
    void cargarFondoEstatuto()
    recalcularDistribucion()
  }
}

watch(
  () => props.visible,
  (val) => {
    if (val) {
      void cargarPreview()
        .then(() => initForm())
        .catch(() => showToast('error', 'Error al cargar', 'No se pudo cargar la vista previa de la liquidación.'))
    }
  },
  { immediate: true },
)

watch([totalVentas, costoInsumos, gastosOperativos], () => {
  recalcularDistribucion()
})

async function guardar() {
  if (guardando.value) return
  if (!periodo.value.trim()) {
    showToast('warn', 'Campo requerido', 'Por favor indique el nombre o periodo de la liquidación.')
    return
  }
  // El backend exige periodo de 1..20 chars: se valida antes del POST.
  if (periodo.value.trim().length > 20) {
    showToast('warn', 'Periodo muy largo', 'El periodo admite máximo 20 caracteres (ej: 2026-09).')
    return
  }

  // Real API: server computes codigo + distribucion, only header totals sent
  // (con ventas elegidas el servidor recalcula todo del snapshot).
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
    ...(haySeleccion.value ? { venta_ids: [...ventasSel.value] } : {}),
  }
  guardando.value = true
  try {
    if (isEditing.value && props.liquidacionEditar) {
      // Editing not supported via API (only state transition in Finanzas).
      showToast('warn', 'Edición', 'La edición de liquidaciones existentes no está soportada por la API. Use cambio de estado para transiciones.')
      return
    }
    const creada = await finanzasApi.createLiquidacion(apiPayload)
    const cod = (creada as unknown as Record<string, unknown>).codigo as string
    showToast('success', 'Liquidación Creada', `Liquidación ${cod} registrada en BD.`)
    emit('guardada', creada)
    emit('update:visible', false)
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? 'Error al crear liquidación'
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
          <InputText v-model="periodo" class="w-full text-xs" placeholder="Ej: 2026-09 (máx. 20 caracteres)" maxlength="20" />
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
          <span v-if="haySeleccion" class="text-[11px] text-emerald-300 font-mono">
            {{ ventasSel.length }} venta(s) elegida(s) — totales del snapshot
          </span>
          <button
            v-if="haySeleccion"
            type="button"
            class="text-[11px] text-stone-400 hover:text-stone-200 underline"
            @click="limpiarSeleccion"
          >
            Limpiar y cargar a mano
          </button>
        </div>

        <!-- Ventas a liquidar (confirmed + sin liquidar) -->
        <div v-if="!isEditing" class="rounded-xl border border-stone-800 bg-stone-950/60 p-3 space-y-2">
          <div class="text-[11px] font-bold text-stone-300 uppercase tracking-wider">
            Ventas a liquidar (opcional — sin tildar se carga a mano)
          </div>
          <div v-if="!ventasElegibles.length" class="text-xs text-stone-500">
            No hay ventas confirmadas sin liquidar.
          </div>
          <div v-else class="max-h-40 overflow-y-auto space-y-1.5">
            <label
              v-for="v in ventasElegibles"
              :key="v.id"
              class="flex items-center gap-2 rounded-lg border border-stone-800 bg-stone-900/60 px-2.5 py-1.5 text-xs cursor-pointer hover:border-amber-500/40"
            >
              <input
                type="checkbox"
                :checked="ventasSel.includes(v.id)"
                class="accent-amber-500"
                @change="toggleVenta(v.id)"
              />
              <span class="font-mono font-bold text-amber-300">{{ v.codigo }}</span>
              <span class="text-stone-400">{{ v.fecha }}</span>
              <span class="text-stone-200 truncate">{{ v.cliente }}</span>
              <span class="font-mono text-stone-300 ml-auto">{{ formatCOP(v.total) }}</span>
            </label>
          </div>
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
              :min-fraction-digits="0"
              :max-fraction-digits="0"
              :disabled="haySeleccion"
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
              :min-fraction-digits="0"
              :max-fraction-digits="0"
              :disabled="haySeleccion"
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
              :min-fraction-digits="0"
              :max-fraction-digits="0"
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
            <span class="text-amber-300 text-[11px]">🏛️ Fondo Taller ({{ fondoPct }}%):</span>
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

        <div class="hidden overflow-x-auto sm:block">
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
                     :min-fraction-digits="0"
                     :max-fraction-digits="0"
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
        <!-- Mobile cards: same distribucionLocal with same editors. No horizontal scroll. -->
        <div class="space-y-3 p-3 sm:hidden max-w-full min-w-0">
          <div v-for="d in distribucionLocal" :key="d.socia_id" class="border border-stone-800 rounded-2xl p-4 space-y-2 min-w-0">
            <div class="flex items-start justify-between gap-2 min-w-0">
              <div class="min-w-0">
                <div class="font-bold text-sm text-stone-100">{{ d.nombre_socia }}</div>
                <div class="text-xs text-stone-500">{{ d.rol_socia }}</div>
              </div>
              <span class="font-mono font-bold text-sm text-amber-400 shrink-0">{{ d.porcentaje }}%</span>
            </div>
            <div class="flex items-center justify-between text-sm">
              <span class="text-xs uppercase tracking-wider text-stone-400">Cuota bruta</span>
              <span class="font-mono font-bold text-stone-200">{{ formatCOP(d.monto_bruto) }}</span>
            </div>
            <div class="flex items-center justify-between gap-2">
              <span class="text-xs uppercase tracking-wider text-stone-400">Anticipos</span>
              <InputNumber v-model="d.deduccion_anticipos" mode="currency" currency="COP" locale="es-CO" :min="0" :min-fraction-digits="0" :max-fraction-digits="0" class="w-36 text-sm font-mono text-rose-400" @update:model-value="d.monto_neto_pagar = Math.max(0, d.monto_bruto - d.deduccion_anticipos)" />
            </div>
            <div class="flex items-center justify-between text-sm">
              <span class="text-xs uppercase tracking-wider text-stone-400">Neto a transferir</span>
              <span class="font-mono font-bold text-emerald-400">{{ formatCOP(d.monto_neto_pagar) }}</span>
            </div>
            <Dropdown v-model="d.estado_pago" :options="[{ label: 'Pendiente', value: 'PENDIENTE' }, { label: 'Pagado', value: 'PAGADO' }, { label: 'Retenido', value: 'RETENIDO' }]" option-label="label" option-value="value" class="w-full text-sm" />
          </div>
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
          :loading="guardando"
          @click="guardar"
        />
      </div>
    </template>
  </Dialog>
</template>
