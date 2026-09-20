<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import type {
  ProveedorRead,
  CanalRead,
  MetodoRead,
  CategoriaRead,
  UbicacionRead,
  TallaRead,
  ProductoSinTallaRead,
  ParametrosRead,
} from '@/services/api/maestros'
import { useMaestros } from '@/composables/useMaestros'
import ConfirmActionDialog from '@/components/ConfirmActionDialog.vue'
import InputNumber from 'primevue/inputnumber'
import { showToast } from '@/utils/toast'

const maestros = useMaestros()

// REAL API state (persists via backend)
const proveedoresList = ref<ProveedorRead[]>([])
const canalesList = ref<CanalRead[]>([])
const metodosList = ref<MetodoRead[]>([])
const categoriasList = ref<CategoriaRead[]>([])
const ubicacionesList = ref<UbicacionRead[]>([])
const tallasList = ref<TallaRead[]>([])
const sinTallaList = ref<ProductoSinTallaRead[]>([])
const parametrosApi = ref<ParametrosRead | null>(null)

// Defaults when the backend has no parametros row yet.
const PARAMETROS_COSTEO_DEFAULT: ParametrosRead = {
  costo_minuto_costura: 280,
  costo_minuto_energia: 0,
  costo_hora_patronaje: 22000,
  margen_meta_global_pct: 65,
  desperdicio_textil_default_pct: 12,
  iva_regimen_pct: 0,
  distribucion_reinversion_pct: 40,
  reparto_margara_pct: 30,
  reparto_valqui_pct: 30,
} as ParametrosRead
const parametrosData = computed(() => (parametrosApi.value ?? PARAMETROS_COSTEO_DEFAULT))

function sanitizeProveedorPayload(form: Record<string, unknown>): Record<string, unknown> {
  const out: Record<string, unknown> = {}
  const nombre = String(form.nombre ?? '').trim()
  if (nombre) out.nombre = nombre
  const categoria = String(form.categoria ?? '').trim()
  if (categoria) out.categoria = categoria
  const ciudad = String(form.ciudad ?? '').trim()
  out.ciudad = ciudad || null
  const emailRaw = String(form.email ?? '').trim()
  out.email = emailRaw || null
  const telRaw = String(form.telefono ?? '').trim()
  out.telefono = telRaw || null
  const cal = form.calificacion
  if (cal !== '' && cal !== null && cal !== undefined) {
    const n = Number(cal)
    if (!Number.isNaN(n)) out.calificacion = Math.max(0, Math.min(5, n))
  }
  const tiempo = form.tiempo_entrega_dias
  if (tiempo !== '' && tiempo !== null && tiempo !== undefined) {
    const n = Number(tiempo)
    if (!Number.isNaN(n)) out.tiempo_entrega_dias = Math.max(0, Math.round(n))
  }
  out.activo = form.activo !== false
  const notas = String(form.notas ?? '').trim()
  out.notas = notas || null
  return out
}

function sanitizeCanalPayload(form: Record<string, unknown>): Record<string, unknown> {
  const out: Record<string, unknown> = {}
  const nombre = String(form.nombre ?? '').trim()
  if (nombre) out.nombre = nombre
  let codigo = String((form as any).codigo ?? '').trim()
  if (!codigo && nombre) codigo = nombre.toUpperCase().replace(/\s+/g, '_').replace(/[^A-Z0-9_]/g, '').slice(0,50) || 'CANAL'
  if (codigo) out.codigo = codigo
  const tipoRaw = String(form.tipo ?? '').trim().toUpperCase()
  if (['FISICO','DIGITAL','EVENTO'].includes(tipoRaw)) out.tipo = tipoRaw
  else out.tipo = 'DIGITAL'
  const com = form.comision_pct
  if (com !== '' && com !== null && com !== undefined) {
    const n = Number(com)
    if (!Number.isNaN(n)) out.comision_pct = Math.max(0, Math.min(100, n))
  }
  const costo = (form as any).costo_fijo_mensual
  if (costo !== '' && costo !== null && costo !== undefined) {
    const n = Number(costo)
    if (!Number.isNaN(n)) out.costo_fijo_mensual = Math.max(0, n)
  }
  out.activo = (form as any).activo !== false
  const desc = String((form as any).descripcion ?? '').trim()
  out.descripcion = desc || null
  return out
}

function sanitizeMetodoPayload(form: Record<string, unknown>): Record<string, unknown> {
  const out: Record<string, unknown> = {}
  const nombre = String(form.nombre ?? '').trim()
  if (nombre) out.nombre = nombre
  let codigo = String((form as any).codigo ?? '').trim()
  if (!codigo && nombre) codigo = nombre.toUpperCase().replace(/\s+/g, '_').replace(/[^A-Z0-9_]/g, '').slice(0,50) || 'METODO'
  if (codigo) out.codigo = codigo
  const tipoRaw = String(form.tipo ?? '').trim().toUpperCase()
  if (['TRANSFERENCIA','BILLETERA_DIGITAL','EFECTIVO','PASARELA_DATAFONO'].includes(tipoRaw)) out.tipo = tipoRaw
  else out.tipo = 'TRANSFERENCIA'
  const com = form.comision_pct
  if (com !== '' && com !== null && com !== undefined) {
    const n = Number(com)
    if (!Number.isNaN(n)) out.comision_pct = Math.max(0, Math.min(100, n))
  }
  const tiempo = String(form.tiempo_acreditacion ?? '').trim()
  out.tiempo_acreditacion = tiempo || null
  out.activo = (form as any).activo !== false
  const datos = String((form as any).datos_cuenta ?? '').trim()
  out.datos_cuenta = datos || null
  const desc = String((form as any).descripcion ?? '').trim()
  out.descripcion = desc || null
  return out
}

async function cargarDatos() {
  try {
    const [prov, cat, ub, can, met, tal, sin, par] = await Promise.all([
      maestros.listProveedores({ limit: 100 }),
      maestros.listCategorias({ limit: 100 }),
      maestros.listUbicaciones({ limit: 100 }),
      maestros.listCanales({ limit: 100 }),
      maestros.listMetodosPago({ limit: 100 }),
      maestros.listTallas({ limit: 100, sort_by: 'orden' }),
      maestros.listProductosSinTalla({ limit: 100 }),
      maestros.getParametros(),
    ])
    proveedoresList.value = (prov.items as unknown as ProveedorRead[]) ?? []
    categoriasList.value = (cat.items as unknown as CategoriaRead[]) ?? []
    ubicacionesList.value = (ub.items as unknown as UbicacionRead[]) ?? []
    canalesList.value = (can.items as unknown as CanalRead[]) ?? []
    metodosList.value = (met.items as unknown as MetodoRead[]) ?? []
    tallasList.value = (tal.items as unknown as TallaRead[]) ?? []
    sinTallaList.value = (sin.items as unknown as ProductoSinTallaRead[]) ?? []
    parametrosApi.value = par as unknown as ParametrosRead
    // sync costeo form
    if (par) Object.assign(parametrosForm.value, par)
  } catch {
    // keep previous state on error
  }
}

onMounted(() => {
  void cargarDatos()
})

// Tab active
type TabType = 'proveedores' | 'canales' | 'pagos' | 'categorias' | 'ubicaciones' | 'costeo' | 'tallas'
const tabActiva = ref<TabType>('proveedores')

// ==========================================
// 1. MODAL: PROVEEDOR
// ==========================================
const modalProveedor = ref(false)
const modoEdicionProveedor = ref(false)
const provForm = ref<Partial<ProveedorRead>>({
  nombre: '',
  categoria: 'Telas Principales',
  ciudad: 'Pereira, Risaralda',
  contacto: '',
  telefono: '',
  email: '',
  tiempo_entrega_dias: 2,
  condicion_pago: 'Contado / Transferencia',
  calificacion: 5,
  activo: true,
  notas: '',
})

function abrirNuevoProveedor() {
  modoEdicionProveedor.value = false
  provForm.value = {
    nombre: '',
    categoria: 'Telas Principales',
    ciudad: 'Pereira, Risaralda',
    contacto: '',
    telefono: '',
    email: '',
    tiempo_entrega_dias: 2,
    condicion_pago: 'Contado / Transferencia',
    calificacion: 5,
    activo: true,
    notas: '',
  }
  modalProveedor.value = true
}

function abrirEditarProveedor(p: ProveedorRead) {
  modoEdicionProveedor.value = true
  provForm.value = { ...p }
  modalProveedor.value = true
}

async function guardarProveedor() {
  if (!provForm.value.nombre) {
    showToast('warn', 'Campo requerido', 'Ingresá el nombre del proveedor.')
    return
  }
  const payload = sanitizeProveedorPayload(provForm.value as unknown as Record<string, unknown>)
  try {
    if (modoEdicionProveedor.value && provForm.value.id) await maestros.updateProveedor(provForm.value.id, payload)
    else await maestros.createProveedor(payload)
    await cargarDatos()
    showToast('success', 'Proveedor guardado', `${provForm.value.nombre} guardado correctamente.`)
    modalProveedor.value = false
  } catch (e: unknown) {
    const msg = (e as any)?.response?.data?.detail ?? (e as Error)?.message ?? 'Error al guardar proveedor'
    const detail = Array.isArray(msg) ? msg.map((d: any) => d.msg || JSON.stringify(d)).join(', ') : String(msg)
    showToast('error', 'Error 422', detail)
  }
}

// ==========================================
// 2. MODAL: CANAL DE VENTA
// ==========================================
const modalCanal = ref(false)
const modoEdicionCanal = ref(false)
const canalForm = ref<Partial<CanalRead>>({
  nombre: '',
  tipo: 'DIGITAL',
  comision_pct: 0,
  costo_fijo_mensual: 0,
  activo: true,
  descripcion: '',
})

function abrirNuevoCanal() {
  modoEdicionCanal.value = false
  canalForm.value = {
    nombre: '',
    tipo: 'DIGITAL',
    comision_pct: 0,
    costo_fijo_mensual: 0,
    activo: true,
    descripcion: '',
  }
  modalCanal.value = true
}

function abrirEditarCanal(c: CanalRead) {
  modoEdicionCanal.value = true
  canalForm.value = { ...c }
  modalCanal.value = true
}

