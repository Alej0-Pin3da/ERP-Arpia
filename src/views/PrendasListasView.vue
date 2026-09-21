<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import InputText from 'primevue/inputtext'
import { useProductos } from '@/composables/useProductos'
import { usePrendas } from '@/composables/usePrendas'
import { useMaestros } from '@/composables/useMaestros'
import type { ProductoRead } from '@/services/api/productos'
import { listVariantes, createVariante } from '@/services/api/productos'
import type { PrendaRead } from '@/services/api/prendas'
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
  void cargarPrendas()
  void cargarProductosParaPrenda()
  void cargarMatrizTallas()
})

// --- Detalle por talla (prendas unitarias: disponible/reservada/vendida/defectuosa) ---
const prendasService = usePrendas()
const maestrosService = useMaestros()
const prendas = ref<PrendaRead[]>([])
const productosParaPrenda = ref<{ id: number; nombre: string }[]>([])
const variantesForm = ref<{ id: number; nombre: string }[]>([])
const formProductoId = ref<number | null>(null)
const formCantidad = ref<number>(1)
const formEstado = ref<string>('disponible')
const guardandoPrenda = ref(false)
// Matriz oficial de tallas (Maestros): une las variantes del producto con la
// matriz para que siempre se pueda cargar. Elegir una talla de matriz que el
// producto no tiene la crea como variante automáticamente al guardar.
const matrizTallas = ref<string[]>([])
async function cargarMatrizTallas() {
  try {
    const r = await maestrosService.listTallas({ limit: 100 })
    matrizTallas.value = ((r.items ?? []) as unknown as Record<string, unknown>[])
      .filter((t) => t.activo !== false)
      .map((t) => String(t.talla ?? '').trim())
      .filter((n) => n.length > 0)
  } catch { matrizTallas.value = [] }
}
interface OpcionTalla { key: string; id: number | null; nombre: string; nueva: boolean }
const opcionesTalla = computed<OpcionTalla[]>(() => {
  const propias = variantesForm.value.map((v) => ({ key: `v:${v.id}`, id: v.id as number, nombre: v.nombre, nueva: false }))
  const nombresPropios = new Set(variantesForm.value.map((v) => v.nombre))
  const deMatriz = matrizTallas.value
    .filter((n) => !nombresPropios.has(n))
    .map((n) => ({ key: `m:${n}`, id: null as number | null, nombre: `${n} (nueva)`, nueva: true }))
  return [...propias, ...deMatriz]
})
const formTallaKey = ref<string>('none')

async function cargarPrendas() {
  try {
    const r = await prendasService.list({ limit: 200 })
    prendas.value = r.items ?? []
  } catch (e) {
    console.error('Error cargando prendas por talla:', e)
  }
}

async function cargarProductosParaPrenda() {
  try {
    const r = await productosService.list({ limit: 100 })
    productosParaPrenda.value = (r.items ?? []).map((p: ProductoRead) => ({ id: p.id, nombre: p.nombre }))
    preciosProducto.value = Object.fromEntries(
      (r.items ?? []).map((p: ProductoRead) => [p.nombre, toNum(p.precio_venta_sugerido)]),
    )
  } catch { productosParaPrenda.value = [] }
}
const preciosProducto = ref<Record<string, number>>({})
const udsDisponibles = computed(() => prendas.value.filter((p) => p.estado === 'disponible').length)
const valorizacionUnitaria = computed(() =>
  prendas.value
    .filter((p) => p.estado === 'disponible')
    .reduce((acc, p) => acc + (toNum(p.precio_venta) || preciosProducto.value[p.nombre_producto ?? ''] || 0), 0),
)

async function onProductoFormChange() {
  formTallaKey.value = 'none'
  variantesForm.value = []
  if (formProductoId.value == null) return
  try {
    const vs = await listVariantes(formProductoId.value)
    variantesForm.value = vs.map((v) => ({ id: v.id, nombre: v.nombre_variante }))
  } catch { variantesForm.value = [] }
}

interface GrupoTalla {
  key: string
  producto: string
  talla: string
  disponible: number
  reservada: number
  vendida: number
  defectuosa: number
  exhibicion: number
  unidades: PrendaRead[]
}

