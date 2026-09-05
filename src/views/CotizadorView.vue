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
import { useAtelierStore } from '@/stores/atelier'
import { useMode } from '@/composables/useMode'
import { showToast } from '@/utils/toast'

const router = useRouter()
const atelier = useAtelierStore()
const { isMock } = useMode()
const productosApi = useProductos()
const bomApi = useBom()
const productosRealCot = ref<any[]>([])
const costoRealCot = ref<number | null>(null)
const loadingCostoReal = ref(false)
async function cargarProductosCotizador() {
  if (isMock.value) return
  try {
    const r = await productosApi.list({ limit: 100 })
    productosRealCot.value = (r.items as any) ?? []
  } catch { productosRealCot.value = [] }
}
onMounted(() => { void cargarProductosCotizador() })
watch(isMock, () => { void cargarProductosCotizador() })

const recetaSeleccionada = ref<number | null>(null)
const nombrePrenda = ref('Bustier Estructurado en Tul y Satén')

// Section 1: Telas & Forros
const metrosTela = ref<number>(1.2)
const precioMetroTela = ref<number>(22000)
const metrosForro = ref<number>(0.6)
const precioMetroForro = ref<number>(12000)

// Section 2: Avíos, Cierres & Empaque
const costoAvios = ref<number>(6500)
const costoEmpaque = ref<number>(4500)

// Section 3: Mano de Obra & Costos Fijos
const tiempoConfeccionMin = ref<number>(120)
const tarifaHora = ref<number>(8000)
const costoCif = ref<number>(2000)

// Margin Slider
const margenPct = ref<number>(60)

const recetasOptions = computed(() => {
  return [
    { label: '-- Cargar desde Receta BOM --', value: null },
    ...(isMock.value ? atelier.recetas : productosRealCot.value).map((r) => ({
      label: `${r.nombre} (${r.codigo ?? `PRD-${r.id}`})`,
      value: r.id,
    })),
  ]
})

async function cargarCostoRealCot() {
  if (isMock.value || !recetaSeleccionada.value) { costoRealCot.value = null; return }
  loadingCostoReal.value = true
  try {
    const c = await bomApi.getCosto(recetaSeleccionada.value) as { total?: number | string }
    costoRealCot.value = Number(c.total ?? 0)
  } catch { costoRealCot.value = null }
  finally { loadingCostoReal.value = false }
}

function onRecetaChange() {
  if (recetaSeleccionada.value) {
    const r = (isMock.value ? atelier.recetas : productosRealCot.value).find((x) => x.id === recetaSeleccionada.value)
    if (r) {
      nombrePrenda.value = r.nombre
      // P0-5: la API manda Numeric como string ("83000.0000") y nulls; normalizar
      // con Number() para que InputNumber/slider no queden vacíos.
      tiempoConfeccionMin.value = Number(r.tiempo_confeccion_min ?? 0)
      costoCif.value = Number(r.cif_energia ?? 0)
      margenPct.value = Math.round(Number(r.markup_pct ?? 0))
      metrosTela.value = 1.0
      precioMetroTela.value = Math.round(Number(r.costo_insumos ?? 0) * 0.7)
      metrosForro.value = 0.5
      precioMetroForro.value = Math.round(Number(r.costo_insumos ?? 0) * 0.3)
      costoAvios.value = 4000
      costoEmpaque.value = 3500
    }
  }
}

watch(recetaSeleccionada, () => { void cargarCostoRealCot() })

function usarCostoReal() {
  if (costoRealCot.value == null) return
  // Distribuye el costo real entre los campos manuales de forma proporcional al cálculo actual
  const totalManual = costoTotalConfeccion.value
  if (totalManual > 0) {
    const ratio = costoRealCot.value / totalManual
    // Ajusta CIF para que el total manual iguale al real (lo más simple y reversible)
    const diff = costoRealCot.value - totalManual
    costoCif.value = Math.max(0, costoCif.value + diff)
    showToast('success', 'Costo real aplicado', `CIF ajustado en ${diff > 0 ? '+' : ''}${Math.round(diff).toLocaleString('es-CO')} para igualar $${Math.round(costoRealCot.value).toLocaleString('es-CO')}`)
  } else {
    costoCif.value = costoRealCot.value
  }
}

