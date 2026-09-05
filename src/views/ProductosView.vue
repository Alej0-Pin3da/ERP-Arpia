<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useProductos } from '@/composables/useProductos'
import { useBom } from '@/composables/useBom'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import { useAtelierStore, type RecetaBOM } from '@/stores/atelier'
import { useMode } from '@/composables/useMode'
import FichaTecnicaModal from '@/components/atelier/FichaTecnicaModal.vue'
import DataSourceBadge from '@/components/DataSourceBadge.vue'
import NuevaRecetaModal from '@/components/atelier/NuevaRecetaModal.vue'
import AsistenteIaModal from '@/components/atelier/AsistenteIaModal.vue'
import { showToast } from '@/utils/toast'

const atelier = useAtelierStore()
const { isMock } = useMode()
const productosApi = useProductos()
const bomApi = useBom()

const search = ref('')
const selectedCategory = ref('Todos los Modelos')
const filtroMargen = ref<'Todos'|'Pérdida'|'Por debajo'|'En meta'|'Alto'>('Todos')
const margenMetaGlobal = ref(35)
const ordenarPor = ref<'nombre'|'precio'|'costo'|'margen'>('nombre')
const ordenarDir = ref<'asc'|'desc'>('asc')

const showFichaModal = ref(false)
const showNuevaModal = ref(false)
const showIaModal = ref(false)
const recetaSeleccionada = ref<RecetaBOM | null>(null)
const recetaEditar = ref<RecetaBOM | null>(null)
const fichaStartEditing = ref(false)

const categorias = [
  'Todos los Modelos',
  'Corsetería',
  'Blusas y Tops',
  'Conjuntos y Sets',
  'Vestidos',
  'Pantalones',
  'Accesorios',
  'Alta Costura',
]

const productosReal = ref<any[]>([])
const bomCounts = ref<Record<number, number>>({})
async function cargarMargenMeta() {
  if (isMock.value) return
  try {
    const { getParametros } = await import('@/services/api/maestros')
    const p = await getParametros()
    margenMetaGlobal.value = Number(p.margen_meta_global_pct ?? 35)
  } catch { /* keep 35 */ }
}

async function cargarProductosReales() {
  if (isMock.value) return
  try {
    const r = await productosApi.list({ limit: 100 })
    productosReal.value = (r.items as any) ?? []
    // Cargar conteo BOM real por producto (no bloquea grilla)
    try {
      const counts = await Promise.all(
        productosReal.value.map(async (p: any) => {
          try {
            const bom = await bomApi.listInsumos(p.id)
            return [p.id, bom.length] as const
          } catch { return [p.id, 0] as const }
        })
      )
      const map: Record<number, number> = {}
      counts.forEach(([id, c]) => { map[id] = c })
      bomCounts.value = map
    } catch { /* ignore BOM counts */ }
  } catch { productosReal.value = [] }
}
onMounted(() => { void cargarProductosReales(); void cargarMargenMeta() })
watch(isMock, () => { void cargarProductosReales(); void cargarMargenMeta() })
const recetasDisplay = computed(() => isMock.value ? (atelier as any).recetas : productosReal.value.map((p: any) => ({
  id: p.id,
  codigo: p.codigo ?? `PRD-${p.id}`,
  nombre: p.nombre,
  tipo_producto_id: p.tipo_producto_id,
  linea: p.linea ?? (p.tipo_producto_id ? `Tipo ${p.tipo_producto_id}` : 'General'),
  descripcion: p.descripcion ?? p.nombre,
  categoria: p.categoria ?? 'General',
  items: [],
  tiempo_confeccion_min: p.tiempo_confeccion_min ?? 60,
  costo_insumos: (() => {
    if (p.costo_insumos != null) return Number(p.costo_insumos)
    const total = Number(p.costos_operativos_fijos ?? 0)
    const mano = Number(p.mano_obra ?? 0)
    const cif = Number(p.cif_energia ?? 0)
    const derived = total - mano - cif
    return derived > 0 ? derived : 0
  })(),
  mano_obra: p.mano_obra != null ? Number(p.mano_obra) : 0,
  cif_energia: p.cif_energia != null ? Number(p.cif_energia) : Number(p.costos_operativos_fijos ?? 0),
  costo_total_unitario: p.costo_insumos != null && p.mano_obra != null && p.cif_energia != null ? Number(p.costo_insumos) + Number(p.mano_obra) + Number(p.cif_energia) : Number(p.costos_operativos_fijos ?? 0),
  precio_venta: Number(p.precio_venta_sugerido ?? 0),
  precio_venta_sugerido: Number(p.precio_venta_sugerido ?? 0),
  costo_estimado_materiales: Number(p.costo_insumos ?? 0),
  tiempo_estimado_confeccion_horas: p.tiempo_confeccion_min ? Math.round(p.tiempo_confeccion_min / 60 * 10)/10 : 1,
  markup_pct: (() => {
    const m = p.markup_pct
    if (m != null && Number(m) !== 0) return Number(m)
    const precio = Number(p.precio_venta_sugerido ?? 0)
    const costo = p.costo_insumos != null && p.mano_obra != null && p.cif_energia != null ? Number(p.costo_insumos) + Number(p.mano_obra) + Number(p.cif_energia) : Number(p.costos_operativos_fijos ?? 0)
    if (precio > 0 && costo > 0) return Math.round(((precio - costo) / precio) * 100)
    return Number(m ?? 0)
  })(),
  recomendaciones_taller: p.recomendaciones_taller ?? '',
  fases: p.fases ?? [],
})))
const recetasFiltradas = computed(() => {
  let list = recetasDisplay.value.filter((r) => {
    const q = search.value.trim().toLowerCase()
    const matchesSearch =
      !q ||
      r.nombre.toLowerCase().includes(q) ||
      r.codigo.toLowerCase().includes(q) ||
      r.descripcion.toLowerCase().includes(q)

    const matchesCat =
      selectedCategory.value === 'Todos los Modelos' ||
      r.categoria === selectedCategory.value

    const m = Number(r.markup_pct ?? 0)
    const meta = Number(margenMetaGlobal.value ?? 35)
    const matchesMargen =
      filtroMargen.value === 'Todos' ||
      (filtroMargen.value === 'Pérdida' && m < 0) ||
      (filtroMargen.value === 'Por debajo' && m >= 0 && m < meta) ||
      (filtroMargen.value === 'En meta' && m >= meta && m <= meta + 25) ||
      (filtroMargen.value === 'Alto' && m > meta + 25)

    return matchesSearch && matchesCat && matchesMargen
  })

  const dir = ordenarDir.value === 'asc' ? 1 : -1
  return [...list].sort((a, b) => {
    if (ordenarPor.value === 'margen') return (Number(a.markup_pct ?? 0) - Number(b.markup_pct ?? 0)) * dir
    if (ordenarPor.value === 'precio') return (Number(a.precio_venta ?? 0) - Number(b.precio_venta ?? 0)) * dir
    if (ordenarPor.value === 'costo') return (Number(a.costo_total_unitario ?? 0) - Number(b.costo_total_unitario ?? 0)) * dir
    return a.nombre.localeCompare(b.nombre) * dir
  })
})

