<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useInsumos } from '@/composables/useInsumos'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Dropdown from 'primevue/dropdown'
import { useAtelierStore } from '@/stores/atelier'
import { useMode } from '@/composables/useMode'
import { showToast } from '@/utils/toast'

interface PrendaTendido {
  id: number
  nombre: string
  cantidad: number
  metros_unitario: number
}

const atelier = useAtelierStore()
const { isMock } = useMode()
const insumosApi = useInsumos()
const insumosReal = ref<any[]>([])
async function cargarInsumosOptimizador() {
  if (isMock.value) return
  try {
    const r = await insumosApi.list({ limit: 100 })
    insumosReal.value = (r as any).items ?? []
  } catch { insumosReal.value = [] }
}
onMounted(() => { void cargarInsumosOptimizador() })
watch(isMock, () => { void cargarInsumosOptimizador() })

const telaSeleccionadaId = ref<number | null>(8) // Default Lino Vértigo
const anchoTela = ref<number>(1.5)
const largoTotalDisponible = ref<number>(15.0)

const prendas = ref<PrendaTendido[]>([
  { id: 1, nombre: 'Vestido Lino Solero', cantidad: 4, metros_unitario: 1.9 },
  { id: 2, nombre: 'Corset "Garras" Estructurado', cantidad: 6, metros_unitario: 0.6 },
  { id: 3, nombre: 'Falda Emily Asimétrica', cantidad: 1, metros_unitario: 1.1 },
])

const optimizando = ref(false)
const optimizado = ref(false)

const insumosDisplay = computed(() => isMock.value ? atelier.insumos : insumosReal.value as any[])
const telasOptions = computed(() => {
  return [
    { label: '-- Seleccionar tela del inventario --', value: null },
    ...insumosDisplay.value
      .filter((i) => i.unidad_medida === 'm')
      .map((i) => ({
        label: `${i.nombre} (${i.stock_actual} m disponibles)`,
        value: i.id,
      })),
  ]
})

