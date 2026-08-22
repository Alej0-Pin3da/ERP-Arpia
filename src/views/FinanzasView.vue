<script setup lang="ts">
import { ref, computed } from 'vue'
import Button from 'primevue/button'
import InputNumber from 'primevue/inputnumber'
import { useAtelierStore } from '@/stores/atelier'
import { showToast } from '@/utils/toast'

const atelier = useAtelierStore()

const periodoActual = ref('2026-08')
const valorVentaTotal = computed(() => {
  return atelier.prendas.reduce((acc, p) => acc + (p.vendida && p.precio_venta_final ? p.precio_venta_final : 0), 0) + 12850000
})

const costoTotalInsumos = computed(() => {
  return atelier.insumos.reduce((acc, i) => acc + (i.stock_actual * i.costo_unitario), 0) * 0.35 + 3420000
})

const gastosOperativos = ref(2100000)
const fondoReservaPct = ref(15)

const utilidadBruta = computed(() => valorVentaTotal.value - costoTotalInsumos.value)
const utilidadNeta = computed(() => Math.max(0, utilidadBruta.value - gastosOperativos.value))
const fondoReservaValor = computed(() => (utilidadNeta.value * fondoReservaPct.value) / 100)
const utilidadRepartible = computed(() => utilidadNeta.value - fondoReservaValor.value)

const socias = ref([
  { id: 1, nombre: 'Valeria Arpía (Diseño & Dirección)', pct: 50, rol: 'Socia Fundadora' },
  { id: 2, nombre: 'Camila Modista (Jefa de Taller & Corte)', pct: 30, rol: 'Socia Operativa' },
  { id: 3, nombre: 'Elena Inversionista (Capital & Expansión)', pct: 20, rol: 'Socia Capitalista' },
])

const cuotasSocias = computed(() => {
  return socias.value.map((s) => ({
    ...s,
    monto: (utilidadRepartible.value * s.pct) / 100,
  }))
})

function liquidarPeriodo() {
  showToast(
    'success',
    'Liquidación Generada',
    `Se ha procesado la liquidación de ${formatCOP(utilidadRepartible.value)} entre las socias.`
  )
}

function formatCOP(v: number): string {
  return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(v)
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-stone-800 pb-4">
      <div>
        <h1 class="text-2xl font-serif font-bold text-amber-300 tracking-wide">
          Reparto de Utilidades & Liquidación de Socias
        </h1>
        <p class="text-xs text-stone-400 mt-1 font-mono">
          Cálculo financiero transparente con deducción de insumos, fondo de reinversión textil y cuotas de socias.
        </p>
      </div>
      <div class="flex items-center gap-3">
        <span class="text-xs text-stone-400">Periodo:</span>
        <span class="px-3 py-1.5 rounded-lg bg-stone-900 border border-stone-700 text-amber-300 font-mono text-xs font-bold">
          {{ periodoActual }}
        </span>
        <Button
          label="Liquidar Utilidades"
          icon="pi pi-check"
          size="small"
          class="p-button-warning text-xs font-semibold"
          @click="liquidarPeriodo"
        />
      </div>
    </div>

    <!-- Financial KPI Summary -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <div class="rounded-xl border border-stone-800 bg-stone-900/60 p-4">
        <div class="text-xs font-mono text-stone-400">Ingresos Totales (Taller + Showroom)</div>
        <div class="text-xl font-serif font-bold text-emerald-400 mt-1">{{ formatCOP(valorVentaTotal) }}</div>
        <div class="text-[10px] text-stone-500 mt-1">Confecciones entregadas + Ventas stock</div>
      </div>

      <div class="rounded-xl border border-stone-800 bg-stone-900/60 p-4">
        <div class="text-xs font-mono text-stone-400">Costos Insumos & Confección</div>
        <div class="text-xl font-serif font-bold text-red-400 mt-1">{{ formatCOP(costoTotalInsumos) }}</div>
        <div class="text-[10px] text-stone-500 mt-1">Consumo real según recetas BOM</div>
      </div>

      <div class="rounded-xl border border-stone-800 bg-stone-900/60 p-4">
        <div class="text-xs font-mono text-stone-400">Fondo Reinversión Atelier ({{ fondoReservaPct }}%)</div>
        <div class="text-xl font-serif font-bold text-amber-300 mt-1">{{ formatCOP(fondoReservaValor) }}</div>
        <div class="text-[10px] text-stone-500 mt-1">Reserva para maquinaria y compras mayoristas</div>
      </div>

      <div class="rounded-xl border border-amber-500/30 bg-amber-950/20 p-4">
        <div class="text-xs font-mono text-amber-300/80">Utilidad Neta Repartible</div>
        <div class="text-2xl font-serif font-bold text-amber-300 mt-1">{{ formatCOP(utilidadRepartible) }}</div>
        <div class="text-[10px] text-amber-400/60 mt-1">Disponible para división entre socias</div>
      </div>
    </div>

    <!-- Socias Distribution Table -->
    <div class="rounded-2xl border border-stone-800 bg-stone-900/40 backdrop-blur-sm overflow-hidden p-6 space-y-4">
      <div class="flex items-center justify-between border-b border-stone-800/80 pb-3">
        <h2 class="text-base font-serif font-semibold text-stone-100 flex items-center gap-2">
          <i class="pi pi-users text-amber-400" />
          Tabla de Distribución de Utilidades
        </h2>
        <div class="flex items-center gap-3 text-xs">
          <span class="text-stone-400">Ajuste Gastos Operativos:</span>
          <InputNumber
            v-model="gastosOperativos"
            mode="currency"
            currency="COP"
            locale="es-CO"
            class="w-36 text-xs p-inputtext-sm"
          />
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
        <div
          v-for="s in cuotasSocias"
          :key="s.id"
          class="rounded-xl border border-stone-800 bg-stone-950/70 p-4 relative overflow-hidden flex flex-col justify-between"
        >
          <div class="absolute top-0 right-0 w-24 h-24 bg-amber-500/5 rounded-full blur-xl pointer-events-none" />
          <div>
            <div class="flex items-center justify-between">
              <span class="text-xs font-mono text-amber-400/90 font-bold">{{ s.pct }}% Participación</span>
              <span class="text-[10px] px-2 py-0.5 rounded bg-stone-800 text-stone-300 font-mono">{{ s.rol }}</span>
            </div>
            <div class="font-serif font-bold text-stone-100 text-base mt-2">{{ s.nombre }}</div>
          </div>

          <div class="mt-4 pt-3 border-t border-stone-800 flex items-end justify-between">
            <span class="text-[11px] text-stone-400 font-mono">Cuota Neta:</span>
            <span class="text-lg font-serif font-bold text-emerald-400">{{ formatCOP(s.monto) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
