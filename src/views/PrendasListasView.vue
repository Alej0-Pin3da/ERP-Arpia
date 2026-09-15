<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import InputText from 'primevue/inputtext'
import { useProductos } from '@/composables/useProductos'
import type { ProductoRead } from '@/services/api/productos'
import EtiquetaPrendaModal from '@/components/atelier/EtiquetaPrendaModal.vue'
import type { EtiquetaPrenda, EtiquetaVariante } from '@/components/atelier/EtiquetaPrendaModal.vue'

const productosService = useProductos()
const search = ref('')

/** LOTE display shape: backend ProductoRead with stock_actual > 0 (batch flow, THE list). */
interface LoteDisplay {
  id: number
  nombre: string
  codigo: string
  stock: number
  precio: number
  coleccion?: string | null
  composicion?: string | null
}

const showEtiquetaModal = ref(false)
const selectedPrenda = ref<EtiquetaPrenda | null>(null)
const selectedVariante = ref<EtiquetaVariante | null>(null)
const selectedProductoId = ref<number | null>(null)
const selectedCantidad = ref<number | null>(null)

const lotes = ref<LoteDisplay[]>([])

function toNum(v: number | string | null | undefined): number {
  const n = Number(v)
  return Number.isFinite(n) ? n : 0
}

async function cargarLotes() {
  try {
    const res = await productosService.list({ limit: 100 })
    lotes.value = res.items
      .filter((p: ProductoRead) => toNum(p.stock_actual) > 0)
      .map((p: ProductoRead) => ({
        id: p.id,
        nombre: p.nombre,
        codigo: p.codigo || `PROD-${p.id}`,
        stock: toNum(p.stock_actual),
        precio: toNum(p.precio_venta_sugerido),
        coleccion: p.coleccion ?? null,
        composicion: p.composicion ?? null,
      }))
  } catch (e) {
    console.error('Error cargando stock por lote:', e)
  }
}

onMounted(() => {
  cargarLotes()
})

const loteFiltrados = computed(() => {
  const q = search.value.trim().toLowerCase()
  return lotes.value.filter(
    (l) =>
      !q ||
      l.nombre.toLowerCase().includes(q) ||
      l.codigo.toLowerCase().includes(q),
  )
})

const loteStockTotal = computed(() => lotes.value.reduce((acc, l) => acc + l.stock, 0))
const loteValorizacion = computed(() => lotes.value.reduce((acc, l) => acc + l.stock * l.precio, 0))
const lotePrecioMedio = computed(() => (loteStockTotal.value > 0 ? loteValorizacion.value / loteStockTotal.value : 0))

function formatCOP(val: number) {
  return `$${Math.round(val).toLocaleString('es-CO')}`
}

/** Etiqueta por lote: prenda = producto (+ coleccion/composicion persistidas),
 *  productoId + cantidad para el modal; sin variante sintética (nada de 'N uds' como talla/color). */
function verEtiquetaLote(l: LoteDisplay) {
  selectedPrenda.value = {
    codigo: l.codigo,
    nombre: l.nombre,
    precio_venta: l.precio,
    coleccion: l.coleccion ?? null,
    composicion: l.composicion ?? null,
  }
  selectedVariante.value = null
  selectedProductoId.value = l.id
  selectedCantidad.value = Math.round(l.stock)
  showEtiquetaModal.value = true
}