const gruposExpandidos = ref<Set<string>>(new Set())
const variantesPorGrupo = ref<Record<string, { id: number; nombre: string }[]>>({})
const ESTADOS_PRENDA = ['disponible', 'reservada', 'vendida', 'defectuosa', 'exhibicion']

function toggleGrupo(key: string) {
  const s = new Set(gruposExpandidos.value)
  if (s.has(key)) s.delete(key)
  else s.add(key)
  gruposExpandidos.value = s
}

async function cargarVariantesGrupo(g: GrupoTalla) {
  if (variantesPorGrupo.value[g.key]) return
  const prod = productosParaPrenda.value.find((p) => p.nombre === g.producto)
  if (!prod) return
  try {
    const vs = await listVariantes(prod.id)
    variantesPorGrupo.value = { ...variantesPorGrupo.value, [g.key]: vs.map((v) => ({ id: v.id, nombre: v.nombre_variante })) }
  } catch { /* sin variantes */ }
}

function onToggleGrupo(g: GrupoTalla) {
  toggleGrupo(g.key)
  if (gruposExpandidos.value.has(g.key)) void cargarVariantesGrupo(g)
}

async function guardarUnidad(u: PrendaRead, patch: Record<string, unknown>) {
  await prendasService.update(u.id, patch)
  await cargarPrendas()
}

async function borrarUnidad(u: PrendaRead) {
  if (!window.confirm(`Eliminar la unidad #${u.id} (${u.talla ?? 'Sin talla'})?`)) return
  await prendasService.remove(u.id)
  await cargarPrendas()
}

const gruposTalla = computed<GrupoTalla[]>(() => {
  const porId: Record<number, string> = {}
  for (const p of productosParaPrenda.value) porId[p.id] = p.nombre
  const nombreDe = (u: PrendaRead): string => {
    const pid = (u as unknown as { producto_id?: number | null }).producto_id
    if (pid != null && porId[pid]) return porId[pid]
    return u.nombre_producto ?? (u.variante_id != null ? `Variante #${u.variante_id}` : 'Sin producto')
  }
  const claveDe = (u: PrendaRead): string => {
    const pid = (u as unknown as { producto_id?: number | null }).producto_id
    if (pid != null) return `p:${pid}`
    if (u.variante_id != null) return `v:${u.variante_id}`
    return 'none'
  }
  const map = new Map<string, GrupoTalla>()
  for (const p of prendas.value) {
    const producto = nombreDe(p)
    const talla = p.talla ?? p.nombre_variante ?? 'Sin talla'
    const key = `${claveDe(p)}||${talla}`
    let g = map.get(key)
    if (!g) {
      g = { key, producto, talla, disponible: 0, reservada: 0, vendida: 0, defectuosa: 0, exhibicion: 0, unidades: [] }
      map.set(key, g)
    }
    g.unidades.push(p)
    if (p.estado === 'disponible') g.disponible++
    else if (p.estado === 'reservada') g.reservada++
    else if (p.estado === 'vendida') g.vendida++
    else if (p.estado === 'defectuosa') g.defectuosa++
    else if (p.estado === 'exhibicion') g.exhibicion++
  }
  return [...map.values()].sort((a, b) => a.producto.localeCompare(b.producto) || a.talla.localeCompare(b.talla))
})

const totalUnidades = computed(() => prendas.value.length)
const totalDisponibles = computed(() => prendas.value.filter((p) => p.estado === 'disponible').length)

