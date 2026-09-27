<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useProductos } from '@/composables/useProductos'
import type { ClienteRead } from '@/services/api/clientes'
import { useBom } from '@/composables/useBom'
import { useRouter } from 'vue-router'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Dropdown from 'primevue/dropdown'
import Slider from 'primevue/slider'
import { showToast } from '@/utils/toast'
import { createCotizacion, listCotizaciones, updateCotizacionEstado, type CotizacionRead, type InsumoCotizacionLinea } from '@/services/api/cotizaciones'
import { useClientes } from '@/composables/useClientes'
import { updateProducto, type ProductoRead } from '@/services/api/productos'
import { getParametros } from '@/services/api/maestros'
import { listInsumos, getInsumo, type InsumoRead } from '@/services/api/insumos'
import type { CostoLineaRead } from '@/services/api/bom'

const router = useRouter()
const productosApi = useProductos()
const bomApi = useBom()
const productos = ref<ProductoRead[]>([])
const costoReal = ref<number | null>(null)
const loadingCostoReal = ref(false)
// Líneas base del BOM real (GET /productos/{id}/costo): referencia informativa.
// Los campos editables arrancan con estos valores; lo que se agregue a mano
// son extras de ESTA cotización (empaque especial, urgencia, ajustes).
const lineasBase = ref<CostoLineaRead[]>([])
// Detalle trazable por línea del BOM para la tabla visible (Material | Cant
// BOM | Conversión a m | Precio unit. | Subtotal | Va a).
type DetalleBase = { nombre: string; cant: number; unidad: string; aMetros: number | null; precio: number; subtotal: number; destino: 'Telas' | 'Forro' | 'Avíos' | 'Empaque' }
const detalleBase = ref<DetalleBase[]>([])
// El bloque Base BOM se muestra EXPANDIDO al cargar receta (el usuario no
// registraba el colapsable cerrado).
const baseExpandida = ref(true)
// true = el tiempo NO vino de la receta (default o receta en 0): supuesto.
const tiempoSupuesto = ref(true)
// Motivo cuando la base quedó parcial (maestro sin precio/categoría mapeable):
// telas y avíos NO se pisan; solo tiempo/CIF/margen + bloque de referencia.
const baseParcial = ref<string | null>(null)
async function cargarProductos() {
  try {
    const r = await productosApi.list({ limit: 100 })
    productos.value = r.items ?? []
  } catch { productos.value = [] }
}
onMounted(() => { void cargarProductos(); void cargarClientes(); void cargarHistorial(); void cargarMeta() })

// Meta global de margen (Maestros → parametros-costeo; fallback 35).
// La prenda nueva sin receta usa la meta como default, no un 60 fijo.
const margenMetaGlobal = ref<number>(35)
// Margen heredado de la receta BOM cargada (null = prenda nueva/manual).
const margenHeredado = ref<number | null>(null)
async function cargarMeta() {
  try {
    const p = await getParametros()
    margenMetaGlobal.value = Number(p.margen_meta_global_pct ?? 35)
    if (margenHeredado.value == null && !recetaSeleccionada.value) {
      margenPct.value = Math.round(Number(margenMetaGlobal.value))
    }
  } catch { /* sin backend: se queda en 35 */ }
}

const recetaSeleccionada = ref<number | null>(null)
const nombrePrenda = ref('Bustier Estructurado en Tul y Satén')

// Section 1: Materiales dinámicos (BOM por líneas).
// Cada línea trae su % desperdicio propio; el servidor calcula igual.
// Las líneas del BOM real se vuelcan acá sin condensar (trazabilidad total).
const UNIDADES_INSUMO = ['m', 'cm', 'mm', 'un', 'doc', 'par', 'pza', 'kg', 'yarda']
const insumos = ref<InsumoCotizacionLinea[]>([])
function agregarInsumo() {
  insumos.value.push({ nombre: '', cantidad: 0, precio_unitario: 0, unidad_medida: 'm', desperdicio_pct: 0 })
}
function eliminarInsumo(index: number) {
  insumos.value.splice(index, 1)
}
function subtotalLinea(l: InsumoCotizacionLinea): number {
  return Number(l.cantidad ?? 0) * (1 + Number(l.desperdicio_pct ?? 0) / 100) * Number(l.precio_unitario ?? 0)
}

// Cliente + notas (el modelo los soporta; antes quedaban huérfanos)
const clientesApi = useClientes()
const clienteSeleccionado = ref<number | null>(null)
const observaciones = ref('')
const clientesOptions = ref<{ label: string; value: number | null }[]>([{ label: '-- Sin cliente --', value: null }])
async function cargarClientes() {
  try {
    const r = await clientesApi.list({ limit: 100 })
    clientesOptions.value = [
      { label: '-- Sin cliente --', value: null },
      ...(r.items ?? []).map((c: ClienteRead & { apellido?: string | null }) => ({ label: `${c.nombre} ${c.apellido ?? ''}`.trim(), value: c.id })),
    ]
  } catch { /* sin clientes: se cotiza igual */ }
}

// Historial (el backend lista con filtros; la vista lo ignoraba)
const historial = ref<CotizacionRead[]>([])
const loadingHistorial = ref(false)
async function cargarHistorial() {
  loadingHistorial.value = true
  try {
    const r = await listCotizaciones({ limit: 10 })
    historial.value = r.items ?? []
  } catch { historial.value = [] }
  finally { loadingHistorial.value = false }
}
async function marcarEstado(c: CotizacionRead, estado: 'enviada' | 'aprobada' | 'descartada') {
  try {
    await updateCotizacionEstado(c.id, estado)
    showToast('success', 'Estado actualizado', `${c.codigo ?? 'COT'} → ${estado}`)
    await cargarHistorial()
  } catch {
    showToast('error', 'No se pudo actualizar', 'Revisá la conexión con el backend.')
  }
}

