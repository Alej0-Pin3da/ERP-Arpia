<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import { usePrendas } from '@/composables/usePrendas'
import { useProductos } from '@/composables/useProductos'
import type { ProductoRead } from '@/services/api/productos'
import EtiquetaPrendaModal from '@/components/atelier/EtiquetaPrendaModal.vue'
import IngresarPrendaModal from '@/components/atelier/IngresarPrendaModal.vue'
import { showToast } from '@/utils/toast'

const prendasService = usePrendas()
const productosService = useProductos()
const search = ref('')

/** REAL display shape: backend PrendaRead normalized for this view. */
interface VarianteDisplay {
  id: number
  talla: string
  color: string
  sku: string
  stock_fisico: number
  reservado: number
  disponible: number
}
interface PrendaDisplay {
  id: number
  codigo: string
  nombre: string
  categoria: string
  costo_base: number
  precio_venta: number
  fisico_total: number
  disponible_total: number
  variantes: VarianteDisplay[]
}

const showEtiquetaModal = ref(false)
const showIngresarModal = ref(false)
const selectedPrenda = ref<PrendaDisplay | null>(null)
const selectedVariante = ref<VarianteDisplay | null>(null)
const prendas = ref<PrendaDisplay[]>([])

async function cargarPrendas() {
  try {
    const res = await prendasService.list({ limit: 100 })
    // Map PrendaRead items to UI structure if needed
    prendas.value = res.items.map((p: any) => ({
      id: p.id,
      codigo: `PRD-${p.id}`,
      nombre: p.nombre_producto || `Prenda #${p.id}`,
      categoria: 'Confección',
      costo_base: Number(p.costo_real) || 0,
      precio_venta: Number(p.precio_venta) || 0,
      fisico_total: p.estado === 'disponible' ? 1 : 0,
      disponible_total: p.estado === 'disponible' ? 1 : 0,
      variantes: [
        {
          id: p.variante_id,
          // P2-7: prenda genérica sin variante → "Sin talla".
          talla: p.talla || (p.variante_id == null ? 'Sin talla' : 'M'),
          color: 'Estándar',
          sku: p.variante_id == null ? 'GENERICA' : `VAR-${p.variante_id}`,
          stock_fisico: p.estado === 'disponible' ? 1 : 0,
          reservado: p.estado === 'reservada' ? 1 : 0,
          disponible: p.estado === 'disponible' ? 1 : 0,
        },
      ],
    }))
  } catch (e) {
    console.error('Error cargando prendas reales:', e)
  }
}

onMounted(() => {
  cargarPrendas()
  cargarLotes()
})

/** LOTE display shape: backend ProductoRead with stock_actual > 0 (new batch flow). */
interface LoteDisplay {
  id: number
  nombre: string
  codigo: string
  stock: number
  precio: number
}

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
      }))
  } catch (e) {
    console.error('Error cargando stock por lote:', e)
  }
}

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

const stockFisico = computed(() => prendas.value.reduce((acc: number, p: any) => acc + (p.fisico_total ?? 1), 0) || prendas.value.length)
const stockDisponible = computed(() => prendas.value.reduce((acc: number, p: any) => acc + (p.disponible_total ?? (p.estado === 'disponible' ? 1 : 0)), 0))
const valorizacion = computed(() => prendas.value.reduce((acc: number, p: any) => acc + Number(p.precio_venta ?? 0), 0))

const prendasFiltradas = computed(() => {
  return prendas.value.filter((p) => {
    const q = search.value.trim().toLowerCase()
    return (
      !q ||
      p.nombre.toLowerCase().includes(q) ||
      (p.codigo && p.codigo.toLowerCase().includes(q)) ||
      (p.categoria && p.categoria.toLowerCase().includes(q))
    )
  })
})

function formatCOP(val: number) {
  return `$${Math.round(val).toLocaleString('es-CO')}`
}