function margenColor(m: number) {
  const meta = Number(margenMetaGlobal.value ?? 35)
  if (m < 0) return 'bg-red-500'
  if (m < meta) return 'bg-amber-500'
  if (m <= meta + 25) return 'bg-emerald-500'
  return 'bg-sky-500'
}

function formatCOP(val: number) {
  return `$${Math.round(val).toLocaleString('es-CO')}`
}

function abrirFicha(r: RecetaBOM) {
  recetaSeleccionada.value = r
  fichaStartEditing.value = false
  showFichaModal.value = true
}

function abrirEditar(r: RecetaBOM) {
  recetaSeleccionada.value = r
  fichaStartEditing.value = true
  showFichaModal.value = true
}

function abrirNueva() {
  recetaEditar.value = null
  showNuevaModal.value = true
}

function handleFichaEditar(r: RecetaBOM) {
  // legacy: now handled inside Ficha directly, keep for compat
  recetaSeleccionada.value = r
  fichaStartEditing.value = true
  showFichaModal.value = true
}

async function handleRecetaGuardada() {
  if (!isMock.value) await cargarProductosReales()
  recetaEditar.value = null
}
async function handleFichaGuardada() {
  if (!isMock.value) await cargarProductosReales()
  fichaStartEditing.value = false
}

