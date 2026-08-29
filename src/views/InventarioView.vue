<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Dropdown from 'primevue/dropdown'
import { useAtelierStore, type InsumoAtelier } from '@/stores/atelier'
import { useInsumos } from '@/composables/useInsumos'
import NuevoInsumoModal from '@/components/atelier/NuevoInsumoModal.vue'
import CompraInsumoModal from '@/components/atelier/CompraInsumoModal.vue'
import SugerirOrdenModal from '@/components/atelier/SugerirOrdenModal.vue'
import OrdenCompraProveedorModal from '@/components/atelier/OrdenCompraProveedorModal.vue'
import { showToast } from '@/utils/toast'

const atelier = useAtelierStore()
const { isMock, list: listInsumosApi } = useInsumos()
const insumosService = useInsumos()

const search = ref('')
const tipoFiltro = ref<'Todos' | 'Directo' | 'Indirecto'>('Todos')
const categoriaFiltro = ref<string>('Todas')
const soloBajoStock = ref(false)

const showNuevoModal = ref(false)
const showCompraModal = ref(false)
const showSugerirModal = ref(false)
const showOrdenProveedorModal = ref(false)
const insumoSeleccionado = ref<InsumoAtelier | null>(null)
const insumosApi = ref<InsumoAtelier[]>([])

async function cargarInsumosReales() {
  if (isMock.value) return
  try {
    const res = await listInsumosApi({ limit: 100 })
    insumosApi.value = res.items.map((i: any) => ({
      id: i.id,
      codigo: i.codigo || `INS-${i.id}`,
      nombre: i.nombre,
      descripcion: i.descripcion || '',
      tipo: (i.tipo as any) || 'Directo',
      categoria: i.nombre_categoria || 'General',
      ubicacion: i.ubicacion || 'Bodega',
      proveedor: 'Atelier',
      stock_actual: Number(i.stock_actual) || 0,
      stock_minimo: Number(i.stock_minimo) || 0,
      unidad_medida: i.unidad_medida,
      costo_unitario: Number(i.costo_promedio_actual) || 0,
      valor_total: (Number(i.stock_actual) || 0) * (Number(i.costo_promedio_actual) || 0),
    }))
  } catch (e) {
    console.error('Error cargando insumos reales:', e)
  }
}

onMounted(() => {
  cargarInsumosReales()
})

watch(isMock, () => void cargarInsumosReales())

const insumosList = computed(() => (isMock.value ? atelier.insumos : insumosApi.value))

const categoriasDisponibles = computed(() => {
  const cats = new Set(insumosList.value.map((i) => i.categoria))
  return ['Todas', ...Array.from(cats)]
})

const insumosFiltrados = computed(() => {
  return insumosList.value.filter((item) => {
    // Search
    const q = search.value.trim().toLowerCase()
    const matchesSearch =
      !q ||
      item.nombre.toLowerCase().includes(q) ||
      (item.codigo && item.codigo.toLowerCase().includes(q)) ||
      (item.proveedor && item.proveedor.toLowerCase().includes(q)) ||
      (item.ubicacion && item.ubicacion.toLowerCase().includes(q))

    // Tipo
    const matchesTipo = tipoFiltro.value === 'Todos' || item.tipo === tipoFiltro.value

    // Categoria
    const matchesCat = categoriaFiltro.value === 'Todas' || item.categoria === categoriaFiltro.value

    // Solo Bajo Stock
    const matchesBajo = !soloBajoStock.value || item.stock_actual <= item.stock_minimo

    return matchesSearch && matchesTipo && matchesCat && matchesBajo
  })
})

const directosCount = computed(() => insumosList.value.filter((i) => i.tipo === 'Directo').length)
const indirectosCount = computed(() => insumosList.value.filter((i) => i.tipo === 'Indirecto').length)
const insumosCriticosCount = computed(() => insumosList.value.filter((i: any) => (i.stock_actual ?? i.stock ?? 0) <= (i.stock_minimo ?? 0)).length)
const valorTotalInventarioReal = computed(() => insumosList.value.reduce((acc: number, i: any) => acc + ((i.stock_actual ?? i.stock ?? 0) * (i.costo_promedio ?? i.costo ?? 0)), 0))

function formatCOP(val: number) {
  return `$${Math.round(val).toLocaleString('es-CO')}`
}

function abrirCompra(item: InsumoAtelier) {
  insumoSeleccionado.value = item
  showCompraModal.value = true
}