// Section 2: Avíos, Cierres & Empaque
const costoAvios = ref<number>(6500)
const costoEmpaque = ref<number>(4500)

// Estimación de hilos por dimensiones de tela (aproximada y transparente).
// Heurística de taller: ~120 m de hilo por metro lineal de tela+forro
// (overlock + recta + remates). El costo por metro es editable porque
// depende del cono que compre el taller. No se suma sola al total:
// se muestra y se aplica a Avíos con un botón para no duplicar.
const costoHiloMetro = ref<number>(8)
// Metros lineales para la heurística de hilos: suma de líneas con unidad
// de longitud (m/cm/mm); el resto no aporta metros de tela.
const metrosTotalesTela = computed(() => insumos.value.reduce((acc, l) => acc + (aMetros(Number(l.cantidad ?? 0), l.unidad_medida ?? '') ?? 0), 0))
const metrosHiloEstimado = computed(() => Math.round(metrosTotalesTela.value * 120))
const costoHilosEstimado = computed(() => Math.round(metrosHiloEstimado.value * Number(costoHiloMetro.value ?? 0)))
function aplicarEstimacionHilos() {
  costoAvios.value = Number(costoAvios.value ?? 0) + costoHilosEstimado.value
  showToast('success', 'Estimación aplicada', `${metrosHiloEstimado.value} m de hilo ≈ ${formatCOP(costoHilosEstimado.value)} sumados a Avíos.`)
}

// Section 3: Mano de Obra & Costos Fijos
const tiempoConfeccionMin = ref<number>(120)
const tarifaHora = ref<number>(8000)
const costoCif = ref<number>(2000)

// Margin Slider: default = meta global (la carga real llega con cargarMeta()).
// Si hay receta cargada, el margen se hereda de ella (badge informativo).
const margenPct = ref<number>(35)

const recetasOptions = computed(() => {
  return [
    { label: '-- Cargar desde Receta BOM --', value: null },
    ...(productos.value).map((r) => ({
      label: `${r.nombre} (${r.codigo ?? `PRD-${r.id}`})`,
      value: r.id,
    })),
  ]
})

// Conversión a metros: el BOM trae longitudes en cm/mm/m según el insumo
// (ej. tela 23400 cm → 234 m). Unidades no-longitud (un, pza, par, doc…)
// devuelven null: jamás van a metros de tela/forro.
function aMetros(cant: number, unidad: string): number | null {
  const u = (unidad ?? '').trim().toLowerCase()
  if (u === 'cm' || u === 'centimetro' || u === 'centimetros' || u === 'centímetro' || u === 'centímetros') return cant / 100
  if (u === 'mm' || u === 'milimetro' || u === 'milimetros' || u === 'milímetro' || u === 'milímetros') return cant / 1000
  if (u === 'm' || u === 'mt' || u === 'mts' || u === 'metro' || u === 'metros') return cant
  return null
}

// Clasificación de una línea BOM contra el maestro de insumos.
// Categorías reales del maestro: Telas | Herrajes | Empaques | Químicos (+ las
// que cree el taller). No hay categoría "forro": el forro/entretela vive bajo
// Telas y se distingue por nombre. Empaque manda por categoría == Empaques
// (misma regla que el backend en migrate/sales.py); los keywords por nombre
// son fallback documentado, no verdad del maestro.
// Mercería ANTES que tela: elásticos/resortes/cintas se venden por metro pero
// son avíos; la vieja regla "unidad m → tela" los sumaba a los metros de tela.
const MERCERIA_RE = /\b(resortes?|el[aá]sticos?|cauchos?|cintas?|sesgos?|ribetes?|vivos?|cord[oó]n(es)?|cremalleras?|cierres?|bot[oó]n(es)?|broches?|ojales?|hebillas?|hilos?)\b/
type ClaseLinea = 'tela' | 'forro' | 'empaque' | 'avio'
function clasificarLineaBom(m: InsumoRead, nombreFallback: string): ClaseLinea {
  const cat = (m.nombre_categoria ?? '').toLowerCase()
  const nom = ((m.nombre ?? '') || nombreFallback).toLowerCase()
  if (cat.includes('empaque') || /\b(empaque|bolsa|etiqueta|caja|papel|envio|envío)\b/.test(nom)) return 'empaque'
  if (MERCERIA_RE.test(nom)) return 'avio'
  // Tela solo por categoría Telas o nombre (ya no por unidad: ver MERCERIA_RE).
  const esTela = cat.includes('tela') || nom.includes('tela')
  if (esTela) {
    if (nom.includes('forro') || nom.includes('entretela') || nom.includes('lining')) return 'forro'
    return 'tela'
  }
  // Forro cargado con otra categoría pero nombre claro (taller que no usa Telas).
  if (nom.includes('forro') || nom.includes('entretela')) return 'forro'
  return 'avio'
}

async function cargarBaseBom() {
  if (!recetaSeleccionada.value) { costoReal.value = null; lineasBase.value = []; detalleBase.value = []; baseParcial.value = null; return }
  loadingCostoReal.value = true
  try {
    const c = await bomApi.getCosto(recetaSeleccionada.value)
    costoReal.value = Number(c.total ?? 0)
    lineasBase.value = Array.isArray(c.lineas) ? c.lineas : []
  } catch { costoReal.value = null; lineasBase.value = [] }
  finally { loadingCostoReal.value = false }
  await aplicarBaseBom()
}