async function eliminarReceta(r: RecetaBOM) {
  if (!isMock.value) {
    try {
      await productosApi.remove(r.id)
      showToast('success','Producto eliminado', `${r.nombre} eliminado correctamente.`)
      await cargarProductosReales()
    } catch (e: any) {
      const detail = e?.response?.data?.detail
      const msg = Array.isArray(detail) ? detail.map((d: any) => d.msg ?? JSON.stringify(d)).join('; ') : (detail ?? e?.message ?? 'Error al eliminar')
      showToast('error','Error al eliminar', String(msg))
    }
    return
  }
  const idx = atelier.recetas.findIndex((x) => x.id === r.id)
  if (idx !== -1) {
    atelier.recetas.splice(idx, 1)
    showToast('info', 'Receta eliminada', `${r.nombre} ha sido removida del catálogo.`)
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
            Recetas de Productos & Fichas Técnicas (BOM)
          </h1>
          <span class="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-amber-950/80 text-amber-300 border border-amber-500/30 uppercase tracking-wider">
            {{ recetasDisplay.length }} Modelos
          </span>
          <DataSourceBadge :is-mock="isMock" :source="isMock ? 'atelier.recetas (memoria)' : 'GET /api/v1/productos (Postgres)'" :count="recetasDisplay.length" endpoint="/productos" />
        </div>
        <p class="text-xs sm:text-sm text-stone-400 m-0 max-w-2xl">
          Escandallo de costeo detallado: consumo de insumos directos/indirectos, tiempos de mano de obra y margen sugerido.
        </p>
      </div>

      <div class="flex flex-wrap items-center gap-2">
        <Button
          label="Planilla Google Sheet (Matriz de Corte)"
          icon="pi pi-file-excel"
          size="small"
          severity="secondary"
          outlined
          class="text-xs font-semibold"
          @click="abrirFicha(recetasDisplay[0])"
        />
        <Button
          label="Generar con IA"
          icon="pi pi-sparkles"
          size="small"
          class="p-button-warning text-xs font-semibold"
          @click="showIaModal = true"
        />
        <Button
          label="Nueva Receta Manual"
          icon="pi pi-plus"
          size="small"
          severity="secondary"
          outlined
          class="text-xs font-semibold"
          @click="abrirNueva"
        />
      </div>
    </div>

    <!-- Search & Category Filters -->
    <div class="space-y-3">
      <!-- Search Input -->
      <div class="w-full md:w-96">
        <span class="p-input-icon-left w-full">
          <InputText
            v-model="search"
            placeholder="Buscar recetas por nombre, código o material..."
            class="w-full text-xs"
          />
        </span>
      </div>

      <!-- Category Filter Pills -->
      <div class="flex flex-wrap gap-1.5 pt-1">
        <button
          v-for="cat in categorias"
          :key="cat"
          type="button"
          class="px-3 py-1.5 rounded-lg text-xs font-semibold border transition"
          :class="selectedCategory === cat ? 'bg-amber-500 text-stone-950 border-amber-500 shadow' : 'bg-stone-900 text-stone-400 border-stone-800 hover:text-stone-200 hover:border-stone-700'"
          @click="selectedCategory = cat"
        >
          {{ cat }}
        </button>
      </div>

          <!-- Filtros margen + orden -->
          <div class="flex flex-wrap items-center gap-2 pt-2">
            <span class="text-[11px] font-bold uppercase text-stone-500">Margen:</span>
            <button v-for="f in (['Todos','Pérdida','Por debajo','En meta','Alto'] as const)" :key="f" type="button" class="px-2.5 py-1 rounded-lg text-xs font-semibold border transition" :class="filtroMargen === f ? 'bg-amber-500 text-stone-950 border-amber-500' : 'bg-stone-900 text-stone-400 border-stone-800 hover:text-stone-200'" @click="filtroMargen = f">{{ f }}</button>
            <span class="h-4 w-px bg-stone-800 mx-1"></span>
            <span class="text-[11px] font-bold uppercase text-stone-500">Ordenar:</span>
            <select v-model="ordenarPor" class="bg-stone-900 border border-stone-800 rounded-lg px-2 py-1 text-xs text-stone-300">
              <option value="nombre">Nombre</option>
              <option value="margen">Margen</option>
              <option value="precio">Precio</option>
              <option value="costo">Costo</option>
            </select>
            <button type="button" class="px-2 py-1 rounded-lg bg-stone-900 border border-stone-800 text-xs text-stone-300" @click="ordenarDir = ordenarDir === 'asc' ? 'desc' : 'asc'">{{ ordenarDir === 'asc' ? '↑' : '↓' }}</button>
            <span class="text-xs text-stone-500">{{ recetasFiltradas.length }} / {{ recetasDisplay.length }}</span>
          </div>
        </div>

        <div v-if="!recetasFiltradas.length" class="text-center py-12 bg-stone-900/40 border border-stone-800 rounded-2xl">
      <i class="pi pi-inbox text-3xl text-stone-500 mb-3 block" />
      <p class="text-sm font-bold text-stone-300">Sin modelos registrados en modo {{ isMock ? 'MOCK' : 'REAL' }}</p>
      <p v-if="!isMock" class="text-xs text-stone-400 mt-1">Los datos vienen de <code>GET /api/v1/productos</code>. Creá un producto desde el backend o volvé a <code>VITE_USE_MOCK=true</code>.</p>
    </div>
    <!-- Recipe Cards Grid -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
      <div
        v-for="r in recetasFiltradas"
        :key="r.id"
        class="bg-stone-900/80 border border-stone-800 rounded-2xl p-5 shadow-lg flex flex-col justify-between hover:border-amber-500/40 transition group"
      >
        <!-- Top: Line Badge & Code -->
        <div class="space-y-3">
          <div class="flex items-center justify-between">
            <span class="px-2.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-amber-950/70 text-amber-300 border border-amber-500/30">
              {{ r.linea }}
            </span>
            <span class="font-mono text-xs font-bold text-stone-400">{{ r.codigo }}</span>
          </div>

          <!-- Title & Description -->
          <div>
            <h3 class="text-base font-bold text-stone-100 group-hover:text-amber-300 transition m-0">
              {{ r.nombre }}
            </h3>
            <p class="text-xs text-stone-400 mt-1.5 line-clamp-2 leading-relaxed">
              {{ r.descripcion }}
            </p>
          </div>

          <!-- Metadata Tags -->
          <div class="flex items-center gap-2 pt-1">
            <span class="px-2 py-0.5 rounded bg-stone-950 border border-stone-800 text-[11px] text-stone-300 font-mono">
              🧵 {{ isMock ? r.items.length : (bomCounts[r.id] ?? 0) }} Insumos BOM
            </span>
            <span class="px-2 py-0.5 rounded bg-stone-950 border border-stone-800 text-[11px] text-stone-300 font-mono">
              ⏱️ {{ r.tiempo_confeccion_min ?? '—' }}{{ r.tiempo_confeccion_min ? ' min confección' : '' }}
            </span>
          </div>

          <!-- Cost Breakdown Strip -->
          <div class="bg-stone-950/70 border border-stone-800/80 rounded-xl p-3 space-y-1.5 text-xs">
            <div class="flex justify-between text-stone-400">
              <span>Costo Insumos:</span>
              <span class="font-mono" :class="Number(r.costo_insumos) > 0 ? 'text-stone-200' : 'text-stone-500'">{{ Number(r.costo_insumos) > 0 ? formatCOP(r.costo_insumos) : '—' }}</span>
            </div>
            <div class="flex justify-between text-stone-400">
              <span>Mano de Obra ({{ r.tiempo_confeccion_min ?? '—' }}{{ r.tiempo_confeccion_min ? 'm' : '' }}):</span>
              <span class="font-mono" :class="Number(r.mano_obra) > 0 ? 'text-stone-200' : 'text-stone-500'">{{ Number(r.mano_obra) > 0 ? formatCOP(r.mano_obra) : '—' }}</span>
            </div>
            <div class="flex justify-between font-bold text-stone-200 border-t border-stone-800/80 pt-1">
              <span>Costo Total Unitario:</span>
              <span class="font-mono text-emerald-400">{{ formatCOP(r.costo_total_unitario) }}</span>
            </div>
                            <div class="h-1.5 w-full bg-stone-800 rounded-full overflow-hidden mt-1">
                  <div class="h-full rounded-full transition-all" :class="margenColor(Number(r.markup_pct ?? 0))" :style="{ width: Math.min(Math.max(Number(r.markup_pct ?? 0), 0), 100) + '%' }"></div>
                </div>
                <div class="flex justify-between items-center bg-stone-900/60 p-1.5 rounded">
                   <span class="text-amber-400 font-bold text-[11px]">PRECIO VENTA ({{ r.markup_pct }}%):</span>
                  <span class="font-mono text-sm font-extrabold" :class="Number(r.markup_pct ?? 0) < 0 ? 'text-red-400' : Number(r.markup_pct ?? 0) < 35 ? 'text-amber-300' : 'text-emerald-300'">{{ formatCOP(r.precio_venta) }}</span>
                </div>
              </div>
        </div>

        <!-- Footer Actions -->
        <div class="flex items-center justify-between pt-4 border-t border-stone-800/80 mt-4">
          <Button
            label="Ver Ficha Técnica >"
            text
            class="text-amber-400 p-0 font-bold text-xs hover:underline"
            @click="abrirFicha(r)"
          />
          <div class="flex items-center gap-1">
            <button
              type="button"
              class="text-stone-500 hover:text-amber-400 p-1.5 transition rounded hover:bg-stone-800"
              title="Editar Receta"
              @click="abrirEditar(r)"
            >
              <i class="pi pi-pencil text-xs" />
            </button>
            <button
              type="button"
              class="text-stone-500 hover:text-red-400 p-1.5 transition rounded hover:bg-stone-800"
              title="Eliminar Receta"
              @click="eliminarReceta(r)"
            >
              <i class="pi pi-trash text-xs" />
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Modals -->
    <FichaTecnicaModal v-model:visible="showFichaModal" :receta="recetaSeleccionada" :start-editing="fichaStartEditing" @editar="handleFichaEditar" @guardado="handleFichaGuardada" @update:visible="(v:boolean) => { if(!v) fichaStartEditing = false }" />
    <NuevaRecetaModal v-model:visible="showNuevaModal" :receta="recetaEditar" @receta-creada="handleRecetaGuardada" @receta-actualizada="handleRecetaGuardada" @update:visible="(v:boolean) => { if(!v) recetaEditar = null }" />
    <AsistenteIaModal v-model:visible="showIaModal" />
  </div>
</template>