async function guardarCanal() {
  if (!canalForm.value.nombre) {
    showToast('warn', 'Campo requerido', 'Ingresá el nombre del canal.')
    return
  }
  const payload = sanitizeCanalPayload(canalForm.value as unknown as Record<string, unknown>)
  try {
    if (modoEdicionCanal.value && canalForm.value.id) await maestros.updateCanal(canalForm.value.id, payload)
    else await maestros.createCanal(payload)
    await cargarDatos()
    showToast('success', 'Canal guardado', `${canalForm.value.nombre} guardado correctamente.`)
    modalCanal.value = false
  } catch (e: unknown) {
    const msg = (e as any)?.response?.data?.detail ?? (e as Error)?.message ?? 'Error al guardar canal'
    const detail = Array.isArray(msg) ? msg.map((d: any) => d.msg || JSON.stringify(d)).join(', ') : String(msg)
    showToast('error', 'Error 422', detail)
  }
}

// ==========================================
// 3. MODAL: MÉTODO DE PAGO
// ==========================================
const modalPago = ref(false)
const modoEdicionPago = ref(false)
const pagoForm = ref<Partial<MetodoRead>>({
  nombre: '',
  tipo: 'TRANSFERENCIA',
  comision_pct: 0,
  tiempo_acreditacion: 'Inmediata',
  activo: true,
  datos_cuenta: '',
})

function abrirNuevoPago() {
  modoEdicionPago.value = false
  pagoForm.value = {
    nombre: '',
    tipo: 'TRANSFERENCIA',
    comision_pct: 0,
    tiempo_acreditacion: 'Inmediata',
    activo: true,
    datos_cuenta: '',
  }
  modalPago.value = true
}

function abrirEditarPago(p: MetodoRead) {
  modoEdicionPago.value = true
  pagoForm.value = { ...p }
  modalPago.value = true
}

async function guardarPago() {
  if (!pagoForm.value.nombre) {
    showToast('warn', 'Campo requerido', 'Ingresá el nombre del método de pago.')
    return
  }
  const payload = sanitizeMetodoPayload(pagoForm.value as unknown as Record<string, unknown>)
  try {
    if (modoEdicionPago.value && pagoForm.value.id) await maestros.updateMetodo(pagoForm.value.id, payload)
    else await maestros.createMetodo(payload)
    await cargarDatos()
    showToast('success', 'Método guardado', `${pagoForm.value.nombre} guardado correctamente.`)
    modalPago.value = false
  } catch (e: unknown) {
    const msg = (e as any)?.response?.data?.detail ?? (e as Error)?.message ?? 'Error al guardar método de pago'
    const detail = Array.isArray(msg) ? msg.map((d: any) => d.msg || JSON.stringify(d)).join(', ') : String(msg)
    showToast('error', 'Error 422', detail)
  }
}

// ==========================================
// 4. MODAL: TALLA ESTÁNDAR
// ==========================================
const modalTalla = ref(false)
const modoEdicionTalla = ref(false)
const tallaForm = ref<Partial<TallaRead>>({
  talla: '',
  busto: '',
  cintura: '',
  cadera: '',
  reduccion_corset: '',
  descripcion: '',
  orden: 1,
  activo: true,
})

function abrirNuevaTalla() {
  modoEdicionTalla.value = false
  tallaForm.value = {
    talla: '',
    busto: '80 – 85 cm',
    cintura: '60 – 65 cm',
    cadera: '85 – 90 cm',
    reduccion_corset: '-5 cm a -7 cm',
    descripcion: 'Nueva talla estándar de confección',
    orden: tallasList.value.length + 1,
    activo: true,
  }
  modalTalla.value = true
}

function abrirEditarTalla(t: TallaRead) {
  modoEdicionTalla.value = true
  tallaForm.value = { ...t }
  modalTalla.value = true
}

async function guardarTalla() {
  if (!tallaForm.value.talla) return
  if (modoEdicionTalla.value && tallaForm.value.id) await maestros.updateTalla(tallaForm.value.id, tallaForm.value as Record<string, unknown>)
  else await maestros.createTalla(tallaForm.value as Record<string, unknown>)
  await cargarDatos()
  modalTalla.value = false
}

// ==========================================
// 5. MODAL: PRODUCTO SIN TALLA
// ==========================================
const modalSinTalla = ref(false)
const modoEdicionSinTalla = ref(false)
const sinTallaForm = ref<Partial<ProductoSinTallaRead>>({
  nombre: '',
  categoria: 'Tote Bags & Bolsos',
  dimensiones: '',
  materiales: '',
  descripcion: '',
  precio_sugerido: 45000,
  activo: true,
})

function abrirNuevoSinTalla() {
  modoEdicionSinTalla.value = false
  sinTallaForm.value = {
    nombre: '',
    categoria: 'Tote Bags & Bolsos',
    dimensiones: '',
    materiales: '',
    descripcion: '',
    precio_sugerido: 40000,
    activo: true,
  }
  modalSinTalla.value = true
}

function abrirEditarSinTalla(p: ProductoSinTallaRead) {
  modoEdicionSinTalla.value = true
  sinTallaForm.value = { ...p }
  modalSinTalla.value = true
}

async function guardarSinTalla() {
  if (!sinTallaForm.value.nombre) return
  if (modoEdicionSinTalla.value && sinTallaForm.value.id) await maestros.updateProductoSinTalla(sinTallaForm.value.id, sinTallaForm.value as Record<string, unknown>)
  else await maestros.createProductoSinTalla(sinTallaForm.value as Record<string, unknown>)
  await cargarDatos()
  modalSinTalla.value = false
}

// ==========================================
// 6. MODAL: FAMILIA / CATEGORÍA COLECCIÓN
// ==========================================
const modalCategoria = ref(false)
const modoEdicionCategoria = ref(false)
const catForm = ref<Partial<CategoriaRead>>({
  nombre: '',
  tipo_talla: 'CON_TALLAS_ESTANDAR',
  descripcion: '',
  margen_meta_pct: 65,
  total_modelos: 0,
  activo: true,
})

function abrirNuevaCategoria() {
  modoEdicionCategoria.value = false
  catForm.value = {
    nombre: '',
    tipo_talla: 'CON_TALLAS_ESTANDAR',
    descripcion: '',
    margen_meta_pct: 65,
    total_modelos: 0,
    activo: true,
  }
  modalCategoria.value = true
}

function abrirEditarCategoria(c: CategoriaRead) {
  modoEdicionCategoria.value = true
  catForm.value = { ...c }
  modalCategoria.value = true
}

async function guardarCategoria() {
  if (!catForm.value.nombre) return
  if (modoEdicionCategoria.value && catForm.value.id) await maestros.updateCategoria(catForm.value.id, catForm.value as Record<string, unknown>)
  else await maestros.createCategoria(catForm.value as Record<string, unknown>)
  await cargarDatos()
  modalCategoria.value = false
}

// ==========================================
// 7. MODAL: UBICACIÓN TALLER
// ==========================================
const modalUbicacion = ref(false)
const modoEdicionUbicacion = ref(false)
const ubForm = ref<Partial<UbicacionRead>>({
  codigo: '',
  nombre: '',
  tipo: 'ROLLOS_TELAS',
  capacidad: '',
  observaciones: '',
})

function abrirNuevaUbicacion() {
  modoEdicionUbicacion.value = false
  ubForm.value = {
    codigo: `UB-${Date.now().toString().slice(-4)}`,
    nombre: '',
    tipo: 'ROLLOS_TELAS',
    capacidad: '20 Unidades',
    observaciones: '',
  }
  modalUbicacion.value = true
}

function abrirEditarUbicacion(u: UbicacionRead) {
  modoEdicionUbicacion.value = true
  ubForm.value = { ...u }
  modalUbicacion.value = true
}

async function guardarUbicacion() {
  if (!ubForm.value.nombre) return
  if (modoEdicionUbicacion.value && ubForm.value.id) await maestros.updateUbicacion(ubForm.value.id, ubForm.value as Record<string, unknown>)
  else await maestros.createUbicacion(ubForm.value as Record<string, unknown>)
  await cargarDatos()
  modalUbicacion.value = false
}

async function eliminarProveedorWrapper(id: number) {
  await maestros.removeProveedor(id); await cargarDatos()
}
async function eliminarCanalWrapper(id: number) {
  await maestros.removeCanal(id); await cargarDatos()
}
async function eliminarMetodoWrapper(id: number) {
  await maestros.removeMetodo(id); await cargarDatos()
}
async function eliminarTallaWrapper(id: number) {
  await maestros.removeTalla(id); await cargarDatos()
}
async function eliminarSinTallaWrapper(id: number) {
  await maestros.removeProductoSinTalla(id); await cargarDatos()
}
async function eliminarCategoriaWrapper(id: number) {
  await maestros.removeCategoria(id); await cargarDatos()
}
async function eliminarUbicacionWrapper(id: number) {
  await maestros.removeUbicacion(id); await cargarDatos()
}

const showEliminarDialog = ref(false)
const eliminarTarget = ref<{ tipo: string; id: number; nombre: string } | null>(null)
const eliminarEnCurso = ref(false)

function solicitarEliminar(tipo: string, id: number, nombre: string) {
  eliminarTarget.value = { tipo, id, nombre }
  showEliminarDialog.value = true
}