async function aplicarBaseBom() {
  const productoId = recetaSeleccionada.value
  if (!productoId) return
  baseParcial.value = null
  let bom: { insumo_id: number; cantidad_requerida: number | string; porcentaje_desperdicio: number | string }[]
  try {
    bom = await bomApi.listInsumos(productoId)
  } catch {
    baseParcial.value = 'No se pudo leer el BOM de la receta; se conserva lo manual.'
    return
  }
  if (!bom.length) {
    showToast('info', 'Receta sin BOM', 'La receta no tiene insumos cargados; conservo tus valores manuales.')
    return
  }
  // Maestro para precio (costo_promedio_actual) y categoría: un solo listado
  // + getInsumo puntual para los ids que falten (límite alto, taller chico).
  const ids = [...new Set(bom.map((l) => Number(l.insumo_id)))]
  const maestro = new Map<number, InsumoRead>()
  try {
    const r = await listInsumos({ limit: 500 })
    for (const it of r.items ?? []) maestro.set(Number(it.id), it)
  } catch { /* cae al puntual */ }
  const faltantes = ids.filter((id) => !maestro.has(id))
  if (faltantes.length) {
    const res = await Promise.allSettled(faltantes.map((id) => getInsumo(id)))
    res.forEach((x, i) => { if (x.status === 'fulfilled') maestro.set(faltantes[i], x.value) })
  }
  const sinMaestro = ids.filter((id) => !maestro.has(id))
  if (sinMaestro.length) {
    // Prohibido fakear: sin precio/categoría del maestro no se inventan
    // metros ni precios. Solo tiempo/CIF/margen (ya aplicados) + referencia.
    baseParcial.value = `Base parcial: ${sinMaestro.length} insumo(s) del BOM sin datos en el maestro; telas y avíos quedan manuales.`
    showToast('warn', 'Base BOM parcial', baseParcial.value)
    return
  }
  const num = (v: unknown) => { const n = Number(v); return Number.isFinite(n) ? n : 0 }
  // El BOM se vuelca línea por línea al arreglo dinámico (sin condensar:
  // cada línea conserva cantidad original, precio y % propio). La tabla
  // trazable (detalleBase) sigue mostrando a dónde fue cada línea.
  const lineas: InsumoCotizacionLinea[] = []
  detalleBase.value = []
  for (const l of bom) {
    const m = maestro.get(Number(l.insumo_id))!
    const cant = num(l.cantidad_requerida)
    const d = num(l.porcentaje_desperdicio)
    const precio = num(m.costo_promedio_actual)
    const unidad = (m.unidad_medida ?? '').trim() || 'un'
    let clase = clasificarLineaBom(m, '')
    const efectiva = cant * (1 + d / 100)
    const subtotal = efectiva * precio
    const conv = aMetros(cant, m.unidad_medida ?? '')
    if ((clase === 'tela' || clase === 'forro') && conv == null) {
      // Unidad no-longitud jamás va a metros: se valoriza como avío para no
      // perder la plata (la tabla lo muestra con Va a = Avíos).
      clase = 'avio'
    }
    let destino: DetalleBase['destino'] = 'Avíos'
    if (clase === 'tela') destino = 'Telas'
    else if (clase === 'forro') destino = 'Forro'
    else if (clase === 'empaque') destino = 'Empaque'
    detalleBase.value.push({
      nombre: m.nombre ?? `Insumo ${l.insumo_id}`,
      cant, unidad, aMetros: conv, precio, subtotal, destino,
    })
    lineas.push({
      nombre: m.nombre ?? `Insumo ${l.insumo_id}`,
      cantidad: cant,
      precio_unitario: precio,
      unidad_medida: unidad,
      desperdicio_pct: d,
    })
  }
  // Tela/forro sin precio en el maestro (>0) no dan un ponderado honesto:
  // parcial antes de pisar. Un avío en 0 solo aporta 0, no distorsiona.
  const lineasTelaForroSinPrecio = lineas.filter((x, i) => {
    const dest = detalleBase.value[i]?.destino
    return (dest === 'Telas' || dest === 'Forro') && x.cantidad > 0 && !(x.precio_unitario > 0)
  })
  if (lineasTelaForroSinPrecio.length) {
    baseParcial.value = `Base parcial: ${lineasTelaForroSinPrecio.length} línea(s) de tela/forro sin precio en el maestro; conservo tus materiales.`
    showToast('warn', 'Base BOM parcial', baseParcial.value)
    return
  }
  // Los agregados manuales (avíos/empaque) no se tocan: el BOM ya vive en
  // las líneas; lo manual son extras de esta cotización.
  insumos.value = lineas
  baseExpandida.value = true
  showToast('success', 'Base real cargada', `Desde el BOM: ${lineas.length} líneas de materiales. Lo manual son extras de esta cotización.`)
}