async function ajustar(item: InsumoAtelier, delta: number) {
  if (isMock.value) {
    atelier.ajustarStockInsumo(item.id, delta)
    return
  }
  try {
    const nuevoStock = Math.max(0, (item.stock_actual ?? 0) + delta)
    await insumosService.update(item.id, { stock_actual: nuevoStock })
    await cargarInsumosReales()
    showToast('success', 'Stock actualizado', `${item.nombre} ajustado en ${delta > 0 ? '+' : ''}${delta}.`)
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : 'Error al ajustar stock'
    showToast('error', 'Error', String(msg))
  }
}

async function eliminar(item: InsumoAtelier) {
  if (isMock.value) {
    const idx = atelier.insumos.findIndex((i) => i.id === item.id)
    if (idx !== -1) {
      atelier.insumos.splice(idx, 1)
      showToast('info', 'Insumo eliminado', `${item.nombre} ha sido removido del catálogo.`)
    }
    return
  }
  try {
    await insumosService.remove(item.id)
    await cargarInsumosReales()
    showToast('info', 'Insumo eliminado', `${item.nombre} ha sido removido del catálogo.`)
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : 'Error al eliminar insumo'
    showToast('error', 'Error', String(msg))
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
            Inventario de Materiales e Insumos
          </h1>
          <span class="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-amber-950/80 text-amber-300 border border-amber-500/30 uppercase tracking-wider">
            {{ insumosList.length }} Insumos Totales
          </span>
        </div>
        <p class="text-xs sm:text-sm text-stone-400 m-0 max-w-2xl">
          Control de materias primas directas (telas, forros, cierres) e indirectas (hilos, etiquetas, empaques).
        </p>
      </div>

      <div class="flex flex-wrap items-center gap-2">
        <Button
          label="Orden a Proveedores"
          icon="pi pi-truck"
          size="small"
          severity="secondary"
          outlined
          class="text-xs font-semibold"
          @click="showOrdenProveedorModal = true"
        />
        <Button
          :label="`Sugerir Orden (${insumosCriticosCount})`"
          icon="pi pi-shopping-cart"
          size="small"
          severity="secondary"
          outlined
          class="text-xs font-semibold"
          @click="showSugerirModal = true"
        />
        <Button
          label="Nuevo Insumo"
          icon="pi pi-plus"
          size="small"
          class="p-button-warning text-xs font-semibold"
          @click="showNuevoModal = true"
        />
      </div>
    </div>

    <!-- 4 KPI Summary Cards -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <!-- 1. Valor Total Inventario -->
      <div class="bg-stone-900/80 border border-stone-800 rounded-2xl p-4 shadow-md">
        <div class="text-xs text-stone-400 font-bold uppercase tracking-wider">Valor Total Inventario</div>
        <div class="text-2xl font-extrabold text-stone-100 mt-2 font-mono">
          {{ formatCOP(isMock ? atelier.valorTotalInventario : valorTotalInventarioReal) }}
        </div>
        <div class="text-[11px] text-stone-400 mt-1">Costo promedio ponderado</div>
      </div>

      <!-- 2. Materiales Directos -->
      <div class="bg-stone-900/80 border border-stone-800 rounded-2xl p-4 shadow-md">
        <div class="text-xs text-stone-400 font-bold uppercase tracking-wider">Materiales Directos</div>
        <div class="text-2xl font-extrabold text-amber-400 mt-2 font-mono">
          {{ directosCount }} items
        </div>
        <div class="text-[11px] text-stone-400 mt-1">Telas, copas, varillas y encajes</div>
      </div>

      <!-- 3. Insumos Indirectos -->
      <div class="bg-stone-900/80 border border-stone-800 rounded-2xl p-4 shadow-md">
        <div class="text-xs text-stone-400 font-bold uppercase tracking-wider">Insumos Indirectos</div>
        <div class="text-2xl font-extrabold text-stone-300 mt-2 font-mono">
          {{ indirectosCount }} items
        </div>
        <div class="text-[11px] text-stone-400 mt-1">Empaques, bolsas y etiquetas</div>
      </div>

      <!-- 4. Insumos en Alerta -->
      <div class="bg-stone-900/80 border border-red-500/30 rounded-2xl p-4 shadow-md">
        <div class="text-xs text-red-400 font-bold uppercase tracking-wider">Insumos en Alerta</div>
        <div class="text-2xl font-extrabold text-red-400 mt-2 font-mono">
          {{ insumosCriticosCount }} items bajos
        </div>
        <div class="text-[11px] text-stone-400 mt-1">Requieren reposición urgente</div>
      </div>
    </div>

    <!-- Search & Filters Bar -->
    <div class="bg-stone-900/80 border border-stone-800 rounded-2xl p-4 shadow-md space-y-3">
      <div class="flex flex-col md:flex-row items-center justify-between gap-3">
        <!-- Search Input -->
        <div class="w-full md:w-80">
          <span class="p-input-icon-left w-full">
            <InputText
              v-model="search"
              placeholder="Buscar por nombre, código o proveedor..."
              class="w-full text-xs"
            />
          </span>
        </div>

        <!-- Filter Controls -->
        <div class="flex flex-wrap items-center gap-2 w-full md:w-auto justify-end">
          <!-- Tipo Tabs -->
          <div class="inline-flex bg-stone-950 rounded-lg p-0.5 border border-stone-800">
            <button
              type="button"
              class="px-3 py-1.5 rounded-md text-xs font-semibold transition"
              :class="tipoFiltro === 'Todos' ? 'bg-amber-500 text-stone-950 shadow' : 'text-stone-400 hover:text-stone-200'"
              @click="tipoFiltro = 'Todos'"
            >
              Todos
            </button>
            <button
              type="button"
              class="px-3 py-1.5 rounded-md text-xs font-semibold transition"
              :class="tipoFiltro === 'Directo' ? 'bg-amber-500 text-stone-950 shadow' : 'text-stone-400 hover:text-stone-200'"
              @click="tipoFiltro = 'Directo'"
            >
              Directos
            </button>
            <button
              type="button"
              class="px-3 py-1.5 rounded-md text-xs font-semibold transition"
              :class="tipoFiltro === 'Indirecto' ? 'bg-amber-500 text-stone-950 shadow' : 'text-stone-400 hover:text-stone-200'"
              @click="tipoFiltro = 'Indirecto'"
            >
              Indirectos
            </button>
          </div>

          <!-- Category Dropdown -->
          <Dropdown
            v-model="categoriaFiltro"
            :options="categoriasDisponibles"
            class="text-xs w-44"
          />

          <!-- Low Stock Toggle -->
          <button
            type="button"
            class="px-3 py-1.5 rounded-lg text-xs font-semibold border transition flex items-center gap-1.5"
            :class="soloBajoStock ? 'bg-red-950/80 text-red-300 border-red-500/50' : 'bg-stone-950 text-stone-400 border-stone-800 hover:text-stone-200'"
            @click="soloBajoStock = !soloBajoStock"
          >
            <span>⚠️ Solo Bajo Stock</span>
            <span v-if="insumosCriticosCount" class="px-1.5 py-0.2 rounded-full bg-red-500 text-white text-[10px] font-bold">
              {{ insumosCriticosCount }}
            </span>
          </button>
        </div>
      </div>
    </div>

    <!-- Data Table -->
    <div class="bg-stone-900/80 border border-stone-800 rounded-2xl overflow-hidden shadow-xl">
      <div class="overflow-x-auto">
        <table class="w-full text-left text-xs border-collapse">
          <thead>
            <tr class="border-b border-stone-800 text-stone-400 bg-stone-950/60 uppercase tracking-wider font-semibold">
              <th class="py-3 px-3.5">Código / Insumo</th>
              <th class="py-3 px-3.5">Tipo & Categoría</th>
              <th class="py-3 px-3.5">Ubicación / Proveedor</th>
              <th class="py-3 px-3.5">Nivel de Stock</th>
              <th class="py-3 px-3.5 text-right">Costo Unitario</th>
              <th class="py-3 px-3.5 text-right">Valor Total</th>
              <th class="py-3 px-3.5 text-center">Ajuste Rápido</th>
              <th class="py-3 px-3.5 text-right">Acciones</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-stone-800/50 text-stone-200">
            <tr v-for="it in insumosFiltrados" :key="it.id" class="hover:bg-stone-800/30">
              <!-- Code & Title -->
              <td class="py-3 px-3.5 max-w-xs">
                <div class="font-bold text-stone-100 text-xs">{{ it.nombre }}</div>
                <div class="font-mono text-[11px] text-amber-400 font-semibold">{{ it.codigo }}</div>
                <div class="text-[11px] text-stone-400 truncate mt-0.5">{{ it.descripcion }}</div>
              </td>

              <!-- Tipo & Category -->
              <td class="py-3 px-3.5">
                <div>
                  <span
                    class="px-2 py-0.5 rounded text-[10px] font-bold"
                    :class="it.tipo === 'Directo' ? 'bg-amber-950/60 text-amber-300 border border-amber-500/30' : 'bg-stone-800 text-stone-300 border border-stone-700'"
                  >
                    {{ it.tipo }}
                  </span>
                </div>
                <div class="text-[11px] text-stone-400 mt-1">{{ it.categoria }}</div>
              </td>

              <!-- Location & Supplier -->
              <td class="py-3 px-3.5">
                <div class="text-stone-200 font-medium">{{ it.ubicacion }}</div>
                <div class="text-[11px] text-stone-400">{{ it.proveedor }}</div>
              </td>

              <!-- Stock Level & Bar -->
              <td class="py-3 px-3.5 min-w-[140px]">
                <div class="flex items-center justify-between font-mono font-bold text-xs">
                  <span :class="it.stock_actual <= it.stock_minimo ? 'text-red-400' : 'text-stone-100'">
                    {{ it.stock_actual }} {{ it.unidad_medida }}
                  </span>
                  <span class="text-[11px] text-stone-400 font-normal">mín {{ it.stock_minimo }} {{ it.unidad_medida }}</span>
                </div>
                <!-- Mini Bar -->
                <div class="w-full bg-stone-800 h-1.5 rounded-full overflow-hidden mt-1.5">
                  <div
                    class="h-full rounded-full"
                    :class="it.stock_actual <= it.stock_minimo ? 'bg-red-500' : 'bg-emerald-400'"
                    :style="{ width: `${Math.min(100, (it.stock_actual / (it.stock_minimo * 2)) * 100)}%` }"
                  />
                </div>
                <div v-if="it.stock_actual <= it.stock_minimo" class="text-[10px] text-red-400 font-bold mt-0.5">
                  ⚠️ REPONER
                </div>
              </td>

              <!-- Unit Cost -->
              <td class="py-3 px-3.5 text-right font-mono">
                {{ formatCOP(it.costo_unitario) }} / {{ it.unidad_medida }}
              </td>

              <!-- Total Value -->
              <td class="py-3 px-3.5 text-right font-mono font-bold text-amber-300">
                {{ formatCOP(it.stock_actual * it.costo_unitario) }}
              </td>

              <!-- Quick Adjustment Buttons -->
              <td class="py-3 px-3.5 text-center">
                <div class="inline-flex items-center bg-stone-950 border border-stone-800 rounded-lg p-0.5">
                  <button
                    type="button"
                    class="w-6 h-6 flex items-center justify-center text-stone-400 hover:text-white hover:bg-stone-800 rounded text-xs transition"
                    title="Restar 1"
                    @click="ajustar(it, -1)"
                  >
                    -
                  </button>
                  <span class="px-1 text-[10px] text-stone-500 font-mono">±1</span>
                  <button
                    type="button"
                    class="w-6 h-6 flex items-center justify-center text-stone-400 hover:text-white hover:bg-stone-800 rounded text-xs transition"
                    title="Sumar 1"
                    @click="ajustar(it, 1)"
                  >
                    +
                  </button>
                </div>
              </td>

              <!-- Action Buttons -->
              <td class="py-3 px-3.5 text-right">
                <div class="flex items-center justify-end gap-1.5">
                  <Button
                    label="+ Compra"
                    icon="pi pi-plus"
                    size="small"
                    severity="warning"
                    outlined
                    class="text-[11px] py-1 px-2 font-semibold"
                    @click="abrirCompra(it)"
                  />
                  <button
                    type="button"
                    class="p-1.5 text-stone-400 hover:text-red-400 rounded transition"
                    title="Eliminar Insumo"
                    @click="eliminar(it)"
                  >
                    <i class="pi pi-trash text-xs" />
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Modals -->
    <NuevoInsumoModal v-model:visible="showNuevoModal" />
    <CompraInsumoModal v-model:visible="showCompraModal" :insumo="insumoSeleccionado" />
    <SugerirOrdenModal v-model:visible="showSugerirModal" />
    <OrdenCompraProveedorModal v-model:visible="showOrdenProveedorModal" />
  </div>
</template>
