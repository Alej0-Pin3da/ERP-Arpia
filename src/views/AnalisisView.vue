<script setup lang="ts">
import { computed } from 'vue'
import { useAtelierStore } from '@/stores/atelier'

const atelier = useAtelierStore()

const metricas = computed(() => {
  const pedidosCompletados = atelier.pedidos.filter((p) => p.estado === 'entregado').length
  const pedidosEnProceso = atelier.pedidos.filter((p) => ['corte', 'confeccion', 'prueba'].includes(p.estado)).length
  const stockPrendas = atelier.prendas.filter((p) => !p.vendida).length
  const insumosAlertas = atelier.insumosCriticos.length

  return {
    pedidosCompletados,
    pedidosEnProceso,
    stockPrendas,
    insumosAlertas,
  }
})

function formatCOP(v: number): string {
  return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(v)
}
</script>

<template>
  <div class="space-y-6">
    <div class="border-b border-stone-800 pb-4">
      <h1 class="text-2xl font-serif font-bold text-amber-300 tracking-wide">
        Análisis de Rendimiento del Atelier
      </h1>
      <p class="text-xs text-stone-400 mt-1 font-mono">
        Métricas de productividad de costura, rotación de insumos y márgenes por tipo de prenda.
      </p>
    </div>

    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <div class="rounded-xl border border-stone-800 bg-stone-900/60 p-4">
        <div class="text-xs font-mono text-stone-400">Prendas en Confección Activa</div>
        <div class="text-2xl font-serif font-bold text-amber-400 mt-1">{{ metricas.pedidosEnProceso }}</div>
      </div>
      <div class="rounded-xl border border-stone-800 bg-stone-900/60 p-4">
        <div class="text-xs font-mono text-stone-400">Pedidos de Alta Costura Entregados</div>
        <div class="text-2xl font-serif font-bold text-emerald-400 mt-1">{{ metricas.pedidosCompletados }}</div>
      </div>
      <div class="rounded-xl border border-stone-800 bg-stone-900/60 p-4">
        <div class="text-xs font-mono text-stone-400">Prendas en Showroom</div>
        <div class="text-2xl font-serif font-bold text-stone-200 mt-1">{{ metricas.stockPrendas }}</div>
      </div>
      <div class="rounded-xl border border-stone-800 bg-stone-900/60 p-4">
        <div class="text-xs font-mono text-stone-400">Insumos con Stock Crítico</div>
        <div class="text-2xl font-serif font-bold text-red-400 mt-1">{{ metricas.insumosAlertas }}</div>
      </div>
    </div>

    <!-- Product Margins Analysis -->
    <div class="rounded-2xl border border-stone-800 bg-stone-900/40 p-6 space-y-4">
      <h2 class="text-base font-serif font-semibold text-stone-100 flex items-center gap-2">
        <i class="pi pi-chart-line text-amber-400" />
        Rentabilidad por Ficha Técnica / Receta BOM
      </h2>

      <div class="overflow-x-auto">
        <table class="w-full text-xs text-left border-collapse">
          <thead>
            <tr class="border-b border-stone-800 text-stone-400 font-mono">
              <th class="py-2.5 px-3">Prenda / Receta</th>
              <th class="py-2.5 px-3">Costo Insumos</th>
              <th class="py-2.5 px-3">Horas Confección</th>
              <th class="py-2.5 px-3">Precio Sugerido</th>
              <th class="py-2.5 px-3">Margen Bruto</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-stone-800/60 font-mono">
            <tr v-for="r in atelier.recetas" :key="r.id" class="hover:bg-stone-900/50">
              <td class="py-3 px-3 font-serif text-sm font-semibold text-stone-200">{{ r.nombre }}</td>
              <td class="py-3 px-3 text-stone-300">{{ formatCOP(r.costo_estimado_materiales) }}</td>
              <td class="py-3 px-3 text-stone-400">{{ r.tiempo_estimado_confeccion_horas }}h</td>
              <td class="py-3 px-3 text-amber-300 font-bold">{{ formatCOP(r.precio_venta_sugerido) }}</td>
              <td class="py-3 px-3 text-emerald-400 font-bold">
                {{ formatCOP(r.precio_venta_sugerido - r.costo_estimado_materiales) }}
                <span class="text-[10px] opacity-75">
                  ({{ Math.round(((r.precio_venta_sugerido - r.costo_estimado_materiales) / r.precio_venta_sugerido) * 100) }}%)
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