/** Etiqueta guardada en el producto: refleja en la fila del lote para la próxima apertura. */
function onEtiquetaGuardada(payload: { coleccion: string | null; composicion: string | null }) {
  if (selectedPrenda.value) {
    selectedPrenda.value.coleccion = payload.coleccion
    selectedPrenda.value.composicion = payload.composicion
  }
  if (selectedProductoId.value != null) {
    const row = lotes.value.find((l) => l.id === selectedProductoId.value)
    if (row) {
      row.coleccion = payload.coleccion
      row.composicion = payload.composicion
    }
  }
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
            {{ Math.round(loteStockTotal) }} uds en Stock
          </span>
        </div>
        <p class="text-xs sm:text-sm text-stone-400 m-0 max-w-2xl">
          Unidades terminadas por lote de producción (GET /productos · stock_actual). Se consumen en Venta, no generan filas unitarias.
        </p>
      </div>

      <div class="flex flex-wrap items-center gap-2">
        <RouterLink
          :to="{ name: 'produccion' }"
          class="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg bg-amber-500 text-stone-950 text-xs font-bold hover:bg-amber-400 transition"
          title="Completar un lote en Producción"
        >
          <i class="pi pi-plus text-xs" />
          <span>Completar lote en Producción</span>
        </RouterLink>
      </div>
    </div>

    <!-- 4 KPI Summary Cards (lote) -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <div class="bg-stone-900/80 border border-stone-800 rounded-2xl p-4 shadow-md">
        <div class="text-xs text-stone-400 font-bold uppercase tracking-wider">Productos con Stock</div>
        <div class="text-2xl font-extrabold text-stone-100 mt-2 font-mono">
          {{ lotes.length }} productos
        </div>
        <div class="text-[11px] text-stone-400 mt-1">Lotes con stock_actual &gt; 0</div>
      </div>

      <div class="bg-stone-900/80 border border-sky-500/30 rounded-2xl p-4 shadow-md">
        <div class="text-xs text-stone-400 font-bold uppercase tracking-wider">Stock por Lote</div>
        <div class="text-2xl font-extrabold text-sky-300 mt-2 font-mono">
          {{ Math.round(loteStockTotal) }} uds
        </div>
        <div class="text-[11px] text-stone-400 mt-1">Unidades en Producto.stock_actual</div>
      </div>

      <div class="bg-stone-900/80 border border-sky-500/30 rounded-2xl p-4 shadow-md">
        <div class="text-xs text-stone-400 font-bold uppercase tracking-wider">Valorización Lote</div>
        <div class="text-2xl font-extrabold text-sky-300 mt-2 font-mono">
          {{ formatCOP(loteValorizacion) }}
        </div>
        <div class="text-[11px] text-stone-400 mt-1">Stock lote × precio sugerido</div>
      </div>

      <div class="bg-stone-900/80 border border-stone-800 rounded-2xl p-4 shadow-md">
        <div class="text-xs text-stone-400 font-bold uppercase tracking-wider">Precio Medio</div>
        <div class="text-2xl font-extrabold text-amber-300 mt-2 font-mono">
          {{ formatCOP(lotePrecioMedio) }}
        </div>
        <div class="text-[11px] text-stone-400 mt-1">Valorización / unidades</div>
      </div>
    </div>

    <!-- Search Input -->
    <div class="w-full md:w-96">
      <span class="p-input-icon-left w-full">
        <InputText
          v-model="search"
          placeholder="Buscar productos por nombre o código..."
          class="w-full text-xs"
        />
      </span>
    </div>

    <!-- Stock por lote (flujo batch: Producto.stock_actual, sin filas por prenda) -->
    <section aria-label="Stock por lote">
      <div class="flex items-center gap-2.5 flex-wrap mb-3">
        <h2 class="text-base sm:text-lg font-bold font-serif tracking-wide text-stone-100 m-0">
          Stock por lote
        </h2>
        <span class="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-sky-950/80 text-sky-300 border border-sky-500/30 uppercase tracking-wider">
          {{ Math.round(loteStockTotal) }} uds en {{ loteFiltrados.length }} productos
        </span>
      </div>

      <div v-if="loteFiltrados.length === 0" class="bg-stone-900/80 border border-stone-800 rounded-2xl p-5 text-sm text-stone-400">
        Sin stock por lote — completá un lote en Producción.
      </div>

      <div v-else class="space-y-4">
        <!-- Desktop table -->
        <div class="hidden overflow-x-auto md:block bg-stone-900/80 border border-stone-800 rounded-2xl shadow-lg">
          <table class="w-full min-w-[640px] text-left text-xs border-collapse">
            <thead>
              <tr class="border-b border-stone-800/80 text-stone-400 bg-stone-900/40 uppercase tracking-wider font-semibold">
                <th class="py-2.5 px-4">Producto</th>
                <th class="py-2.5 px-4 whitespace-nowrap">Código</th>
                <th class="py-2.5 px-4 text-center whitespace-nowrap">Stock (uds)</th>
                <th class="py-2.5 px-4 text-right whitespace-nowrap">Precio sugerido</th>
                <th class="py-2.5 px-4 text-right whitespace-nowrap">Etiqueta</th>
                <th class="py-2.5 px-4 text-right whitespace-nowrap">Ficha</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-stone-800/50 text-stone-200 font-mono">
              <tr v-for="l in loteFiltrados" :key="l.id" class="hover:bg-stone-800/30">
                <td class="py-2.5 px-4 font-bold text-stone-100 font-sans">{{ l.nombre }}</td>
                <td class="py-2.5 px-4 text-sky-300 whitespace-nowrap">{{ l.codigo }}</td>
                <td class="py-2.5 px-4 text-center font-bold text-sky-300 whitespace-nowrap">{{ Math.round(l.stock) }} uds</td>
                <td class="py-2.5 px-4 text-right text-amber-300 whitespace-nowrap">{{ formatCOP(l.precio) }}</td>
                <td class="py-2.5 px-4 text-right font-sans whitespace-nowrap">
                  <button
                    type="button"
                    class="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-amber-950/70 border border-amber-500/40 text-amber-300 hover:text-amber-200 text-xs font-semibold transition"
                    title="Generar Etiqueta de Autor & QR"
                    @click="verEtiquetaLote(l)"
                  >
                    <i class="pi pi-qrcode text-xs" />
                    <span>Etiqueta QR</span>
                  </button>
                </td>
                <td class="py-2.5 px-4 text-right font-sans whitespace-nowrap">
                  <RouterLink :to="{ name: 'productos' }" class="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-sky-950/70 border border-sky-500/40 text-sky-300 hover:text-sky-200 text-xs font-semibold transition" title="Abrir ficha en Productos">
                    <i class="pi pi-book text-xs" />
                    <span>Ficha</span>
                  </RouterLink>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <!-- Mobile cards -->
        <div class="space-y-3 md:hidden">
          <div v-for="l in loteFiltrados" :key="l.id" class="bg-stone-900/80 border border-stone-800 rounded-2xl p-4 space-y-2 min-w-0">
            <div class="flex items-start justify-between gap-2 min-w-0">
              <div class="font-bold text-sm text-stone-100 min-w-0">{{ l.nombre }}</div>
              <span class="font-mono text-xs text-sky-300 shrink-0">{{ l.codigo }}</span>
            </div>
            <div class="flex items-center justify-between text-sm">
              <span class="text-xs uppercase tracking-wider text-stone-400">Stock</span>
              <span class="font-mono font-bold text-sky-300">{{ Math.round(l.stock) }} uds</span>
            </div>
            <div class="flex items-center justify-between text-sm">
              <span class="text-xs uppercase tracking-wider text-stone-400">Precio sugerido</span>
              <span class="font-mono font-bold text-amber-300">{{ formatCOP(l.precio) }}</span>
            </div>
            <div class="flex gap-2 pt-1">
              <button type="button" class="flex-1 min-h-[40px] rounded-lg bg-amber-950/70 border border-amber-500/40 text-amber-300 text-sm font-semibold" title="Generar Etiqueta de Autor & QR" @click="verEtiquetaLote(l)">Etiqueta QR</button>
              <RouterLink :to="{ name: 'productos' }" class="flex-1 flex items-center justify-center min-h-[40px] rounded-lg bg-sky-950/70 border border-sky-500/40 text-sky-300 text-sm font-semibold" title="Abrir ficha en Productos">
                Ficha
              </RouterLink>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Etiqueta Modal (lote: prenda = producto, cantidad informativa fuera del tag) -->
    <EtiquetaPrendaModal
      v-model:visible="showEtiquetaModal"
      :prenda="selectedPrenda"
      :variante="selectedVariante"
      :producto-id="selectedProductoId"
      :cantidad="selectedCantidad"
      @guardado="onEtiquetaGuardada"
    />
  </div>
</template>
