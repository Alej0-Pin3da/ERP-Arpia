<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'
import Dropdown from 'primevue/dropdown'
import Textarea from 'primevue/textarea'
import { type ClienteCRM, useAtelierStore } from '@/stores/atelier'
import { showToast } from '@/utils/toast'

const props = defineProps<{
  visible: boolean
  cliente: ClienteCRM | null
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
  (e: 'guardar', clienteActualizado: Partial<ClienteCRM>): void
}>()

const atelier = useAtelierStore()

const tallaSeleccionada = ref('S')
const tallaSuperior = ref('S')
const tallaInferior = ref('S')
const categoriaPreferida = ref('Corsetería & Tops')
const notasCalce = ref('')

const tallasPrenda = [
  { label: 'XXS', value: 'XXS' },
  { label: 'XS', value: 'XS' },
  { label: 'S', value: 'S' },
  { label: 'M', value: 'M' },
  { label: 'L', value: 'L' },
  { label: 'XL', value: 'XL' },
  { label: '👜 Sin Talla (Tote Bags / Accesorios)', value: 'Sin Talla (Tote Bags)' },
  { label: '✨ Talla Única / Surtido', value: 'Talla Única / Surtido' },
]

// Guía oficial de medidas de referencia de las tallas estándar Atelier Arpía
const tablaTallasEstandar = [
  { talla: 'XXS', busto: '78 - 82', cintura: '58 - 62', cadera: '84 - 88', tipo: 'Prendas Petite / Confección reducida' },
  { talla: 'XS', busto: '82 - 86', cintura: '62 - 66', cadera: '88 - 92', tipo: 'Talla estándar pequeña' },
  { talla: 'S', busto: '86 - 90', cintura: '66 - 70', cadera: '92 - 96', tipo: 'Talla más vendida en corsetería' },
  { talla: 'M', busto: '90 - 94', cintura: '70 - 74', cadera: '96 - 100', tipo: 'Talla media estándar' },
  { talla: 'L', busto: '94 - 98', cintura: '74 - 78', cadera: '100 - 104', tipo: 'Talla amplia estructurada' },
  { talla: 'XL', busto: '98 - 104', cintura: '78 - 84', cadera: '104 - 110', tipo: 'Talla máxima de catálogo' },
]

