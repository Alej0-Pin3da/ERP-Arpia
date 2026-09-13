<script setup lang="ts">
import { ref, computed } from 'vue'
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'
import { showToast } from '@/utils/toast'

/** Minimal pedido shape this modal reads (REAL display object from the caller). */
export interface PedidoTallerDetalle {
  codigo: string
  cliente_nombre: string
  prenda_nombre: string
  estado: string
  precio_venta?: number
}

const props = defineProps<{
  visible: boolean
  pedido: PedidoTallerDetalle | null
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
}>()

// REAL-only: no hay endpoint de tiempos por fase ni de pruebas de calce.
// Se renderizan estados vacíos hasta que el backend los provea.
const fasesTaller = ref<Array<{ id: number; fase: string; modista: string; estimadoMin: number; realMin: number; completado: boolean }>>([])

const pruebasCalce = ref<Array<{ id: number; fecha: string; tipo: string; estado: string; notas: string }>>([])

const anticipoPagado = ref<boolean | null>(null)

const totalHorasTaller = computed(() => '—')

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
