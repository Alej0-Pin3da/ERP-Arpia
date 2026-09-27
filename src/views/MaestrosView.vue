<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import type {
  ProveedorRead,
  CanalRead,
  MetodoRead,
  CategoriaRead,
  CategoriaProductoRead,
  UbicacionRead,
  TallaRead,
  ProductoSinTallaRead,
  ParametrosRead,
} from '@/services/api/maestros'
import { useMaestros } from '@/composables/useMaestros'
import ConfirmActionDialog from '@/components/ConfirmActionDialog.vue'
import { showToast } from '@/utils/toast'

import MaestroProveedoresTab from '@/components/maestros/MaestroProveedoresTab.vue'
import MaestroCanalesTab from '@/components/maestros/MaestroCanalesTab.vue'
import MaestroMetodosPagoTab from '@/components/maestros/MaestroMetodosPagoTab.vue'
import MaestroTallasTab from '@/components/maestros/MaestroTallasTab.vue'
import MaestroCategoriasTab from '@/components/maestros/MaestroCategoriasTab.vue'
import MaestroCatProdTab from '@/components/maestros/MaestroCatProdTab.vue'
import MaestroUbicacionesTab from '@/components/maestros/MaestroUbicacionesTab.vue'
import MaestroCosteoTab from '@/components/maestros/MaestroCosteoTab.vue'
import MaestroKitsTab from '@/components/maestros/MaestroKitsTab.vue'
import { listKits, deleteKit, type KitRead } from '@/services/api/kits'

const maestros = useMaestros()

// REAL API state
const proveedoresList = ref<ProveedorRead[]>([])
const canalesList = ref<CanalRead[]>([])
const metodosList = ref<MetodoRead[]>([])
const categoriasList = ref<CategoriaRead[]>([])
const catProdList = ref<CategoriaProductoRead[]>([])
const ubicacionesList = ref<UbicacionRead[]>([])
const tallasList = ref<TallaRead[]>([])
const sinTallaList = ref<ProductoSinTallaRead[]>([])
const parametrosApi = ref<ParametrosRead | null>(null)
const kitsList = ref<KitRead[]>([])

async function cargarDatos(force = false) {
  try {
    const [prov, cat, ub, can, met, tal, sin, par, catprod] = await Promise.all([
      maestros.listProveedores({ limit: 100 }, force),
      maestros.listCategorias({ limit: 100 }, force),
      maestros.listUbicaciones({ limit: 100 }, force),
      maestros.listCanales({ limit: 100 }, force),
      maestros.listMetodosPago({ limit: 100 }, force),
      maestros.listTallas({ limit: 100, sort_by: 'orden' }, force),
      maestros.listProductosSinTalla({ limit: 100 }, force),
      maestros.getParametros(force),
      maestros.listCategoriasProducto({ limit: 100 }, force),
    ])
    proveedoresList.value = (prov.items as unknown as ProveedorRead[]) ?? []
    categoriasList.value = (cat.items as unknown as CategoriaRead[]) ?? []
    catProdList.value = (catprod.items as unknown as CategoriaProductoRead[]) ?? []
    ubicacionesList.value = (ub.items as unknown as UbicacionRead[]) ?? []
    canalesList.value = (can.items as unknown as CanalRead[]) ?? []
    metodosList.value = (met.items as unknown as MetodoRead[]) ?? []
    tallasList.value = (tal.items as unknown as TallaRead[]) ?? []
    sinTallaList.value = (sin.items as unknown as ProductoSinTallaRead[]) ?? []
    parametrosApi.value = par as unknown as ParametrosRead
  } catch {
    // keep previous state on error
  }
}

onMounted(() => {
  void cargarDatos()
  void cargarKits()
})

async function cargarKits() {
  try {
    const r = await listKits({ limit: 100 })
    kitsList.value = r.items ?? []
  } catch {
    // keep previous state on error
  }
}

// Tab active
type TabType = 'proveedores' | 'canales' | 'pagos' | 'categorias' | 'catprod' | 'ubicaciones' | 'costeo' | 'tallas' | 'kits'
const tabActiva = ref<TabType>('proveedores')