// Calculations
const subtotalTelas = computed(() => {
  return (metrosTela.value * precioMetroTela.value) + (metrosForro.value * precioMetroForro.value)
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
  const text = `✨ *PRESUPUESTO DE CONFECCIÓN • ATELIER ARPÍA* ✨\n\n👗 *Prenda:* ${nombrePrenda.value}\n🧵 *Tiempo estimado de confección:* ${tiempoConfeccionMin.value} min\n📦 *Incluye:* Telas de alta costura, forros anatómicos, herrajes reforzados y empaque de lujo.\n\n💎 *Valor Total de la Prenda:* ${formatCOP(precioVentaSugerido.value)} COP\n\n_Para apartar cupo en el taller requerimos un abono del 50%._ 🖤`

  navigator.clipboard.writeText(text)
  showToast('success', 'Copiado al Portapapeles', 'El presupuesto formateado para WhatsApp se ha copiado con éxito.')
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
              <InputNumber v-model="metrosTela" :min="0.1" :max-fraction-digits="2" class="w-full font-mono text-xs" />
            </div>
            <div>
              <label class="block text-[11px] text-stone-400 mb-1">Precio Metro ($)</label>
              <InputNumber v-model="precioMetroTela" mode="currency" currency="COP" locale="es-CO" :min-fraction-digits="0" class="w-full font-mono text-xs" />
            </div>
            <div>
              <label class="block text-[11px] text-stone-400 mb-1">Metros Forro / Entretela</label>
              <InputNumber v-model="metrosForro" :min="0" :max-fraction-digits="2" class="w-full font-mono text-xs" />
            </div>
            <div>
              <label class="block text-[11px] text-stone-400 mb-1">Precio Forro/m ($)</label>
              <InputNumber v-model="precioMetroForro" mode="currency" currency="COP" locale="es-CO" :min-fraction-digits="0" class="w-full font-mono text-xs" />
            </div>
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
              <InputNumber v-model="costoAvios" mode="currency" currency="COP" locale="es-CO" :min-fraction-digits="0" class="w-full font-mono text-xs" />
            </div>
            <div>
              <label class="block text-[11px] text-stone-400 mb-1">Empaque, Bolsa & Etiquetas ($)</label>
              <InputNumber v-model="costoEmpaque" mode="currency" currency="COP" locale="es-CO" :min-fraction-digits="0" class="w-full font-mono text-xs" />
            </div>
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
              <InputNumber v-model="tarifaHora" mode="currency" currency="COP" locale="es-CO" :min-fraction-digits="0" class="w-full font-mono text-xs" />
            </div>
            <div>
              <label class="block text-[11px] text-stone-400 mb-1">Costos CIF / Luz ($)</label>
              <InputNumber v-model="costoCif" mode="currency" currency="COP" locale="es-CO" :min-fraction-digits="0" class="w-full font-mono text-xs" />
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

              <div v-if="!isMock && recetaSeleccionada" class="flex justify-between py-1.5 text-xs bg-amber-950/20 border border-amber-500/20 rounded-lg px-2">
                <span class="text-amber-300 flex items-center gap-1"><i class="pi pi-database text-[10px]" /> Costo real BOM (DB):</span>
                <span class="font-mono font-bold" :class="loadingCostoReal ? 'text-stone-400' : 'text-amber-300'">{{ loadingCostoReal ? 'Cargando...' : (costoRealCot !== null ? formatCOP(costoRealCot!) : 'Sin BOM') }}</span>
              </div>
              <div v-if="!isMock && costoRealCot !== null" class="flex justify-end">
                <button type="button" class="px-2.5 py-1 rounded-lg bg-amber-500/20 border border-amber-500/30 text-amber-300 text-xs font-bold hover:bg-amber-500/30" @click="usarCostoReal">Usar costo real</button>
              </div>
              <div v-if="!isMock && costoRealCot !== null && Math.abs(costoRealCot - costoTotalConfeccion) > 100" class="text-[11px] text-center" :class="costoRealCot > costoTotalConfeccion ? 'text-amber-400' : 'text-emerald-400'">
                {{ costoRealCot > costoTotalConfeccion ? '▲' : '▼' }} Diferencia {{ formatCOP(Math.abs(costoRealCot - costoTotalConfeccion)) }} vs cálculo manual
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
  </div>
</template>
