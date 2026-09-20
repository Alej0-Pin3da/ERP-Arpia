<script setup lang="ts">
import { ref } from 'vue'
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'
import Textarea from 'primevue/textarea'

/** Built-in workshop suggestion shown read-only (bundled examples, no backend or AI service). */
export interface RecetaSugerida {
  nombre: string
  categoria: string
  linea: string
  descripcion: string
  tiempo_confeccion_min: number
  costo_insumos: number
  mano_obra: number
  cif_energia: number
  costo_total_unitario: number
  precio_venta: number
  markup_pct: number
  recomendaciones_taller: string
  items: { nombre: string; consumo_unitario: number; unidad: string; merma_pct: number; costo_unitario: number; subtotal: number }[]
}

defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
}>()

const prompt = ref('')
const loading = ref(false)
const respuesta = ref<string | null>(null)
const recetaSugerida = ref<RecetaSugerida | null>(null)

const presets = [
  'Costear nuevo Corset en Tul Bordado con 6 varillas y copas forradas',
  'Consejos para reducir el desperdicio al cortar lino al sesgo',
  'Sugerir precio de venta para Bralette Bicolor con 65% de margen',
  'Fórmula de empaque y subproductos para retazos de tela malla',
]

function selectPreset(p: string) {
  prompt.value = p
}

async function consultarSugerencia() {
  if (!prompt.value.trim()) return
  loading.value = true
  respuesta.value = null
  recetaSugerida.value = null

  setTimeout(() => {
    loading.value = false
    const q = prompt.value.toLowerCase()

    if (q.includes('corset') || q.includes('receta') || q.includes('costear') || q.includes('bralette')) {
      recetaSugerida.value = {
        nombre: 'Corset Alta Costura "Nocturna Gold"',
        categoria: 'Corsetería',
        linea: 'Alta Costura',
        descripcion: 'Corset estructurado con varillas alemanas, forro en powernet y recubrimiento de tul bordado negro con herrajes de oro cepillado.',
        tiempo_confeccion_min: 190,
        costo_insumos: 34500,
        mano_obra: 12000,
        cif_energia: 2500,
        costo_total_unitario: 49000,
        precio_venta: 140000,
        markup_pct: 65,
        recomendaciones_taller: 'Utilizar cinta de refuerzo en la cintura para soportar la tensión de los ojalillos posteriores.',
        items: [
          { nombre: 'Tul Bordado Negro 24cm', consumo_unitario: 1.5, unidad: 'm', merma_pct: 4, costo_unitario: 10512.82, subtotal: 15769 },
          { nombre: 'Powernet Negro Estructurante', consumo_unitario: 0.9, unidad: 'm', merma_pct: 3, costo_unitario: 18000, subtotal: 16200 },
          { nombre: 'Mallatex Forro', consumo_unitario: 0.4, unidad: 'm', merma_pct: 2, costo_unitario: 8000, subtotal: 3200 },
        ],
      }
      respuesta.value = `Ejemplo de referencia del taller (no usa tus datos).\n\nPara este diseño de ejemplo, el costo de materia prima es de **$34.500 COP**, sumado a 190 min de mano de obra calificada ($12.000 COP) y CIF ($2.500 COP). El costo total de confección es de **$49.000 COP**. Con un margen comercial del 65%, el precio de venta de referencia es de **$140.000 COP**. Para crear la receta de verdad, usá "Nueva Receta Manual".`
    } else if (q.includes('retazo') || q.includes('desperdicio') || q.includes('lino') || q.includes('corte')) {
      respuesta.value = `✂️ **Estrategia de Optimización Textil de Atelier Arpía**:\n\n1. **Tendido Intercalado**: Al cortar piezas simétricas de bustiers y corsetería, invierte el patrón 180° sobre el orillo para ahorrar entre un 7% y 11% de tela por metro.\n2. **Subproductos Inmediatos**: Los retazos menores a 20x30 cm son ideales para confeccionar *Scrunchies de satén*, *Máscaras de descanso para ojos* o *Mini portacuchillas para máquinas de coser*.\n3. **Cuidado de Hilo**: Cortar al sesgo a 45° solo en piezas que requieran elasticidad natural (copas y sesgos); en cuerpos estructurados, mantén el hilo recto para evitar deformaciones.`
    } else {
      respuesta.value = `🧵 **Sugerencia general del taller** (ejemplo, no usa tus datos): conviene programar lotes de corte agrupados por color de hilo para optimizar los tiempos de enhebrado en las máquinas Singer y fileteadoras.`
    }
  }, 1000)
}

</script>

<template>
  <Dialog
    :visible="visible"
    modal
    header="Sugerencias de taller • Atelier Arpía"
    :style="{ width: '90vw', maxWidth: '680px' }"
    @update:visible="(v) => emit('update:visible', v)"
  >
    <div class="space-y-4 pt-1">
      <div class="bg-amber-950/20 border border-amber-500/20 rounded-xl p-3 text-xs text-amber-200/90 leading-relaxed flex items-center gap-2.5">
        <i class="pi pi-lightbulb text-amber-400 text-base flex-shrink-0" />
        <span>Ejemplos y sugerencias incorporadas del taller para orientar costeo y corte. Son textos de referencia: no analizan tus datos.</span>
      </div>

      <div>
        <label class="block text-xs font-semibold uppercase tracking-wider text-stone-400 mb-2">Preguntas o Presupuestos Frecuentes</label>
        <div class="flex flex-wrap gap-1.5">
          <button
            v-for="(p, idx) in presets"
            :key="idx"
            type="button"
            class="text-xs bg-stone-900/90 hover:bg-stone-800 text-stone-300 border border-stone-800 rounded-lg px-2.5 py-1.5 transition text-left"
            @click="selectPreset(p)"
          >
            {{ p }}
          </button>
        </div>
      </div>

      <div>
        <label class="block text-xs font-semibold uppercase tracking-wider text-stone-400 mb-1.5">¿Qué deseas consultar o confeccionar?</label>
        <Textarea
          v-model="prompt"
          rows="3"
          placeholder="Ej: Necesito costear un bustier de satén con encaje francés, 12 varillas y copas prehormadas..."
          class="w-full text-sm font-sans"
        />
      </div>

      <div class="flex justify-end gap-2">
        <Button
          label="Ver sugerencia"
          icon="pi pi-lightbulb"
          :loading="loading"
          class="p-button-warning font-semibold text-sm"
          @click="consultarSugerencia"
        />
      </div>

      <!-- Result Card -->
      <div v-if="respuesta" class="bg-stone-900/80 border border-amber-500/30 rounded-xl p-4 text-sm space-y-3 mt-4 animate-fade-in">
        <div class="flex items-center gap-2 text-amber-400 font-semibold text-xs tracking-wider uppercase border-b border-stone-800 pb-2">
          <i class="pi pi-check-circle" /> Sugerencia del taller (ejemplo)
        </div>
        <div class="text-stone-200 whitespace-pre-line text-xs sm:text-sm leading-relaxed">
          {{ respuesta }}
        </div>

        <div v-if="recetaSugerida" class="pt-3 border-t border-stone-800">
          <span class="text-xs text-stone-400">Ejemplo de referencia: <strong class="text-amber-300">{{ recetaSugerida.nombre }}</strong>. Para crearla de verdad, usá "Nueva Receta Manual".</span>
        </div>
      </div>
    </div>
  </Dialog>
</template>
