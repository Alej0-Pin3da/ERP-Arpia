<script setup lang="ts">
import { ref } from 'vue'
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'
import Textarea from 'primevue/textarea'
import { useAtelierStore, type RecetaBOM } from '@/stores/atelier'
import { useMode } from '@/composables/useMode'
import { showToast } from '@/utils/toast'

defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
  (e: 'receta-generada', receta: RecetaBOM): void
}>()

const atelier = useAtelierStore()
const { isMock } = useMode()
const prompt = ref('')
const loading = ref(false)
const respuesta = ref<string | null>(null)
const recetaSugerida = ref<RecetaBOM | null>(null)

const presets = [
  'Costear nuevo Corset en Tul Bordado con 6 varillas y copas forradas',
  'Consejos para reducir el desperdicio al cortar lino al sesgo',
  'Sugerir precio de venta para Bralette Bicolor con 65% de margen',
  'Fórmula de empaque y subproductos para retazos de tela malla',
]

function selectPreset(p: string) {
  prompt.value = p
}

async function consultarIA() {
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
      respuesta.value = `✨ He analizado los costos de confección y los insumos en tu inventario actual.\n\nPara este diseño, el costo estimado de materia prima es de **$34.500 COP**, sumado a 190 min de mano de obra calificada ($12.000 COP) y CIF ($2.500 COP). El costo total de confección es de **$49.000 COP**. Con un margen comercial del 65%, el precio de venta recomendado es de **$140.000 COP**.`
    } else if (q.includes('retazo') || q.includes('desperdicio') || q.includes('lino') || q.includes('corte')) {
      respuesta.value = `✂️ **Estrategia de Optimización Textil de Atelier Arpía**:\n\n1. **Tendido Intercalado**: Al cortar piezas simétricas de bustiers y corsetería, invierte el patrón 180° sobre el orillo para ahorrar entre un 7% y 11% de tela por metro.\n2. **Subproductos Inmediatos**: Los retazos menores a 20x30 cm son ideales para confeccionar *Scrunchies de satén*, *Máscaras de descanso para ojos* o *Mini portacuchillas para máquinas de coser*.\n3. **Cuidado de Hilo**: Cortar al sesgo a 45° solo en piezas que requieran elasticidad natural (copas y sesgos); en cuerpos estructurados, mantén el hilo recto para evitar deformaciones.`
    } else {
      respuesta.value = `🧵 **Recomendación AtelierPro**: Basado en el balance actual de pedidos y el stock de insumos críticos (${(isMock.value ? atelier.insumosCriticos : []).map(i => i.nombre).join(', ')}), te sugiero programar lotes de corte agrupados por color de hilo para optimizar los tiempos de enhebrado en las máquinas Singer y fileteadoras.`
    }
  }, 1000)
}

function aplicarReceta() {
  if (recetaSugerida.value) {
    if (isMock.value) atelier.crearReceta(recetaSugerida.value)
    showToast('success', 'Receta generada', 'Se ha guardado la nueva receta en el catálogo de fichas BOM.')
    emit('receta-generada', recetaSugerida.value)
    emit('update:visible', false)
  }
}
</script>

<template>
  <Dialog
    :visible="visible"
    modal
    header="✨ Asistente IA • Atelier Arpía"
    :style="{ width: '90vw', maxWidth: '680px' }"
    @update:visible="(v) => emit('update:visible', v)"
  >
    <div class="space-y-4 pt-1">
      <div class="bg-amber-950/20 border border-amber-500/20 rounded-xl p-3 text-xs text-amber-200/90 leading-relaxed flex items-center gap-2.5">
        <i class="pi pi-sparkles text-amber-400 text-base flex-shrink-0" />
        <span>El asistente inteligente de taller analiza tu inventario, fichas técnicas y precios para generar cotizaciones y escandallos precisos.</span>
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
          label="Consultar Atelier IA"
          icon="pi pi-sparkles"
          :loading="loading"
          class="p-button-warning font-semibold text-sm"
          @click="consultarIA"
        />
      </div>

      <!-- Result Card -->
      <div v-if="respuesta" class="bg-stone-900/80 border border-amber-500/30 rounded-xl p-4 text-sm space-y-3 mt-4 animate-fade-in">
        <div class="flex items-center gap-2 text-amber-400 font-semibold text-xs tracking-wider uppercase border-b border-stone-800 pb-2">
          <i class="pi pi-check-circle" /> Respuesta del Asistente
        </div>
        <div class="text-stone-200 whitespace-pre-line text-xs sm:text-sm leading-relaxed">
          {{ respuesta }}
        </div>

        <div v-if="recetaSugerida" class="pt-3 border-t border-stone-800 flex items-center justify-between">
          <span class="text-xs text-stone-400">Receta: <strong class="text-amber-300">{{ recetaSugerida.nombre }}</strong></span>
          <Button
            label="Guardar como Receta BOM"
            icon="pi pi-plus"
            size="small"
            class="p-button-sm p-button-warning"
            @click="aplicarReceta"
          />
        </div>
      </div>
    </div>
  </Dialog>
</template>
