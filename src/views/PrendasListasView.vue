<script setup lang="ts">
import { ref, computed } from 'vue'
import Button from 'primevue/button'
import InputText from 'primevue/inputText'
import { useAtelierStore } from '@/stores/atelier'
import { showToast } from '@/utils/toast'

const atelier = useAtelierStore()
const search = ref('')

const prendasFiltradas = computed(() => {
  return atelier.prendasListas.filter((p) => {
    const q = search.value.trim().toLowerCase()
    return (
      !q ||
      p.nombre.toLowerCase().includes(q) ||
      p.codigo.toLowerCase().includes(q) ||
      p.categoria.toLowerCase().includes(q)
    )
  })
})

function formatCOP(val: number) {
  return `$${Math.round(val).toLocaleString('es-CO')}`
}

function ajustarStock(productoId: number, varianteId: number, delta: number) {
  atelier.ajustarStockPrenda(productoId, varianteId, delta)
}

function ingresarPrendaModal() {
  showToast('info', 'Ingreso de Prendas', 'Selecciona el modelo para registrar unidades confeccionadas al perchero.')
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header Banner -->
    <div class="bg-gradient-to-r from-stone-900 via-stone-900/90 to-stone-950 border border-amber-500/20 rounded-2xl p-5 sm:p-6 shadow-xl flex flex-col lg:flex-row lg:items-center justify-between gap-4">
      <div class="space-y-1.5">
        <div class="flex items-center gap-2.5 flex-wrap">
          <h1 class="text-xl sm:text-2xl font-bold font-serif tracking-wide text-stone-100 m-0">
            Inventario de Productos Confeccionados
          </h1>
          <span class="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-amber-950/80 text-amber-300 border border-amber-500/30 uppercase tracking-wider">
            {{ atelier.prendasStockFisico }} Prendas en Stock
          </span>
        </div>
        <p class="text-xs sm:text-sm text-stone-400 m-0 max-w-2xl">
          Prendas y accesorios terminados en showroom/perchero listos para entrega directa o venta.
        </p>
      </div>

      <div class="flex flex-wrap items-center gap-2">
        <Button
          label="Ingresar Prenda Confeccionada"
          icon="pi pi-plus"
          size="small"
          class="p-button-warning text-xs font-semibold"
          @click="ingresarPrendaModal"
        />
      </div>
    </div>

    <!-- 4 KPI Summary Cards -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <div class="bg-stone-900/80 border border-stone-800 rounded-2xl p-4 shadow-md">
        <div class="text-xs text-stone-400 font-bold uppercase tracking-wider">Prendas Físicas en Perchero</div>
        <div class="text-2xl font-extrabold text-stone-100 mt-2 font-mono">
          {{ atelier.prendasStockFisico }} unidades
        </div>
        <div class="text-[11px] text-stone-400 mt-1">Existencia real en taller</div>
      </div>

      <div class="bg-stone-900/80 border border-stone-800 rounded-2xl p-4 shadow-md">
        <div class="text-xs text-stone-400 font-bold uppercase tracking-wider">Stock Disponible para Venta</div>
        <div class="text-2xl font-extrabold text-emerald-400 mt-2 font-mono">
          {{ atelier.prendasStockDisponible }} unidades
        </div>
        <div class="text-[11px] text-stone-400 mt-1">Listos para despacho inmediato</div>
      </div>

      <div class="bg-stone-900/80 border border-stone-800 rounded-2xl p-4 shadow-md">
        <div class="text-xs text-stone-400 font-bold uppercase tracking-wider">Prendas Reservadas en Pedidos</div>
        <div class="text-2xl font-extrabold text-amber-400 mt-2 font-mono">
          {{ atelier.prendasStockFisico - atelier.prendasStockDisponible }} unidades
        </div>
        <div class="text-[11px] text-stone-400 mt-1">Con abono o reserva previa</div>
      </div>

      <div class="bg-stone-900/80 border border-stone-800 rounded-2xl p-4 shadow-md">
        <div class="text-xs text-stone-400 font-bold uppercase tracking-wider">Valorización a PVP</div>
        <div class="text-2xl font-extrabold text-amber-300 mt-2 font-mono">
          {{ formatCOP(atelier.valorizacionPVP) }}
        </div>
        <div class="text-[11px] text-stone-400 mt-1">Total mercancía a precio venta</div>
      </div>
    </div>

    <!-- Search Input -->
    <div class="w-full md:w-96">
      <span class="p-input-icon-left w-full">
        <InputText
          v-model="search"
          placeholder="Buscar prendas por nombre o código..."
          class="w-full text-xs"
        />
      </span>
    </div>

    <!-- Garment Cards List with Variant Sub-Tables -->
    <div class="space-y-4">
      <div
        v-for="p in prendasFiltradas"
        :key="p.id"
        class="bg-stone-900/80 border border-stone-800 rounded-2xl overflow-hidden shadow-lg hover:border-stone-700 transition"
      >
        <!-- Card Top Bar -->
        <div class="p-4 bg-stone-950/70 border-b border-stone-800 flex flex-col md:flex-row md:items-center justify-between gap-3">
          <div class="flex items-center gap-3">
            <div class="w-9 h-9 rounded-xl bg-amber-950/60 border border-amber-500/30 flex items-center justify-center text-amber-400 text-base flex-shrink-0">
              👗
            </div>
            <div>
              <div class="flex items-center gap-2">
                <h3 class="text-sm font-bold text-stone-100 m-0">{{ p.nombre }}</h3>
                <span class="font-mono text-xs text-amber-400 font-semibold">({{ p.codigo }})</span>
              </div>
              <span class="text-xs text-stone-400">{{ p.categoria }}</span>
            </div>
          </div>

          <div class="flex flex-wrap items-center gap-4 text-xs font-mono">
            <div>
              <span class="text-stone-400 font-sans">Costo Base: </span>
              <strong class="text-stone-200">{{ formatCOP(p.costo_base) }}</strong>
            </div>
            <div>
              <span class="text-stone-400 font-sans">Precio Venta: </span>
              <strong class="text-amber-300 font-bold">{{ formatCOP(p.precio_venta) }}</strong>
            </div>
            <div class="px-2 py-0.5 rounded bg-stone-900 border border-stone-800">
              <span class="text-stone-400 font-sans">Físico: </span>
              <strong class="text-stone-100">{{ p.fisico_total }}</strong>
            </div>
            <div class="px-2 py-0.5 rounded bg-emerald-950/60 border border-emerald-500/30 text-emerald-300">
              <span class="font-sans">Disponible: </span>
              <strong class="font-bold">{{ p.disponible_total }}</strong>
            </div>
          </div>
        </div>

        <!-- Variants Sub-Table -->
        <div class="overflow-x-auto">
          <table class="w-full text-left text-xs border-collapse">
            <thead>
              <tr class="border-b border-stone-800/80 text-stone-400 bg-stone-900/40 uppercase tracking-wider font-semibold">
                <th class="py-2.5 px-4">Talla</th>
                <th class="py-2.5 px-4">Color / Variante</th>
                <th class="py-2.5 px-4">SKU</th>
                <th class="py-2.5 px-4 text-center">Stock Físico</th>
                <th class="py-2.5 px-4 text-center">Reservado</th>
                <th class="py-2.5 px-4 text-center">Disponible</th>
                <th class="py-2.5 px-4 text-right">Ajuste de Stock</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-stone-800/50 text-stone-200 font-mono">
              <tr v-for="v in p.variantes" :key="v.id" class="hover:bg-stone-800/30">
                <td class="py-2.5 px-4 font-bold text-amber-300 font-sans">{{ v.talla }}</td>
                <td class="py-2.5 px-4 font-sans text-stone-300">{{ v.color }}</td>
                <td class="py-2.5 px-4 text-stone-400">{{ v.sku }}</td>
                <td class="py-2.5 px-4 text-center font-bold text-stone-100">{{ v.stock_fisico }}</td>
                <td class="py-2.5 px-4 text-center text-amber-400">{{ v.reservado }}</td>
                <td class="py-2.5 px-4 text-center font-bold text-emerald-400">{{ v.disponible }}</td>
                <td class="py-2.5 px-4 text-right font-sans">
                  <div class="inline-flex items-center bg-stone-950 border border-stone-800 rounded-lg p-0.5">
                    <button
                      type="button"
                      class="px-2 py-0.5 text-stone-400 hover:text-white hover:bg-stone-800 rounded text-xs transition"
                      @click="ajustarStock(p.id, v.id, -1)"
                    >
                      -1
                    </button>
                    <button
                      type="button"
                      class="px-2 py-0.5 text-amber-400 hover:text-amber-300 hover:bg-stone-800 rounded text-xs font-bold transition"
                      @click="ajustarStock(p.id, v.id, 1)"
                    >
                      +1
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>
