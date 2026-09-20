<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useInsumos } from '@/composables/useInsumos'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Dropdown from 'primevue/dropdown'

interface PrendaTendido {
  id: number
  nombre: string
  cantidad: number
  metros_unitario: number
}

const insumosApi = useInsumos()
const insumos = ref<any[]>([])
async function cargarInsumos() {
  try {
    const r = await insumosApi.list({ limit: 100 })
    insumos.value = (r as any).items ?? []
  } catch { insumos.value = [] }
}
onMounted(() => { void cargarInsumos() })

const telaSeleccionadaId = ref<number | null>(null) // No default: the user picks a real fabric from inventory
const anchoTela = ref<number>(1.5)
const largoTotalDisponible = ref<number>(15.0)

// Fixed selvedge assumption: 2 cm per edge (2 x 0.02 m = 0.04 m) are not
// usable for cutting. Simple arithmetic only, no nesting computation.
const ORILLO_POR_BORDE_M = 0.02
const DESPERDICIO_ORILLOS_M = ORILLO_POR_BORDE_M * 2

const prendas = ref<PrendaTendido[]>([
  { id: 1, nombre: 'Vestido Lino Solero', cantidad: 4, metros_unitario: 1.9 },
  { id: 2, nombre: 'Corset "Garras" Estructurado', cantidad: 6, metros_unitario: 0.6 },
  { id: 3, nombre: 'Falda Emily Asimétrica', cantidad: 1, metros_unitario: 1.1 },
])

const telasOptions = computed(() => {
  return [
    { label: '-- Seleccionar tela del inventario --', value: null },
    ...insumos.value
      .filter((i) => i.unidad_medida === 'm')
      .map((i) => ({
        label: `${i.nombre} (${i.stock_actual} m disponibles)`,
        value: i.id,
      })),
  ]
})

function onTelaChange() {
  if (telaSeleccionadaId.value) {
    const item = insumos.value.find((i: any) => i.id === telaSeleccionadaId.value)
    if (item) {
      largoTotalDisponible.value = item.stock_actual
    }
  }
}

const totalMetrosRequeridos = computed(() => {
  return prendas.value.reduce((acc, p) => acc + (p.cantidad * p.metros_unitario), 0)
})

const metrosRestantes = computed(() => {
  return largoTotalDisponible.value - totalMetrosRequeridos.value
})

// Usable width = nominal width minus fixed selvedge waste (never negative).
const anchoUtilEstimado = computed(() => {
  return Math.max(0, anchoTela.value - DESPERDICIO_ORILLOS_M)
})

// Selvedge waste share of the nominal width, as a percentage.
const desperdicioOrillosPct = computed(() => {
  if (anchoTela.value <= 0) return 0
  return Math.min(100, (DESPERDICIO_ORILLOS_M / anchoTela.value) * 100)
})

// Whether there is anything to calculate (honest data-driven flag).
const tieneCalculo = computed(() => {
  return prendas.value.length > 0 && largoTotalDisponible.value > 0
})

const porcentajeAprovechamiento = computed(() => {
  if (largoTotalDisponible.value <= 0) return 0
  return Math.min(100, Math.round((totalMetrosRequeridos.value / largoTotalDisponible.value) * 100))
})

// Efficiency label from the real length calculation (honest thresholds).
const etiquetaEficiencia = computed(() => {
  const p = porcentajeAprovechamiento.value
  if (p >= 85) return 'Alta Eficiencia'
  if (p >= 60) return 'Eficiencia Media'
  if (p > 0) return 'Baja Eficiencia'
  return 'Sin cálculo'
})

function agregarPrenda() {
  const nextId = (prendas.value.length ? Math.max(...prendas.value.map((p) => p.id)) : 0) + 1
  prendas.value.push({
    id: nextId,
    nombre: 'Nueva Prenda de Corte',
    cantidad: 2,
    metros_unitario: 0.8,
  })
}

