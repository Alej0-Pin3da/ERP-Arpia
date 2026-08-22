<script setup lang="ts">
import { computed } from 'vue'
import { useAtelierStore } from '@/stores/atelier'

const atelier = useAtelierStore()

const prendasVendidas = computed(() => atelier.prendas.filter((p) => p.vendida))

function formatCOP(v: number): string {
  return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(v)
}
</script>

<template>
  <div class="space-y-6">
    <div class="border-b border-stone-800 pb-4">
      <h1 class="text-2xl font-serif font-bold text-amber-300 tracking-wide">
        Registro de Ventas Realizadas
      </h1>
      <p class="text-xs text-stone-400 mt-1 font-mono">
        Historial de ventas de prendas de showroom y pedidos personalizados despachados.
      </p>
    </div>

    <div class="rounded-2xl border border-stone-800 bg-stone-900/40 p-6 space-y-4">
      <div v-if="prendasVendidas.length === 0" class="text-center py-12 text-stone-500 font-mono text-xs">
        No se han registrado ventas en el showroom en la sesión actual.
      </div>
      <div v-else class="overflow-x-auto">
        <table class="w-full text-xs text-left border-collapse">
          <thead>
            <tr class="border-b border-stone-800 text-stone-400 font-mono">
              <th class="py-2.5 px-3">Código</th>
              <th class="py-2.5 px-3">Prenda</th>
              <th class="py-2.5 px-3">Talla / Color</th>
              <th class="py-2.5 px-3">Fecha Venta</th>
              <th class="py-2.5 px-3 text-right">Total Facturado</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-stone-800/60 font-mono">
            <tr v-for="p in prendasVendidas" :key="p.id" class="hover:bg-stone-900/50">
              <td class="py-3 px-3 text-amber-400 font-bold">{{ p.codigo_etiqueta }}</td>
              <td class="py-3 px-3 font-serif font-semibold text-stone-200">{{ p.nombre_prenda }}</td>
              <td class="py-3 px-3 text-stone-400">{{ p.talla }} · {{ p.color }}</td>
              <td class="py-3 px-3 text-stone-400">{{ p.fecha_confeccion }}</td>
              <td class="py-3 px-3 text-right text-emerald-400 font-bold text-sm">
                {{ formatCOP(p.precio_venta_final || 0) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
