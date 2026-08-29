<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'
import Dropdown from 'primevue/dropdown'
import Textarea from 'primevue/textarea'
import { type ClienteCRM, type MedidasAnatomicas, useAtelierStore } from '@/stores/atelier'
import { useMode } from '@/composables/useMode'
import { showToast } from '@/utils/toast'

const props = defineProps<{
  visible: boolean
  cliente: ClienteCRM | null
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
  (e: 'guardar', medidas: MedidasAnatomicas): void
}>()

const atelier = useAtelierStore()
const { isMock } = useMode()

const tallaSeleccionada = ref('S')
const tallaSuperior = ref('S')
const tallaInferior = ref('S')
const categoriaPreferida = ref('Corsetería & Tops')
const notasCalce = ref('')

const tablaTallasEstandar = [
  { talla: 'XXS', busto: '78 - 82', cintura: '58 - 62', cadera: '84 - 88', tipo: 'Petite / Extra pequeña' },
  { talla: 'XS', busto: '82 - 86', cintura: '62 - 66', cadera: '88 - 92', tipo: 'Talla pequeña estándar' },
  { talla: 'S', busto: '86 - 90', cintura: '66 - 70', cadera: '92 - 96', tipo: 'Talla más solicitada' },
  { talla: 'M', busto: '90 - 94', cintura: '70 - 74', cadera: '96 - 100', tipo: 'Talla media estándar' },
  { talla: 'L', busto: '94 - 98', cintura: '74 - 78', cadera: '100 - 104', tipo: 'Talla amplia estructurada' },
  { talla: 'XL', busto: '98 - 104', cintura: '78 - 84', cadera: '104 - 110', tipo: 'Talla máxima de catálogo' },
]

watch(
  () => props.cliente,
  (c) => {
    if (c) {
      tallaSeleccionada.value = c.talla_habitual || 'S'
      tallaSuperior.value = c.talla_superior || c.talla_habitual || 'S'
      tallaInferior.value = c.talla_inferior || c.talla_habitual || 'S'
      categoriaPreferida.value = c.categoria_preferida || 'Corsetería & Tops'
      notasCalce.value = c.notas || ''
    }
  },
  { immediate: true },
)

const esSinTalla = computed(() => {
  return tallaSeleccionada.value.includes('Sin Talla') || categoriaPreferida.value.includes('Tote Bags')
})

function guardar() {
  if (props.cliente) {
    atelier.actualizarCliente(props.cliente.id, {
      talla_habitual: tallaSeleccionada.value,
      talla_superior: tallaSuperior.value,
      talla_inferior: tallaInferior.value,
      categoria_preferida: categoriaPreferida.value,
      tipo_producto_frecuente: esSinTalla.value ? 'PRODUCTOS_SIN_TALLA' : 'PRENDAS_TALLAS',
      notas: notasCalce.value.trim(),
    })
    showToast('success', 'Ficha de Talla Actualizada', `Talla guardada como ${tallaSeleccionada.value} para ${props.cliente.nombre}.`)
    emit('guardar', { busto: '-', cintura: '-', cadera: '-', espalda: '-', talle: '-', largo: '-' })
  }
  emit('update:visible', false)
}
</script>