async function onRecetaChange() {
  if (!recetaSeleccionada.value) {
    // Prenda nueva/manual: se limpia lo heredado y el margen vuelve a la meta.
    margenHeredado.value = null
    margenPct.value = Math.round(Number(margenMetaGlobal.value ?? 35))
    costoReal.value = null
    lineasBase.value = []
    detalleBase.value = []
    baseParcial.value = null
    tiempoSupuesto.value = true
    return
  }
  const r = (productos.value).find((x) => x.id === recetaSeleccionada.value)
  if (r) {
    nombrePrenda.value = r.nombre
    // Solo receta: nombre, tiempos, CIF y margen. Tarifa $/hora no existe en la
    // receta (mano_obra es un total, no una tasa): queda manual como siempre.
    // P0-5: la API manda Numeric como string ("83000.0000") y nulls; normalizar
    // con Number() para que InputNumber/slider no queden vacíos.
    // Ceros de receta NO pisan: se conserva el valor actual con aviso.
    const t = r.tiempo_confeccion_min
    if (t == null || Number(t) <= 0) {
      // Fallback: suma de fases estándar (0036) si existe alguna.
      const fases = ['tiempo_corte_min', 'tiempo_costura_min', 'tiempo_acabados_min', 'tiempo_calidad_min']
        .map((k) => Number((r as Record<string, unknown>)[k] ?? 0))
        .filter((n) => Number.isFinite(n) && n > 0)
      if (fases.length) {
        tiempoConfeccionMin.value = fases.reduce((a, b) => a + b, 0)
        tiempoSupuesto.value = false
        showToast('info', 'Tiempo por fases estándar', `La receta no trae tiempo total; sumé fases (${tiempoConfeccionMin.value} min).`)
      } else {
        tiempoSupuesto.value = true
        showToast('warn', 'Tiempo en 0 en la receta', 'La receta trae 0 en tiempo de confección, conservo tu valor.')
      }
    } else {
      tiempoConfeccionMin.value = Number(t)
      tiempoSupuesto.value = false
    }
    const cif = r.cif_energia
    if (cif == null || Number(cif) <= 0) {
      showToast('warn', 'CIF en 0 en la receta', 'La receta trae 0 en CIF, conservo tu valor.')
    } else {
      costoCif.value = Number(cif)
    }
    const m = r.markup_pct
    if (m == null || Number(m) <= 0) {
      showToast('warn', 'Margen en 0 en la receta', 'La receta trae 0 en margen, conservo tu valor.')
      margenHeredado.value = null
    } else {
      margenHeredado.value = Math.round(Number(m))
      margenPct.value = Math.round(Number(m))
    }
  }
  await cargarBaseBom()
}

// Materials: dynamic BOM lines, each with its own waste % (same as backend).
const subtotalMateriales = computed(() => {
  return insumos.value.reduce((acc, l) => acc + subtotalLinea(l), 0)
})

const subtotalAvios = computed(() => {
  return costoAvios.value + costoEmpaque.value
})

const subtotalManoObra = computed(() => {
  return (tiempoConfeccionMin.value / 60) * tarifaHora.value
})

const costoTotalConfeccion = computed(() => {
  return subtotalMateriales.value + subtotalAvios.value + subtotalManoObra.value + costoCif.value
})

const precioVentaSugerido = computed(() => {
  // Regla de margen sincera (misma que el servidor en _calcular):
  // margen normal → costo / (1 - margen); margen ≥100% → ×2.2 fijo;
  // margen que deje menos de 5% de factor → ×2 (tope anti-margen-cero).
  if (margenPct.value >= 100) return costoTotalConfeccion.value * 2.2
  const factor = 1 - (margenPct.value / 100)
  if (factor <= 0.05) return costoTotalConfeccion.value * 2
  return costoTotalConfeccion.value / factor
})

const gananciaNeta = computed(() => {
  return precioVentaSugerido.value - costoTotalConfeccion.value
})

// Piso a meta global (referencia): mismo costo, margen de Maestros (default 35%).
// Solo informativo — el precio lista lo manda el margen del slider/heredado.
const precioAMeta = computed(() => {
  const meta = Number(margenMetaGlobal.value ?? 35)
  if (meta >= 100) return costoTotalConfeccion.value * 2.2
  const factor = 1 - (meta / 100)
  if (factor <= 0.05) return costoTotalConfeccion.value * 2
  return costoTotalConfeccion.value / factor
})

function formatCOP(val: number) {
  return `$${Math.round(val).toLocaleString('es-CO')}`
}

// Cantidades del BOM con unidad original (ej. 23.400 cm): máx 2 decimales.
function fmtCant(val: number) {
  return Number(val ?? 0).toLocaleString('es-CO', { maximumFractionDigits: 2 })
}

// Precio unitario exacto con su unidad (ej. $0,793/cm): sin redondear,
// porque formatCOP redondea a pesos y la tabla mostraba $1 en todo.
function fmtPrecioU(val: number, unidad: string) {
  const p = Number(val ?? 0).toLocaleString('es-CO', { maximumFractionDigits: 3 })
  return `$${p}/${unidad || 'un'}`
}

function onBaseToggle(e: Event) {
  baseExpandida.value = (e.target as HTMLDetailsElement).open
}

function copiarPresupuestoWhatsApp() {
  const nombreCliente = clientesOptions.value.find((c) => c.value === clienteSeleccionado.value)?.label
  const lineas = [
    `✨ *PRESUPUESTO DE CONFECCIÓN • ARPÍA* ✨`,
    ``,
    `👗 *Prenda:* ${nombrePrenda.value}`,
    ...(nombreCliente && clienteSeleccionado.value ? [`👤 *Cliente:* ${nombreCliente}`] : []),
    `🧵 *Tiempo estimado:* ${tiempoConfeccionMin.value} min`,
    `🧷 *Materiales (${insumos.value.length} líneas):* ${formatCOP(subtotalMateriales.value)}`,
    `🧵 *Hilos estimados:* ${metrosHiloEstimado.value} m ≈ ${formatCOP(costoHilosEstimado.value)}`,
    `📦 *Avíos y empaque:* ${formatCOP(subtotalAvios.value)}`,
    `💪 *Mano de obra:* ${formatCOP(subtotalManoObra.value)} · *CIF:* ${formatCOP(costoCif.value)}`,
    `💎 *Valor total:* ${formatCOP(precioVentaSugerido.value)} COP (margen ${margenPct.value}%)`,
    ...(observaciones.value.trim() ? [`📝 ${observaciones.value.trim()}`] : []),
    ``,
    `_Para apartar cupo en el taller requerimos un abono del 50%._ 🖤`,
  ]
  navigator.clipboard.writeText(lineas.join('\n'))
  showToast('success', 'Copiado al Portapapeles', 'El presupuesto con desglose se ha copiado con éxito.')
}

const guardando = ref(false)

