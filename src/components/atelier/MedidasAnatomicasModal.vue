<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'
import InputNumber from 'primevue/inputnumber'
import Textarea from 'primevue/textarea'
import { type ClienteCRM, type MedidasAnatomicas } from '@/stores/atelier'
import { showToast } from '@/utils/toast'

const props = defineProps<{
  visible: boolean
  cliente: ClienteCRM | null
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
  (e: 'guardar', medidas: MedidasAnatomicas): void
}>()

const medidasLocales = ref<MedidasAnatomicas>({
  busto: 90,
  cintura: 68,
  cadera: 96,
  espalda: 36,
  talle: 42,
  largo: 105,
})

const bajoBusto = ref<number>(75)
const cinturaCorse = ref<number>(60)
const altoCadera = ref<number>(88)
const separacionBusto = ref<number>(18)
const alturaBusto = ref<number>(25)
const notasCalce = ref<string>('')

watch(
  () => props.cliente,
  (c) => {
    if (c && c.medidas) {
      medidasLocales.value = {
        busto: Number(c.medidas.busto) || 90,
        cintura: Number(c.medidas.cintura) || 68,
        cadera: Number(c.medidas.cadera) || 96,
        espalda: Number(c.medidas.espalda) || 36,
        talle: Number(c.medidas.talle) || 42,
        largo: Number(c.medidas.largo) || 105,
      }
      cinturaCorse.value = Math.max(45, (Number(c.medidas.cintura) || 68) - 6)
      bajoBusto.value = Math.max(60, (Number(c.medidas.busto) || 90) - 15)
    }
  },
  { immediate: true }
)

const reduccionCinturaCm = computed(() => {
  const natural = Number(medidasLocales.value.cintura) || 0
  const corse = cinturaCorse.value || 0
  return Math.max(0, natural - corse)
})

const reduccionPct = computed(() => {
  const natural = Number(medidasLocales.value.cintura) || 1
  return Math.round((reduccionCinturaCm.value / natural) * 100)
})

const nivelReduccion = computed(() => {
  if (reduccionCinturaCm.value <= 4) return { label: 'Confort / Moda Ligera (0-4 cm)', color: 'text-emerald-400', badge: 'bg-emerald-950/80 border-emerald-500/30' }
  if (reduccionCinturaCm.value <= 8) return { label: 'Corsetería Clásica de Autor (5-8 cm)', color: 'text-amber-300', badge: 'bg-amber-950/80 border-amber-500/30' }
  return { label: 'Tight-Lacing / Alta Reducción (9+ cm)', color: 'text-rose-400', badge: 'bg-rose-950/80 border-rose-500/30' }
})

function guardar() {
  if (props.cliente) {
    showToast('success', 'Ficha Anatómica Guardada', `Medidas actualizadas para ${props.cliente.nombre}.`)
    emit('guardar', { ...medidasLocales.value })
  }
  emit('update:visible', false)
}
</script>