// Matriz de stock: filas = productos, columnas = tallas (orden de matriz
// oficial + extras presentes). Click en celda = detalle editable.
const tallasColumnas = computed<string[]>(() => {
  const enDatos = new Set<string>()
  for (const g of gruposTalla.value) enDatos.add(g.talla)
  const deMatriz = matrizTallas.value.filter((n) => enDatos.has(n))
  const extras = [...enDatos].filter((n) => !matrizTallas.value.includes(n)).sort((a, b) => a.localeCompare(b))
  return [...deMatriz, ...extras]
})
interface CeldaMatrix { disponible: number; exhibicion: number; key: string | null }
const matrizCeldas = computed<Record<string, Record<string, CeldaMatrix>>>(() => {
  const m: Record<string, Record<string, CeldaMatrix>> = {}
  for (const p of gruposProducto.value) {
    m[p.nombre] = {}
    for (const g of p.tallas) {
      m[p.nombre][g.talla] = { disponible: g.disponible, exhibicion: g.exhibicion, key: g.key }
    }
  }
  return m
})
const matrizTotales = computed(() => {
  const porTalla: Record<string, number> = {}
  let granTotal = 0
  for (const t of tallasColumnas.value) {
    let s = 0
    for (const p of gruposProductoFiltrados.value) s += matrizCeldas.value[p.nombre]?.[t]?.disponible ?? 0
    porTalla[t] = s
    granTotal += s
  }
  return { porTalla, granTotal }
})
function grupoDeCelda(producto: string, talla: string): GrupoTalla | null {
  const p = gruposProducto.value.find((x) => x.nombre === producto)
  return p?.tallas.find((g) => g.talla === talla) ?? null
}

interface GrupoProducto {
  nombre: string
  total: number
  disponibles: number
  tallas: GrupoTalla[]
}

const gruposProducto = computed<GrupoProducto[]>(() => {
  const map = new Map<string, GrupoProducto>()
  for (const g of gruposTalla.value) {
    let p = map.get(g.producto)
    if (!p) {
      p = { nombre: g.producto, total: 0, disponibles: 0, tallas: [] }
      map.set(g.producto, p)
    }
    p.tallas.push(g)
    p.total += g.unidades.length
    p.disponibles += g.disponible
  }
  return [...map.values()].sort((a, b) => a.nombre.localeCompare(b.nombre))
})

