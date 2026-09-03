<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import { useMode } from '@/composables/useMode'
import { showToast } from '@/utils/toast'
import * as auditoriaApi from '@/services/api/auditoria'
import type { PrecioVersionRead, CostoVersionRead, CierreMensualRead } from '@/services/api/auditoria'

const { isMock } = useMode()

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

async function cargarReales() {
  if (isMock.value) return
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
  void cargarReales()
}

function limpiarFiltro() {
  filtroProductoId.value = ''
  void cargarReales()
}

onMounted(() => { void cargarReales() })
watch(isMock, () => { void cargarReales() })
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

    <div v-if="isMock" class="rounded-2xl border border-stone-800 bg-stone-900/40 p-6">
      <div class="py-8 text-center text-stone-500">
        <i class="pi pi-inbox text-2xl mb-2 block" />
        Sin datos de auditoría en modo MOCK.
        <span class="block text-[11px] mt-1">
          Cambiá a modo REAL para leer <code>GET /api/v1/audit-fiscal/precio-versions</code>,
          <code>/costo-versions</code> y <code>/cierres</code>. Esta vista no modifica datos del atelier.
        </span>
      </div>
    </div>

    <div v-else class="rounded-2xl border border-stone-800 bg-stone-900/40 p-6 space-y-4">
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
        <InputText
          v-model="filtroProductoId"
          placeholder="Filtrar por producto_id"
          inputmode="numeric"
          class="w-52"
          @keyup.enter="aplicarFiltro"
        />
        <Button label="Filtrar" size="small" :loading="loading" @click="aplicarFiltro" />
        <Button label="Limpiar" size="small" severity="secondary" text :disabled="loading" @click="limpiarFiltro" />
      </div>

      <div v-if="loading" class="py-8 text-center text-stone-500 font-mono text-xs">
        <i class="pi pi-spin pi-spinner text-2xl mb-2 block" />
        Cargando auditoría fiscal…
      </div>

      <table v-else-if="activeTab === 'precios'" class="w-full text-xs text-left border-collapse">
        <thead>
          <tr class="border-b border-stone-800 text-stone-400 font-mono">
            <th class="py-2.5 px-3">ID</th>
            <th class="py-2.5 px-3">Producto</th>
            <th class="py-2.5 px-3">Variante</th>
            <th class="py-2.5 px-3 text-right">Precio</th>
            <th class="py-2.5 px-3">Vigente desde</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-stone-800/60 font-mono">
          <tr v-if="!precios.length">
            <td colspan="5" class="py-8 text-center text-stone-500">
              <i class="pi pi-inbox text-2xl mb-2 block" />
              Sin versiones de precio registradas.
              <span class="block text-[11px] mt-1">Los datos vienen de <code>GET /api/v1/audit-fiscal/precio-versions</code>.</span>
            </td>
          </tr>
          <tr v-for="p in precios" :key="p.id">
            <td class="py-3 px-3 text-stone-500">{{ p.id }}</td>
            <td class="py-3 px-3 text-amber-300 font-bold">#{{ p.producto_id }}</td>
            <td class="py-3 px-3 text-stone-400">{{ p.variante_id ?? '—' }}</td>
            <td class="py-3 px-3 text-right text-stone-300 font-semibold">${{ p.precio }}</td>
            <td class="py-3 px-3 text-stone-400">{{ p.fecha_desde }}</td>
          </tr>
        </tbody>
      </table>

      <table v-else-if="activeTab === 'costos'" class="w-full text-xs text-left border-collapse">
        <thead>
          <tr class="border-b border-stone-800 text-stone-400 font-mono">
            <th class="py-2.5 px-3">ID</th>
            <th class="py-2.5 px-3">Producto</th>
            <th class="py-2.5 px-3 text-right">Costo</th>
            <th class="py-2.5 px-3">Vigente desde</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-stone-800/60 font-mono">
          <tr v-if="!costos.length">
            <td colspan="4" class="py-8 text-center text-stone-500">
              <i class="pi pi-inbox text-2xl mb-2 block" />
              Sin versiones de costo registradas.
              <span class="block text-[11px] mt-1">Los datos vienen de <code>GET /api/v1/audit-fiscal/costo-versions</code>.</span>
            </td>
          </tr>
          <tr v-for="c in costos" :key="c.id">
            <td class="py-3 px-3 text-stone-500">{{ c.id }}</td>
            <td class="py-3 px-3 text-amber-300 font-bold">#{{ c.producto_id }}</td>
            <td class="py-3 px-3 text-right text-stone-300 font-semibold">${{ c.costo }}</td>
            <td class="py-3 px-3 text-stone-400">{{ c.fecha_desde }}</td>
          </tr>
        </tbody>
      </table>

      <table v-else class="w-full text-xs text-left border-collapse">
        <thead>
          <tr class="border-b border-stone-800 text-stone-400 font-mono">
            <th class="py-2.5 px-3">ID</th>
            <th class="py-2.5 px-3">Período</th>
            <th class="py-2.5 px-3">Estado</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-stone-800/60 font-mono">
          <tr v-if="!cierres.length">
            <td colspan="3" class="py-8 text-center text-stone-500">
              <i class="pi pi-inbox text-2xl mb-2 block" />
              Sin cierres mensuales registrados.
              <span class="block text-[11px] mt-1">Los datos vienen de <code>GET /api/v1/audit-fiscal/cierres</code>.</span>
            </td>
          </tr>
          <tr v-for="s in cierres" :key="s.id">
            <td class="py-3 px-3 text-stone-500">{{ s.id }}</td>
            <td class="py-3 px-3 text-amber-300 font-bold">{{ s.periodo }}</td>
            <td class="py-3 px-3 text-stone-300">{{ s.estado ?? 'cerrado' }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