async function ajustarStock(productoId: number, varianteId: number, delta: number) {
  // No hay endpoint de delta de stock y cada fila es 1 unidad:
  // no se finge un PATCH vacío con éxito (los botones están deshabilitados).
  showToast('info', 'Stock en REAL', 'El stock se mueve con "Ingresar Prenda Confeccionada" (cada fila es 1 unidad).')
  await cargarPrendas()
}

function verEtiqueta(p: PrendaDisplay, v?: VarianteDisplay) {
  selectedPrenda.value = p
  selectedVariante.value = v || (p.variantes && p.variantes[0]) || null
  showEtiquetaModal.value = true
}

function ingresarPrendaModal() {
  showIngresarModal.value = true
}

async function onPrendaIngresada() {
  await cargarPrendas()
  await cargarLotes()
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
            {{ stockFisico }} Prendas en Stock
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

    <!-- 4 KPI Summary Cards (prendas unitarias) + 2 lote cards (stock por lote, unidades separadas) -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
      <div class="bg-stone-900/80 border border-stone-800 rounded-2xl p-4 shadow-md">
        <div class="text-xs text-stone-400 font-bold uppercase tracking-wider">Prendas Físicas en Perchero</div>
        <div class="text-2xl font-extrabold text-stone-100 mt-2 font-mono">
          {{ stockFisico }} unidades
        </div>
        <div class="text-[11px] text-stone-400 mt-1">Existencia real en taller</div>
      </div>

      <div class="bg-stone-900/80 border border-stone-800 rounded-2xl p-4 shadow-md">
        <div class="text-xs text-stone-400 font-bold uppercase tracking-wider">Stock Disponible para Venta</div>
        <div class="text-2xl font-extrabold text-emerald-400 mt-2 font-mono">
          {{ stockDisponible }} unidades
        </div>
        <div class="text-[11px] text-stone-400 mt-1">Listos para despacho inmediato</div>
      </div>

      <div class="bg-stone-900/80 border border-stone-800 rounded-2xl p-4 shadow-md">
        <div class="text-xs text-stone-400 font-bold uppercase tracking-wider">Prendas Reservadas en Pedidos</div>
        <div class="text-2xl font-extrabold text-amber-400 mt-2 font-mono">
          {{ stockFisico - stockDisponible }} unidades
        </div>
        <div class="text-[11px] text-stone-400 mt-1">Con abono o reserva previa</div>
      </div>

      <div class="bg-stone-900/80 border border-stone-800 rounded-2xl p-4 shadow-md">
        <div class="text-xs text-stone-400 font-bold uppercase tracking-wider">Valorización a PVP</div>
        <div class="text-2xl font-extrabold text-amber-300 mt-2 font-mono">
          {{ formatCOP(valorizacion) }}
        </div>
        <div class="text-[11px] text-stone-400 mt-1">Total mercancía a precio venta</div>
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

    <!-- Stock por lote (nuevo flujo batch: Producto.stock_actual, sin filas por prenda) -->
    <section aria-label="Stock por lote">
      <div class="flex items-center gap-2.5 flex-wrap mb-3">
        <h2 class="text-base sm:text-lg font-bold font-serif tracking-wide text-stone-100 m-0">
          Stock por lote
        </h2>
        <span class="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-sky-950/80 text-sky-300 border border-sky-500/30 uppercase tracking-wider">
          {{ Math.round(loteStockTotal) }} uds en {{ loteFiltrados.length }} productos
        </span>
      </div>
      <p class="text-xs sm:text-sm text-stone-400 m-0 mb-3 max-w-2xl">
        Unidades terminadas por lote de producción (GET /productos · stock_actual). Se consumen en Venta, no generan filas unitarias.
      </p>

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
            <RouterLink :to="{ name: 'productos' }" class="flex items-center justify-center min-h-[40px] rounded-lg bg-sky-950/70 border border-sky-500/40 text-sky-300 text-sm font-semibold" title="Abrir ficha en Productos">
              Ficha
            </RouterLink>
          </div>
        </div>
      </div>
    </section>

    <!-- Prendas unitarias (flujo excepción: muestras/ajustes — 1 fila = 1 prenda) -->
    <section aria-label="Prendas unitarias">
      <div class="flex items-center gap-2.5 flex-wrap mb-3">
        <h2 class="text-base sm:text-lg font-bold font-serif tracking-wide text-stone-100 m-0">
          Prendas unitarias
        </h2>
        <span class="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-amber-950/80 text-amber-300 border border-amber-500/30 uppercase tracking-wider">
          {{ prendasFiltradas.length }} unidades · muestras / ajustes
        </span>
      </div>
      <p class="text-xs sm:text-sm text-stone-400 m-0 mb-3 max-w-2xl">
        Filas individuales de GET /prendas-confeccionadas (1 fila = 1 prenda). Solo para excepciones: muestras y ajustes.
      </p>

      <div v-if="prendasFiltradas.length === 0" class="bg-stone-900/80 border border-stone-800 rounded-2xl p-5 text-sm text-stone-400">
        Sin prendas unitarias registradas — usá "Ingresar Prenda Confeccionada" solo para muestras o ajustes.
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
            <button
              type="button"
              class="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-amber-950/70 border border-amber-500/40 text-amber-300 hover:text-amber-200 text-xs font-semibold transition"
              title="Generar Etiqueta de Autor & QR"
              @click="verEtiqueta(p)"
            >
              <i class="pi pi-qrcode text-xs" />
              <span>Etiqueta QR</span>
            </button>
          </div>
        </div>

        <!-- Variants Sub-Table (desktop) + Cards (mobile) -->
        <div class="hidden overflow-x-auto md:block">
          <table class="w-full min-w-[760px] text-left text-xs border-collapse">
            <thead>
              <tr class="border-b border-stone-800/80 text-stone-400 bg-stone-900/40 uppercase tracking-wider font-semibold">
                <th class="py-2.5 px-4 sticky left-0 z-10 bg-stone-950/95">Talla</th>
                <th class="py-2.5 px-4">Color / Variante</th>
                <th class="py-2.5 px-4 whitespace-nowrap">SKU</th>
                <th class="py-2.5 px-4 text-center whitespace-nowrap">Stock Físico</th>
                <th class="py-2.5 px-4 text-center whitespace-nowrap">Reservado</th>
                <th class="py-2.5 px-4 text-center whitespace-nowrap">Disponible</th>
                <th class="py-2.5 px-4 text-right whitespace-nowrap">Acciones</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-stone-800/50 text-stone-200 font-mono">
              <tr v-for="v in p.variantes" :key="v.id" class="hover:bg-stone-800/30">
                <td class="py-2.5 px-4 font-bold text-amber-300 font-sans sticky left-0 z-10 bg-stone-900/95 whitespace-nowrap">{{ v.talla }}</td>
                <td class="py-2.5 px-4 font-sans text-stone-300 min-w-[180px]">{{ v.color }}</td>
                <td class="py-2.5 px-4 text-stone-400 whitespace-nowrap">{{ v.sku }}</td>
                <td class="py-2.5 px-4 text-center font-bold text-stone-100 whitespace-nowrap">{{ v.stock_fisico }}</td>
                <td class="py-2.5 px-4 text-center text-amber-400 whitespace-nowrap">{{ v.reservado }}</td>
                <td class="py-2.5 px-4 text-center font-bold text-emerald-400 whitespace-nowrap">{{ v.disponible }}</td>
                <td class="py-2.5 px-4 text-right font-sans whitespace-nowrap">
                  <div class="inline-flex items-center gap-1.5">
                    <button
                      type="button"
                      class="p-1 text-stone-400 hover:text-amber-300 rounded transition"
                      title="Ver Etiqueta de esta Talla"
                      @click="verEtiqueta(p, v)"
                    >
                      <i class="pi pi-qrcode text-xs" />
                    </button>
                    <div class="inline-flex items-center bg-stone-950 border border-stone-800 rounded-lg p-0.5">
                      <button
                        type="button"
                        class="px-2 py-0.5 text-stone-400 hover:text-white hover:bg-stone-800 rounded text-xs transition disabled:opacity-40 disabled:cursor-not-allowed"
                        disabled
                        title="El stock se mueve con Ingresar Prenda (cada fila es 1 unidad)"
                        @click="ajustarStock(p.id, v.id, -1)"
                      >
                        -1
                      </button>
                      <button
                        type="button"
                        class="px-2 py-0.5 text-amber-400 hover:text-amber-300 hover:bg-stone-800 rounded text-xs font-bold transition disabled:opacity-40 disabled:cursor-not-allowed"
                        disabled
                        title="El stock se mueve con Ingresar Prenda (cada fila es 1 unidad)"
                        @click="ajustarStock(p.id, v.id, 1)"
                      >
                        +1
                      </button>
                    </div>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <!-- Mobile variant cards: same p.variantes. No horizontal scroll. -->
        <div class="space-y-3 p-4 md:hidden max-w-full min-w-0">
          <div v-for="v in p.variantes" :key="v.id" class="bg-stone-950/70 border border-stone-800 rounded-2xl p-4 space-y-2 min-w-0">
            <div class="flex items-start justify-between gap-2 min-w-0">
              <div class="min-w-0">
                <div class="font-bold text-sm text-amber-300">Talla {{ v.talla }}</div>
                <div class="text-sm text-stone-300">{{ v.color }}</div>
              </div>
              <span class="font-mono text-xs text-stone-400 shrink-0">{{ v.sku }}</span>
            </div>
            <div class="flex items-center justify-between text-sm">
              <span class="text-xs uppercase tracking-wider text-stone-400">Físico</span>
              <span class="font-mono font-bold text-stone-100">{{ v.stock_fisico }}</span>
            </div>
            <div class="flex items-center justify-between text-sm">
              <span class="text-xs uppercase tracking-wider text-stone-400">Reservado</span>
              <span class="font-mono text-amber-400">{{ v.reservado }}</span>
            </div>
            <div class="flex items-center justify-between text-sm">
              <span class="text-xs uppercase tracking-wider text-stone-400">Disponible</span>
              <span class="font-mono font-bold text-emerald-400">{{ v.disponible }}</span>
            </div>
            <div class="flex gap-2 pt-1">
              <button type="button" class="flex-1 min-h-[40px] rounded-lg bg-stone-800 text-stone-200 text-sm font-semibold" title="Ver Etiqueta de esta Talla" @click="verEtiqueta(p, v)">Etiqueta QR</button>
              <button type="button" class="min-w-[44px] min-h-[40px] px-3 rounded-lg bg-stone-800 text-stone-200 font-bold disabled:opacity-40" disabled title="El stock se mueve con Ingresar Prenda (cada fila es 1 unidad)" @click="ajustarStock(p.id, v.id, -1)">−1</button>
              <button type="button" class="min-w-[44px] min-h-[40px] px-3 rounded-lg bg-stone-800 text-amber-400 font-bold disabled:opacity-40" disabled title="El stock se mueve con Ingresar Prenda (cada fila es 1 unidad)" @click="ajustarStock(p.id, v.id, 1)">+1</button>
            </div>
          </div>
        </div>
      </div>
    </div>
    </section>

    <!-- Etiqueta Modal -->
    <EtiquetaPrendaModal
      v-model:visible="showEtiquetaModal"
      :prenda="selectedPrenda"
      :variante="selectedVariante"
    />

    <!-- Ingresar Prenda Modal -->
    <IngresarPrendaModal
      v-model:visible="showIngresarModal"
      @prenda-ingresada="onPrendaIngresada"
    />
  </div>
</template>
