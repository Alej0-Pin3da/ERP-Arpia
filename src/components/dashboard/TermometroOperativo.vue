<script setup lang="ts">
import { ref, onMounted } from 'vue'
import ProgressBar from 'primevue/progressbar'
import { getTermometro, type TermometroRead } from '@/services/api/punto-equilibrio'

const datos = ref<TermometroRead | null>(null)
const cargando = ref(false)
const fallo = ref(false)

function num(v: number | string | null | undefined): number {
  const n = Number(v ?? 0)
  return Number.isFinite(n) ? n : 0
}

function formatCOP(v: number | string | null | undefined): string {
  return `$${Math.round(num(v)).toLocaleString('es-CO')}`
}

async function cargar(): Promise<void> {
  cargando.value = true
  fallo.value = false
  try {
    datos.value = await getTermometro()
  } catch {
    datos.value = null
    fallo.value = true
  } finally {
    cargando.value = false
  }
}

onMounted(() => {
  void cargar()
})
</script>

<template>
  <div class="bg-stone-900/80 border border-stone-800 rounded-2xl p-5 shadow-lg space-y-3">
    <div class="flex items-center justify-between border-b border-stone-800/80 pb-3">
      <div class="text-xs font-bold uppercase tracking-wider text-amber-400">Termómetro Operativo del Mes</div>
      <div v-if="datos" class="text-[11px] font-mono text-stone-500">{{ datos.periodo }}</div>
    </div>

    <div v-if="cargando" class="text-xs text-stone-500">Midiendo el mes...</div>
    <div v-else-if="fallo || !datos" class="text-xs text-stone-500">No se pudo medir el mes; revisá la conexión.</div>
    <div v-else-if="datos.estado === 'sin_datos'" class="text-xs text-stone-400">Sin ventas registradas este mes todavía.</div>

    <div v-else-if="datos.estado === 'sin_configurar'" class="space-y-2">
      <div class="flex items-center justify-between text-xs">
        <span class="text-stone-400">Ventas netas <strong class="font-mono text-stone-100">{{ formatCOP(datos.ventas_netas) }}</strong></span>
        <span class="text-stone-400">Margen <strong class="font-mono text-stone-100">{{ num(datos.margen_pct) }}%</strong></span>
      </div>
      <p class="text-[11px] text-amber-300 m-0">Cargá los costos fijos mensuales en Maestros → Costeo para ver la meta.</p>
    </div>

    <div v-else-if="datos.estado === 'alerta'" class="rounded-xl border border-red-500/40 bg-red-500/10 p-4">
      <p class="text-xs font-bold text-red-300 m-0">Alerta Crítica: El margen operativo promedio del mes es negativo o nulo. Revisa urgentemente los costos o precios.</p>
      <p class="text-[11px] text-stone-400 m-0 mt-2">Ventas netas {{ formatCOP(datos.ventas_netas) }} · Margen {{ num(datos.margen_pct) }}%</p>
    </div>

    <div v-else class="space-y-2">
      <div class="flex items-center justify-between text-xs">
        <span class="text-stone-400">Ventas <strong class="font-mono text-stone-100">{{ formatCOP(datos.ventas_netas) }}</strong></span>
        <span class="text-stone-400">Meta <strong class="font-mono text-stone-100">{{ formatCOP(datos.meta_ventas) }}</strong></span>
      </div>
      <ProgressBar :value="datos.estado === 'superada' ? 100 : num(datos.avance_pct)" :show-value="false" class="h-3" />
      <div v-if="datos.estado === 'en_camino'" class="text-sm font-bold text-amber-300">Faltan {{ formatCOP(datos.faltante) }} en ventas para ser rentables este mes</div>
      <div v-else class="text-sm font-bold text-emerald-300">Utilidad Extra: +{{ formatCOP(datos.utilidad_extra) }}</div>
    </div>
  </div>
</template>
