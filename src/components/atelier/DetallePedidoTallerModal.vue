<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'
import { showToast } from '@/utils/toast'
import {
  FASES_PRODUCCION,
  extractApiDetail,
  siguienteFase,
  updatePedidoProduccion,
} from '@/services/api/pedidos-produccion'

/** Minimal pedido shape this modal reads (REAL display object from the caller). */
export interface PedidoTallerDetalle {
  id: number
  codigo: string
  cliente_nombre: string
  prenda_nombre: string
  estado: string
  // Workshop phase + lot data (backend migración 0030; null-safe for legacy rows).
  fase?: string | null
  cantidad?: number | null
  cantidad_producida?: number | null
  costo_unitario_snapshot?: number | string | null
  precio_venta?: number
}

const props = defineProps<{
  visible: boolean
  pedido: PedidoTallerDetalle | null
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
  (e: 'fase-avanzada', fase: string): void
}>()

// REAL-only: no hay endpoint de tiempos por fase ni de pruebas de calce.
// Se renderizan estados vacíos hasta que el backend los provea.
const fasesTaller = ref<Array<{ id: number; fase: string; modista: string; estimadoMin: number; realMin: number; completado: boolean }>>([])

const pruebasCalce = ref<Array<{ id: number; fecha: string; tipo: string; estado: string; notas: string }>>([])

const anticipoPagado = ref<boolean | null>(null)

const totalHorasTaller = computed(() => '—')

// Fase actual: prop del backend, con override local tras un avance exitoso
// (el objeto del padre es un snapshot y puede tardar en recargarse).
const faseLocal = ref<string | null>(null)
const errorAvance = ref<string | null>(null)
const avanzando = ref(false)

watch(
  () => props.pedido,
  () => {
    faseLocal.value = null
    errorAvance.value = null
  },
)

const faseActual = computed(() => faseLocal.value ?? props.pedido?.fase ?? null)
const faseSiguiente = computed(() => siguienteFase(faseActual.value))
const tieneCostoSnapshot = computed(
  () =>
    props.pedido?.costo_unitario_snapshot !== null &&
    props.pedido?.costo_unitario_snapshot !== undefined,
)

async function avanzarFase() {
  if (!props.pedido || avanzando.value) return
  const next = faseSiguiente.value
  if (!next) return
  avanzando.value = true
  errorAvance.value = null
  try {
    const updated = await updatePedidoProduccion(props.pedido.id, { fase: next })
    faseLocal.value = updated.fase
    emit('fase-avanzada', updated.fase)
    showToast('success', 'Fase actualizada', `Orden ${props.pedido.codigo} avanzada a ${next.toUpperCase()}.`)
  } catch (e: unknown) {
    // 400/422/409 del backend, verbatim (incluye el detalle por-insumo del 409).
    const detail = extractApiDetail(e)
    errorAvance.value = detail
    showToast('error', 'No se pudo avanzar', detail)
  } finally {
    avanzando.value = false
  }
}

function formatCOP(val: number) {
  return `$${Math.round(val).toLocaleString('es-CO')}`
}

function generarReciboAnticipo() {
  showToast(
    'success',
    'Recibo de Caja Generado',
    `Comprobante de anticipo por ${formatCOP((props.pedido?.precio_venta || 0) * 0.5)} listo para enviar a la clienta.`
  )
}
</script>

