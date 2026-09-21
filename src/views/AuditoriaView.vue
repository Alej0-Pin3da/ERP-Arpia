<script setup lang="ts">
import { ref, onMounted } from 'vue'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import { showToast } from '@/utils/toast'
import * as auditoriaApi from '@/services/api/auditoria'
import type { PrecioVersionRead, CostoVersionRead, CierreMensualRead } from '@/services/api/auditoria'
import { useProductos } from '@/composables/useProductos'

const productosApi = useProductos()
const nombresProductos = ref<Record<number, string>>({})
async function cargarNombresProductos() {
  try {
    const r = await productosApi.list({ limit: 100 })
    const map: Record<number, string> = {}
    for (const p of (r.items ?? []) as unknown as Record<string, unknown>[]) {
      map[Number(p.id)] = String(p.nombre ?? '')
    }
    nombresProductos.value = map
  } catch { nombresProductos.value = {} }
}
function nombreProducto(id: number): string {
  return nombresProductos.value[id] || `Producto #${id}`
}

type Tab = 'precios' | 'costos' | 'cierres'
const activeTab = ref<Tab>('precios')
const tabs: { value: Tab; label: string }[] = [
  { value: 'precios', label: 'Versiones de precio' },
  { value: 'costos', label: 'Versiones de costo' },
  { value: 'cierres', label: 'Cierres mensuales' },
]

const filtroProductoId = ref('')
const loading = ref(false)
const precios = ref<PrecioVersionRead[]>([])
const costos = ref<CostoVersionRead[]>([])
const cierres = ref<CierreMensualRead[]>([])