// Eliminar genérico
const showEliminarDialog = ref(false)
const eliminarTarget = ref<{ tipo: string; id: number; nombre: string } | null>(null)
const eliminarEnCurso = ref(false)

function solicitarEliminar(target: { tipo: string; id: number; nombre: string }) {
  eliminarTarget.value = target
  showEliminarDialog.value = true
}

async function confirmarEliminar() {
  const t = eliminarTarget.value
  if (!t) return
  eliminarEnCurso.value = true
  try {
    if (t.tipo === 'proveedor') await maestros.removeProveedor(t.id)
    else if (t.tipo === 'canal') await maestros.removeCanal(t.id)
    else if (t.tipo === 'metodo') await maestros.removeMetodo(t.id)
    else if (t.tipo === 'talla') await maestros.removeTalla(t.id)
    else if (t.tipo === 'sintalla') await maestros.removeProductoSinTalla(t.id)
    else if (t.tipo === 'categoria') await maestros.removeCategoria(t.id)
    else if (t.tipo === 'catprod') await maestros.removeCategoriaProducto(t.id)
    else if (t.tipo === 'ubicacion') await maestros.removeUbicacion(t.id)
    else if (t.tipo === 'kit') await deleteKit(t.id)

    if (t.tipo === 'kit') await cargarKits()
    else await cargarDatos(true)
    showToast('info', 'Eliminado', `${t.nombre} eliminado del catálogo.`)
  } catch (e: unknown) {
    const detail = (e as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail
    showToast('error', 'No se pudo eliminar', typeof detail === 'string' ? detail : 'Es posible que tenga registros asociados.')
  } finally {
    eliminarEnCurso.value = false
    eliminarTarget.value = null
    showEliminarDialog.value = false
  }
}

// Stats computadas
const totalProveedores = computed(() => proveedoresList.value.length)
const totalCanales = computed(() => canalesList.value.length)
const totalMetodos = computed(() => metodosList.value.length)
const totalTallas = computed(() => tallasList.value.length)
const totalSinTalla = computed(() => sinTallaList.value.length)
const totalCategorias = computed(() => categoriasList.value.length)
const totalCatProd = computed(() => catProdList.value.length)
const totalUbicaciones = computed(() => ubicacionesList.value.length)
</script>

<template>
  <div class="space-y-6 max-w-7xl mx-auto pb-16">
    <!-- Header -->
    <div class="border-b border-stone-800 pb-5">
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div class="flex items-center gap-2">
            <span class="text-xl">⚙️</span>
            <h1 class="text-2xl font-serif font-bold text-amber-300 tracking-wide">
              Catálogos & Parámetros Maestros
            </h1>
            <span class="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-950/80 text-amber-300 border border-amber-800/80 font-bold uppercase">
              CRUD Activo
            </span>
          </div>
          <p class="text-xs text-stone-400 mt-1 font-mono">
            Configuración global de Arpía: Gestión integral (Crear, Editar, Eliminar) de proveedores, canales comerciales, pasarelas, tabla de tallas, merch sin talla, colecciones y tarifas de costeo.
          </p>
        </div>

        <!-- Quick Metrics Pill -->
        <div class="flex items-center gap-2 overflow-x-auto text-xs font-mono">
          <div class="bg-stone-900 border border-stone-800 rounded-lg px-3 py-1.5 flex items-center gap-2 text-stone-300">
            <span class="w-2 h-2 rounded-full bg-amber-400"></span>
            <span>Proveedores: <strong class="text-amber-300">{{ totalProveedores }}</strong></span>
          </div>
          <div class="bg-stone-900 border border-stone-800 rounded-lg px-3 py-1.5 flex items-center gap-2 text-stone-300">
            <span class="w-2 h-2 rounded-full bg-purple-400"></span>
            <span>Tallas Estándar: <strong class="text-purple-300">{{ totalTallas }}</strong></span>
          </div>
          <div class="bg-stone-900 border border-stone-800 rounded-lg px-3 py-1.5 flex items-center gap-2 text-stone-300">
            <span class="w-2 h-2 rounded-full bg-emerald-400"></span>
            <span>Sin Talla (Merch): <strong class="text-emerald-300">{{ totalSinTalla }}</strong></span>
          </div>
        </div>
      </div>

      <!-- Navigation Tabs -->
      <div class="flex items-center gap-2 mt-6 overflow-x-auto pb-1 border-b border-stone-800/60 scrollbar-none">
        <button
          id="btn-tab-proveedores"
          @click="tabActiva = 'proveedores'"
          class="px-4 py-2 text-xs font-mono font-medium rounded-t-lg transition-colors flex items-center gap-2 whitespace-nowrap"
          :class="tabActiva === 'proveedores'
            ? 'bg-stone-800 text-amber-300 border-t-2 border-amber-400 shadow-inner'
            : 'text-stone-400 hover:text-stone-200 hover:bg-stone-900/60'"
        >
          <span>🏭</span> Proveedores Textil & Herrajes ({{ totalProveedores }})
        </button>

        <button
          id="btn-tab-canales"
          @click="tabActiva = 'canales'"
          class="px-4 py-2 text-xs font-mono font-medium rounded-t-lg transition-colors flex items-center gap-2 whitespace-nowrap"
          :class="tabActiva === 'canales'
            ? 'bg-stone-800 text-amber-300 border-t-2 border-amber-400 shadow-inner'
            : 'text-stone-400 hover:text-stone-200 hover:bg-stone-900/60'"
        >
          <span>🛍️</span> Canales de Venta ({{ totalCanales }})
        </button>

        <button
          id="btn-tab-pagos"
          @click="tabActiva = 'pagos'"
          class="px-4 py-2 text-xs font-mono font-medium rounded-t-lg transition-colors flex items-center gap-2 whitespace-nowrap"
          :class="tabActiva === 'pagos'
            ? 'bg-stone-800 text-amber-300 border-t-2 border-amber-400 shadow-inner'
            : 'text-stone-400 hover:text-stone-200 hover:bg-stone-900/60'"
        >
          <span>💳</span> Métodos de Pago ({{ totalMetodos }})
        </button>

        <button
          id="btn-tab-tallas"
          @click="tabActiva = 'tallas'"
          class="px-4 py-2 text-xs font-mono font-medium rounded-t-lg transition-colors flex items-center gap-2 whitespace-nowrap"
          :class="tabActiva === 'tallas'
            ? 'bg-stone-800 text-amber-300 border-t-2 border-amber-400 shadow-inner'
            : 'text-stone-400 hover:text-stone-200 hover:bg-stone-900/60'"
        >
          <span>📐</span> Matriz de Tallas & Sin Talla ({{ totalTallas + totalSinTalla }})
        </button>

        <button
          id="btn-tab-categorias"
          @click="tabActiva = 'categorias'"
          class="px-4 py-2 text-xs font-mono font-medium rounded-t-lg transition-colors flex items-center gap-2 whitespace-nowrap"
          :class="tabActiva === 'categorias'
            ? 'bg-stone-800 text-amber-300 border-t-2 border-amber-400 shadow-inner'
            : 'text-stone-400 hover:text-stone-200 hover:bg-stone-900/60'"
        >
          <span>👗</span> Familias de Colección ({{ totalCategorias }})
        </button>

        <button
          id="btn-tab-catprod"
          @click="tabActiva = 'catprod'"
          class="px-4 py-2 text-xs font-mono font-medium rounded-t-lg transition-colors flex items-center gap-2 whitespace-nowrap"
          :class="tabActiva === 'catprod'
            ? 'bg-stone-800 text-amber-300 border-t-2 border-amber-400 shadow-inner'
            : 'text-stone-400 hover:text-stone-200 hover:bg-stone-900/60'"
        >
          <span>🏷️</span> Categorías & Líneas ({{ totalCatProd }})
        </button>

        <button
          id="btn-tab-ubicaciones"
          @click="tabActiva = 'ubicaciones'"
          class="px-4 py-2 text-xs font-mono font-medium rounded-t-lg transition-colors flex items-center gap-2 whitespace-nowrap"
          :class="tabActiva === 'ubicaciones'
            ? 'bg-stone-800 text-amber-300 border-t-2 border-amber-400 shadow-inner'
            : 'text-stone-400 hover:text-stone-200 hover:bg-stone-900/60'"
        >
          <span>📍</span> Ubicaciones Taller ({{ totalUbicaciones }})
        </button>

        <button
          id="btn-tab-costeo"
          @click="tabActiva = 'costeo'"
          class="px-4 py-2 text-xs font-mono font-medium rounded-t-lg transition-colors flex items-center gap-2 whitespace-nowrap"
          :class="tabActiva === 'costeo'
            ? 'bg-stone-800 text-amber-300 border-t-2 border-amber-400 shadow-inner'
            : 'text-stone-400 hover:text-stone-200 hover:bg-stone-900/60'"
        >
          <span>⚖️</span> Tarifas de Costeo & Mano de Obra
        </button>

        <button
          id="btn-tab-kits"
          @click="tabActiva = 'kits'"
          class="px-4 py-2 text-xs font-mono font-medium rounded-t-lg transition-colors flex items-center gap-2 whitespace-nowrap"
          :class="tabActiva === 'kits'
            ? 'bg-stone-800 text-amber-300 border-t-2 border-amber-400 shadow-inner'
            : 'text-stone-400 hover:text-stone-200 hover:bg-stone-900/60'"
        >
          <span>📦</span> Kits & Cajas ({{ kitsList.length }})
        </button>
      </div>
    </div>

    <!-- Active Tab Components -->
    <MaestroProveedoresTab
      v-if="tabActiva === 'proveedores'"
      :proveedores="proveedoresList"
      @actualizado="cargarDatos(true)"
      @solicitar-eliminar="solicitarEliminar"
    />

    <MaestroCanalesTab
      v-else-if="tabActiva === 'canales'"
      :canales="canalesList"
      @actualizado="cargarDatos(true)"
      @solicitar-eliminar="solicitarEliminar"
    />

    <MaestroMetodosPagoTab
      v-else-if="tabActiva === 'pagos'"
      :metodos="metodosList"
      @actualizado="cargarDatos(true)"
      @solicitar-eliminar="solicitarEliminar"
    />

    <MaestroTallasTab
      v-else-if="tabActiva === 'tallas'"
      :tallas="tallasList"
      :sin-talla="sinTallaList"
      @actualizado="cargarDatos(true)"
      @solicitar-eliminar="solicitarEliminar"
    />

    <MaestroCategoriasTab
      v-else-if="tabActiva === 'categorias'"
      :categorias="categoriasList"
      @actualizado="cargarDatos(true)"
      @solicitar-eliminar="solicitarEliminar"
    />

    <MaestroCatProdTab
      v-else-if="tabActiva === 'catprod'"
      :cat-prod-list="catProdList"
      @actualizado="cargarDatos(true)"
      @solicitar-eliminar="solicitarEliminar"
    />

    <MaestroUbicacionesTab
      v-else-if="tabActiva === 'ubicaciones'"
      :ubicaciones="ubicacionesList"
      @actualizado="cargarDatos(true)"
      @solicitar-eliminar="solicitarEliminar"
    />

    <MaestroCosteoTab
      v-else-if="tabActiva === 'costeo'"
      :parametros="parametrosApi"
      @actualizado="parametrosApi = $event"
    />

    <MaestroKitsTab
      v-else-if="tabActiva === 'kits'"
      :kits="kitsList"
      @actualizado="cargarKits()"
      @solicitar-eliminar="solicitarEliminar"
    />

    <!-- Global Delete Confirmation Dialog -->
    <ConfirmActionDialog
      :visible="showEliminarDialog"
      title="Confirmar Eliminación de Catálogo"
      :message="`¿Estás seguro de que deseás eliminar '${eliminarTarget?.nombre}'? Esta acción no se puede deshacer.`"
      confirm-label="Eliminar Definitivamente"
      :loading="eliminarEnCurso"
      @confirm="confirmarEliminar"
      @cancel="showEliminarDialog = false"
    />
  </div>
</template>