async function guardarCotizacion() {
  if (!nombrePrenda.value.trim()) {
    showToast('warn', 'Sin nombre', 'Poné nombre a la prenda antes de guardar.')
    return
  }
  guardando.value = true
  try {
    const lineasValidas = insumos.value
      .filter((l) => l.nombre.trim() && Number(l.cantidad) > 0)
      .map((l) => ({
        nombre: l.nombre.trim(),
        cantidad: Number(l.cantidad),
        precio_unitario: Number(l.precio_unitario ?? 0),
        unidad_medida: l.unidad_medida || 'un',
        desperdicio_pct: Number(l.desperdicio_pct ?? 0),
      }))
    if (lineasValidas.length < insumos.value.length) {
      showToast('info', 'Líneas incompletas', 'Las líneas sin nombre o con cantidad 0 no se guardan.')
    }
    const saved = await createCotizacion({
      producto_id: recetaSeleccionada.value,
      cliente_id: clienteSeleccionado.value,
      nombre_prenda: nombrePrenda.value.trim(),
      insumos: lineasValidas,
      costo_avios: costoAvios.value,
      costo_empaque: costoEmpaque.value,
      tiempo_confeccion_min: Math.round(tiempoConfeccionMin.value),
      tarifa_hora: tarifaHora.value,
      costo_cif: costoCif.value,
      margen_pct: margenPct.value,
      costo_hilo_m: Number(costoHiloMetro.value ?? 0),
      metros_hilo: metrosHiloEstimado.value,
      observaciones: observaciones.value.trim() || null,
    })
    showToast('success', 'Cotización guardada', `${saved.codigo ?? 'COT'} · ${formatCOP(Number(saved.precio_sugerido))}`)
    await cargarHistorial()
  } catch (e) {
    console.error('Error guardando cotización:', e)
    showToast('error', 'No se pudo guardar', 'Revisá la conexión con el backend e intentá de nuevo.')
  } finally {
    guardando.value = false
  }
}