function extractDetail(e: unknown): string {
  const axiosDetail = (e as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail
  if (Array.isArray(axiosDetail)) {
    return axiosDetail.map((d: any) => d.msg ?? JSON.stringify(d)).join('; ')
  }
  if (typeof axiosDetail === 'string' && axiosDetail) return axiosDetail
  if (e instanceof Error && e.message) return e.message
  return 'No se pudo cargar la auditoría fiscal'
}

function productoIdParam(): { producto_id?: number } {
  const n = Number(filtroProductoId.value)
  return Number.isInteger(n) && n > 0 ? { producto_id: n } : {}
}

async function cargarAuditoria() {
  loading.value = true
  try {
    const params = productoIdParam()
    const [p, c, s] = await Promise.all([
      auditoriaApi.listPrecioVersions(params),
      auditoriaApi.listCostoVersions(params),
      auditoriaApi.listCierres(),
    ])
    precios.value = p
    costos.value = c
    cierres.value = s
  } catch (e) {
    precios.value = []
    costos.value = []
    cierres.value = []
    showToast('error', 'Error al cargar auditoría', extractDetail(e))
  } finally {
    loading.value = false
  }
}

function aplicarFiltro() {
  void cargarAuditoria()
}

function limpiarFiltro() {
  filtroProductoId.value = ''
  void cargarAuditoria()
}

onMounted(() => { void cargarAuditoria(); void cargarNombresProductos() })
</script>

<template>
  <div class="space-y-6">
    <div class="border-b border-stone-800 pb-4">
      <h1 class="text-2xl font-serif font-bold text-amber-300 tracking-wide">
        Auditoría Fiscal &amp; Cierres
      </h1>
      <p class="text-xs text-stone-400 mt-1 font-mono">
        Historial de versiones de precio y costo por producto, y cierres mensuales. Vista de solo lectura.
      </p>
    </div>

    <div class="rounded-2xl border border-stone-800 bg-stone-900/40 p-6 space-y-4">
      <div class="flex flex-wrap items-center gap-2">
        <button
          v-for="t in tabs"
          :key="t.value"
          type="button"
          class="px-3 py-1.5 rounded-full text-xs font-mono border transition-colors"
          :class="activeTab === t.value
            ? 'bg-amber-300 text-stone-900 border-amber-300 font-bold'
            : 'text-stone-400 border-stone-700 hover:border-amber-300/60'"
          @click="activeTab = t.value"
        >
          {{ t.label }}
        </button>
      </div>

      <div v-if="activeTab !== 'cierres'" class="flex flex-wrap items-center gap-2">
        <select
          v-model="filtroProductoId"
          class="bg-stone-950 border border-stone-700 text-stone-200 text-xs rounded-lg px-3 py-2 font-mono focus:border-amber-400 focus:outline-none w-64"
          @change="aplicarFiltro"
        >
          <option value="">Todos los productos</option>
          <option v-for="(nombre, id) in nombresProductos" :key="id" :value="String(id)">{{ nombre }}</option>
        </select>
        <Button label="Limpiar" size="small" severity="secondary" text :disabled="loading" @click="limpiarFiltro" />
      </div>

      <div v-if="loading" class="py-8 text-center text-stone-500 font-mono text-xs">
        <i class="pi pi-spin pi-spinner text-2xl mb-2 block" />
        Cargando auditoría fiscal…
      </div>

      <template v-else-if="activeTab === 'precios'">
      <div class="hidden overflow-x-auto md:block">
      <table class="w-full min-w-[640px] text-xs text-left border-collapse">
        <thead>
          <tr class="border-b border-stone-800 text-stone-400 font-mono">
            <th class="py-2.5 px-3 sticky left-0 z-10 bg-stone-950/95">ID</th>
            <th class="py-2.5 px-3">Producto</th>
            <th class="py-2.5 px-3">Variante</th>
            <th class="py-2.5 px-3 text-right whitespace-nowrap">Precio</th>
            <th class="py-2.5 px-3 whitespace-nowrap">Vigente desde</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-stone-800/60 font-mono">
          <tr v-if="!precios.length">
            <td colspan="5" class="py-8 text-center text-stone-500">
              <i class="pi pi-inbox text-2xl mb-2 block" />
              Sin versiones de precio registradas.
            </td>
          </tr>
          <tr v-for="p in precios" :key="p.id">
            <td class="py-3 px-3 text-stone-500 sticky left-0 z-10 bg-stone-900/95 whitespace-nowrap">{{ p.id }}</td>
            <td class="py-3 px-3 text-amber-300 font-bold whitespace-nowrap">{{ nombreProducto(p.producto_id) }}</td>
            <td class="py-3 px-3 text-stone-400 whitespace-nowrap">{{ p.variante_id ?? '—' }}</td>
            <td class="py-3 px-3 text-right text-stone-300 font-semibold whitespace-nowrap">${{ p.precio }}</td>
            <td class="py-3 px-3 text-stone-400 whitespace-nowrap">{{ p.fecha_desde }}</td>
          </tr>
        </tbody>
      </table>
      </div>
      <!-- Mobile cards: same precios. No horizontal scroll. -->
      <div class="space-y-3 md:hidden max-w-full min-w-0">
        <div v-if="!precios.length" class="text-center py-8 text-sm text-stone-500">Sin versiones de precio registradas.</div>
        <div v-for="p in precios" :key="p.id" class="bg-stone-900/80 border border-stone-800 rounded-2xl p-4 space-y-1 min-w-0">
          <div class="flex items-start justify-between gap-2 min-w-0">
            <div class="font-bold text-sm text-amber-300">Producto {{ nombreProducto(p.producto_id) }}</div>
            <span class="text-xs font-mono text-stone-500 shrink-0">ID {{ p.id }}</span>
          </div>
          <div class="text-sm text-stone-300">Variante: {{ p.variante_id ?? '—' }}</div>
          <div class="flex items-center justify-between text-sm">
            <span class="text-xs uppercase tracking-wider text-stone-400">Precio</span>
            <span class="font-mono font-bold text-stone-100">${{ p.precio }}</span>
          </div>
          <div class="text-xs text-stone-500">Vigente desde {{ p.fecha_desde }}</div>
        </div>
      </div>
      </template>

      <template v-else-if="activeTab === 'costos'">
      <div class="hidden overflow-x-auto md:block">
      <table class="w-full min-w-[640px] text-xs text-left border-collapse">
        <thead>
          <tr class="border-b border-stone-800 text-stone-400 font-mono">
            <th class="py-2.5 px-3 sticky left-0 z-10 bg-stone-950/95">ID</th>
            <th class="py-2.5 px-3">Producto</th>
            <th class="py-2.5 px-3 text-right whitespace-nowrap">Costo</th>
            <th class="py-2.5 px-3 whitespace-nowrap">Vigente desde</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-stone-800/60 font-mono">
          <tr v-if="!costos.length">
            <td colspan="4" class="py-8 text-center text-stone-500">
              <i class="pi pi-inbox text-2xl mb-2 block" />
              Sin versiones de costo registradas.
            </td>
          </tr>
          <tr v-for="c in costos" :key="c.id">
            <td class="py-3 px-3 text-stone-500 sticky left-0 z-10 bg-stone-900/95 whitespace-nowrap">{{ c.id }}</td>
            <td class="py-3 px-3 text-amber-300 font-bold whitespace-nowrap">{{ nombreProducto(c.producto_id) }}</td>
            <td class="py-3 px-3 text-right text-stone-300 font-semibold whitespace-nowrap">${{ c.costo }}</td>
            <td class="py-3 px-3 text-stone-400 whitespace-nowrap">{{ c.fecha_desde }}</td>
          </tr>
        </tbody>
      </table>
      </div>
      <!-- Mobile cards: same costos. No horizontal scroll. -->
      <div class="space-y-3 md:hidden max-w-full min-w-0">
        <div v-if="!costos.length" class="text-center py-8 text-sm text-stone-500">Sin versiones de costo registradas.</div>
        <div v-for="c in costos" :key="c.id" class="bg-stone-900/80 border border-stone-800 rounded-2xl p-4 space-y-1 min-w-0">
          <div class="flex items-start justify-between gap-2 min-w-0">
            <div class="font-bold text-sm text-amber-300">Producto {{ nombreProducto(c.producto_id) }}</div>
            <span class="text-xs font-mono text-stone-500 shrink-0">ID {{ c.id }}</span>
          </div>
          <div class="flex items-center justify-between text-sm">
            <span class="text-xs uppercase tracking-wider text-stone-400">Costo</span>
            <span class="font-mono font-bold text-stone-100">${{ c.costo }}</span>
          </div>
          <div class="text-xs text-stone-500">Vigente desde {{ c.fecha_desde }}</div>
        </div>
      </div>
      </template>

      <template v-else>
      <div class="hidden overflow-x-auto md:block">
      <table class="w-full min-w-[640px] text-xs text-left border-collapse">
        <thead>
          <tr class="border-b border-stone-800 text-stone-400 font-mono">
            <th class="py-2.5 px-3 sticky left-0 z-10 bg-stone-950/95">ID</th>
            <th class="py-2.5 px-3">Período</th>
            <th class="py-2.5 px-3 whitespace-nowrap">Estado</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-stone-800/60 font-mono">
          <tr v-if="!cierres.length">
            <td colspan="3" class="py-8 text-center text-stone-500">
              <i class="pi pi-inbox text-2xl mb-2 block" />
              Sin cierres mensuales registrados.
            </td>
          </tr>
          <tr v-for="s in cierres" :key="s.id">
            <td class="py-3 px-3 text-stone-500 sticky left-0 z-10 bg-stone-900/95 whitespace-nowrap">{{ s.id }}</td>
            <td class="py-3 px-3 text-amber-300 font-bold whitespace-nowrap">{{ s.periodo }}</td>
            <td class="py-3 px-3 text-stone-300 whitespace-nowrap">{{ s.estado ?? 'cerrado' }}</td>
          </tr>
        </tbody>
      </table>
      </div>
      <!-- Mobile cards: same cierres. No horizontal scroll. -->
      <div class="space-y-3 md:hidden max-w-full min-w-0">
        <div v-if="!cierres.length" class="text-center py-8 text-sm text-stone-500">Sin cierres mensuales registrados.</div>
        <div v-for="s in cierres" :key="s.id" class="bg-stone-900/80 border border-stone-800 rounded-2xl p-4 space-y-1 min-w-0">
          <div class="flex items-start justify-between gap-2 min-w-0">
            <div class="font-bold text-sm text-amber-300">{{ s.periodo }}</div>
            <span class="text-xs font-mono text-stone-500 shrink-0">ID {{ s.id }}</span>
          </div>
          <div class="text-sm text-stone-300">Estado: {{ s.estado ?? 'cerrado' }}</div>
        </div>
      </div>
      </template>
    </div>
  </div>
</template>