<template>
  <Dialog
    :visible="props.visible"
    modal
    :header="`Ficha Anatómica & Patronaje: ${props.cliente?.nombre || 'Clienta'}`"
    :style="{ width: '880px', maxWidth: '95vw' }"
    class="p-dialog-arpia"
    @update:visible="emit('update:visible', $event)"
  >
    <div class="space-y-6 pt-2">
      <!-- Top banner -->
      <div class="rounded-xl border border-amber-500/20 bg-stone-900/80 p-4 flex flex-col md:flex-row items-center justify-between gap-4">
        <div>
          <div class="text-xs font-mono text-amber-400 font-bold uppercase tracking-wider">
            Patrón Base de Alta Costura & Corsetería
          </div>
          <div class="text-xs text-stone-300 mt-0.5">
            Las medidas registradas alimentan el cálculo de varillas de acero, tensión de ojales y corte anatómico.
          </div>
        </div>
        <div class="flex items-center gap-2 px-3 py-1.5 rounded-lg border font-mono text-xs" :class="nivelReduccion.badge">
          <i class="pi pi-shield" />
          <span :class="nivelReduccion.color" class="font-bold">{{ nivelReduccion.label }}</span>
        </div>
      </div>

      <!-- Main Layout: Mannequin Visual & Input Fields -->
      <div class="grid grid-cols-1 md:grid-cols-12 gap-6 items-start">
        <!-- SVG Mannequin Diagram (Visual Interactive) -->
        <div class="md:col-span-5 rounded-2xl border border-stone-800 bg-stone-950/90 p-4 flex flex-col items-center justify-center relative overflow-hidden">
          <div class="text-[11px] font-mono text-amber-400/90 font-bold mb-2">
            DIAGRAMA DE SILUETA DE ATELIER
          </div>
          
          <svg viewBox="0 0 240 320" class="w-48 h-64 select-none drop-shadow-md">
            <!-- Background Gradients -->
            <defs>
              <linearGradient id="corsetGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="#dfb15b" stop-opacity="0.3" />
                <stop offset="50%" stop-color="#c5a059" stop-opacity="0.15" />
                <stop offset="100%" stop-color="#785c27" stop-opacity="0.35" />
              </linearGradient>
            </defs>

            <!-- Mannequin Outline -->
            <path
              d="M120 20 C110 20 102 30 102 45 C102 52 106 58 112 62 C85 70 70 95 68 120 C72 135 90 145 92 165 C94 185 80 205 75 240 C72 260 85 295 105 310 L135 310 C155 295 168 260 165 240 C160 205 146 185 148 165 C150 145 168 135 172 120 C170 95 155 70 128 62 C134 58 138 52 138 45 C138 30 130 20 120 20 Z"
              fill="url(#corsetGrad)"
              stroke="#dfb15b"
              stroke-width="1.5"
              stroke-linecap="round"
            />

            <!-- Bust Line -->
            <line x1="68" y1="120" x2="172" y2="120" stroke="#f3e5ab" stroke-width="1.5" stroke-dasharray="3 2" />
            <circle cx="120" cy="120" r="3" fill="#dfb15b" />
            <text x="180" y="124" fill="#dfb15b" font-size="10" font-family="monospace">Busto {{ medidasLocales.busto }}cm</text>

            <!-- Underbust Line -->
            <line x1="74" y1="140" x2="166" y2="140" stroke="#c5a059" stroke-width="1" stroke-dasharray="2 2" />
            <text x="175" y="144" fill="#a8a29e" font-size="9" font-family="monospace">Bajo Busto {{ bajoBusto }}cm</text>

            <!-- Waist Line (Corset Reduction) -->
            <line x1="92" y1="165" x2="148" y2="165" stroke="#ef4444" stroke-width="2" />
            <circle cx="120" cy="165" r="3" fill="#ef4444" />
            <text x="155" y="169" fill="#ef4444" font-size="10" font-weight="bold" font-family="monospace">Corsé {{ cinturaCorse }}cm</text>

            <!-- High Hip Line -->
            <line x1="84" y1="205" x2="156" y2="205" stroke="#c5a059" stroke-width="1" stroke-dasharray="2 2" />

            <!-- Hip Line -->
            <line x1="75" y1="240" x2="165" y2="240" stroke="#f3e5ab" stroke-width="1.5" stroke-dasharray="3 2" />
            <circle cx="120" cy="240" r="3" fill="#dfb15b" />
            <text x="175" y="244" fill="#dfb15b" font-size="10" font-family="monospace">Cadera {{ medidasLocales.cadera }}cm</text>

            <!-- Corset Boning lines mockup -->
            <line x1="110" y1="125" x2="106" y2="210" stroke="#c5a059" stroke-width="1" stroke-opacity="0.6" />
            <line x1="130" y1="125" x2="134" y2="210" stroke="#c5a059" stroke-width="1" stroke-opacity="0.6" />
            <line x1="120" y1="120" x2="120" y2="215" stroke="#dfb15b" stroke-width="1.5" stroke-opacity="0.8" />
          </svg>

          <!-- Corset Reduction Summary Widget -->
          <div class="w-full mt-3 p-2.5 rounded-xl bg-stone-900 border border-stone-800 text-xs flex items-center justify-between font-mono">
            <div>
              <span class="text-stone-400 block text-[10px]">Reducción Cintura:</span>
              <span class="text-amber-300 font-bold text-sm">-{{ reduccionCinturaCm }} cm ({{ reduccionPct }}%)</span>
            </div>
            <div class="text-right">
              <span class="text-stone-400 block text-[10px]">Tolerancia Varillas:</span>
              <span class="text-stone-200 font-semibold">12-16 aceros</span>
            </div>
          </div>
        </div>

        <!-- Form Inputs Grid -->
        <div class="md:col-span-7 space-y-4">
          <div class="grid grid-cols-2 gap-3">
            <div class="space-y-1">
              <label class="text-[11px] font-mono text-stone-300 font-semibold">Contorno Busto (cm)</label>
              <InputNumber v-model="medidasLocales.busto" :min="60" :max="160" suffix=" cm" class="w-full text-xs" />
            </div>

            <div class="space-y-1">
              <label class="text-[11px] font-mono text-stone-300 font-semibold">Bajo Busto (cm)</label>
              <InputNumber v-model="bajoBusto" :min="50" :max="140" suffix=" cm" class="w-full text-xs" />
            </div>

            <div class="space-y-1">
              <label class="text-[11px] font-mono text-stone-300 font-semibold">Cintura Natural (cm)</label>
              <InputNumber v-model="medidasLocales.cintura" :min="40" :max="150" suffix=" cm" class="w-full text-xs" />
            </div>

            <div class="space-y-1">
              <label class="text-[11px] font-mono text-rose-300 font-semibold">Cintura Corsé (Reducción)</label>
              <InputNumber v-model="cinturaCorse" :min="40" :max="140" suffix=" cm" class="w-full text-xs" />
            </div>

            <div class="space-y-1">
              <label class="text-[11px] font-mono text-stone-300 font-semibold">Contorno Cadera (cm)</label>
              <InputNumber v-model="medidasLocales.cadera" :min="60" :max="180" suffix=" cm" class="w-full text-xs" />
            </div>

            <div class="space-y-1">
              <label class="text-[11px] font-mono text-stone-300 font-semibold">Alto Cadera (cm)</label>
              <InputNumber v-model="altoCadera" :min="50" :max="150" suffix=" cm" class="w-full text-xs" />
            </div>

            <div class="space-y-1">
              <label class="text-[11px] font-mono text-stone-300 font-semibold">Ancho Espalda (cm)</label>
              <InputNumber v-model="medidasLocales.espalda" :min="25" :max="60" suffix=" cm" class="w-full text-xs" />
            </div>

            <div class="space-y-1">
              <label class="text-[11px] font-mono text-stone-300 font-semibold">Talle Delantero (cm)</label>
              <InputNumber v-model="medidasLocales.talle" :min="30" :max="65" suffix=" cm" class="w-full text-xs" />
            </div>

            <div class="space-y-1">
              <label class="text-[11px] font-mono text-stone-300 font-semibold">Separación Busto (cm)</label>
              <InputNumber v-model="separacionBusto" :min="12" :max="30" suffix=" cm" class="w-full text-xs" />
            </div>

            <div class="space-y-1">
              <label class="text-[11px] font-mono text-stone-300 font-semibold">Altura Busto (cm)</label>
              <InputNumber v-model="alturaBusto" :min="18" :max="40" suffix=" cm" class="w-full text-xs" />
            </div>
          </div>

          <div class="space-y-1">
            <label class="text-[11px] font-mono text-stone-300 font-semibold">Notas Anatómicas & Ajustes de Taller</label>
            <Textarea
              v-model="notasCalce"
              rows="2"
              placeholder="Ej: Asimetría leve de hombro derecho (0.5cm), preferencia de copa balconette armada, soporte lumbar reforzado..."
              class="w-full text-xs"
            />
          </div>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="flex items-center justify-between w-full pt-3 border-t border-stone-800">
        <span class="text-[11px] text-stone-400 font-mono">Arpía Atelier Haute Couture System</span>
        <div class="flex items-center gap-2">
          <Button
            label="Cancelar"
            icon="pi pi-times"
            size="small"
            severity="secondary"
            outlined
            class="text-xs"
            @click="emit('update:visible', false)"
          />
          <Button
            label="Guardar Medidas"
            icon="pi pi-check"
            size="small"
            class="p-button-warning text-xs font-semibold"
            @click="guardar"
          />
        </div>
      </div>
    </template>
  </Dialog>
</template>
