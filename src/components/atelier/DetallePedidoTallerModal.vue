<script setup lang="ts">
import { ref, computed } from 'vue'
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'
import { type PedidoProduccion } from '@/stores/atelier'
import { showToast } from '@/utils/toast'

const props = defineProps<{
  visible: boolean
  pedido: PedidoProduccion | null
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
}>()

// Phased timers / modiste time logging
const fasesTaller = ref([
  { id: 1, fase: 'Patronaje & Escala', modista: 'Camila Modista', estimadoMin: 45, realMin: 50, completado: true },
  { id: 2, fase: 'Corte Anatómico & Fusing', modista: 'Camila Modista', estimadoMin: 35, realMin: 30, completado: true },
  { id: 3, fase: 'Canales de Varillas & Envarillado', modista: 'Valeria Arpía', estimadoMin: 60, realMin: 55, completado: false },
  { id: 4, fase: 'Ojales & Puntas de Acero', modista: 'Camila Modista', estimadoMin: 40, realMin: 0, completado: false },
  { id: 5, fase: 'Acabados a Mano & Sesgo Francés', modista: 'Valeria Arpía', estimadoMin: 50, realMin: 0, completado: false },
])

const pruebasCalce = ref([
  { id: 1, fecha: '2026-08-18', tipo: 'Toile de Prueba (Retor)', estado: 'Aprobada', notas: 'Cintura perfecta, reducir 1cm en sisa axilar.' },
  { id: 2, fecha: '2026-08-23', tipo: '1ª Prueba en Seda & Varillas', estado: 'Pendiente', notas: 'Verificar tensión de cierre de espalda.' },
])

const anticipoPagado = ref(true)

const totalHorasTaller = computed(() => {
  const mins = fasesTaller.value.reduce((acc, f) => acc + (f.realMin || f.estimadoMin), 0)
  return (mins / 60).toFixed(1)
})

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
            <span class="text-amber-300 font-bold text-sm">{{ totalHorasTaller }}h</span>
          </div>
          <div class="bg-stone-900 border border-stone-800 p-2 rounded-lg text-center">
            <span class="text-[10px] text-stone-400 block">Precio Acordado</span>
            <span class="text-emerald-400 font-bold text-sm">{{ formatCOP(props.pedido?.precio_venta || 0) }}</span>
          </div>
        </div>
      </div>

      <!-- Financial Split: 50% Anticipo / 50% Saldo -->
      <div class="rounded-xl border border-amber-500/20 bg-stone-900/60 p-4 space-y-3">
        <div class="flex items-center justify-between">
          <div class="text-xs font-mono font-bold text-amber-400 uppercase">
            Control de Anticipos & Saldo Contra Entrega (50% / 50%)
          </div>
          <Button
            label="Recibo de Anticipo"
            icon="pi pi-file-pdf"
            size="small"
            outlined
            class="text-xs"
            @click="generarReciboAnticipo"
          />
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs font-mono">
          <div
            class="p-3 rounded-lg border flex items-center justify-between cursor-pointer transition"
            :class="anticipoPagado ? 'border-emerald-500/30 bg-emerald-950/20' : 'border-stone-800 bg-stone-900/80'"
            @click="anticipoPagado = !anticipoPagado"
          >
            <div>
              <span class="text-[10px] uppercase font-bold block" :class="anticipoPagado ? 'text-emerald-300' : 'text-stone-400'">
                Anticipo 50% (Reserva de Taller)
              </span>
              <span class="text-base font-bold" :class="anticipoPagado ? 'text-emerald-400' : 'text-stone-300'">
                {{ formatCOP((props.pedido?.precio_venta || 0) * 0.5) }}
              </span>
            </div>
            <span
              class="px-2 py-0.5 rounded text-[10px] font-bold"
              :class="anticipoPagado ? 'bg-emerald-900/80 text-emerald-300' : 'bg-stone-800 text-stone-400'"
            >
              {{ anticipoPagado ? '✓ Pagado' : 'Pendiente' }}
            </span>
          </div>

          <div class="p-3 rounded-lg border border-stone-800 bg-stone-900/80 flex items-center justify-between">
            <div>
              <span class="text-[10px] text-stone-400 uppercase block">Saldo Pendiente 50% (Contra Entrega)</span>
              <span class="text-base font-bold text-amber-300">{{ formatCOP((props.pedido?.precio_venta || 0) * 0.5) }}</span>
            </div>
            <span class="px-2 py-0.5 rounded bg-amber-950/80 text-amber-300 border border-amber-500/30 text-[10px] font-bold">
              Pendiente
            </span>
          </div>
        </div>
      </div>

      <!-- Workshop Phases & Timing Log -->
      <div class="space-y-3">
        <div class="text-xs font-mono font-bold text-stone-300 uppercase">
          Tiempos Reales por Fase de Modistería
        </div>
        <div class="overflow-x-auto border border-stone-800 rounded-xl bg-stone-950/60">
          <table class="w-full text-xs text-left border-collapse">
            <thead>
              <tr class="border-b border-stone-800 bg-stone-900/80 text-stone-400 font-mono text-[11px]">
                <th class="py-2.5 px-3">Fase de Confección</th>
                <th class="py-2.5 px-3">Modista / Especialista</th>
                <th class="py-2.5 px-3">Tiempo Estimado</th>
                <th class="py-2.5 px-3">Tiempo Real</th>
                <th class="py-2.5 px-3 text-right">Estado</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-stone-800/60 font-mono">
              <tr v-for="f in fasesTaller" :key="f.id" class="hover:bg-stone-900/40">
                <td class="py-2.5 px-3 font-sans font-medium text-stone-200">{{ f.fase }}</td>
                <td class="py-2.5 px-3 text-stone-400">{{ f.modista }}</td>
                <td class="py-2.5 px-3 text-stone-400">{{ f.estimadoMin }} min</td>
                <td class="py-2.5 px-3 font-bold text-amber-300">{{ f.realMin > 0 ? `${f.realMin} min` : '-' }}</td>
                <td class="py-2.5 px-3 text-right">
                  <span
                    class="px-2 py-0.5 rounded text-[10px] font-bold"
                    :class="f.completado ? 'bg-emerald-950/80 text-emerald-300 border border-emerald-500/30' : 'bg-stone-900 text-stone-400 border border-stone-800'"
                  >
                    {{ f.completado ? 'Completado' : 'En Curso' }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Fitting Sessions (Pruebas de Calce) -->
      <div class="space-y-3">
        <div class="text-xs font-mono font-bold text-stone-300 uppercase">
          Historial de Pruebas de Calce en Atelier
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div
            v-for="p in pruebasCalce"
            :key="p.id"
            class="p-3 rounded-xl border border-stone-800 bg-stone-900/40 space-y-1.5"
          >
            <div class="flex items-center justify-between text-xs font-mono">
              <span class="font-bold text-stone-200">{{ p.tipo }}</span>
              <span class="text-[10px] px-2 py-0.5 rounded bg-stone-800 text-amber-300">{{ p.fecha }}</span>
            </div>
            <p class="text-xs text-stone-400 m-0">{{ p.notas }}</p>
          </div>
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