<template>
  <Dialog
    :visible="props.visible"
    modal
    :header="`📏 Ficha de Tallas Estándar • ${props.cliente?.nombre || 'Clienta'}`"
    :style="{ width: '840px', maxWidth: '95vw' }"
    class="p-dialog-arpia"
    @update:visible="emit('update:visible', $event)"
  >
    <div class="space-y-5 pt-2 text-xs text-stone-200">
      <!-- Standard sizing banner -->
      <div class="rounded-xl border border-amber-500/30 bg-stone-900/90 p-4 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div>
          <div class="text-xs font-mono text-amber-400 font-bold uppercase tracking-wider">
            Confección por Tallas de Marca (XXS, XS, S, M, L, XL)
          </div>
          <div class="text-xs text-stone-300 mt-1">
            En Atelier Arpía no se confecciona a medida anatómica individual. Las prendas se elaboran en tallas estándar y los productos como <strong>TOTE BAGS</strong> y accesorios son <strong>Sin Talla</strong>.
          </div>
        </div>
        <div class="flex items-center gap-2 px-3 py-1.5 rounded-lg border font-mono text-xs bg-amber-950/80 border-amber-500/40 text-amber-300 font-bold whitespace-nowrap">
          <span>Talla: {{ tallaSeleccionada }}</span>
        </div>
      </div>

      <!-- Quick size selector -->
      <div class="bg-stone-950/80 p-4 rounded-xl border border-stone-800 space-y-3 font-mono">
        <label class="block text-[11px] font-bold uppercase tracking-wider text-amber-300">
          Asignar Talla Estándar a la Clienta:
        </label>

        <div class="grid grid-cols-3 sm:grid-cols-7 gap-2">
          <button
            v-for="t in ['XXS', 'XS', 'S', 'M', 'L', 'XL']"
            :key="t"
            type="button"
            class="py-2 text-center font-bold rounded-lg border text-xs transition cursor-pointer"
            :class="tallaSeleccionada === t
              ? 'bg-amber-400 text-stone-950 border-amber-300 shadow-md font-black'
              : 'bg-stone-900 text-stone-300 border-stone-800 hover:border-amber-500/40'"
            @click="tallaSeleccionada = t"
          >
            {{ t }}
          </button>

          <button
            type="button"
            class="py-2 text-center font-bold rounded-lg border text-[11px] transition cursor-pointer"
            :class="tallaSeleccionada.includes('Sin Talla')
              ? 'bg-amber-400 text-stone-950 border-amber-300 font-black'
              : 'bg-stone-900 text-stone-300 border-stone-800 hover:border-amber-500/40'"
            @click="tallaSeleccionada = 'Sin Talla (Tote Bags)'"
          >
            👜 Sin Talla
          </button>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
          <div>
            <label class="block text-[10px] text-stone-400 uppercase font-bold mb-1">Categoría de Preferencia</label>
            <Dropdown
              v-model="categoriaPreferida"
              :options="[
                { label: 'Corsetería & Tops (Con Talla: XXS-XL)', value: 'Corsetería & Tops' },
                { label: 'Faldas & Conjuntos (Con Talla: XXS-XL)', value: 'Faldas & Conjuntos' },
                { label: 'Tote Bags de Lona (Sin Talla)', value: 'Tote Bags de Lona' },
                { label: 'Accesorios & Joyería Textil (Sin Talla)', value: 'Accesorios & Merch' },
              ]"
              option-label="label"
              option-value="value"
              class="w-full text-xs"
            />
          </div>

          <div>
            <label class="block text-[10px] text-stone-400 uppercase font-bold mb-1">Notas de Calce / Estilo</label>
            <Textarea
              v-model="notasCalce"
              rows="1"
              class="w-full text-xs"
              placeholder="Ej: Calce ceñido, compradora de Tote Bags..."
            />
          </div>
        </div>
      </div>

      <!-- Sizing guide matrix -->
      <div class="space-y-2 font-mono">
        <div class="text-[11px] font-bold uppercase tracking-wider text-stone-300 flex items-center gap-2">
          <i class="pi pi-table text-amber-400" />
          Guía de Equivalencias Oficiales Atelier Arpía
        </div>

        <div class="rounded-xl border border-stone-800 overflow-hidden">
          <table class="w-full text-left border-collapse text-xs">
            <thead>
              <tr class="bg-stone-950 text-stone-400 uppercase text-[10px] border-b border-stone-800">
                <th class="py-2 px-3">Talla</th>
                <th class="py-2 px-3 text-center">Busto (cm)</th>
                <th class="py-2 px-3 text-center">Cintura (cm)</th>
                <th class="py-2 px-3 text-center">Cadera (cm)</th>
                <th class="py-2 px-3">Detalle</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-stone-800/60">
              <tr
                v-for="r in tablaTallasEstandar"
                :key="r.talla"
                class="hover:bg-stone-800/30 transition-colors"
                :class="tallaSeleccionada === r.talla ? 'bg-amber-500/10 text-amber-300 font-bold' : 'text-stone-300'"
              >
                <td class="py-2 px-3">
                  <span
                    class="px-2 py-0.5 rounded font-mono font-bold"
                    :class="tallaSeleccionada === r.talla ? 'bg-amber-400 text-stone-950' : 'bg-stone-800 text-stone-300'"
                  >
                    {{ r.talla }}
                  </span>
                </td>
                <td class="py-2 px-3 text-center">{{ r.busto }}</td>
                <td class="py-2 px-3 text-center">{{ r.cintura }}</td>
                <td class="py-2 px-3 text-center">{{ r.cadera }}</td>
                <td class="py-2 px-3 text-[11px] font-sans text-stone-400">{{ r.tipo }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="flex items-center justify-end gap-2 pt-2 border-t border-stone-800">
        <Button
          label="Cerrar"
          icon="pi pi-times"
          size="small"
          class="p-button-text p-button-secondary text-xs"
          @click="emit('update:visible', false)"
        />
        <Button
          label="Guardar Talla"
          icon="pi pi-check"
          size="small"
          class="p-button-warning text-xs font-semibold px-4"
          @click="guardar"
        />
      </div>
    </template>
  </Dialog>
</template>