async function llevarPrecioAProducto() {
  if (!recetaSeleccionada.value) {
    showToast('warn', 'Sin receta', 'Cargá la cotización desde una receta BOM para llevarle el precio.')
    return
  }
  try {
    await updateProducto(recetaSeleccionada.value, { precio_venta_sugerido: Math.round(precioVentaSugerido.value) })
    showToast('success', 'Precio actualizado', `Precio sugerido llevado al producto (${formatCOP(precioVentaSugerido.value)}).`)
  } catch (e) {
    console.error('Error llevando precio al producto:', e)
    showToast('error', 'No se pudo actualizar', 'Revisá la conexión con el backend e intentá de nuevo.')
  }
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header Banner -->
    <div class="bg-gradient-to-r from-stone-900 via-stone-900/90 to-stone-950 border border-amber-500/20 rounded-2xl p-5 sm:p-6 shadow-xl">
      <div class="space-y-1.5">
        <h1 class="text-xl sm:text-2xl font-bold font-serif tracking-wide text-stone-100 m-0">
          Cotizador Rápido de Costura & Presupuestos
        </h1>
        <p class="text-xs sm:text-sm text-stone-400 m-0 max-w-3xl">
          Calcula en segundos el precio exacto para tus clientes considerando metros de tela, forros, avíos y mano de obra.
        </p>
      </div>
    </div>

    <!-- Main Content: Form vs Summary -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Left (2 Cols): Form Sections -->
      <div class="lg:col-span-2 space-y-5">
        <!-- Prenda / Model Name & Recipe Selector -->
        <div class="bg-stone-900/80 border border-stone-800 rounded-2xl p-5 shadow-lg space-y-4">
          <div class="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-amber-400">
            <i class="pi pi-tag" /> Prenda o Modelo a Confeccionar
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label class="block text-xs text-stone-400 mb-1">Cargar desde Receta BOM</label>
              <Dropdown
                v-model="recetaSeleccionada"
                :options="recetasOptions"
                option-label="label"
                option-value="value"
                class="w-full text-xs"
                @change="onRecetaChange"
              />
            </div>
            <div>
              <label class="block text-xs text-stone-400 mb-1">Nombre de la Prenda</label>
              <InputText v-model="nombrePrenda" class="w-full text-xs" />
            </div>
            <div>
              <label class="block text-xs text-stone-400 mb-1">Cliente (opcional)</label>
              <Dropdown
                v-model="clienteSeleccionado"
                :options="clientesOptions"
                option-label="label"
                option-value="value"
                class="w-full text-xs"
              />
            </div>
            <div>
              <label class="block text-xs text-stone-400 mb-1">Observaciones (opcional)</label>
              <InputText v-model="observaciones" placeholder="Ej: tela del cliente, entrega urgente..." class="w-full text-xs" />
            </div>
          </div>
        </div>

        <!-- Section 1: Materiales dinámicos (BOM) -->
        <div class="bg-stone-900/80 border border-stone-800 rounded-2xl p-5 shadow-lg space-y-4">
          <div class="flex items-center justify-between border-b border-stone-800 pb-2">
            <div class="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-amber-400">
              <i class="pi pi-clone" /> 1. Materiales (BOM dinámico)
            </div>
            <span class="font-mono text-xs font-bold text-stone-300">{{ formatCOP(subtotalMateriales) }}</span>
          </div>

          <div v-if="!insumos.length" class="text-xs text-stone-500">Sin líneas todavía: cargá una receta BOM o añadí insumos a mano.</div>
          <div v-for="(l, idx) in insumos" :key="idx" class="grid grid-cols-2 sm:grid-cols-12 gap-2 items-end rounded-xl border border-stone-800/70 bg-stone-950/40 p-2">
            <div class="col-span-2 sm:col-span-4">
              <label class="block text-[11px] text-stone-400 mb-1">Insumo</label>
              <InputText v-model="l.nombre" placeholder="Tela, forro, botón..." class="w-full text-xs" />
            </div>
            <div class="col-span-1 sm:col-span-2">
              <label class="block text-[11px] text-stone-400 mb-1">Cantidad</label>
              <InputNumber v-model="l.cantidad" mode="decimal" locale="es-CO" :min="0" :max-fraction-digits="2" class="w-full font-mono text-xs" />
            </div>
            <div class="col-span-1 sm:col-span-2">
              <label class="block text-[11px] text-stone-400 mb-1">Unidad</label>
              <Dropdown v-model="l.unidad_medida" :options="UNIDADES_INSUMO" class="w-full text-xs" />
            </div>
            <div class="col-span-1 sm:col-span-2">
              <label class="block text-[11px] text-stone-400 mb-1">Precio unit. ($)</label>
              <InputNumber v-model="l.precio_unitario" mode="currency" currency="COP" locale="es-CO" :min-fraction-digits="0" :max-fraction-digits="2" class="w-full font-mono text-xs" />
            </div>
            <div class="col-span-1 sm:col-span-1">
              <label class="block text-[11px] text-stone-400 mb-1">% Desp.</label>
              <InputNumber v-model="l.desperdicio_pct" :min="0" class="w-full font-mono text-xs" />
            </div>
            <div class="col-span-2 sm:col-span-1 flex items-end justify-between gap-1">
              <span class="font-mono text-[11px] text-emerald-300">{{ formatCOP(subtotalLinea(l)) }}</span>
              <button type="button" class="px-2 py-1 rounded-lg bg-stone-800 text-stone-400 text-xs hover:bg-red-900/50 hover:text-red-300" title="Eliminar línea" @click="eliminarInsumo(idx)">✕</button>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <button type="button" class="px-3 py-1.5 rounded-lg bg-amber-500/20 border border-amber-500/30 text-amber-300 text-xs font-bold hover:bg-amber-500/30" @click="agregarInsumo">+ Añadir insumo</button>
            <span class="text-[10px] text-stone-500">Cada línea lleva su % de merma, como el BOM.</span>
          </div>
        </div>

        <!-- Section 2: Avíos, Cierres & Empaque -->
        <div class="bg-stone-900/80 border border-stone-800 rounded-2xl p-5 shadow-lg space-y-4">
          <div class="flex items-center justify-between border-b border-stone-800 pb-2">
            <div class="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-amber-400">
              <i class="pi pi-box" /> 2. Avíos, Cierres & Empaque
            </div>
            <span class="font-mono text-xs font-bold text-stone-300">{{ formatCOP(subtotalAvios) }}</span>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label class="block text-[11px] text-stone-400 mb-1">Cierres, Botones, Elásticos e Hilo ($)</label>
              <InputNumber v-model="costoAvios" mode="currency" currency="COP" locale="es-CO" :min-fraction-digits="0" :max-fraction-digits="0" class="w-full font-mono text-xs" />
            </div>
            <div>
              <label class="block text-[11px] text-stone-400 mb-1">Empaque, Bolsa & Etiquetas ($)</label>
              <InputNumber v-model="costoEmpaque" mode="currency" currency="COP" locale="es-CO" :min-fraction-digits="0" :max-fraction-digits="0" class="w-full font-mono text-xs" />
            </div>
          </div>

          <div class="rounded-xl border border-stone-800 bg-stone-950/60 p-3 text-xs space-y-2">
            <div class="flex items-center justify-between">
              <span class="font-bold uppercase tracking-wider text-stone-400 text-[11px]">Estimación hilos por tela (aprox.)</span>
              <span class="font-mono text-stone-300">{{ metrosTotalesTela.toFixed(2) }} m tela → {{ metrosHiloEstimado }} m hilo ≈ {{ formatCOP(costoHilosEstimado) }}</span>
            </div>
            <div class="flex items-center gap-2">
              <label class="text-[11px] text-stone-400">Costo hilo $/m</label>
              <InputNumber v-model="costoHiloMetro" mode="currency" currency="COP" locale="es-CO" :min-fraction-digits="0" :max-fraction-digits="0" class="w-32 font-mono text-xs" />
              <button type="button" class="px-2.5 py-1 rounded-lg bg-amber-500/20 border border-amber-500/30 text-amber-300 text-xs font-bold hover:bg-amber-500/30" @click="aplicarEstimacionHilos">Sumar a Avíos</button>
            </div>
            <p class="text-[10px] text-stone-500 m-0">Heurística: 120 m hilo por metro de tela+forro (overlock+recta+remates). Ajustá el $/m según tu cono.</p>
          </div>
        </div>

        <!-- Section 3: Mano de Obra & Costos Fijos (CIF) -->
        <div class="bg-stone-900/80 border border-stone-800 rounded-2xl p-5 shadow-lg space-y-4">
          <div class="flex items-center justify-between border-b border-stone-800 pb-2">
            <div class="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-amber-400">
              <i class="pi pi-cog" /> 3. Mano de Obra & Costos Fijos (CIF)
            </div>
            <span class="font-mono text-xs font-bold text-stone-300">{{ formatCOP(subtotalManoObra + costoCif) }}</span>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label class="block text-[11px] text-stone-400 mb-1">Tiempo Confección (min)</label>
              <InputNumber v-model="tiempoConfeccionMin" :min="1" class="w-full font-mono text-xs" />
              <p v-if="tiempoSupuesto" class="text-[10px] text-amber-400/90 m-0 mt-1">supuesto — cronometrar en taller</p>
            </div>
            <div>
              <label class="block text-[11px] text-stone-400 mb-1">Tarifa $/hora</label>
              <InputNumber v-model="tarifaHora" mode="currency" currency="COP" locale="es-CO" :min-fraction-digits="0" :max-fraction-digits="0" class="w-full font-mono text-xs" />
            </div>
            <div>
              <label class="block text-[11px] text-stone-400 mb-1">Costos CIF / Luz ($)</label>
              <InputNumber v-model="costoCif" mode="currency" currency="COP" locale="es-CO" :min-fraction-digits="0" :max-fraction-digits="0" class="w-full font-mono text-xs" />
            </div>
          </div>
        </div>

        <!-- Margin Slider -->
        <div class="bg-stone-900/80 border border-stone-800 rounded-2xl p-5 shadow-lg space-y-4">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-amber-400">
              <i class="pi pi-percentage" /> Margen de Ganancia Deseado
            </div>
            <span class="flex items-center gap-2">
              <span v-if="margenHeredado !== null" class="px-2 py-0.5 rounded-full border border-amber-500/30 bg-amber-500/10 text-amber-300 text-[10px] font-bold">margen heredado {{ margenHeredado }}% de la receta</span>
              <span class="font-mono text-sm font-extrabold text-amber-300">{{ margenPct }}%</span>
            </span>
          </div>

          <Slider v-model="margenPct" :min="20" :max="90" class="w-full" />

          <div class="flex justify-between text-[11px] text-stone-500 font-medium">
            <span>20% (Mayorista)</span>
            <span class="text-amber-400 font-bold">55% - 65% (Taller Estándar)</span>
            <span>80%+ (Alta Costura)</span>
          </div>
          <p class="text-[10px] text-stone-500 m-0">Regla visible: margen ≥100% usa ×2.2 fijo; margen que deje menos de 5% de factor usa ×2 (tope anti-margen-cero). Igual en servidor.</p>
          <p class="text-[11px] text-stone-400 m-0">A meta {{ margenMetaGlobal }}% daría {{ formatCOP(precioAMeta) }} (piso de referencia; el precio lista manda).</p>
        </div>
      </div>

      <!-- Right (1 Col): Resumen de Cotización Card -->
      <div class="space-y-4">
        <div class="bg-gradient-to-br from-stone-900 via-stone-950 to-amber-950/40 border border-amber-500/30 rounded-2xl p-5 shadow-2xl space-y-4 sticky top-4">
          <div class="border-b border-stone-800 pb-3">
            <div class="text-[11px] uppercase font-bold text-amber-400 tracking-wider">Resumen de Cotización</div>
            <h3 class="text-base font-bold text-stone-100 mt-1 m-0">{{ nombrePrenda }}</h3>
          </div>

          <div class="space-y-2.5 text-xs">
            <div class="flex justify-between text-stone-300">
              <span>Materiales ({{ insumos.length }} líneas):</span>
              <span class="font-mono font-semibold">{{ formatCOP(subtotalMateriales) }}</span>
            </div>
            <div class="flex justify-between text-stone-300">
              <span>Avíos, Hilos & Empaque:</span>
              <span class="font-mono font-semibold">{{ formatCOP(subtotalAvios) }}</span>
            </div>
            <div class="flex justify-between text-stone-300">
              <span>Mano de Obra ({{ tiempoConfeccionMin }} min):</span>
              <span class="font-mono font-semibold">{{ formatCOP(subtotalManoObra) }}</span>
            </div>
            <div class="flex justify-between text-stone-300">
              <span>Costos Generales Taller (CIF):</span>
              <span class="font-mono font-semibold">{{ formatCOP(costoCif) }}</span>
            </div>

            <div class="flex justify-between py-2 border-t border-stone-800 text-stone-200 font-bold">
              <span>Costo Total de Confección:</span>
              <span class="font-mono text-emerald-400">{{ formatCOP(costoTotalConfeccion) }}</span>
            </div>

              <div v-if="recetaSeleccionada" class="flex justify-between py-1.5 text-xs bg-amber-950/20 border border-amber-500/20 rounded-lg px-2">
                <span class="text-amber-300 flex items-center gap-1"><i class="pi pi-database text-[10px]" /> Costo real BOM (DB):</span>
                <span class="font-mono font-bold" :class="loadingCostoReal ? 'text-stone-400' : 'text-amber-300'">{{ loadingCostoReal ? 'Cargando...' : (costoReal !== null ? formatCOP(costoReal!) : 'Sin BOM') }}</span>
              </div>
              <details v-if="detalleBase.length || lineasBase.length" :open="baseExpandida" class="rounded-lg border border-stone-800 bg-stone-950/60 px-2 py-1.5 text-[11px]" @toggle="onBaseToggle">
                <summary class="cursor-pointer text-stone-400 font-bold">Base BOM ({{ detalleBase.length || lineasBase.length }} líneas) — cada línea dice a dónde fue</summary>
                <div v-if="detalleBase.length" class="overflow-x-auto">
                  <table class="w-full mt-1.5 text-[10px] text-stone-300 border-collapse">
                    <thead>
                      <tr class="text-stone-500 uppercase tracking-wider text-[9px] text-left">
                        <th class="py-1 pr-1 font-bold">Material</th>
                        <th class="py-1 pr-1 font-bold text-right">Cant. BOM</th>
                        <th class="py-1 pr-1 font-bold text-right">A m</th>
                        <th class="py-1 pr-1 font-bold text-right">Precio unit.</th>
                        <th class="py-1 pr-1 font-bold text-right">Subtotal</th>
                        <th class="py-1 font-bold text-right">Va a</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="(d, i) in detalleBase" :key="`${d.nombre}-${i}`" class="border-t border-stone-800/60">
                        <td class="py-1 pr-1 max-w-[110px] truncate" :title="d.nombre">{{ d.nombre }}</td>
                        <td class="py-1 pr-1 font-mono text-right whitespace-nowrap">{{ fmtCant(d.cant) }} {{ d.unidad }}</td>
                        <td class="py-1 pr-1 font-mono text-right whitespace-nowrap">{{ d.aMetros == null ? '—' : `${fmtCant(d.aMetros)} m` }}</td>
                        <td class="py-1 pr-1 font-mono text-right whitespace-nowrap">{{ fmtPrecioU(d.precio, d.unidad) }}</td>
                        <td class="py-1 pr-1 font-mono text-right whitespace-nowrap">{{ formatCOP(d.subtotal) }}</td>
                        <td class="py-1 font-bold text-right whitespace-nowrap text-amber-300/90">{{ d.destino }}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
                <div v-else class="mt-1 space-y-1">
                  <div v-for="(l, i) in lineasBase" :key="`${l.tipo}-${l.id}-${i}`" class="flex justify-between gap-2 text-stone-300">
                    <span class="truncate">{{ l.nombre }} <span class="text-stone-500">× {{ Number(l.cantidad) }}</span></span>
                    <span class="font-mono shrink-0">{{ formatCOP(Number(l.costo_total)) }}</span>
                  </div>
                </div>
                <p v-if="baseParcial" class="text-amber-400 m-0 mt-1">{{ baseParcial }}</p>
                <p v-else class="text-stone-500 m-0 mt-1">Lo que agregues a mano son extras de esta cotización (empaque especial, urgencia, ajustes).</p>
              </details>
          </div>

          <!-- Suggested Sale Price Box -->
          <div class="bg-stone-950/90 border border-amber-500/40 rounded-xl p-4 text-center space-y-1 shadow-inner">
            <div class="text-[11px] font-bold text-amber-400 uppercase tracking-wider">
              PRECIO DE VENTA SUGERIDO AL CLIENTE
            </div>
            <div class="text-2xl sm:text-3xl font-extrabold font-mono text-amber-300">
              {{ formatCOP(precioVentaSugerido) }}
            </div>
            <div class="text-xs text-emerald-400 font-semibold pt-1">
              Ganancia Neta: {{ formatCOP(gananciaNeta) }} ({{ margenPct }}%)
            </div>
          </div>

          <!-- Action Buttons -->
          <div class="space-y-2 pt-2">
            <button
              type="button"
              class="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs shadow-lg transition"
              @click="copiarPresupuestoWhatsApp"
            >
              <i class="pi pi-whatsapp text-sm" />
              <span>Copiar Presupuesto para WhatsApp</span>
            </button>

            <Button
              label="Guardar Cotización"
              icon="pi pi-save"
              class="w-full text-xs font-semibold p-button-warning"
              :loading="guardando"
              :disabled="guardando"
              @click="guardarCotizacion"
            />

            <Button
              label="Llevar precio al producto"
              icon="pi pi-tag"
              severity="secondary"
              outlined
              class="w-full text-xs font-semibold"
              :disabled="!recetaSeleccionada"
              title="Requiere receta BOM cargada"
              @click="llevarPrecioAProducto"
            />

            <Button
              label="Ir a Gestión de Pedidos"
              icon="pi pi-arrow-right"
              severity="secondary"
              outlined
              class="w-full text-xs font-semibold"
              @click="router.push('/produccion')"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- Historial: últimas cotizaciones con estado -->
    <div class="bg-stone-900/80 border border-stone-800 rounded-2xl p-5 shadow-lg space-y-3">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-amber-400">
          <i class="pi pi-history" /> Últimas Cotizaciones
        </div>
        <button type="button" class="text-[11px] text-stone-400 hover:text-stone-200" @click="cargarHistorial">↻ Actualizar</button>
      </div>
      <div v-if="loadingHistorial" class="text-xs text-stone-500">Cargando...</div>
      <div v-else-if="!historial.length" class="text-xs text-stone-500">Todavía no guardaste cotizaciones.</div>
      <div v-for="c in historial" :key="c.id" class="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-stone-800 bg-stone-950/60 px-3 py-2 text-xs">
        <div class="flex items-center gap-2 min-w-0">
          <span class="font-mono font-bold text-amber-300">{{ c.codigo ?? `COT-${c.id}` }}</span>
          <span class="text-stone-200 truncate">{{ c.nombre_prenda }}</span>
          <span class="font-mono text-emerald-300">{{ formatCOP(Number(c.precio_sugerido ?? 0)) }}</span>
          <span class="px-2 py-0.5 rounded-full border text-[10px] font-bold uppercase" :class="c.estado === 'aprobada' ? 'text-emerald-300 border-emerald-500/30 bg-emerald-500/10' : c.estado === 'enviada' ? 'text-amber-300 border-amber-500/30 bg-amber-500/10' : c.estado === 'descartada' ? 'text-stone-500 border-stone-700' : 'text-stone-300 border-stone-700'">{{ c.estado }}</span>
        </div>
        <div class="flex items-center gap-1.5">
          <button v-if="c.estado === 'borrador'" type="button" class="px-2 py-1 rounded-lg bg-stone-800 text-stone-200 text-[11px] font-bold hover:bg-stone-700" @click="marcarEstado(c, 'enviada')">Enviada</button>
          <button v-if="c.estado === 'enviada'" type="button" class="px-2 py-1 rounded-lg bg-emerald-600/20 border border-emerald-500/30 text-emerald-300 text-[11px] font-bold hover:bg-emerald-600/30" @click="marcarEstado(c, 'aprobada')">Aprobar</button>
          <button v-if="c.estado !== 'descartada' && c.estado !== 'aprobada'" type="button" class="px-2 py-1 rounded-lg bg-stone-800 text-stone-400 text-[11px] hover:bg-stone-700" @click="marcarEstado(c, 'descartada')">Descartar</button>
        </div>
      </div>
    </div>
  </div>
</template>