async function confirmarEliminar() {
  const t = eliminarTarget.value
  if (!t) return
  eliminarEnCurso.value = true
  try {
    if (t.tipo === 'proveedor') await eliminarProveedorWrapper(t.id)
    else if (t.tipo === 'canal') await eliminarCanalWrapper(t.id)
    else if (t.tipo === 'metodo') await eliminarMetodoWrapper(t.id)
    else if (t.tipo === 'talla') await eliminarTallaWrapper(t.id)
    else if (t.tipo === 'sintalla') await eliminarSinTallaWrapper(t.id)
    else if (t.tipo === 'categoria') await eliminarCategoriaWrapper(t.id)
    else if (t.tipo === 'ubicacion') await eliminarUbicacionWrapper(t.id)
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

// ==========================================
// 8. PARÁMETROS GLOBALES DE COSTEO
// ==========================================
const parametrosForm = ref<ParametrosRead>({ ...PARAMETROS_COSTEO_DEFAULT })
const guardandoParametros = ref(false)
const mensajeParametros = ref('')

const sumaDistribucion = computed(() => {
  return (
    Number(parametrosForm.value.distribucion_reinversion_pct || 0) +
    Number(parametrosForm.value.reparto_margara_pct || 0) +
    Number(parametrosForm.value.reparto_valqui_pct || 0)
  )
})

async function guardarParametros() {
  if (sumaDistribucion.value !== 100) {
    alert(`La suma del reparto de utilidades debe ser exactamente 100% (actualmente suma ${sumaDistribucion.value}%).`)
    return
  }
  guardandoParametros.value = true
  try {
    const updated = await maestros.updateParametros(parametrosForm.value as unknown as Record<string, unknown>)
    parametrosApi.value = updated as unknown as ParametrosRead
    Object.assign(parametrosForm.value, updated)
    mensajeParametros.value = '✓ Parámetros maestros de costeo y márgenes guardados con éxito'
    setTimeout(() => { mensajeParametros.value = '' }, 4000)
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : 'Error al guardar parámetros'
    alert(msg)
  } finally {
    guardandoParametros.value = false
  }
}

function restaurarParametrosDefecto() {
  parametrosForm.value = { ...PARAMETROS_COSTEO_DEFAULT }
}

// ==========================================
// STATS & FILTROS
// ==========================================
const totalProveedores = computed(() => proveedoresList.value.length)
const totalCanales = computed(() => canalesList.value.length)
const totalMetodos = computed(() => metodosList.value.length)
const totalTallas = computed(() => tallasList.value.length)
const totalSinTalla = computed(() => sinTallaList.value.length)
const totalCategorias = computed(() => categoriasList.value.length)
const totalUbicaciones = computed(() => ubicacionesList.value.length)

// Filter for suppliers
const filtroCategoriaProv = ref('TODOS')
const proveedoresFiltrados = computed(() => {
  if (filtroCategoriaProv.value === 'TODOS') return proveedoresList.value
  return proveedoresList.value.filter((p) => p.categoria === filtroCategoriaProv.value)
})

// Format Currency
function formatoCOP(val: number) {
  return new Intl.NumberFormat('es-CO', {
    style: 'currency',
    currency: 'COP',
    maximumFractionDigits: 0,
  }).format(val)
}
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
            Configuración global de Atelier Arpía: Gestión integral (Crear, Editar, Eliminar) de proveedores, canales comerciales, pasarelas, tabla de tallas, merch sin talla, colecciones y tarifas de costeo.
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
      </div>
    </div>

    <!-- TAB 1: PROVEEDORES TEXTIL & HERRAJES -->
    <div v-if="tabActiva === 'proveedores'" class="space-y-4">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-stone-900/50 p-4 rounded-xl border border-stone-800">
        <div>
          <h2 class="text-lg font-serif font-bold text-stone-100">Directorio Oficial de Proveedores</h2>
          <p class="text-xs text-stone-400 font-mono">Fábricas de telas, importadores de herrajes, hilaturas y talleres de serigrafía.</p>
        </div>

        <div class="flex items-center gap-3">
          <select
            id="filtro-categoria-proveedor"
            v-model="filtroCategoriaProv"
            class="bg-stone-950 border border-stone-700 text-stone-200 text-xs rounded-lg px-3 py-2 font-mono focus:border-amber-400 focus:outline-none"
          >
            <option value="TODOS">Todas las Categorías</option>
            <option value="Telas Principales">Telas Principales</option>
            <option value="Herrajes & Corsetería">Herrajes & Corsetería</option>
            <option value="Lonas & Estampación">Lonas & Estampación</option>
            <option value="Hilos & Accesorios">Hilos & Accesorios</option>
          </select>

          <button
            id="btn-nuevo-proveedor"
            @click="abrirNuevoProveedor"
            class="bg-amber-400 hover:bg-amber-300 text-stone-950 font-mono text-xs font-semibold px-3.5 py-2 rounded-lg transition-colors flex items-center gap-1.5 shadow-sm whitespace-nowrap"
          >
            <span>+</span> Nuevo Proveedor
          </button>
        </div>
      </div>

      <!-- Grid of Suppliers -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div
          v-for="prov in proveedoresFiltrados"
          :key="prov.id"
          :id="`card-proveedor-${prov.id}`"
          class="bg-stone-900/60 border border-stone-800 rounded-xl p-4 flex flex-col justify-between hover:border-stone-700 transition-all"
        >
          <div>
            <div class="flex items-start justify-between gap-2">
              <span class="text-[10px] font-mono px-2 py-0.5 rounded bg-stone-800 text-amber-300 border border-stone-700/60">
                {{ prov.categoria }}
              </span>
              <div class="flex items-center gap-1 text-amber-400 text-xs">
                <span>★</span>
                <span class="font-mono font-bold">{{ prov.calificacion }}</span>
              </div>
            </div>

            <h3 class="text-base font-serif font-bold text-stone-100 mt-2.5 flex items-center gap-2">
              {{ prov.nombre }}
            </h3>
            <p class="text-xs text-stone-400 font-mono mt-0.5 flex items-center gap-1">
              <span>📍</span> {{ prov.ciudad }}
            </p>

            <div class="mt-3 bg-stone-950/70 p-2.5 rounded-lg border border-stone-800/80 space-y-1.5 text-xs font-mono">
              <div class="flex justify-between text-stone-300">
                <span class="text-stone-500">Contacto:</span>
                <span class="font-medium text-stone-200">{{ prov.contacto || 'No especificado' }}</span>
              </div>
              <div class="flex justify-between text-stone-300">
                <span class="text-stone-500">Teléfono/WhatsApp:</span>
                <span class="font-medium text-amber-300">{{ prov.telefono || 'Sin registro' }}</span>
              </div>
              <div class="flex justify-between text-stone-300">
                <span class="text-stone-500">Tiempo Entrega:</span>
                <span class="font-medium text-stone-200">{{ prov.tiempo_entrega_dias }} días hábiles</span>
              </div>
              <div class="flex justify-between text-stone-300">
                <span class="text-stone-500">Condición Pago:</span>
                <span class="font-medium text-emerald-400">{{ prov.condicion_pago }}</span>
              </div>
            </div>

            <p v-if="prov.notas" class="text-xs text-stone-400 mt-2.5 italic bg-stone-900/40 p-2 rounded border border-stone-800/50">
              "{{ prov.notas }}"
            </p>
          </div>

          <div class="mt-4 pt-3 border-t border-stone-800 flex items-center justify-between">
            <a
              v-if="prov.telefono"
              :href="`https://wa.me/${(prov.telefono ?? '').replace(/[^0-9]/g, '')}`"
              target="_blank"
              class="text-xs text-emerald-400 hover:text-emerald-300 font-mono flex items-center gap-1"
            >
              <span>💬</span> WhatsApp
            </a>
            <span v-else class="text-xs text-stone-500 font-mono">Sin WhatsApp</span>

            <div class="flex items-center gap-2">
              <button
                :id="`btn-editar-prov-${prov.id}`"
                @click="abrirEditarProveedor(prov)"
                class="text-xs text-stone-400 hover:text-amber-300 font-mono px-2 py-1 bg-stone-800/70 hover:bg-stone-800 rounded border border-stone-700/60 transition-colors"
              >
                Editar
              </button>
              <button
                :id="`btn-eliminar-prov-${prov.id}`"
                @click="solicitarEliminar('proveedor', prov.id, prov.nombre)"
                class="text-xs text-stone-500 hover:text-rose-400 font-mono p-1 transition-colors"
                title="Eliminar Proveedor"
              >
                ✕
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- TAB 2: CANALES DE VENTA -->
    <div v-if="tabActiva === 'canales'" class="space-y-4">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-stone-900/50 p-4 rounded-xl border border-stone-800">
        <div>
          <h2 class="text-lg font-serif font-bold text-stone-100">Canales de Comercialización & Eventos</h2>
          <p class="text-xs text-stone-400 font-mono">Puntos de venta propios, redes sociales, stands en convenciones y boutiques multimarca.</p>
        </div>

        <button
          id="btn-nuevo-canal"
          @click="abrirNuevoCanal"
          class="bg-amber-400 hover:bg-amber-300 text-stone-950 font-mono text-xs font-semibold px-3.5 py-2 rounded-lg transition-colors flex items-center gap-1.5 shadow-sm whitespace-nowrap self-start sm:self-auto"
        >
          <span>+</span> Nuevo Canal
        </button>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div
          v-for="canal in canalesList"
          :key="canal.id"
          :id="`card-canal-${canal.id}`"
          class="bg-stone-900/60 border border-stone-800 rounded-xl p-4 flex flex-col justify-between hover:border-stone-700 transition-all"
        >
          <div>
            <div class="flex items-center justify-between">
              <span
                class="text-[10px] font-mono px-2 py-0.5 rounded uppercase font-bold"
                :class="{
                  'bg-purple-950 text-purple-300 border border-purple-800': canal.tipo === 'EVENTO',
                  'bg-blue-950 text-blue-300 border border-blue-800': canal.tipo === 'DIGITAL',
                  'bg-emerald-950 text-emerald-300 border border-emerald-800': canal.tipo === 'FISICO',
                }"
              >
                {{ canal.tipo }}
              </span>

              <span
                class="text-[10px] font-mono px-2 py-0.5 rounded"
                :class="canal.activo ? 'bg-emerald-950/60 text-emerald-400' : 'bg-stone-800 text-stone-500'"
              >
                {{ canal.activo ? 'Activo' : 'Inactivo' }}
              </span>
            </div>

            <h3 class="text-base font-serif font-bold text-stone-100 mt-2.5">
              {{ canal.nombre }}
            </h3>
            <p class="text-xs text-stone-400 mt-1">
              {{ canal.descripcion }}
            </p>

            <div class="mt-4 bg-stone-950/70 p-3 rounded-lg border border-stone-800 space-y-2 text-xs font-mono">
              <div class="flex justify-between text-stone-300">
                <span class="text-stone-500">Comisión por Venta:</span>
                <span class="font-bold text-amber-300">{{ canal.comision_pct }}%</span>
              </div>
              <div class="flex justify-between text-stone-300">
                <span class="text-stone-500">Costo Fijo / Stand:</span>
                <span class="font-medium text-stone-200">{{ formatoCOP(canal.costo_fijo_mensual) }}</span>
              </div>
            </div>
          </div>

          <div class="mt-4 pt-3 border-t border-stone-800 flex items-center justify-end gap-2">
            <button
              :id="`btn-editar-canal-${canal.id}`"
              @click="abrirEditarCanal(canal)"
              class="text-xs text-stone-400 hover:text-amber-300 font-mono px-2.5 py-1 bg-stone-800/70 hover:bg-stone-800 rounded border border-stone-700/60 transition-colors"
            >
              Editar
            </button>
            <button
              :id="`btn-eliminar-canal-${canal.id}`"
              @click="solicitarEliminar('canal', canal.id, canal.nombre)"
              class="text-xs text-stone-500 hover:text-rose-400 font-mono p-1 transition-colors"
              title="Eliminar Canal"
            >
              ✕
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- TAB 3: MÉTODOS DE PAGO -->
    <div v-if="tabActiva === 'pagos'" class="space-y-4">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-stone-900/50 p-4 rounded-xl border border-stone-800">
        <div>
          <h2 class="text-lg font-serif font-bold text-stone-100">Medios de Pago & Pasarelas</h2>
          <p class="text-xs text-stone-400 font-mono">Configuración de cuentas bancarias, pasarelas Bold/Wompi y comisiones financieras aplicadas.</p>
        </div>

        <button
          id="btn-nuevo-pago"
          @click="abrirNuevoPago"
          class="bg-amber-400 hover:bg-amber-300 text-stone-950 font-mono text-xs font-semibold px-3.5 py-2 rounded-lg transition-colors flex items-center gap-1.5 shadow-sm whitespace-nowrap self-start sm:self-auto"
        >
          <span>+</span> Nuevo Método de Pago
        </button>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div
          v-for="pago in metodosList"
          :key="pago.id"
          :id="`card-pago-${pago.id}`"
          class="bg-stone-900/60 border border-stone-800 rounded-xl p-4 flex flex-col justify-between hover:border-stone-700 transition-all"
        >
          <div>
            <div class="flex items-center justify-between">
              <span class="text-[10px] font-mono px-2 py-0.5 rounded bg-stone-800 text-amber-300 border border-stone-700/60">
                {{ (pago.tipo ?? '').replace('_', ' ') }}
              </span>
              <span
                class="text-[10px] font-mono px-2 py-0.5 rounded"
                :class="pago.activo ? 'bg-emerald-950/60 text-emerald-400' : 'bg-stone-800 text-stone-500'"
              >
                {{ pago.activo ? 'Habilitado' : 'Deshabilitado' }}
              </span>
            </div>

            <h3 class="text-base font-serif font-bold text-stone-100 mt-2.5">
              {{ pago.nombre }}
            </h3>

            <div class="mt-3 bg-stone-950/70 p-3 rounded-lg border border-stone-800 space-y-2 text-xs font-mono">
              <div class="flex justify-between text-stone-300">
                <span class="text-stone-500">Tasa Comisión:</span>
                <span class="font-bold text-amber-300">{{ pago.comision_pct }}%</span>
              </div>
              <div class="flex justify-between text-stone-300">
                <span class="text-stone-500">Acreditación:</span>
                <span class="font-medium text-stone-200">{{ pago.tiempo_acreditacion }}</span>
              </div>
              <div v-if="pago.datos_cuenta" class="pt-1 border-t border-stone-800/80">
                <div class="text-stone-500 text-[11px]">Detalle / Cuenta:</div>
                <div class="text-stone-300 text-[11px] break-words">{{ pago.datos_cuenta }}</div>
              </div>
            </div>
          </div>

          <div class="mt-4 pt-3 border-t border-stone-800 flex items-center justify-end gap-2">
            <button
              :id="`btn-editar-pago-${pago.id}`"
              @click="abrirEditarPago(pago)"
              class="text-xs text-stone-400 hover:text-amber-300 font-mono px-2.5 py-1 bg-stone-800/70 hover:bg-stone-800 rounded border border-stone-700/60 transition-colors"
            >
              Editar
            </button>
            <button
              :id="`btn-eliminar-pago-${pago.id}`"
              @click="solicitarEliminar('metodo', pago.id, pago.nombre)"
              class="text-xs text-stone-500 hover:text-rose-400 font-mono p-1 transition-colors"
              title="Eliminar Método"
            >
              ✕
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- TAB 4: MATRIZ DE TALLAS & PRODUCTOS SIN TALLA (FULL CRUD) -->
    <div v-if="tabActiva === 'tallas'" class="space-y-8">
      <!-- Section 4.1: Standard Sizes Table (CRUD) -->
      <div class="space-y-4">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-stone-900/50 p-4 rounded-xl border border-stone-800">
          <div>
            <h2 class="text-lg font-serif font-bold text-stone-100">Matriz Oficial de Tallas Estándar</h2>
            <p class="text-xs text-stone-400 font-mono mt-0.5">
              Definición y escalado de medidas anatómicas estándar para la corsetería y prendas de Atelier Arpía.
            </p>
          </div>

          <button
            id="btn-nueva-talla"
            @click="abrirNuevaTalla"
            class="bg-amber-400 hover:bg-amber-300 text-stone-950 font-mono text-xs font-semibold px-3.5 py-2 rounded-lg transition-colors flex items-center gap-1.5 shadow-sm whitespace-nowrap self-start sm:self-auto"
          >
            <span>+</span> Nueva Talla Estándar
          </button>
        </div>

        <div class="bg-stone-900/40 border border-stone-800 rounded-xl overflow-hidden shadow-lg">
          <div class="hidden overflow-x-auto md:block">
            <table class="w-full min-w-[760px] text-left text-xs font-mono">
              <thead class="bg-stone-950/80 text-stone-400 uppercase tracking-wider border-b border-stone-800">
                <tr>
                  <th class="py-3 px-4 sticky left-0 z-10 bg-stone-950/95">Talla</th>
                  <th class="py-3 px-4 text-center whitespace-nowrap">Contorno Busto</th>
                  <th class="py-3 px-4 text-center whitespace-nowrap">Contorno Cintura</th>
                  <th class="py-3 px-4 text-center whitespace-nowrap">Contorno Cadera</th>
                  <th class="py-3 px-4 whitespace-nowrap">Reducción Corset</th>
                  <th class="py-3 px-4 min-w-[180px]">Descripción de Silueta</th>
                  <th class="py-3 px-4 text-right whitespace-nowrap">Acciones</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-stone-800/60 text-stone-200">
                <tr
                  v-for="t in tallasList"
                  :key="t.id"
                  class="hover:bg-stone-800/30 transition-colors"
                >
                  <td class="py-3.5 px-4 font-bold text-amber-400 flex items-center gap-2 sticky left-0 z-10 bg-stone-900/95">
                    <span class="w-1.5 h-1.5 rounded-full bg-amber-400"></span>
                    <span>{{ t.talla }}</span>
                  </td>
                  <td class="py-3.5 px-4 whitespace-nowrap">{{ t.busto }}</td>
                  <td class="py-3.5 px-4 whitespace-nowrap">{{ t.cintura }}</td>
                  <td class="py-3.5 px-4 whitespace-nowrap">{{ t.cadera }}</td>
                  <td class="py-3.5 px-4 text-emerald-400 whitespace-nowrap">{{ t.reduccion_corset }}</td>
                  <td class="py-3.5 px-4 text-stone-400 min-w-[180px]">{{ t.descripcion }}</td>
                  <td class="py-3.5 px-4 text-right whitespace-nowrap">
                    <div class="flex items-center justify-end gap-2">
                      <button
                        :id="`btn-editar-talla-${t.id}`"
                        @click="abrirEditarTalla(t)"
                        class="text-[11px] text-stone-300 hover:text-amber-300 font-mono px-2 py-1 bg-stone-800 hover:bg-stone-700 rounded border border-stone-700/70"
                      >
                        Editar
                      </button>
                      <button
                        :id="`btn-eliminar-talla-${t.id}`"
                        @click="solicitarEliminar('talla', t.id, `Talla ${t.talla}`)"
                        class="text-[11px] text-stone-500 hover:text-rose-400 p-1"
                        title="Eliminar Talla"
                      >
                        ✕
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <!-- Mobile cards: same tallasList. No horizontal scroll. -->
          <div class="space-y-3 p-4 md:hidden max-w-full min-w-0">
            <div v-for="t in tallasList" :key="t.id" class="bg-stone-950/70 border border-stone-800 rounded-2xl p-4 space-y-2 min-w-0">
              <div class="flex items-center gap-2">
                <span class="w-1.5 h-1.5 rounded-full bg-amber-400 shrink-0" />
                <div class="font-bold text-sm text-amber-400">Talla {{ t.talla }}</div>
              </div>
              <div class="grid grid-cols-3 gap-2 text-sm">
                <div><div class="text-xs uppercase tracking-wider text-stone-400">Busto</div><div class="font-mono text-stone-100">{{ t.busto }}</div></div>
                <div><div class="text-xs uppercase tracking-wider text-stone-400">Cintura</div><div class="font-mono text-stone-100">{{ t.cintura }}</div></div>
                <div><div class="text-xs uppercase tracking-wider text-stone-400">Cadera</div><div class="font-mono text-stone-100">{{ t.cadera }}</div></div>
              </div>
              <div class="text-sm text-emerald-400">{{ t.reduccion_corset }}</div>
              <div class="text-sm text-stone-400">{{ t.descripcion }}</div>
              <div class="flex gap-2 pt-1">
                <button type="button" class="flex-1 min-h-[40px] rounded-lg bg-stone-800 text-stone-200 text-sm font-semibold" @click="abrirEditarTalla(t)">Editar</button>
                <button type="button" class="min-w-[44px] min-h-[40px] px-3 rounded-lg border border-stone-700 text-stone-500" title="Eliminar Talla" @click="solicitarEliminar('talla', t.id, `Talla ${t.talla}`)">✕</button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Section 4.2: Products Without Size / Merch (CRUD) -->
      <div class="space-y-4">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-stone-900/50 p-4 rounded-xl border border-stone-800">
          <div>
            <h2 class="text-lg font-serif font-bold text-stone-100 flex items-center gap-2">
              <span>👜</span> Catálogo de Formatos Sin Talla (Tote Bags & Merch)
            </h2>
            <p class="text-xs text-stone-400 font-mono mt-0.5">
              Especificaciones de producción, dimensiones y precio base para productos sin requerimiento de calce corporal.
            </p>
          </div>

          <button
            id="btn-nuevo-sintalla"
            @click="abrirNuevoSinTalla"
            class="bg-amber-400 hover:bg-amber-300 text-stone-950 font-mono text-xs font-semibold px-3.5 py-2 rounded-lg transition-colors flex items-center gap-1.5 shadow-sm whitespace-nowrap self-start sm:self-auto"
          >
            <span>+</span> Nuevo Producto Sin Talla
          </button>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div
            v-for="p in sinTallaList"
            :key="p.id"
            :id="`card-sintalla-${p.id}`"
            class="bg-stone-900/60 border border-stone-800 rounded-xl p-4 flex flex-col justify-between hover:border-stone-700 transition-all"
          >
            <div>
              <div class="flex items-center justify-between">
                <span class="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-950/70 text-amber-300 border border-amber-800/80 font-bold">
                  {{ p.categoria }}
                </span>
                <span class="text-xs font-mono text-emerald-400 font-bold">
                  PVP Sugerido: {{ formatoCOP(p.precio_sugerido) }}
                </span>
              </div>

              <h3 class="text-base font-serif font-bold text-stone-100 mt-2.5">
                {{ p.nombre }}
              </h3>
              <p class="text-xs text-stone-400 mt-1">
                {{ p.descripcion }}
              </p>

              <div class="mt-3 bg-stone-950/70 p-3 rounded-lg border border-stone-800 space-y-1.5 text-xs font-mono">
                <div class="flex flex-col sm:flex-row sm:justify-between text-stone-300 gap-0.5">
                  <span class="text-stone-500">Dimensiones:</span>
                  <span class="font-medium text-stone-200 text-right">{{ p.dimensiones }}</span>
                </div>
                <div class="flex flex-col sm:flex-row sm:justify-between text-stone-300 gap-0.5 pt-1 border-t border-stone-800/80">
                  <span class="text-stone-500">Materiales:</span>
                  <span class="font-medium text-stone-200 text-right">{{ p.materiales }}</span>
                </div>
              </div>
            </div>

            <div class="mt-4 pt-3 border-t border-stone-800 flex items-center justify-end gap-2">
              <button
                :id="`btn-editar-sintalla-${p.id}`"
                @click="abrirEditarSinTalla(p)"
                class="text-xs text-stone-400 hover:text-amber-300 font-mono px-2.5 py-1 bg-stone-800/70 hover:bg-stone-800 rounded border border-stone-700/60 transition-colors"
              >
                Editar
              </button>
              <button
                :id="`btn-eliminar-sintalla-${p.id}`"
                @click="solicitarEliminar('sintalla', p.id, p.nombre)"
                class="text-xs text-stone-500 hover:text-rose-400 font-mono p-1 transition-colors"
                title="Eliminar Producto Sin Talla"
              >
                ✕
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- TAB 5: FAMILIAS DE COLECCIÓN (FULL CRUD) -->
    <div v-if="tabActiva === 'categorias'" class="space-y-4">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-stone-900/50 p-4 rounded-xl border border-stone-800">
        <div>
          <h2 class="text-lg font-serif font-bold text-stone-100">Familias & Categorías de Colección</h2>
          <p class="text-xs text-stone-400 font-mono">Líneas de producto, márgenes objetivo de rentabilidad y segmentación por tipo de talla.</p>
        </div>

        <button
          id="btn-nueva-categoria"
          @click="abrirNuevaCategoria"
          class="bg-amber-400 hover:bg-amber-300 text-stone-950 font-mono text-xs font-semibold px-3.5 py-2 rounded-lg transition-colors flex items-center gap-1.5 shadow-sm whitespace-nowrap self-start sm:self-auto"
        >
          <span>+</span> Nueva Familia de Colección
        </button>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div
          v-for="cat in categoriasList"
          :key="cat.id"
          :id="`card-cat-${cat.id}`"
          class="bg-stone-900/60 border border-stone-800 rounded-xl p-4 flex flex-col justify-between hover:border-stone-700 transition-all"
        >
          <div>
            <div class="flex items-center justify-between">
              <span
                class="text-[10px] font-mono px-2 py-0.5 rounded font-bold"
                :class="cat.tipo_talla === 'CON_TALLAS_ESTANDAR'
                  ? 'bg-amber-950 text-amber-300 border border-amber-800'
                  : 'bg-indigo-950 text-indigo-300 border border-indigo-800'"
              >
                {{ cat.tipo_talla === 'CON_TALLAS_ESTANDAR' ? 'Tallas XXS-XL' : 'Sin Talla / Merch' }}
              </span>

              <span class="text-xs font-mono text-emerald-400 font-bold">
                Margen Meta: {{ cat.margen_meta_pct }}%
              </span>
            </div>

            <h3 class="text-base font-serif font-bold text-stone-100 mt-2.5">
              {{ cat.nombre }}
            </h3>
            <p class="text-xs text-stone-400 mt-1">
              {{ cat.descripcion }}
            </p>
          </div>

          <div class="mt-4 pt-3 border-t border-stone-800 flex items-center justify-between text-xs font-mono">
            <span class="text-stone-500">Modelos en Ficha BOM: <strong class="text-stone-300">{{ cat.total_modelos }}</strong></span>
            
            <div class="flex items-center gap-2">
              <button
                :id="`btn-editar-cat-${cat.id}`"
                @click="abrirEditarCategoria(cat)"
                class="text-xs text-stone-400 hover:text-amber-300 font-mono px-2.5 py-1 bg-stone-800/70 hover:bg-stone-800 rounded border border-stone-700/60 transition-colors"
              >
                Editar
              </button>
              <button
                :id="`btn-eliminar-cat-${cat.id}`"
                @click="solicitarEliminar('categoria', cat.id, cat.nombre)"
                class="text-xs text-stone-500 hover:text-rose-400 font-mono p-1 transition-colors"
                title="Eliminar Categoría"
              >
                ✕
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- TAB 6: UBICACIONES FÍSICAS DE ALMACENAMIENTO (FULL CRUD) -->
    <div v-if="tabActiva === 'ubicaciones'" class="space-y-4">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-stone-900/50 p-4 rounded-xl border border-stone-800">
        <div>
          <h2 class="text-lg font-serif font-bold text-stone-100">Ubicaciones Físicas de Almacenamiento</h2>
          <p class="text-xs text-stone-400 font-mono">Gavetas de herrajes, estantes de rollos de tela, percheros de showroom y bodegas auxiliares.</p>
        </div>

        <button
          id="btn-nueva-ubicacion"
          @click="abrirNuevaUbicacion"
          class="bg-amber-400 hover:bg-amber-300 text-stone-950 font-mono text-xs font-semibold px-3.5 py-2 rounded-lg transition-colors flex items-center gap-1.5 shadow-sm whitespace-nowrap self-start sm:self-auto"
        >
          <span>+</span> Nueva Ubicación
        </button>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div
          v-for="ub in ubicacionesList"
          :key="ub.id"
          :id="`card-ub-${ub.id}`"
          class="bg-stone-900/60 border border-stone-800 rounded-xl p-4 flex flex-col justify-between hover:border-stone-700 transition-all"
        >
          <div>
            <div class="flex items-center justify-between">
              <span class="text-[10px] font-mono px-2 py-0.5 rounded bg-stone-800 text-stone-300 font-bold">
                {{ ub.codigo }}
              </span>
              <span class="text-xs font-mono text-amber-400 font-medium">
                Capacidad: {{ ub.capacidad }}
              </span>
            </div>

            <h3 class="text-base font-serif font-bold text-stone-100 mt-2.5">
              {{ ub.nombre }}
            </h3>
            <p class="text-xs text-stone-400 mt-1">
              {{ ub.observaciones }}
            </p>
          </div>

          <div class="mt-4 pt-3 border-t border-stone-800 flex items-center justify-between text-xs font-mono">
            <span class="text-stone-500 text-[11px]">{{ (ub.tipo ?? '').replace('_', ' ') }}</span>

            <div class="flex items-center gap-2">
              <button
                :id="`btn-editar-ub-${ub.id}`"
                @click="abrirEditarUbicacion(ub)"
                class="text-xs text-stone-400 hover:text-amber-300 font-mono px-2.5 py-1 bg-stone-800/70 hover:bg-stone-800 rounded border border-stone-700/60 transition-colors"
              >
                Editar
              </button>
              <button
                :id="`btn-eliminar-ub-${ub.id}`"
                @click="solicitarEliminar('ubicacion', ub.id, ub.nombre || ub.codigo)"
                class="text-xs text-stone-500 hover:text-rose-400 font-mono p-1 transition-colors"
                title="Eliminar Ubicación"
              >
                ✕
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- TAB 7: PARÁMETROS GLOBALES DE COSTEO Y MANO DE OBRA -->
    <div v-if="tabActiva === 'costeo'" class="space-y-6">
      <div class="bg-stone-900/50 p-4 rounded-xl border border-stone-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h2 class="text-lg font-serif font-bold text-stone-100">Tarifas de Mano de Obra & Parámetros de Rentabilidad</h2>
          <p class="text-xs text-stone-400 font-mono">
            Valores base aplicados automáticamente en el Cotizador Rápido de Costura, Fichas de Recetas BOM y Liquidación de Socias.
          </p>
        </div>

        <button
          id="btn-restaurar-defecto"
          type="button"
          @click="restaurarParametrosDefecto"
          class="text-xs text-stone-400 hover:text-stone-200 font-mono px-3 py-1.5 bg-stone-800 hover:bg-stone-700 rounded-lg border border-stone-700 transition-colors self-start sm:self-auto"
        >
          ↺ Restaurar Valores por Defecto
        </button>
      </div>

      <div class="bg-stone-900/60 border border-stone-800 rounded-xl p-6 space-y-6">
        <div v-if="mensajeParametros" class="p-3 rounded-lg bg-emerald-950/80 border border-emerald-800 text-emerald-300 font-mono text-xs flex items-center gap-2">
          {{ mensajeParametros }}
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <!-- Costo minuto costura -->
          <div class="space-y-2">
            <label for="param-minuto-costura" class="block text-xs font-mono text-stone-300">
              Valor Minuto de Confección (COP/min):
            </label>
            <div class="relative">
              <InputNumber
                v-model="parametrosForm.costo_minuto_costura"
                inputId="param-minuto-costura"
                mode="decimal"
                locale="es-CO"
                :min="0"
                :step="10"
                :min-fraction-digits="0"
                :max-fraction-digits="2"
                suffix=" COP"
                class="w-full"
                inputClass="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-stone-100 font-mono text-sm focus:border-amber-400 focus:outline-none"
              />
            </div>
            <p class="text-[11px] text-stone-400">Tarifa por minuto de armado, planchado y colocado de varillas.</p>
          </div>

          <!-- Costo minuto energía -->
          <div class="space-y-2">
            <label for="param-minuto-energia" class="block text-xs font-mono text-stone-300">
              Valor Minuto de Energía (COP/min):
            </label>
            <div class="relative">
              <InputNumber
                v-model="parametrosForm.costo_minuto_energia"
                inputId="param-minuto-energia"
                mode="decimal"
                locale="es-CO"
                :min="0"
                :step="10"
                :min-fraction-digits="0"
                :max-fraction-digits="2"
                suffix=" COP"
                class="w-full"
                inputClass="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-stone-100 font-mono text-sm focus:border-amber-400 focus:outline-none"
              />
            </div>
            <p class="text-[11px] text-stone-400">Tarifa por minuto de energía de maquinaria en costura.</p>
          </div>

          <!-- Costo hora patronaje -->
          <div class="space-y-2">
            <label for="param-hora-patronaje" class="block text-xs font-mono text-stone-300">
              Valor Hora Patronaje & Corte (COP/hora):
            </label>
            <div class="relative">
              <InputNumber
                v-model="parametrosForm.costo_hora_patronaje"
                inputId="param-hora-patronaje"
                mode="decimal"
                locale="es-CO"
                :min="0"
                :step="1000"
                :min-fraction-digits="0"
                :max-fraction-digits="2"
                suffix=" COP"
                class="w-full"
                inputClass="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-stone-100 font-mono text-sm focus:border-amber-400 focus:outline-none"
              />
            </div>
            <p class="text-[11px] text-stone-400">Hora de diseño, digitalización y corte manual de precisión.</p>
          </div>

          <!-- Margen global meta -->
          <div class="space-y-2">
            <label for="param-margen-meta" class="block text-xs font-mono text-stone-300">
              Margen Meta de Utilidad Sugerido (%):
            </label>
            <div class="relative">
              <InputNumber
                v-model="parametrosForm.margen_meta_global_pct"
                inputId="param-margen-meta"
                mode="decimal"
                locale="es-CO"
                :min="0"
                :max="100"
                :step="0.5"
                :min-fraction-digits="0"
                :max-fraction-digits="2"
                suffix=" %"
                class="w-full"
                inputClass="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-stone-100 font-mono text-sm focus:border-amber-400 focus:outline-none"
              />
            </div>
            <p class="text-[11px] text-stone-400">Margen por defecto aplicado en el Cotizador rápido.</p>
          </div>

          <!-- Desperdicio merma textil -->
          <div class="space-y-2">
            <label for="param-desperdicio" class="block text-xs font-mono text-stone-300">
              Factor de Merma / Desperdicio Textil (%):
            </label>
            <div class="relative">
              <InputNumber
                v-model="parametrosForm.desperdicio_textil_default_pct"
                inputId="param-desperdicio"
                mode="decimal"
                locale="es-CO"
                :min="0"
                :max="50"
                :step="0.5"
                :min-fraction-digits="0"
                :max-fraction-digits="2"
                suffix=" %"
                class="w-full"
                inputClass="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-stone-100 font-mono text-sm focus:border-amber-400 focus:outline-none"
              />
            </div>
            <p class="text-[11px] text-stone-400">Porcentaje de tela adicional estimado por mermas en tizado.</p>
          </div>

          <!-- Distribución 40/30/30 Editable -->
          <div class="space-y-2 md:col-span-2">
            <div class="flex items-center justify-between">
              <label class="block text-xs font-mono text-stone-300">
                Regla de Distribución de Utilidades Socias (Debe sumar 100%):
              </label>
              <span
                class="text-xs font-mono font-bold px-2 py-0.5 rounded"
                :class="sumaDistribucion === 100 ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' : 'bg-rose-950 text-rose-400 border border-rose-800'"
              >
                Suma: {{ sumaDistribucion }}%
              </span>
            </div>

            <div class="grid grid-cols-3 gap-3 bg-stone-950 p-4 rounded-lg border border-stone-800 text-xs font-mono">
              <div>
                <label for="param-dist-taller" class="block text-stone-400 mb-1">Fondo Taller (%):</label>
                <InputNumber
                  v-model="parametrosForm.distribucion_reinversion_pct"
                  inputId="param-dist-taller"
                  mode="decimal"
                  locale="es-CO"
                  :min="0"
                  :max="100"
                  :step="0.5"
                  :min-fraction-digits="0"
                  :max-fraction-digits="2"
                  class="w-full"
                  inputClass="w-full bg-stone-900 border border-stone-700 rounded-lg px-2.5 py-1.5 text-amber-300 font-bold focus:border-amber-400 focus:outline-none"
                />
              </div>

              <div>
                <label for="param-dist-margara" class="block text-stone-400 mb-1">Margara (%):</label>
                <InputNumber
                  v-model="parametrosForm.reparto_margara_pct"
                  inputId="param-dist-margara"
                  mode="decimal"
                  locale="es-CO"
                  :min="0"
                  :max="100"
                  :step="0.5"
                  :min-fraction-digits="0"
                  :max-fraction-digits="2"
                  class="w-full"
                  inputClass="w-full bg-stone-900 border border-stone-700 rounded-lg px-2.5 py-1.5 text-stone-200 font-bold focus:border-amber-400 focus:outline-none"
                />
              </div>

              <div>
                <label for="param-dist-valqui" class="block text-stone-400 mb-1">Valqui (%):</label>
                <InputNumber
                  v-model="parametrosForm.reparto_valqui_pct"
                  inputId="param-dist-valqui"
                  mode="decimal"
                  locale="es-CO"
                  :min="0"
                  :max="100"
                  :step="0.5"
                  :min-fraction-digits="0"
                  :max-fraction-digits="2"
                  class="w-full"
                  inputClass="w-full bg-stone-900 border border-stone-700 rounded-lg px-2.5 py-1.5 text-stone-200 font-bold focus:border-amber-400 focus:outline-none"
                />
              </div>
            </div>
            <p class="text-[11px] text-stone-400">Estatuto de reparto mensual de utilidades netas del Atelier.</p>
          </div>
        </div>

        <div class="pt-4 border-t border-stone-800 flex justify-end">
          <button
            id="btn-guardar-parametros"
            @click="guardarParametros"
            :disabled="guardandoParametros || sumaDistribucion !== 100"
            class="bg-amber-400 hover:bg-amber-300 disabled:opacity-50 text-stone-950 font-mono text-xs font-bold px-5 py-2.5 rounded-lg transition-colors flex items-center gap-2 shadow"
          >
            <span>💾</span>
            <span>{{ guardandoParametros ? 'Guardando...' : 'Guardar Parámetros de Costeo' }}</span>
          </button>
        </div>
      </div>
    </div>

    <!-- ========================================== -->
    <!-- MODAL 1: PROVEEDOR (CRUD) -->
    <!-- ========================================== -->
    <div
      v-if="modalProveedor"
      class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm"
    >
      <div class="bg-stone-900 border border-stone-700 rounded-xl max-w-lg w-full p-6 space-y-4 shadow-2xl">
        <div class="flex items-center justify-between border-b border-stone-800 pb-3">
          <h3 class="text-base font-serif font-bold text-amber-300">
            {{ modoEdicionProveedor ? 'Editar Proveedor' : 'Nuevo Proveedor Textil / Insumos' }}
          </h3>
          <button @click="modalProveedor = false" class="text-stone-400 hover:text-stone-200 text-lg">✕</button>
        </div>

        <form @submit.prevent="guardarProveedor" class="space-y-4 text-xs font-mono">
          <div>
            <label class="block text-stone-300 mb-1">Nombre Comercial:</label>
            <input
              id="input-prov-nombre"
              v-model="provForm.nombre"
              required
              class="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-stone-100 focus:border-amber-400 focus:outline-none"
              placeholder="Ej: Atenea Bordados"
            />
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-stone-300 mb-1">Categoría:</label>
              <select
                id="input-prov-cat"
                v-model="provForm.categoria"
                class="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-stone-100 focus:border-amber-400 focus:outline-none"
              >
                <option value="Telas Principales">Telas Principales</option>
                <option value="Herrajes & Corsetería">Herrajes & Corsetería</option>
                <option value="Lonas & Estampación">Lonas & Estampación</option>
                <option value="Hilos & Accesorios">Hilos & Accesorios</option>
              </select>
            </div>
            <div>
              <label class="block text-stone-300 mb-1">Ciudad / Sede:</label>
              <input
                id="input-prov-ciudad"
                v-model="provForm.ciudad"
                class="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-stone-100 focus:border-amber-400 focus:outline-none"
                placeholder="Pereira, Risaralda"
              />
            </div>
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-stone-300 mb-1">Contacto / Asesor:</label>
              <input
                id="input-prov-contacto"
                v-model="provForm.contacto"
                class="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-stone-100 focus:border-amber-400 focus:outline-none"
                placeholder="Nombre del asesor"
              />
            </div>
            <div>
              <label class="block text-stone-300 mb-1">Teléfono / WhatsApp:</label>
              <input
                id="input-prov-tel"
                v-model="provForm.telefono"
                class="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-stone-100 focus:border-amber-400 focus:outline-none"
                placeholder="+57 312 000 0000"
              />
            </div>
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-stone-300 mb-1">Tiempo de Entrega (Días):</label>
              <InputNumber
                v-model="provForm.tiempo_entrega_dias"
                inputId="input-prov-dias"
                mode="decimal"
                locale="es-CO"
                :min="1"
                :step="1"
                :min-fraction-digits="0"
                :max-fraction-digits="0"
                class="w-full"
                inputClass="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-stone-100 focus:border-amber-400 focus:outline-none"
              />
            </div>
            <div>
              <label class="block text-stone-300 mb-1">Condición de Pago:</label>
              <input
                id="input-prov-pago"
                v-model="provForm.condicion_pago"
                class="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-stone-100 focus:border-amber-400 focus:outline-none"
                placeholder="Contado / 30 días"
              />
            </div>
          </div>

          <div>
            <label class="block text-stone-300 mb-1">Notas / Especialidad:</label>
            <textarea
              id="input-prov-notas"
              v-model="provForm.notas"
              rows="2"
              class="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-stone-100 focus:border-amber-400 focus:outline-none"
              placeholder="Detalles sobre insumos específicos o condiciones..."
            ></textarea>
          </div>

          <div class="flex items-center justify-end gap-3 pt-3 border-t border-stone-800">
            <button
              type="button"
              @click="modalProveedor = false"
              class="px-4 py-2 bg-stone-800 text-stone-300 hover:bg-stone-700 rounded-lg"
            >
              Cancelar
            </button>
            <button
              type="submit"
              class="px-4 py-2 bg-amber-400 text-stone-950 font-bold hover:bg-amber-300 rounded-lg shadow"
            >
              Guardar Proveedor
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- ========================================== -->
    <!-- MODAL 2: CANAL DE VENTA (CRUD) -->
    <!-- ========================================== -->
    <div
      v-if="modalCanal"
      class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm"
    >
      <div class="bg-stone-900 border border-stone-700 rounded-xl max-w-md w-full p-6 space-y-4 shadow-2xl">
        <div class="flex items-center justify-between border-b border-stone-800 pb-3">
          <h3 class="text-base font-serif font-bold text-amber-300">
            {{ modoEdicionCanal ? 'Editar Canal de Venta' : 'Nuevo Canal de Venta' }}
          </h3>
          <button @click="modalCanal = false" class="text-stone-400 hover:text-stone-200 text-lg">✕</button>
        </div>

        <form @submit.prevent="guardarCanal" class="space-y-4 text-xs font-mono">
          <div>
            <label class="block text-stone-300 mb-1">Nombre del Canal:</label>
            <input
              id="input-canal-nombre"
              v-model="canalForm.nombre"
              required
              class="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-stone-100 focus:border-amber-400 focus:outline-none"
              placeholder="Ej: Feria NANA Pereira"
            />
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-stone-300 mb-1">Tipo:</label>
              <select
                id="input-canal-tipo"
                v-model="canalForm.tipo"
                class="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-stone-100 focus:border-amber-400 focus:outline-none"
              >
                <option value="DIGITAL">Digital (DM / Web)</option>
                <option value="FISICO">Físico (Showroom / Tienda)</option>
                <option value="EVENTO">Evento (Feria / Convención)</option>
              </select>
            </div>
            <div>
              <label class="block text-stone-300 mb-1">Comisión (%):</label>
              <InputNumber
                v-model="canalForm.comision_pct"
                inputId="input-canal-comision"
                mode="decimal"
                locale="es-CO"
                :min="0"
                :max="100"
                :step="0.1"
                :min-fraction-digits="0"
                :max-fraction-digits="2"
                suffix=" %"
                class="w-full"
                inputClass="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-stone-100 focus:border-amber-400 focus:outline-none"
              />
            </div>
          </div>

          <div>
            <label class="block text-stone-300 mb-1">Costo Fijo / Stand (COP):</label>
            <InputNumber
              v-model="canalForm.costo_fijo_mensual"
              inputId="input-canal-costo-fijo"
              mode="decimal"
              locale="es-CO"
              :min="0"
              :step="10000"
              :min-fraction-digits="0"
              :max-fraction-digits="2"
              suffix=" COP"
              class="w-full"
              inputClass="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-stone-100 focus:border-amber-400 focus:outline-none"
            />
          </div>

          <div>
            <label class="block text-stone-300 mb-1">Descripción:</label>
            <textarea
              id="input-canal-desc"
              v-model="canalForm.descripcion"
              rows="2"
              class="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-stone-100 focus:border-amber-400 focus:outline-none"
              placeholder="Notas y detalles del canal..."
            ></textarea>
          </div>

          <div class="flex items-center justify-end gap-3 pt-3 border-t border-stone-800">
            <button
              type="button"
              @click="modalCanal = false"
              class="px-4 py-2 bg-stone-800 text-stone-300 hover:bg-stone-700 rounded-lg"
            >
              Cancelar
            </button>
            <button
              type="submit"
              class="px-4 py-2 bg-amber-400 text-stone-950 font-bold hover:bg-amber-300 rounded-lg shadow"
            >
              Guardar Canal
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- ========================================== -->
    <!-- MODAL 3: MÉTODO DE PAGO (CRUD) -->
    <!-- ========================================== -->
    <div
      v-if="modalPago"
      class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm"
    >
      <div class="bg-stone-900 border border-stone-700 rounded-xl max-w-md w-full p-6 space-y-4 shadow-2xl">
        <div class="flex items-center justify-between border-b border-stone-800 pb-3">
          <h3 class="text-base font-serif font-bold text-amber-300">
            {{ modoEdicionPago ? 'Editar Método de Pago' : 'Nuevo Método de Pago' }}
          </h3>
          <button @click="modalPago = false" class="text-stone-400 hover:text-stone-200 text-lg">✕</button>
        </div>

        <form @submit.prevent="guardarPago" class="space-y-4 text-xs font-mono">
          <div>
            <label class="block text-stone-300 mb-1">Nombre Comercial:</label>
            <input
              id="input-pago-nombre"
              v-model="pagoForm.nombre"
              required
              class="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-stone-100 focus:border-amber-400 focus:outline-none"
              placeholder="Ej: Transferencia Bancolombia"
            />
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-stone-300 mb-1">Tipo:</label>
              <select
                id="input-pago-tipo"
                v-model="pagoForm.tipo"
                class="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-stone-100 focus:border-amber-400 focus:outline-none"
              >
                <option value="TRANSFERENCIA">Transferencia Bancaria</option>
                <option value="BILLETERA_DIGITAL">Billetera Móvil (Nequi/Davi)</option>
                <option value="EFECTIVO">Efectivo / Caja</option>
                <option value="PASARELA_DATAFONO">Pasarela / Datáfono</option>
              </select>
            </div>
            <div>
              <label class="block text-stone-300 mb-1">Comisión (%):</label>
              <InputNumber
                v-model="pagoForm.comision_pct"
                inputId="input-pago-comision"
                mode="decimal"
                locale="es-CO"
                :min="0"
                :max="100"
                :step="0.01"
                :min-fraction-digits="0"
                :max-fraction-digits="2"
                suffix=" %"
                class="w-full"
                inputClass="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-stone-100 focus:border-amber-400 focus:outline-none"
              />
            </div>
          </div>

          <div>
            <label class="block text-stone-300 mb-1">Tiempo de Acreditación:</label>
            <input
              id="input-pago-tiempo"
              v-model="pagoForm.tiempo_acreditacion"
              class="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-stone-100 focus:border-amber-400 focus:outline-none"
              placeholder="Inmediata / 24 horas"
            />
          </div>

          <div>
            <label class="block text-stone-300 mb-1">Detalle de Cuenta / Llave:</label>
            <input
              id="input-pago-cuenta"
              v-model="pagoForm.datos_cuenta"
              class="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-stone-100 focus:border-amber-400 focus:outline-none"
              placeholder="Número de cuenta, teléfono o link"
            />
          </div>

          <div class="flex items-center justify-end gap-3 pt-3 border-t border-stone-800">
            <button
              type="button"
              @click="modalPago = false"
              class="px-4 py-2 bg-stone-800 text-stone-300 hover:bg-stone-700 rounded-lg"
            >
              Cancelar
            </button>
            <button
              type="submit"
              class="px-4 py-2 bg-amber-400 text-stone-950 font-bold hover:bg-amber-300 rounded-lg shadow"
            >
              Guardar Método
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- ========================================== -->
    <!-- MODAL 4: TALLA ESTÁNDAR (CRUD) -->
    <!-- ========================================== -->
    <div
      v-if="modalTalla"
      class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm"
    >
      <div class="bg-stone-900 border border-stone-700 rounded-xl max-w-md w-full p-6 space-y-4 shadow-2xl">
        <div class="flex items-center justify-between border-b border-stone-800 pb-3">
          <h3 class="text-base font-serif font-bold text-amber-300">
            {{ modoEdicionTalla ? 'Editar Talla Estándar' : 'Nueva Talla Estándar de Confección' }}
          </h3>
          <button @click="modalTalla = false" class="text-stone-400 hover:text-stone-200 text-lg">✕</button>
        </div>

        <form @submit.prevent="guardarTalla" class="space-y-4 text-xs font-mono">
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-stone-300 mb-1">Nombre / Código Talla:</label>
              <input
                id="input-talla-nombre"
                v-model="tallaForm.talla"
                required
                class="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-amber-300 font-bold focus:border-amber-400 focus:outline-none"
                placeholder="Ej: XXL, 3XL, XXS"
              />
            </div>
            <div>
              <label class="block text-stone-300 mb-1">Reducción Corset:</label>
              <input
                id="input-talla-reduccion"
                v-model="tallaForm.reduccion_corset"
                class="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-stone-100 focus:border-amber-400 focus:outline-none"
                placeholder="Ej: -6 cm a -8 cm"
              />
            </div>
          </div>

          <div class="grid grid-cols-3 gap-2">
            <div>
              <label class="block text-stone-300 mb-1 text-[11px]">Busto:</label>
              <input
                id="input-talla-busto"
                v-model="tallaForm.busto"
                class="w-full bg-stone-950 border border-stone-700 rounded-lg px-2 py-1.5 text-stone-100 focus:border-amber-400 focus:outline-none"
                placeholder="86 – 90 cm"
              />
            </div>
            <div>
              <label class="block text-stone-300 mb-1 text-[11px]">Cintura:</label>
              <input
                id="input-talla-cintura"
                v-model="tallaForm.cintura"
                class="w-full bg-stone-950 border border-stone-700 rounded-lg px-2 py-1.5 text-stone-100 focus:border-amber-400 focus:outline-none"
                placeholder="66 – 70 cm"
              />
            </div>
            <div>
              <label class="block text-stone-300 mb-1 text-[11px]">Cadera:</label>
              <input
                id="input-talla-cadera"
                v-model="tallaForm.cadera"
                class="w-full bg-stone-950 border border-stone-700 rounded-lg px-2 py-1.5 text-stone-100 focus:border-amber-400 focus:outline-none"
                placeholder="92 – 96 cm"
              />
            </div>
          </div>

          <div>
            <label class="block text-stone-300 mb-1">Descripción de Silueta:</label>
            <input
              id="input-talla-desc"
              v-model="tallaForm.descripcion"
              class="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-stone-100 focus:border-amber-400 focus:outline-none"
              placeholder="Ej: Silueta intermedia de alta rotación"
            />
          </div>

          <div class="flex items-center justify-end gap-3 pt-3 border-t border-stone-800">
            <button
              type="button"
              @click="modalTalla = false"
              class="px-4 py-2 bg-stone-800 text-stone-300 hover:bg-stone-700 rounded-lg"
            >
              Cancelar
            </button>
            <button
              type="submit"
              class="px-4 py-2 bg-amber-400 text-stone-950 font-bold hover:bg-amber-300 rounded-lg shadow"
            >
              Guardar Talla
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- ========================================== -->
    <!-- MODAL 5: PRODUCTO SIN TALLA (CRUD) -->
    <!-- ========================================== -->
    <div
      v-if="modalSinTalla"
      class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm"
    >
      <div class="bg-stone-900 border border-stone-700 rounded-xl max-w-md w-full p-6 space-y-4 shadow-2xl">
        <div class="flex items-center justify-between border-b border-stone-800 pb-3">
          <h3 class="text-base font-serif font-bold text-amber-300">
            {{ modoEdicionSinTalla ? 'Editar Producto Sin Talla' : 'Nuevo Producto / Formato Sin Talla' }}
          </h3>
          <button @click="modalSinTalla = false" class="text-stone-400 hover:text-stone-200 text-lg">✕</button>
        </div>

        <form @submit.prevent="guardarSinTalla" class="space-y-4 text-xs font-mono">
          <div>
            <label class="block text-stone-300 mb-1">Nombre del Formato / Producto:</label>
            <input
              id="input-sintalla-nombre"
              v-model="sinTallaForm.nombre"
              required
              class="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-stone-100 focus:border-amber-400 focus:outline-none"
              placeholder="Ej: Tote Bag Ilustrada Mini"
            />
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-stone-300 mb-1">Categoría:</label>
              <select
                id="input-sintalla-cat"
                v-model="sinTallaForm.categoria"
                class="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-stone-100 focus:border-amber-400 focus:outline-none"
              >
                <option value="Tote Bags & Bolsos">Tote Bags & Bolsos</option>
                <option value="Accesorios Textiles">Accesorios Textiles</option>
                <option value="Pines & Joyería">Pines & Joyería</option>
                <option value="Merchandising">Merchandising</option>
              </select>
            </div>
            <div>
              <label class="block text-stone-300 mb-1">PVP Sugerido (COP):</label>
              <InputNumber
                v-model="sinTallaForm.precio_sugerido"
                inputId="input-sintalla-precio"
                mode="decimal"
                locale="es-CO"
                :min="0"
                :step="1000"
                :min-fraction-digits="0"
                :max-fraction-digits="2"
                suffix=" COP"
                class="w-full"
                inputClass="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-emerald-400 font-bold focus:border-amber-400 focus:outline-none"
              />
            </div>
          </div>

          <div>
            <label class="block text-stone-300 mb-1">Dimensiones / Medidas Técnicas:</label>
            <input
              id="input-sintalla-dim"
              v-model="sinTallaForm.dimensiones"
              class="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-stone-100 focus:border-amber-400 focus:outline-none"
              placeholder="Ej: 40 cm alto × 35 cm ancho × 8 cm fuelle"
            />
          </div>

          <div>
            <label class="block text-stone-300 mb-1">Materiales & Confección:</label>
            <input
              id="input-sintalla-mat"
              v-model="sinTallaForm.materiales"
              class="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-stone-100 focus:border-amber-400 focus:outline-none"
              placeholder="Ej: Lona cruda 100% algodón 320g"
            />
          </div>

          <div>
            <label class="block text-stone-300 mb-1">Descripción / Uso:</label>
            <textarea
              id="input-sintalla-desc"
              v-model="sinTallaForm.descripcion"
              rows="2"
              class="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-stone-100 focus:border-amber-400 focus:outline-none"
              placeholder="Descripción del formato y canal de preferencia..."
            ></textarea>
          </div>

          <div class="flex items-center justify-end gap-3 pt-3 border-t border-stone-800">
            <button
              type="button"
              @click="modalSinTalla = false"
              class="px-4 py-2 bg-stone-800 text-stone-300 hover:bg-stone-700 rounded-lg"
            >
              Cancelar
            </button>
            <button
              type="submit"
              class="px-4 py-2 bg-amber-400 text-stone-950 font-bold hover:bg-amber-300 rounded-lg shadow"
            >
              Guardar Formato
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- ========================================== -->
    <!-- MODAL 6: CATEGORÍA DE COLECCIÓN (CRUD) -->
    <!-- ========================================== -->
    <div
      v-if="modalCategoria"
      class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm"
    >
      <div class="bg-stone-900 border border-stone-700 rounded-xl max-w-md w-full p-6 space-y-4 shadow-2xl">
        <div class="flex items-center justify-between border-b border-stone-800 pb-3">
          <h3 class="text-base font-serif font-bold text-amber-300">
            {{ modoEdicionCategoria ? 'Editar Familia de Colección' : 'Nueva Familia de Colección' }}
          </h3>
          <button @click="modalCategoria = false" class="text-stone-400 hover:text-stone-200 text-lg">✕</button>
        </div>

        <form @submit.prevent="guardarCategoria" class="space-y-4 text-xs font-mono">
          <div>
            <label class="block text-stone-300 mb-1">Nombre de la Familia:</label>
            <input
              id="input-cat-nombre"
              v-model="catForm.nombre"
              required
              class="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-stone-100 focus:border-amber-400 focus:outline-none"
              placeholder="Ej: Corsetería Overbust de Gala"
            />
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-stone-300 mb-1">Tipo de Talla:</label>
              <select
                id="input-cat-tipo-talla"
                v-model="catForm.tipo_talla"
                class="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-stone-100 focus:border-amber-400 focus:outline-none"
              >
                <option value="CON_TALLAS_ESTANDAR">Con Tallas (XXS-XL)</option>
                <option value="SIN_TALLA_MERCH">Sin Talla / Merch</option>
                <option value="TALLA_UNICA">Talla Única</option>
              </select>
            </div>
            <div>
              <label class="block text-stone-300 mb-1">Margen Meta (%):</label>
              <InputNumber
                v-model="catForm.margen_meta_pct"
                inputId="input-cat-margen"
                mode="decimal"
                locale="es-CO"
                :min="0"
                :max="100"
                :step="0.5"
                :min-fraction-digits="0"
                :max-fraction-digits="2"
                suffix=" %"
                class="w-full"
                inputClass="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-emerald-400 font-bold focus:border-amber-400 focus:outline-none"
              />
            </div>
          </div>

          <div>
            <label class="block text-stone-300 mb-1">Descripción:</label>
            <textarea
              id="input-cat-desc"
              v-model="catForm.descripcion"
              rows="2"
              class="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-stone-100 focus:border-amber-400 focus:outline-none"
              placeholder="Detalles sobre patrones, insumos clave y características..."
            ></textarea>
          </div>

          <div class="flex items-center justify-end gap-3 pt-3 border-t border-stone-800">
            <button
              type="button"
              @click="modalCategoria = false"
              class="px-4 py-2 bg-stone-800 text-stone-300 hover:bg-stone-700 rounded-lg"
            >
              Cancelar
            </button>
            <button
              type="submit"
              class="px-4 py-2 bg-amber-400 text-stone-950 font-bold hover:bg-amber-300 rounded-lg shadow"
            >
              Guardar Familia
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- ========================================== -->
    <!-- MODAL 7: UBICACIÓN TALLER (CRUD) -->
    <!-- ========================================== -->
    <div
      v-if="modalUbicacion"
      class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm"
    >
      <div class="bg-stone-900 border border-stone-700 rounded-xl max-w-md w-full p-6 space-y-4 shadow-2xl">
        <div class="flex items-center justify-between border-b border-stone-800 pb-3">
          <h3 class="text-base font-serif font-bold text-amber-300">
            {{ modoEdicionUbicacion ? 'Editar Ubicación' : 'Nueva Ubicación de Almacenamiento' }}
          </h3>
          <button @click="modalUbicacion = false" class="text-stone-400 hover:text-stone-200 text-lg">✕</button>
        </div>

        <form @submit.prevent="guardarUbicacion" class="space-y-4 text-xs font-mono">
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-stone-300 mb-1">Código Ubicación:</label>
              <input
                id="input-ub-cod"
                v-model="ubForm.codigo"
                required
                class="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-amber-300 font-bold focus:border-amber-400 focus:outline-none"
                placeholder="UB-GAV-H3"
              />
            </div>
            <div>
              <label class="block text-stone-300 mb-1">Tipo:</label>
              <select
                id="input-ub-tipo"
                v-model="ubForm.tipo"
                class="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-stone-100 focus:border-amber-400 focus:outline-none"
              >
                <option value="ROLLOS_TELAS">Rollos de Tela</option>
                <option value="GAVETAS_HERRAJES">Gaveta Herrajes</option>
                <option value="PERCHERO_SHOWROOM">Perchero Showroom</option>
                <option value="ACCESORIOS_BODEGA">Bodega / Merch</option>
              </select>
            </div>
          </div>

          <div>
            <label class="block text-stone-300 mb-1">Nombre Descriptivo:</label>
            <input
              id="input-ub-nom"
              v-model="ubForm.nombre"
              required
              class="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-stone-100 focus:border-amber-400 focus:outline-none"
              placeholder="Ej: Estante Superior Telas Atenea"
            />
          </div>

          <div>
            <label class="block text-stone-300 mb-1">Capacidad Estimada:</label>
            <input
              id="input-ub-cap"
              v-model="ubForm.capacidad"
              class="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-stone-100 focus:border-amber-400 focus:outline-none"
              placeholder="Ej: 30 Rollos / 50 Prendas"
            />
          </div>

          <div>
            <label class="block text-stone-300 mb-1">Observaciones / Insumos que contiene:</label>
            <textarea
              id="input-ub-obs"
              v-model="ubForm.observaciones"
              rows="2"
              class="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-stone-100 focus:border-amber-400 focus:outline-none"
              placeholder="Detalles sobre qué se guarda en esta ubicación..."
            ></textarea>
          </div>

          <div class="flex items-center justify-end gap-3 pt-3 border-t border-stone-800">
            <button
              type="button"
              @click="modalUbicacion = false"
              class="px-4 py-2 bg-stone-800 text-stone-300 hover:bg-stone-700 rounded-lg"
            >
              Cancelar
            </button>
            <button
              type="submit"
              class="px-4 py-2 bg-amber-400 text-stone-950 font-bold hover:bg-amber-300 rounded-lg shadow"
            >
              Guardar Ubicación
            </button>
          </div>
        </form>
      </div>
    </div>

    <ConfirmActionDialog
      v-model:visible="showEliminarDialog"
      titulo="Eliminar maestro"
      mensaje="¿Eliminar este registro maestro? Esta acción no se puede deshacer."
      :detalle="eliminarTarget?.nombre"
      :loading="eliminarEnCurso"
      @confirmar="confirmarEliminar"
    />
  </div>
</template>