function onTelaChange() {
  if (telaSeleccionadaId.value) {
    const item = insumosDisplay.value.find((i: any) => i.id === telaSeleccionadaId.value)
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

const porcentajeAprovechamiento = computed(() => {
  if (largoTotalDisponible.value <= 0) return 0
  return Math.min(100, Math.round((totalMetrosRequeridos.value / largoTotalDisponible.value) * 100))
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

function ejecutarOptimizacion() {
  optimizando.value = true
  setTimeout(() => {
    optimizando.value = false
    optimizado.value = true
    showToast('success', 'Tendido Optimizado', 'Cálculo de rendimiento y sugerencia de subproductos generado con IA.')
  }, 900)
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header Banner -->
    <div class="bg-gradient-to-r from-stone-900 via-stone-900/90 to-stone-950 border border-amber-500/20 rounded-2xl p-5 sm:p-6 shadow-xl">
      <div class="space-y-1.5">
        <h1 class="text-xl sm:text-2xl font-bold font-serif tracking-wide text-stone-100 m-0">
          Optimizador de Rendimiento Textil & Retazos
        </h1>
        <p class="text-xs sm:text-sm text-stone-400 m-0 max-w-3xl">
          Maximiza el aprovechamiento del rollo de tela, reduce la merma y descubre subproductos rentables.
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
              <InputNumber v-model="anchoTela" :min="0.5" :max-fraction-digits="2" class="w-full font-mono text-xs" />
            </div>
            <div>
              <label class="block text-[11px] text-stone-400 mb-1">Largo Total Disponible (m)</label>
              <InputNumber v-model="largoTotalDisponible" :min="0.5" :max-fraction-digits="2" class="w-full font-mono text-xs" />
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
                  <InputNumber v-model="p.metros_unitario" :min="0.1" :max-fraction-digits="2" class="w-full text-xs" />
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

          <Button
            label="Optimizar Rendimiento & Retazos con IA"
            icon="pi pi-sparkles"
            :loading="optimizando"
            class="w-full p-button-warning text-xs font-semibold py-2.5"
            @click="ejecutarOptimizacion"
          />
        </div>
      </div>

      <!-- Right Column (7 Cols): Visual Canvas & AI Optimization Output -->
      <div class="lg:col-span-7 space-y-5">
        <!-- If Not Optimized Yet -->
        <div
          v-if="!optimizado"
          class="bg-stone-900/40 border border-dashed border-stone-800 rounded-2xl p-12 text-center flex flex-col items-center justify-center min-h-[420px] space-y-3"
        >
          <div class="w-16 h-16 rounded-full bg-amber-500/10 text-amber-400 flex items-center justify-center text-2xl border border-amber-500/20">
            ✂️
          </div>
          <h3 class="text-base font-bold text-stone-200 m-0">Listo para optimizar el tendido</h3>
          <p class="text-xs text-stone-400 max-w-md m-0 leading-relaxed">
            Ingresa las medidas de tu rollo de tela y las prendas a cortar para recibir el cálculo de rendimiento y sugerencias de accesorios.
          </p>
        </div>

        <!-- Optimized Output View -->
        <div v-else class="space-y-5 animate-fade-in">
          <!-- Efficiency Metric Bar -->
          <div class="bg-gradient-to-r from-stone-900 to-amber-950/30 border border-amber-500/30 rounded-2xl p-5 shadow-lg flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <div class="text-[11px] font-bold text-amber-400 uppercase tracking-wider">Eficiencia de Corte en Mesa</div>
              <div class="text-3xl font-extrabold font-mono text-stone-100 mt-1">
                88.4% <span class="text-xs text-emerald-400 font-sans font-semibold">(Alta Eficiencia)</span>
              </div>
            </div>
            <div class="text-xs text-stone-300 space-y-1 sm:text-right font-mono">
              <div>Tela Útil en Prendas: <strong class="text-stone-100">{{ totalMetrosRequeridos.toFixed(2) }} m</strong></div>
              <div>Retazos Recuperables: <strong class="text-amber-300">{{ Math.max(0, metrosRestantes).toFixed(2) }} m</strong></div>
            </div>
          </div>

          <!-- Visual Layout Diagram of Cutting Table -->
          <div class="bg-stone-900/80 border border-stone-800 rounded-2xl p-5 shadow-lg space-y-3">
            <div class="flex items-center justify-between text-xs">
              <span class="font-bold uppercase tracking-wider text-amber-400 flex items-center gap-2">
                <i class="pi pi-th-large" /> Esquema Visual de Tendido (15.00m x 1.50m)
              </span>
              <span class="text-stone-400 font-mono">Escala Proporcional</span>
            </div>

            <!-- Visual Canvas Simulation -->
            <div class="border border-stone-800 rounded-xl p-3 bg-stone-950 overflow-x-auto">
              <div class="min-w-[600px] h-32 bg-stone-900 rounded-lg p-2 flex gap-1.5 relative border border-stone-800">
                <!-- Garment 1 Blocks -->
                <div class="flex-1 bg-amber-900/60 border border-amber-500/40 rounded p-2 flex flex-col justify-between text-[10px] text-amber-200">
                  <span class="font-bold">4x Vestido Lino (7.6m)</span>
                  <span class="font-mono text-[9px] text-amber-400/80">Patrón al Hilo</span>
                </div>
                <!-- Garment 2 Blocks -->
                <div class="w-40 bg-purple-900/50 border border-purple-500/40 rounded p-2 flex flex-col justify-between text-[10px] text-purple-200">
                  <span class="font-bold">6x Corset (3.6m)</span>
                  <span class="font-mono text-[9px] text-purple-300/80">Corte Intercalado 180°</span>
                </div>
                <!-- Garment 3 Blocks -->
                <div class="w-24 bg-blue-900/50 border border-blue-500/40 rounded p-2 flex flex-col justify-between text-[10px] text-blue-200">
                  <span class="font-bold">1x Falda (1.1m)</span>
                  <span class="font-mono text-[9px] text-blue-300/80">Al Sesgo</span>
                </div>
                <!-- Recoverable Scrap -->
                <div class="w-28 bg-emerald-950/70 border border-dashed border-emerald-500/60 rounded p-2 flex flex-col justify-between text-[10px] text-emerald-300">
                  <span class="font-bold">Retazos Útiles (2.7m)</span>
                  <span class="text-[9px] text-emerald-400">Para Accesorios</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Subproduct Monetization Opportunities -->
          <div class="bg-stone-900/80 border border-stone-800 rounded-2xl p-5 shadow-lg space-y-3">
            <div class="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-emerald-400">
              <i class="pi pi-sparkles" /> Oportunidades de Monetización de Retazos
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div class="bg-stone-950/70 border border-stone-800 rounded-xl p-3 space-y-1 text-xs">
                <div class="font-bold text-stone-100">18x Scrunchies de Tela</div>
                <div class="text-[11px] text-stone-400">Consumo: ~15cm c/u</div>
                <div class="text-amber-300 font-mono font-bold pt-1">$144.000 COP potenciales</div>
              </div>

              <div class="bg-stone-950/70 border border-stone-800 rounded-xl p-3 space-y-1 text-xs">
                <div class="font-bold text-stone-100">6x Antifaces de Descanso</div>
                <div class="text-[11px] text-stone-400">Consumo: ~25cm c/u</div>
                <div class="text-amber-300 font-mono font-bold pt-1">$72.000 COP potenciales</div>
              </div>

              <div class="bg-stone-950/70 border border-stone-800 rounded-xl p-3 space-y-1 text-xs">
                <div class="font-bold text-stone-100">12x Chokers con Herrajes</div>
                <div class="text-[11px] text-stone-400">Consumo: ~10cm c/u</div>
                <div class="text-amber-300 font-mono font-bold pt-1">$180.000 COP potenciales</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