async function cargarPrendasForm() {
  if (formProductoId.value == null) return
  const cant = Math.max(1, Math.floor(Number(formCantidad.value) || 1))
  guardandoPrenda.value = true
  try {
    let varianteId: number | null = null
    let tallaNombre = 'Sin talla'
    if (formTallaKey.value !== 'none') {
      const op = opcionesTalla.value.find((o) => o.key === formTallaKey.value)
      if (op) {
        if (op.nueva) {
          // La matriz trae tallas que el producto aún no tiene: se crean.
          const creada = await createVariante(formProductoId.value, op.nombre.replace(/ \(nueva\)$/, ''))
          varianteId = creada.id
          tallaNombre = creada.nombre_variante
          await onProductoFormChange()
          formTallaKey.value = `v:${varianteId}`
        } else {
          varianteId = op.id
          tallaNombre = variantesForm.value.find((v) => v.id === op.id)?.nombre ?? tallaNombre
        }
      }
    }
    for (let i = 0; i < cant; i++) {
      await prendasService.create({
        producto_id: formProductoId.value,
        variante_id: varianteId,
        talla: tallaNombre,
        estado: formEstado.value,
      })
    }
    formCantidad.value = 1
    await cargarPrendas()
  } finally {
    guardandoPrenda.value = false
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
const lotePrecioMedio = computed(() => (loteStockTotal.value > 0 ? loteValorizacion.value / loteStockTotal.value : 0))
// Totales unificados lote + talla (lo que la dueña opera).
const stockTotalUds = computed(() => loteStockTotal.value + udsDisponibles.value)
const valorizacionTotal = computed(() => loteValorizacion.value + valorizacionUnitaria.value)
const precioMedioTotal = computed(() => (stockTotalUds.value > 0 ? valorizacionTotal.value / stockTotalUds.value : 0))
const udsExhibicion = computed(() => prendas.value.filter((p) => p.estado === 'exhibicion').length)
const productosConStock = computed(() => {
  const nombres = new Set<string>()
  for (const l of lotes.value) nombres.add(l.nombre)
  for (const p of gruposProducto.value) nombres.add(p.nombre)
  return nombres.size
})
const gruposProductoFiltrados = computed(() => {
  const q = search.value.trim().toLowerCase()
  if (!q) return gruposProducto.value
  return gruposProducto.value.filter((p) => p.nombre.toLowerCase().includes(q))
})

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
            {{ Math.round(stockTotalUds) }} uds en Stock
          </span>
        </div>
        <p class="text-xs sm:text-sm text-stone-400 m-0 max-w-2xl">
          Prendas terminadas listas para vender: por lote de producción y por talla.
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

    <!-- 4 KPI Summary Cards (stock total: lote + talla) -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <div class="bg-stone-900/80 border border-stone-800 rounded-2xl p-4 shadow-md">
        <div class="text-xs text-stone-400 font-bold uppercase tracking-wider">Prendas terminadas</div>
        <div class="text-2xl font-extrabold text-stone-100 mt-2 font-mono">
          {{ Math.round(stockTotalUds) }} uds
        </div>
        <div class="text-[11px] text-stone-400 mt-1">{{ productosConStock }} productos · {{ Math.round(loteStockTotal) }} lote + {{ udsDisponibles }} talla</div>
      </div>

      <div class="bg-stone-900/80 border border-sky-500/30 rounded-2xl p-4 shadow-md">
        <div class="text-xs text-stone-400 font-bold uppercase tracking-wider">Valorización</div>
        <div class="text-2xl font-extrabold text-sky-300 mt-2 font-mono">
          {{ formatCOP(valorizacionTotal) }}
        </div>
        <div class="text-[11px] text-stone-400 mt-1 font-mono">{{ formatCOP(loteValorizacion) }} lote + {{ formatCOP(valorizacionUnitaria) }} talla</div>
      </div>

      <div class="bg-stone-900/80 border border-stone-800 rounded-2xl p-4 shadow-md">
        <div class="text-xs text-stone-400 font-bold uppercase tracking-wider">Precio Medio</div>
        <div class="text-2xl font-extrabold text-amber-300 mt-2 font-mono">
          {{ formatCOP(precioMedioTotal) }}
        </div>
        <div class="text-[11px] text-stone-400 mt-1">Valorización / unidades</div>
      </div>

      <div class="bg-stone-900/80 border border-stone-800 rounded-2xl p-4 shadow-md">
        <div class="text-xs text-stone-400 font-bold uppercase tracking-wider">En exhibición</div>
        <div class="text-2xl font-extrabold text-sky-300 mt-2 font-mono">
          {{ udsExhibicion }} uds
        </div>
        <div class="text-[11px] text-stone-400 mt-1">Fotos y muestra · no vendibles</div>
      </div>
    </div>

    <!-- Search Input (filtra matriz por producto) -->
    <div class="w-full md:w-96">
      <span class="p-input-icon-left w-full">
        <InputText
          v-model="search"
          placeholder="Buscar productos por nombre..."
          class="w-full text-xs"
        />
      </span>
    </div>

    <!-- Stock por lote (flujo batch: Producto.stock_actual) -->
    <section v-if="loteFiltrados.length > 0" aria-label="Stock por lote">
      <div class="flex items-center gap-2.5 flex-wrap mb-3">
        <h2 class="text-base sm:text-lg font-bold font-serif tracking-wide text-stone-100 m-0">
          Stock por lote
        </h2>
        <span class="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-sky-950/80 text-sky-300 border border-sky-500/30 uppercase tracking-wider">
          {{ Math.round(loteStockTotal) }} uds en {{ loteFiltrados.length }} productos
        </span>
      </div>

      <div class="space-y-4">
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

    <div v-if="loteFiltrados.length === 0 && gruposProducto.length === 0" class="bg-stone-900/80 border border-stone-800 rounded-2xl p-5 text-sm text-stone-400">
      Sin stock todavía — cargá prendas por talla arriba o completá un lote en Producción.
    </div>

    <!-- Detalle por talla (prendas unitarias: disponible/reservada/vendida/defectuosa) -->
    <section aria-label="Detalle por talla">
      <div class="flex items-center gap-2.5 flex-wrap mb-3">
        <h2 class="text-base sm:text-lg font-bold font-serif tracking-wide text-stone-100 m-0">
          Detalle por talla
        </h2>
        <span class="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-emerald-950/80 text-emerald-300 border border-emerald-500/30 uppercase tracking-wider">
          {{ totalDisponibles }} disponibles de {{ totalUnidades }} uds
        </span>
      </div>

      <div class="bg-stone-900/80 border border-stone-800 rounded-2xl p-4 mb-4">
        <div class="text-xs text-stone-400 font-bold uppercase tracking-wider mb-3">Cargar prendas terminadas</div>
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          <div>
            <label class="block text-[11px] uppercase font-bold text-stone-400 mb-1" for="form-prenda-producto">Producto</label>
            <select
              id="form-prenda-producto"
              v-model="formProductoId"
              class="w-full bg-stone-950 border border-stone-700 text-stone-200 text-xs rounded-lg px-3 py-2 font-mono focus:border-amber-400 focus:outline-none"
              @change="onProductoFormChange"
            >
              <option :value="null">Elegir producto…</option>
              <option v-for="p in productosParaPrenda" :key="p.id" :value="p.id">{{ p.nombre }}</option>
            </select>
          </div>
          <div>
            <label class="block text-[11px] uppercase font-bold text-stone-400 mb-1" for="form-prenda-talla">Talla (matriz + propias)</label>
            <select
              id="form-prenda-talla"
              v-model="formTallaKey"
              class="w-full bg-stone-950 border border-stone-700 text-stone-200 text-xs rounded-lg px-3 py-2 font-mono focus:border-amber-400 focus:outline-none"
            >
              <option value="none">Sin talla</option>
              <option v-for="o in opcionesTalla" :key="o.key" :value="o.key">{{ o.nombre }}</option>
            </select>
          </div>
          <div>
            <label class="block text-[11px] uppercase font-bold text-stone-400 mb-1" for="form-prenda-cantidad">Cantidad</label>
            <input
              id="form-prenda-cantidad"
              v-model.number="formCantidad"
              type="number"
              min="1"
              class="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-xs font-mono text-stone-200"
            />
          </div>
          <div>
            <label class="block text-[11px] uppercase font-bold text-stone-400 mb-1" for="form-prenda-estado">Estado</label>
            <select
              id="form-prenda-estado"
              v-model="formEstado"
              class="w-full bg-stone-950 border border-stone-700 text-stone-200 text-xs rounded-lg px-3 py-2 font-mono focus:border-amber-400 focus:outline-none"
            >
              <option v-for="e in ESTADOS_PRENDA" :key="e" :value="e">{{ e }}</option>
            </select>
          </div>
          <div class="flex items-end">
            <button
              type="button"
              :disabled="formProductoId == null || guardandoPrenda"
              class="w-full min-h-[38px] rounded-lg bg-amber-500 text-stone-950 text-xs font-bold hover:bg-amber-400 transition disabled:opacity-40"
              @click="cargarPrendasForm"
            >
              {{ guardandoPrenda ? 'Guardando…' : '+ Cargar' }}
            </button>
          </div>
        </div>
        <p class="text-[11px] text-stone-500 mt-2">Sin talla se atribuye igual al producto elegido.</p>
      </div>

      <div v-if="gruposProducto.length === 0" class="bg-stone-900/80 border border-stone-800 rounded-2xl p-5 text-sm text-stone-400">
        Sin prendas unitarias — cargá las terminadas por talla arriba.
      </div>

      <div v-else class="space-y-4">
        <div class="overflow-x-auto bg-stone-900/80 border border-stone-800 rounded-2xl shadow-lg">
          <table class="w-full min-w-[560px] text-left text-xs border-collapse">
            <thead>
              <tr class="border-b border-stone-800/80 text-stone-400 bg-stone-900/40 uppercase tracking-wider font-semibold">
                <th class="py-2.5 px-4 sticky left-0 z-10 bg-stone-950/95 min-w-[180px]">Producto</th>
                <th v-for="t in tallasColumnas" :key="t" class="py-2.5 px-3 text-center whitespace-nowrap">{{ t }}</th>
                <th class="py-2.5 px-3 text-center whitespace-nowrap">Total</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-stone-800/50 text-stone-200 font-mono">
              <template v-for="p in gruposProductoFiltrados" :key="p.nombre">
              <tr class="hover:bg-stone-800/30">
                <td class="py-2.5 px-4 font-bold text-stone-100 font-sans sticky left-0 z-10 bg-stone-900/95 min-w-[180px]">{{ p.nombre }}</td>
                <td
                  v-for="t in tallasColumnas"
                  :key="t"
                  class="py-2 px-3 text-center whitespace-nowrap cursor-pointer hover:bg-amber-950/30"
                  :class="(matrizCeldas[p.nombre]?.[t]?.disponible ?? 0) > 0 ? 'font-bold text-emerald-300' : 'text-stone-600'"
                  :title="`Ver unidades: ${p.nombre} · ${t}`"
                  @click="(() => { const g = grupoDeCelda(p.nombre, t); if (g) onToggleGrupo(g) })()"
                >
                  {{ matrizCeldas[p.nombre]?.[t]?.disponible ?? '—' }}
                  <span v-if="(matrizCeldas[p.nombre]?.[t]?.exhibicion ?? 0) > 0" class="text-[10px] text-sky-400">+{{ matrizCeldas[p.nombre][t].exhibicion }}E</span>
                </td>
                <td class="py-2.5 px-3 text-center font-bold text-amber-300 whitespace-nowrap">{{ p.disponibles }}</td>
              </tr>
              <template v-for="g in p.tallas" :key="g.key">
              <tr v-if="gruposExpandidos.has(g.key)" class="bg-stone-950/60">
                <td class="py-2 px-4 pl-6 text-sky-300 whitespace-nowrap sticky left-0 z-10 bg-stone-950/95">↳ {{ g.talla }} <span class="text-stone-500 font-sans text-[11px]">R{{ g.reservada }}/V{{ g.vendida }}/D{{ g.defectuosa }}/E{{ g.exhibicion }}</span></td>
                <td :colspan="tallasColumnas.length + 1" class="py-2 px-4">
                  <div class="space-y-1.5">
                    <div v-for="u in g.unidades" :key="u.id" class="flex flex-wrap items-center gap-2 text-xs font-sans">
                      <span class="text-stone-500 font-mono">#{{ u.id }}</span>
                      <select
                        :value="u.variante_id ?? 'none'"
                        class="bg-stone-950 border border-stone-700 text-stone-200 rounded-lg px-2 py-1 font-mono focus:border-amber-400 focus:outline-none"
                        :title="`Talla de la unidad #${u.id}`"
                        @change="guardarUnidad(u, { variante_id: ($event.target as HTMLSelectElement).value === 'none' ? null : Number(($event.target as HTMLSelectElement).value), talla: ($event.target as HTMLSelectElement).selectedOptions[0]?.textContent?.trim() ?? u.talla })"
                      >
                        <option value="none">Sin talla</option>
                        <option v-for="v in (variantesPorGrupo[g.key] ?? [])" :key="v.id" :value="v.id">{{ v.nombre }}</option>
                      </select>
                      <select
                        :value="u.estado"
                        class="bg-stone-950 border border-stone-700 text-stone-200 rounded-lg px-2 py-1 font-mono focus:border-amber-400 focus:outline-none"
                        :title="`Estado de la unidad #${u.id}`"
                        @change="guardarUnidad(u, { estado: ($event.target as HTMLSelectElement).value })"
                      >
                        <option v-for="e in ESTADOS_PRENDA" :key="e" :value="e">{{ e }}</option>
                      </select>
                      <button
                        type="button"
                        class="text-stone-500 hover:text-rose-400 font-mono p-1 transition-colors"
                        :title="`Eliminar unidad #${u.id}`"
                        @click="borrarUnidad(u)"
                      >
                        ✕
                      </button>
                    </div>
                  </div>
                </td>
              </tr>
              </template>
              </template>
              <tr class="bg-stone-900/60 font-bold">
                <td class="py-2.5 px-4 text-stone-100 font-sans sticky left-0 z-10 bg-stone-950/95 min-w-[180px]">TOTAL</td>
                <td v-for="t in tallasColumnas" :key="t" class="py-2.5 px-3 text-center text-amber-300 whitespace-nowrap">{{ matrizTotales.porTalla[t] }}</td>
                <td class="py-2.5 px-3 text-center text-amber-300 whitespace-nowrap">{{ matrizTotales.granTotal }}</td>
              </tr>
            </tbody>
          </table>
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