function eliminarPrenda(id: number) {
  prendas.value = prendas.value.filter((p) => p.id !== id)
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header Banner -->
    <div class="bg-gradient-to-r from-stone-900 via-stone-900/90 to-stone-950 border border-amber-500/20 rounded-2xl p-5 sm:p-6 shadow-xl">
      <div class="space-y-1.5">
        <h1 class="text-xl sm:text-2xl font-bold font-serif tracking-wide text-stone-100 m-0">
          Calculadora de Tendido y Rendimiento Textil
        </h1>
        <p class="text-xs sm:text-sm text-stone-400 m-0 max-w-3xl">
          Calcula cuánta tela requiere el tendido, el aprovechamiento del rollo y una estimación simple del sobrante.
        </p>
      </div>
    </div>

    <!-- Main Grid -->
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
      <!-- Left Column (5 Cols): Form Parameters -->
      <div class="lg:col-span-5 space-y-5">
        <!-- Fabric Roll Data -->
        <div class="bg-stone-900/80 border border-stone-800 rounded-2xl p-5 shadow-lg space-y-4">
          <div class="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-amber-400 border-b border-stone-800 pb-2">
            <i class="pi pi-box" /> Datos del Rollo o Corte de Tela
          </div>

          <div>
            <label class="block text-xs text-stone-400 mb-1">Cargar Tela desde Inventario</label>
            <Dropdown
              v-model="telaSeleccionadaId"
              :options="telasOptions"
              option-label="label"
              option-value="value"
              class="w-full text-xs"
              @change="onTelaChange"
            />
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-[11px] text-stone-400 mb-1">Ancho de Tela (m)</label>
              <InputNumber v-model="anchoTela" mode="decimal" locale="es-CO" :min="0.5" :max-fraction-digits="2" class="w-full font-mono text-xs" />
              <p class="text-[10px] text-stone-500 mt-1 m-0">Se descuentan 2 × 2 cm de orillos no utilizables del ancho total.</p>
            </div>
            <div>
              <label class="block text-[11px] text-stone-400 mb-1">Largo Total Disponible (m)</label>
              <InputNumber v-model="largoTotalDisponible" mode="decimal" locale="es-CO" :min="0.5" :max-fraction-digits="2" class="w-full font-mono text-xs" />
            </div>
          </div>
        </div>

        <!-- Garment Cuts Table -->
        <div class="bg-stone-900/80 border border-stone-800 rounded-2xl p-5 shadow-lg space-y-4">
          <div class="flex items-center justify-between border-b border-stone-800 pb-2">
            <div class="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-amber-400">
              <i class="pi pi-list" /> Prendas a Cortar en la Mesa
            </div>
            <button
              type="button"
              class="text-xs text-amber-400 hover:underline font-bold flex items-center gap-1"
              @click="agregarPrenda"
            >
              + Agregar Prenda
            </button>
          </div>

          <div class="space-y-3">
            <div
              v-for="p in prendas"
              :key="p.id"
              class="bg-stone-950/70 border border-stone-800/80 rounded-xl p-3 space-y-2 text-xs"
            >
              <div class="flex items-center justify-between gap-2">
                <InputText v-model="p.nombre" class="w-full text-xs font-medium" placeholder="Nombre de la prenda" />
                <button
                  type="button"
                  class="p-1.5 text-stone-500 hover:text-red-400 transition"
                  title="Eliminar fila"
                  @click="eliminarPrenda(p.id)"
                >
                  <i class="pi pi-trash text-xs" />
                </button>
              </div>

              <div class="grid grid-cols-2 gap-2 font-mono">
                <div>
                  <span class="block text-[10px] text-stone-400 font-sans">Cantidad</span>
                  <InputNumber v-model="p.cantidad" :min="1" class="w-full text-xs" />
                </div>
                <div>
                  <span class="block text-[10px] text-stone-400 font-sans">Metros c/u</span>
                  <InputNumber v-model="p.metros_unitario" mode="decimal" locale="es-CO" :min="0.1" :max-fraction-digits="2" class="w-full text-xs" />
                </div>
              </div>

              <div class="flex justify-between items-center text-[11px] text-stone-400 pt-1 border-t border-stone-800/60 font-mono">
                <span>Subtotal Tela:</span>
                <strong class="text-amber-300">{{ (p.cantidad * p.metros_unitario).toFixed(2) }} m</strong>
              </div>
            </div>
          </div>

          <!-- Total Requirement Indicator -->
          <div class="bg-stone-950/90 border border-stone-800 rounded-xl p-3.5 space-y-2">
            <div class="flex justify-between text-xs font-mono">
              <span class="text-stone-400 font-sans">Total Tela Requerida:</span>
              <strong class="text-stone-100">{{ totalMetrosRequeridos.toFixed(2) }} m de {{ largoTotalDisponible.toFixed(2) }} m</strong>
            </div>
            <div class="w-full bg-stone-800 h-2 rounded-full overflow-hidden">
              <div
                class="h-full rounded-full"
                :class="porcentajeAprovechamiento > 100 ? 'bg-red-500' : 'bg-gradient-to-r from-amber-500 to-emerald-400'"
                :style="{ width: `${Math.min(100, porcentajeAprovechamiento)}%` }"
              />
            </div>
            <div class="flex justify-between text-[11px]">
              <span class="text-stone-400">Aprovechamiento: {{ porcentajeAprovechamiento }}%</span>
              <span :class="metrosRestantes < 0 ? 'text-red-400 font-bold' : 'text-emerald-400 font-bold'">
                {{ metrosRestantes >= 0 ? `Sobrante: ${metrosRestantes.toFixed(2)} m` : `Faltan: ${Math.abs(metrosRestantes).toFixed(2)} m` }}
              </span>
            </div>
          </div>

          <!-- Results update automatically from the inputs above (no calculation step needed). -->
        </div>
      </div>

      <!-- Right Column (7 Cols): Live calculation results -->
      <div class="lg:col-span-7 space-y-5">
        <!-- Empty state: no rows to calculate yet -->
        <div
          v-if="!tieneCalculo"
          class="bg-stone-900/40 border border-dashed border-stone-800 rounded-2xl p-12 text-center flex flex-col items-center justify-center min-h-[420px] space-y-3"
        >
          <div class="w-16 h-16 rounded-full bg-amber-500/10 text-amber-400 flex items-center justify-center text-2xl border border-amber-500/20">
            ✂️
          </div>
          <h3 class="text-base font-bold text-stone-200 m-0">Agrega prendas para ver el cálculo del tendido</h3>
          <p class="text-xs text-stone-400 max-w-md m-0 leading-relaxed">
            Ingresa las medidas de tu rollo de tela y las prendas a cortar para ver el cálculo de rendimiento y el sobrante estimado.
          </p>
        </div>

        <!-- Live results (computed synchronously from the inputs) -->
        <div v-else class="space-y-5 animate-fade-in">
          <!-- Efficiency Metric Bar -->
          <div class="bg-gradient-to-r from-stone-900 to-amber-950/30 border border-amber-500/30 rounded-2xl p-5 shadow-lg flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <div class="text-[11px] font-bold text-amber-400 uppercase tracking-wider">Eficiencia de Corte en Mesa</div>
              <div class="text-3xl font-extrabold font-mono text-stone-100 mt-1">
                {{ porcentajeAprovechamiento }}% <span class="text-xs text-emerald-400 font-sans font-semibold">({{ etiquetaEficiencia }})</span>
              </div>
            </div>
            <div class="text-xs text-stone-300 space-y-1 sm:text-right font-mono">
              <div>Tela Útil en Prendas: <strong class="text-stone-100">{{ totalMetrosRequeridos.toFixed(2) }} m</strong></div>
              <div>Retazos Recuperables: <strong class="text-amber-300">{{ Math.max(0, metrosRestantes).toFixed(2) }} m</strong></div>
            </div>
          </div>

          <!-- Width usage: nominal width vs usable width after selvedge -->
          <div class="bg-stone-900/80 border border-stone-800 rounded-2xl p-5 shadow-lg space-y-2">
            <div class="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-amber-400">
              <i class="pi pi-arrows-h" /> Aprovechamiento del Ancho
            </div>
            <div class="text-xs text-stone-300 font-mono space-y-1">
              <div>Ancho total: <strong class="text-stone-100">{{ anchoTela.toFixed(2) }} m</strong></div>
              <div>Ancho útil estimado: <strong class="text-stone-100">{{ anchoUtilEstimado.toFixed(2) }} m</strong></div>
              <div>Desperdicio estimado (orillos): <strong class="text-amber-300">{{ desperdicioOrillosPct.toFixed(1) }} %</strong></div>
            </div>
            <p class="text-[10px] text-stone-500 m-0">Estimación simple: se restan 2 × 2 cm de orillos del ancho total. Sin cálculo de encaje de patrones.</p>
          </div>

          <!-- Visual Layout Diagram of Cutting Table -->
          <div class="bg-stone-900/80 border border-stone-800 rounded-2xl p-5 shadow-lg space-y-3">
            <div class="flex items-center justify-between text-xs">
              <span class="font-bold uppercase tracking-wider text-amber-400 flex items-center gap-2">
                <i class="pi pi-th-large" /> Esquema Visual de Tendido ({{ largoTotalDisponible.toFixed(2) }}m x {{ anchoTela.toFixed(2) }}m)
              </span>
              <span class="text-stone-400 font-mono">Escala Proporcional</span>
            </div>

            <!-- Visual Canvas Simulation -->
            <div class="border border-stone-800 rounded-xl p-3 bg-stone-950 overflow-x-auto">
              <div class="min-w-[600px] h-32 bg-stone-900 rounded-lg p-2 flex gap-1.5 relative border border-stone-800">
                <div
                  v-for="(p, idx) in prendas"
                  :key="p.id"
                  class="rounded p-2 flex flex-col justify-between text-[10px]"
                  :class="idx % 3 === 0 ? 'bg-amber-900/60 border border-amber-500/40 text-amber-200' : idx % 3 === 1 ? 'bg-purple-900/50 border border-purple-500/40 text-purple-200' : 'bg-blue-900/50 border border-blue-500/40 text-blue-200'"
                  :style="{ flex: `${p.cantidad * p.metros_unitario}` }"
                >
                  <span class="font-bold">{{ p.cantidad }}x {{ p.nombre }} ({{ (p.cantidad * p.metros_unitario).toFixed(1) }}m)</span>
                  <span class="font-mono text-[9px] opacity-80">Patrón al Hilo</span>
                </div>
                <!-- Recoverable Scrap -->
                <div
                  v-if="metrosRestantes > 0"
                  class="bg-emerald-950/70 border border-dashed border-emerald-500/60 rounded p-2 flex flex-col justify-between text-[10px] text-emerald-300"
                  :style="{ flex: `${metrosRestantes}` }"
                >
                  <span class="font-bold">Retazos Útiles ({{ metrosRestantes.toFixed(2) }}m)</span>
                  <span class="text-[9px] text-emerald-400">Para Accesorios</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Remnant reuse ideas (simple estimates from the leftover meters) -->
          <div v-if="metrosRestantes > 0" class="bg-stone-900/80 border border-stone-800 rounded-2xl p-5 shadow-lg space-y-3">
            <div class="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-emerald-400">
              <i class="pi pi-lightbulb" /> Ideas para Aprovechar los Retazos
            </div>
            <p class="text-[10px] text-stone-500 m-0">Estimación simple a partir de los metros sobrantes; los valores son potenciales, no precios de venta.</p>
            <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div class="bg-stone-950/70 border border-stone-800 rounded-xl p-3 space-y-1 text-xs">
                <div class="font-bold text-stone-100">{{ Math.floor(metrosRestantes / 0.15) }}x Scrunchies de Tela</div>
                <div class="text-[11px] text-stone-400">Consumo: ~0.15m c/u</div>
                <div class="text-amber-300 font-mono font-bold pt-1">${{(Math.floor(metrosRestantes / 0.15) * 8000).toLocaleString('es-CO')}} COP potenciales</div>
              </div>

              <div class="bg-stone-950/70 border border-stone-800 rounded-xl p-3 space-y-1 text-xs">
                <div class="font-bold text-stone-100">{{ Math.floor(metrosRestantes / 0.25) }}x Antifaces de Descanso</div>
                <div class="text-[11px] text-stone-400">Consumo: ~0.25m c/u</div>
                <div class="text-amber-300 font-mono font-bold pt-1">${{(Math.floor(metrosRestantes / 0.25) * 12000).toLocaleString('es-CO')}} COP potenciales</div>
              </div>

              <div class="bg-stone-950/70 border border-stone-800 rounded-xl p-3 space-y-1 text-xs">
                <div class="font-bold text-stone-100">{{ Math.floor(metrosRestantes / 0.10) }}x Chokers con Herrajes</div>
                <div class="text-[11px] text-stone-400">Consumo: ~0.10m c/u</div>
                <div class="text-amber-300 font-mono font-bold pt-1">${{(Math.floor(metrosRestantes / 0.10) * 15000).toLocaleString('es-CO')}} COP potenciales</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
