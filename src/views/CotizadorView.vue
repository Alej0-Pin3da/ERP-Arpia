<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useProductos } from '@/composables/useProductos'
import { useBom } from '@/composables/useBom'
import { useRouter } from 'vue-router'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Dropdown from 'primevue/dropdown'
import Slider from 'primevue/slider'
import { showToast } from '@/utils/toast'
import { createCotizacion, listCotizaciones, updateCotizacionEstado, type CotizacionRead } from '@/services/api/cotizaciones'
import { useClientes } from '@/composables/useClientes'
import { updateProducto } from '@/services/api/productos'

const router = useRouter()
const productosApi = useProductos()
const bomApi = useBom()
const productos = ref<any[]>([])
const costoReal = ref<number | null>(null)
const loadingCostoReal = ref(false)
async function cargarProductos() {
  try {
    const r = await productosApi.list({ limit: 100 })
    productos.value = (r.items as any) ?? []
  } catch { productos.value = [] }
}
onMounted(() => { void cargarProductos(); void cargarClientes(); void cargarHistorial() })

const recetaSeleccionada = ref<number | null>(null)
const nombrePrenda = ref('Bustier Estructurado en Tul y Satén')

// Section 1: Telas & Forros (+ % desperdicio como el BOM)
const metrosTela = ref<number>(1.2)
const precioMetroTela = ref<number>(22000)
const metrosForro = ref<number>(0.6)
const precioMetroForro = ref<number>(12000)
const desperdicioPct = ref<number>(5)

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
      ...((r.items as any[]) ?? []).map((c: any) => ({ label: `${c.nombre} ${c.apellido ?? ''}`.trim(), value: c.id })),
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
const metrosTotalesTela = computed(() => Number(metrosTela.value ?? 0) + Number(metrosForro.value ?? 0))
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

// Margin Slider
const margenPct = ref<number>(60)

const recetasOptions = computed(() => {
  return [
    { label: '-- Cargar desde Receta BOM --', value: null },
    ...(productos.value).map((r) => ({
      label: `${r.nombre} (${r.codigo ?? `PRD-${r.id}`})`,
      value: r.id,
    })),
  ]
})

async function cargarCostoReal() {
  if (!recetaSeleccionada.value) { costoReal.value = null; return }
  loadingCostoReal.value = true
  try {
    const c = await bomApi.getCosto(recetaSeleccionada.value) as { total?: number | string }
    costoReal.value = Number(c.total ?? 0)
  } catch { costoReal.value = null }
  finally { loadingCostoReal.value = false }
}

function onRecetaChange() {
  if (recetaSeleccionada.value) {
    const r = (productos.value).find((x) => x.id === recetaSeleccionada.value)
    if (r) {
      nombrePrenda.value = r.nombre
      // Solo receta: nombre, tiempos, CIF y margen. Las telas/precios/avíos
      // NO se pisan: son decisión de esta cotización, no de la receta.
      // P0-5: la API manda Numeric como string ("83000.0000") y nulls; normalizar
      // con Number() para que InputNumber/slider no queden vacíos.
      tiempoConfeccionMin.value = Number(r.tiempo_confeccion_min ?? 0)
      costoCif.value = Number(r.cif_energia ?? 0)
      margenPct.value = Math.round(Number(r.markup_pct ?? 0))
    }
  }
}

watch(recetaSeleccionada, () => { void cargarCostoReal() })

function usarCostoReal() {
  if (costoReal.value == null) return
  // Proporcional: escala todos los insumos monetarios por el mismo ratio para
  // que el total iguale al real sin distorsionar solo el CIF.
  const totalManual = costoTotalConfeccion.value
  if (totalManual > 0) {
    const ratio = costoReal.value / totalManual
    const round = (v: number) => Math.max(0, Math.round(v))
    precioMetroTela.value = round(precioMetroTela.value * ratio)
    precioMetroForro.value = round(precioMetroForro.value * ratio)
    costoAvios.value = round(costoAvios.value * ratio)
    costoEmpaque.value = round(costoEmpaque.value * ratio)
    tarifaHora.value = round(tarifaHora.value * ratio)
    costoCif.value = round(costoCif.value * ratio)
    showToast('success', 'Costo real aplicado', `Insumos escalados ×${ratio.toFixed(2)} para igualar $${Math.round(costoReal.value).toLocaleString('es-CO')}`)
  } else {
    costoCif.value = costoReal.value
  }
}

// Calculations (telas con % desperdicio, como el BOM con porcentaje_desperdicio)
const subtotalTelas = computed(() => {
  const base = (metrosTela.value * precioMetroTela.value) + (metrosForro.value * precioMetroForro.value)
  return base * (1 + Number(desperdicioPct.value ?? 0) / 100)
})

const subtotalAvios = computed(() => {
  return costoAvios.value + costoEmpaque.value
})

const subtotalManoObra = computed(() => {
  return (tiempoConfeccionMin.value / 60) * tarifaHora.value
})