<template>
  <Dialog
    :visible="props.visible"
    modal
    :header="`Ficha de Taller & Tiempos: ${props.pedido?.codigo || 'Pedido'} - ${props.pedido?.prenda_nombre}`"
    :style="{ width: '840px', maxWidth: '95vw' }"
    class="p-dialog-arpia"
    @update:visible="emit('update:visible', $event)"
  >
    <div class="space-y-6 pt-1">
      <!-- Order Summary Card -->
      <div class="rounded-2xl border border-stone-800 bg-stone-950/70 p-4 flex flex-col md:flex-row items-center justify-between gap-4">
        <div class="space-y-1">
          <div class="flex items-center gap-2">
            <span class="text-sm font-bold text-stone-100">{{ props.pedido?.cliente_nombre }}</span>
            <span class="text-xs font-mono text-amber-400 font-bold">({{ props.pedido?.codigo }})</span>
          </div>
          <div class="text-xs text-stone-400 font-mono">
            Prenda: <strong class="text-stone-200">{{ props.pedido?.prenda_nombre }}</strong> · Estado: <span class="text-amber-300 font-bold">{{ props.pedido?.estado }}</span>
          </div>
        </div>

        <div class="flex items-center gap-4 text-xs font-mono">
          <div class="bg-stone-900 border border-stone-800 p-2 rounded-lg text-center">
            <span class="text-[10px] text-stone-400 block">Horas Acumuladas</span>
            <span class="text-amber-300 font-bold text-sm">{{ totalHorasTaller }}</span>
          </div>
          <div class="bg-stone-900 border border-stone-800 p-2 rounded-lg text-center">
            <span class="text-[10px] text-stone-400 block">Precio Acordado</span>
            <span class="text-emerald-400 font-bold text-sm">{{ formatCOP(props.pedido?.precio_venta || 0) }}</span>
          </div>
        </div>
      </div>

      <!-- Anticipo: solo con datos reales de venta/anticipo. Sin endpoint, se oculta con nota. -->
      <div v-if="anticipoPagado === null" class="rounded-xl border border-stone-800 bg-stone-900/60 p-4 text-xs text-stone-400 font-mono">
        Sin registro — pendiente: el control de anticipos requiere datos reales de venta/anticipo.
      </div>

      <!-- Fase & lote (datos REALES del backend, migración 0030) -->
      <div class="space-y-3">
        <div class="text-xs font-mono font-bold text-stone-300 uppercase">
          Fase de confección & avance de lote
        </div>
        <div class="rounded-xl border border-stone-800 bg-stone-950/60 p-4 space-y-3">
          <!-- 5-phase stepper -->
          <div class="flex items-center gap-1">
            <template v-for="(f, i) in FASES_PRODUCCION" :key="f">
              <div class="flex-1 text-center">
                <div
                  class="mx-auto w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold border"
                  :class="faseActual && FASES_PRODUCCION.indexOf(faseActual) >= i
                    ? 'bg-amber-500 text-stone-950 border-amber-500'
                    : 'bg-stone-900 text-stone-500 border-stone-700'"
                >
                  {{ i + 1 }}
                </div>
                <div
                  class="text-[9px] font-mono uppercase mt-1"
                  :class="faseActual === f ? 'text-amber-300 font-bold' : 'text-stone-500'"
                >
                  {{ f }}
                </div>
              </div>
              <div v-if="i < FASES_PRODUCCION.length - 1" class="h-px flex-1 bg-stone-800 -mt-4" />
            </template>
          </div>

          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs font-mono">
            <div class="text-stone-400">
              Fase actual: <strong class="text-amber-300">{{ (faseActual || '—').toUpperCase() }}</strong>
              <span class="text-stone-500">·</span>
              Lote: <strong class="text-stone-200">{{ props.pedido?.cantidad_producida ?? 0 }}/{{ props.pedido?.cantidad ?? '—' }} uds</strong>
              <template v-if="tieneCostoSnapshot">
                <span class="text-stone-500">·</span>
                Costo unit.: <strong class="text-emerald-400">{{ formatCOP(Number(props.pedido?.costo_unitario_snapshot)) }}</strong>
              </template>
            </div>
            <Button
              v-if="faseSiguiente"
              label="Avanzar fase"
              icon="pi pi-arrow-right"
              size="small"
              class="p-button-warning text-xs font-semibold"
              :loading="avanzando"
              :disabled="avanzando"
              @click="avanzarFase"
            />
            <span v-else class="text-[11px] text-stone-500">Lote en fase final.</span>
          </div>

          <!-- Backend error verbatim (400 salto/retroceso, 422 fase inválida, 409 faltante con detalle por-insumo) -->
          <div v-if="errorAvance" class="rounded-lg border border-red-500/40 bg-red-950/40 p-3 text-[11px] text-red-300 font-mono whitespace-pre-wrap">
            {{ errorAvance }}
          </div>
        </div>
      </div>

      <!-- Workshop Phases & Timing Log -->
      <div class="space-y-3">
        <div class="text-xs font-mono font-bold text-stone-300 uppercase">
          Tiempos Reales por Fase de Modistería
        </div>
        <div class="border border-stone-800 rounded-xl bg-stone-950/60 p-6 text-center text-xs text-stone-400 font-mono">
          Sin registro de tiempos por fase — pendiente.
        </div>
      </div>

      <!-- Fitting Sessions (Pruebas de Calce) -->
      <div class="space-y-3">
        <div class="text-xs font-mono font-bold text-stone-300 uppercase">
          Historial de Pruebas de Calce en Atelier
        </div>
        <div class="border border-stone-800 rounded-xl bg-stone-900/40 p-6 text-center text-xs text-stone-400 font-mono">
          Sin pruebas de calce registradas — pendiente.
        </div>
      </div>
    </div>

    <template #footer>
      <div class="flex items-center justify-end w-full pt-3 border-t border-stone-800">
        <Button
          label="Cerrar Ficha"
          icon="pi pi-check"
          size="small"
          class="p-button-warning text-xs font-semibold"
          @click="emit('update:visible', false)"
        />
      </div>
    </template>
  </Dialog>
</template>