// Productos sin talla
const productosSinTalla = [
  { nombre: '👜 Totebag Ilustrado Arpía', material: 'Lona 100% algodón / Gabardina', descripcion: 'Bolso de tela sin talla para uso diario y ferias.' },
  { nombre: '🎀 Pañoletas & Scrunchies', material: 'Satín licrado / Retazos seda', descripcion: 'Accesorios textiles confeccionados a partir de retazos.' },
  { nombre: '🖤 Arnés & Straps Ajustables', material: 'Reata con herrajes metálicos', descripcion: 'Ajuste universal con correas graduables.' },
  { nombre: '✨ Futuros Accesorios & Merch', material: 'Materiales varios', descripcion: 'Llaveros, pines, parches y bolsas utilitarias.' },
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

const esClientaSinTalla = computed(() => {
  return (
    tallaSeleccionada.value.includes('Sin Talla') ||
    categoriaPreferida.value.includes('Tote Bags')
  )
})

function guardarFicha() {
  if (props.cliente) {
    const updated: Partial<ClienteCRM> = {
      talla_habitual: tallaSeleccionada.value,
      talla_superior: tallaSuperior.value,
      talla_inferior: tallaInferior.value,
      categoria_preferida: categoriaPreferida.value,
      tipo_producto_frecuente: esClientaSinTalla.value ? 'PRODUCTOS_SIN_TALLA' : 'PRENDAS_TALLAS',
      notas: notasCalce.value.trim(),
    }
    atelier.actualizarCliente(props.cliente.id, updated)
    showToast('success', 'Ficha de Talla Actualizada', `Talla guardada como ${tallaSeleccionada.value} para ${props.cliente.nombre}.`)
    emit('guardar', updated)
  }
  emit('update:visible', false)
}

function enviarGuiaWhatsApp() {
  if (!props.cliente) return
  const cleanPhone = (props.cliente.telefono || '').replace(/\D/g, '')
  const msg = encodeURIComponent(
    `¡Hola ${props.cliente.nombre}! Te compartimos la Guía Oficial de Tallas de Atelier Arpía ✨:\n\n` +
    `• Tallas Estándar: XXS, XS, S, M, L, XL\n` +
    `• Tu talla registrada: ${tallaSeleccionada.value}\n` +
    `• Productos Sin Talla: Tote Bags ilustradas y accesorios\n\n` +
    `¿Deseas encargar alguna prenda de nuestra colección? 🪡`
  )
  window.open(`https://wa.me/${cleanPhone || '573124567890'}?text=${msg}`, '_blank')
}
</script>

<template>
  <Dialog
    :visible="visible"
    modal
    :header="`📏 Ficha de Talla & Guía de Confección • ${props.cliente?.nombre || 'Clienta'}`"
    :style="{ width: '860px', maxWidth: '95vw' }"
    @update:visible="emit('update:visible', $event)"
  >
    <div class="space-y-5 pt-1 text-xs text-stone-200">
      <!-- Policy banner explaining standard sizes & no bespoke body measurements -->
      <div class="rounded-xl border border-amber-500/30 bg-amber-950/20 p-3.5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div class="space-y-1">
          <div class="flex items-center gap-2">
            <span class="px-2 py-0.5 rounded bg-amber-400 text-stone-950 font-mono font-black text-[10px] uppercase">
              Patrón Estándar Arpía
            </span>
            <span class="font-bold text-amber-300">Confección por Tallas de Marca</span>
          </div>
          <p class="text-[11px] text-stone-300 m-0">
            En Atelier Arpía las prendas se confeccionan exclusivamente en tallas estándar (<strong>XXS, XS, S, M, L, XL</strong>).
            Los productos de merch y accesorios (como las <strong>TOTE BAGS</strong>) son <em>Sin Talla</em>.
          </p>
        </div>

        <Button
          label="Enviar Guía x WhatsApp"
          icon="pi pi-whatsapp"
          size="small"
          class="p-button-success text-xs font-semibold whitespace-nowrap"
          @click="enviarGuiaWhatsApp"
        />
      </div>

      <!-- Client's Size Selection Controls -->
      <div class="bg-stone-900/80 p-4 rounded-xl border border-stone-800 space-y-3 font-mono">
        <div class="flex items-center justify-between">
          <div class="text-[11px] font-bold uppercase tracking-wider text-amber-300">
            Talla Asignada a {{ props.cliente?.nombre || 'la Clienta' }}:
          </div>
          <span class="text-xs font-bold px-2.5 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/30">
            {{ tallaSeleccionada }}
          </span>
        </div>

        <!-- Quick Size Selector Buttons -->
        <div class="grid grid-cols-4 sm:grid-cols-8 gap-2">
          <button
            v-for="t in ['XXS', 'XS', 'S', 'M', 'L', 'XL']"
            :key="t"
            type="button"
            class="py-2 text-center font-bold rounded-lg border text-xs transition cursor-pointer"
            :class="tallaSeleccionada === t
              ? 'bg-amber-400 text-stone-950 border-amber-300 shadow-md font-black'
              : 'bg-stone-950 text-stone-300 border-stone-800 hover:border-amber-500/40'"
            @click="tallaSeleccionada = t"
          >
            {{ t }}
          </button>

          <button
            type="button"
            class="col-span-2 py-2 text-center font-bold rounded-lg border text-[11px] transition cursor-pointer truncate"
            :class="tallaSeleccionada.includes('Sin Talla')
              ? 'bg-amber-400 text-stone-950 border-amber-300 font-black'
              : 'bg-stone-950 text-stone-300 border-stone-800 hover:border-amber-500/40'"
            @click="tallaSeleccionada = 'Sin Talla (Tote Bags)'"
          >
            👜 Sin Talla
          </button>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
          <div>
            <label class="block text-[10px] text-stone-400 uppercase font-bold mb-1">Talla Tops / Corsets</label>
            <Dropdown
              v-model="tallaSuperior"
              :options="tallasPrenda"
              option-label="label"
              option-value="value"
              class="w-full text-xs"
            />
          </div>

          <div>
            <label class="block text-[10px] text-stone-400 uppercase font-bold mb-1">Talla Faldas / Inferior</label>
            <Dropdown
              v-model="tallaInferior"
              :options="tallasPrenda"
              option-label="label"
              option-value="value"
              class="w-full text-xs"
            />
          </div>

          <div>
            <label class="block text-[10px] text-stone-400 uppercase font-bold mb-1">Categoría Frecuente</label>
            <Dropdown
              v-model="categoriaPreferida"
              :options="[
                { label: 'Corsetería & Tops (Con Talla)', value: 'Corsetería & Tops' },
                { label: 'Faldas & Conjuntos (Con Talla)', value: 'Faldas & Conjuntos' },
                { label: 'Tote Bags de Lona (Sin Talla)', value: 'Tote Bags de Lona' },
                { label: 'Accesorios & Joyería Textil (Sin Talla)', value: 'Accesorios & Merch' },
              ]"
              option-label="label"
              option-value="value"
              class="w-full text-xs"
            />
          </div>
        </div>
      </div>

      <!-- Official Sizing Table (Matrix) -->
      <div class="space-y-2">
        <div class="flex items-center justify-between">
          <div class="text-[11px] font-bold uppercase tracking-wider text-stone-300 font-mono flex items-center gap-2">
            <i class="pi pi-table text-amber-400" />
            Tabla de Equivalencias Estándar Atelier Arpía (cm de referencia)
          </div>
          <span class="text-[10px] text-stone-500 font-mono">Para guía de confección</span>
        </div>

        <div class="rounded-xl border border-stone-800 overflow-hidden">
          <table class="w-full text-left border-collapse text-xs font-mono">
            <thead>
              <tr class="bg-stone-950 text-stone-400 uppercase text-[10px] border-b border-stone-800">
                <th class="py-2 px-3">Talla</th>
                <th class="py-2 px-3 text-center">Busto (cm)</th>
                <th class="py-2 px-3 text-center">Cintura (cm)</th>
                <th class="py-2 px-3 text-center">Cadera (cm)</th>
                <th class="py-2 px-3">Descripción de Silueta</th>
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

      <!-- Non-sized products section (Tote Bags, Accesorios) -->
      <div class="space-y-2">
        <div class="text-[11px] font-bold uppercase tracking-wider text-stone-300 font-mono flex items-center gap-2">
          <i class="pi pi-shopping-bag text-amber-400" />
          Catálogo de Productos Sin Talla / Talla Única
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
          <div
            v-for="p in productosSinTalla"
            :key="p.nombre"
            class="p-3 rounded-xl border border-stone-800 bg-stone-950/60 font-mono space-y-1"
          >
            <div class="font-bold text-stone-200 text-xs flex items-center justify-between">
              <span>{{ p.nombre }}</span>
              <span class="text-[9px] px-1.5 py-0.5 rounded bg-stone-800 text-amber-300">Sin Talla</span>
            </div>
            <div class="text-[10px] text-stone-400 font-sans">{{ p.descripcion }}</div>
            <div class="text-[9px] text-stone-500">Material: {{ p.material }}</div>
          </div>
        </div>
      </div>

      <!-- Notes -->
      <div class="bg-stone-900/60 p-3 rounded-xl border border-stone-800">
        <label class="block text-[10px] uppercase font-bold text-stone-400 mb-1">
          Notas de Calce o Preferencias Específicas
        </label>
        <Textarea
          v-model="notasCalce"
          rows="2"
          class="w-full text-xs"
          placeholder="Ej: Prefiere ajuste de ojaletes cerrado en corsets, compradora recurrente de Tote Bags..."
        />
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
          label="Guardar Talla de Clienta"
          icon="pi pi-check"
          size="small"
          class="p-button-warning text-xs font-semibold px-4"
          @click="guardarFicha"
        />
      </div>
    </template>
  </Dialog>
</template>