const costoTotalConfeccion = computed(() => {
  return subtotalTelas.value + subtotalAvios.value + subtotalManoObra.value + costoCif.value
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

function formatCOP(val: number) {
  return `$${Math.round(val).toLocaleString('es-CO')}`
}

function copiarPresupuestoWhatsApp() {
  const nombreCliente = clientesOptions.value.find((c) => c.value === clienteSeleccionado.value)?.label
  const lineas = [
    `✨ *PRESUPUESTO DE CONFECCIÓN • ARPÍA* ✨`,
    ``,
    `👗 *Prenda:* ${nombrePrenda.value}`,
    ...(nombreCliente && clienteSeleccionado.value ? [`👤 *Cliente:* ${nombreCliente}`] : []),
    `🧵 *Tiempo estimado:* ${tiempoConfeccionMin.value} min`,
    `🧷 *Telas y forros (+${Number(desperdicioPct.value ?? 0)}% desperdicio):* ${formatCOP(subtotalTelas.value)}`,
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
    const saved = await createCotizacion({
      producto_id: recetaSeleccionada.value,
      cliente_id: clienteSeleccionado.value,
      nombre_prenda: nombrePrenda.value.trim(),
      metros_tela: metrosTela.value,
      precio_metro_tela: precioMetroTela.value,
      metros_forro: metrosForro.value,
      precio_metro_forro: precioMetroForro.value,
      costo_avios: costoAvios.value,
      costo_empaque: costoEmpaque.value,
      tiempo_confeccion_min: Math.round(tiempoConfeccionMin.value),
      tarifa_hora: tarifaHora.value,
      costo_cif: costoCif.value,
      margen_pct: margenPct.value,
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

        <!-- Section 1: Telas y Forros -->
        <div class="bg-stone-900/80 border border-stone-800 rounded-2xl p-5 shadow-lg space-y-4">
          <div class="flex items-center justify-between border-b border-stone-800 pb-2">
            <div class="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-amber-400">
              <i class="pi pi-clone" /> 1. Telas y Forros Directos
            </div>
            <span class="font-mono text-xs font-bold text-stone-300">{{ formatCOP(subtotalTelas) }}</span>
          </div>

          <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div>
              <label class="block text-[11px] text-stone-400 mb-1">Metros Tela Principal</label>
              <InputNumber v-model="metrosTela" mode="decimal" locale="es-CO" :min="0.1" :max-fraction-digits="2" class="w-full font-mono text-xs" />
            </div>
            <div>
              <label class="block text-[11px] text-stone-400 mb-1">Precio Metro ($)</label>
              <InputNumber v-model="precioMetroTela" mode="currency" currency="COP" locale="es-CO" :min-fraction-digits="0" :max-fraction-digits="2" class="w-full font-mono text-xs" />
            </div>
            <div>
              <label class="block text-[11px] text-stone-400 mb-1">Metros Forro / Entretela</label>
              <InputNumber v-model="metrosForro" mode="decimal" locale="es-CO" :min="0" :max-fraction-digits="2" class="w-full font-mono text-xs" />
            </div>
            <div>
              <label class="block text-[11px] text-stone-400 mb-1">Precio Forro/m ($)</label>
              <InputNumber v-model="precioMetroForro" mode="currency" currency="COP" locale="es-CO" :min-fraction-digits="0" :max-fraction-digits="2" class="w-full font-mono text-xs" />
            </div>
          </div>
          <div class="flex items-center gap-2">
            <label class="text-[11px] text-stone-400">Desperdicio telas (%)</label>
            <InputNumber v-model="desperdicioPct" :min="0" :max="50" class="w-24 font-mono text-xs" />
            <span class="text-[10px] text-stone-500">Como el BOM: cubre merma de corte.</span>
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
            <span class="font-mono text-sm font-extrabold text-amber-300">{{ margenPct }}%</span>
          </div>

          <Slider v-model="margenPct" :min="20" :max="90" class="w-full" />

          <div class="flex justify-between text-[11px] text-stone-500 font-medium">
            <span>20% (Mayorista)</span>
            <span class="text-amber-400 font-bold">55% - 65% (Taller Estándar)</span>
            <span>80%+ (Alta Costura)</span>
          </div>
          <p class="text-[10px] text-stone-500 m-0">Regla visible: margen ≥100% usa ×2.2 fijo; margen que deje menos de 5% de factor usa ×2 (tope anti-margen-cero). Igual en servidor.</p>
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
              <span>Telas & Forros:</span>
              <span class="font-mono font-semibold">{{ formatCOP(subtotalTelas) }}</span>
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
              <div v-if="costoReal !== null" class="flex justify-end">
                <button type="button" class="px-2.5 py-1 rounded-lg bg-amber-500/20 border border-amber-500/30 text-amber-300 text-xs font-bold hover:bg-amber-500/30" @click="usarCostoReal">Usar costo real</button>
              </div>
              <div v-if="costoReal !== null && Math.abs(costoReal - costoTotalConfeccion) > 100" class="text-[11px] text-center" :class="costoReal > costoTotalConfeccion ? 'text-amber-400' : 'text-emerald-400'">
                {{ costoReal > costoTotalConfeccion ? '▲' : '▼' }} Diferencia {{ formatCOP(Math.abs(costoReal - costoTotalConfeccion)) }} vs cálculo manual
              </div>
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
