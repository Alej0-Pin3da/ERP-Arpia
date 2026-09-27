<script setup lang="ts">
import { ref, computed } from 'vue'
import InputNumber from 'primevue/inputnumber'
import Slider from 'primevue/slider'
import { formatCOP } from './types'

const precioPromedioCorse = ref(450000)
const costoInsumosPromedio = ref(130000)
const horasManoObraPromedio = ref(6)
const costoHoraTaller = ref(15000)
const gastosOperativosSimulator = ref(2100000)
const prendasMetaSimuladas = ref(15)

const margenContribucionUnitario = computed(() => {
  const costoTotalUnitario = costoInsumosPromedio.value + horasManoObraPromedio.value * costoHoraTaller.value
  return Math.max(1, precioPromedioCorse.value - costoTotalUnitario)
})

const puntoEquilibrioUnidades = computed(() => {
  return Math.ceil(gastosOperativosSimulator.value / margenContribucionUnitario.value)
})

const utilidadSimulada = computed(() => {
  const ingresoSim = prendasMetaSimuladas.value * margenContribucionUnitario.value
  return Math.max(0, ingresoSim - gastosOperativosSimulator.value)
})
</script>

<template>
  <div class="rounded-2xl border border-amber-500/20 bg-stone-900/60 p-6 space-y-5">
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-stone-800 pb-3">
      <div>
        <h2 class="text-base font-serif font-semibold text-stone-100 flex items-center gap-2 m-0">
          <i class="pi pi-chart-line text-amber-400" />
          Simulador de Rentabilidad & Punto de Equilibrio Textil
        </h2>
        <p class="text-xs text-stone-400 mt-0.5 m-0 font-mono">
          Proyección de unidades mínimas para cubrir costos fijos del taller y rentabilidad esperada por socias.
        </p>
      </div>
      <div class="px-3 py-1 rounded-lg bg-stone-950 border border-amber-500/30 text-amber-300 font-mono text-xs font-bold">
        Punto de Equilibrio: {{ puntoEquilibrioUnidades }} Corsets / Mes
      </div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-4 gap-4 text-xs font-mono">
      <div class="space-y-1">
        <label class="text-stone-400 block text-[11px]">PVP Promedio Corset</label>
        <InputNumber
          v-model="precioPromedioCorse"
          mode="currency"
          currency="COP"
          locale="es-CO"
          :min-fraction-digits="0"
          :max-fraction-digits="0"
          class="w-full text-xs"
        />
      </div>

      <div class="space-y-1">
        <label class="text-stone-400 block text-[11px]">Costo Insumos Promedio</label>
        <InputNumber
          v-model="costoInsumosPromedio"
          mode="currency"
          currency="COP"
          locale="es-CO"
          :min-fraction-digits="0"
          :max-fraction-digits="2"
          class="w-full text-xs"
        />
      </div>

      <div class="space-y-1">
        <label class="text-stone-400 block text-[11px]">Horas Confección Promedio</label>
        <InputNumber
          v-model="horasManoObraPromedio"
          mode="decimal"
          locale="es-CO"
          :min="1"
          :max="30"
          :step="0.5"
          :min-fraction-digits="0"
          :max-fraction-digits="1"
          suffix=" horas"
          class="w-full text-xs"
        />
      </div>

      <div class="space-y-1">
        <label class="text-stone-400 block text-[11px]">Costo Hora Taller</label>
        <InputNumber
          v-model="costoHoraTaller"
          mode="currency"
          currency="COP"
          locale="es-CO"
          :min-fraction-digits="0"
          :max-fraction-digits="0"
          class="w-full text-xs"
        />
      </div>
    </div>

    <!-- Interactive Goal Slider & Projected Profit -->
    <div class="p-4 rounded-xl bg-stone-950/80 border border-stone-800 space-y-3">
      <div class="flex items-center justify-between text-xs font-mono">
        <span class="text-stone-300">Meta Mensual de Confección Simulada:</span>
        <span class="text-amber-300 font-bold text-sm">{{ prendasMetaSimuladas }} prendas</span>
      </div>
      <Slider v-model="prendasMetaSimuladas" :min="1" :max="50" class="w-full" />

      <div class="grid grid-cols-1 sm:grid-cols-4 gap-3 pt-2 font-mono text-xs">
        <div class="p-2.5 rounded-lg bg-stone-900/60 border border-stone-800">
          <span class="text-stone-400 block text-[10px]">Margen Unitario:</span>
          <span class="text-emerald-400 font-bold text-sm">{{ formatCOP(margenContribucionUnitario) }}</span>
        </div>
        <div class="p-2.5 rounded-lg bg-stone-900/60 border border-stone-800">
          <span class="text-stone-400 block text-[10px]">Costos Fijos Taller:</span>
          <span class="text-stone-200 font-bold text-sm">{{ formatCOP(gastosOperativosSimulator) }}</span>
        </div>
        <div class="p-2.5 rounded-lg bg-amber-950/40 border border-amber-500/30">
          <span class="text-amber-300 block text-[10px]">Fondo Taller (estimado):</span>
          <span class="text-amber-300 font-bold text-sm">{{ formatCOP(Math.round(utilidadSimulada * 0.4)) }}</span>
        </div>
        <div class="p-2.5 rounded-lg bg-emerald-950/40 border border-emerald-500/30">
          <span class="text-emerald-300 block text-[10px]">Cuota por socia (estimado):</span>
          <span class="text-emerald-300 font-bold text-sm">{{ formatCOP(Math.round(utilidadSimulada * 0.3)) }} c/u</span>
        </div>
      </div>
    </div>
  </div>
</template>
