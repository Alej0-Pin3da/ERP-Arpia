<script setup lang="ts">
import { ref, watch } from 'vue'
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Dropdown from 'primevue/dropdown'
import Textarea from 'primevue/textarea'
import { useAtelierStore, type ClienteCRM } from '@/stores/atelier'
import { showToast } from '@/utils/toast'

const props = defineProps<{
  visible: boolean
  clienteEditar?: ClienteCRM | null
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
  (e: 'cliente-guardado', cliente: ClienteCRM): void
}>()

const atelier = useAtelierStore()

const nombre = ref('')
const tipo = ref('Clienta Habitual')
const telefono = ref('')
const email = ref('')
const ciudad = ref('Pereira')
const direccion = ref('')
const tallaHabitual = ref('S')
const tallaSuperior = ref('S')
const tallaInferior = ref('S')
const categoriaPreferida = ref('Corsetería & Tops')
const notas = ref('')

const tiposClientaOptions = [
  { label: 'Clienta Habitual', value: 'Clienta Habitual' },
  { label: 'Clienta VIP / Showroom', value: 'Clienta VIP' },
  { label: 'Compradora Showroom Pereira', value: 'Clienta Showroom' },
  { label: 'Feria / Stand Mayorista', value: 'Feria / Stand Mayorista' },
  { label: 'Clienta Online / Envíos', value: 'Clienta Online' },
]

const tallasPrenda = [
  { label: 'XXS', value: 'XXS' },
  { label: 'XS', value: 'XS' },
  { label: 'S', value: 'S' },
  { label: 'M', value: 'M' },
  { label: 'L', value: 'L' },
  { label: 'XL', value: 'XL' },
  { label: 'Sin Talla', value: 'Sin Talla' },
]

const categoriasOptions = [
  { label: 'Corsetería & Tops (Con Talla: XXS-XL)', value: 'Corsetería & Tops' },
  { label: 'Faldas & Prendas Inferiores (Con Talla: XXS-XL)', value: 'Faldas & Conjuntos' },
  { label: 'Sets & Colecciones Completas', value: 'Sets & Corsets' },
  { label: '👜 Tote Bags Ilustradas (Sin Talla)', value: 'Tote Bags de Lona' },
  { label: '🎀 Accesorios & Joyería Textil (Sin Talla)', value: 'Accesorios & Merch' },
]

watch(
  () => props.clienteEditar,
  (c) => {
    if (c) {
      nombre.value = c.nombre
      tipo.value = c.tipo || 'Clienta Habitual'
      telefono.value = c.telefono || ''
      email.value = c.email || ''
      ciudad.value = c.ciudad || 'Pereira'
      direccion.value = c.direccion || ''
      tallaHabitual.value = c.talla_habitual || 'S'
      tallaSuperior.value = c.talla_superior || c.talla_habitual || 'S'
      tallaInferior.value = c.talla_inferior || c.talla_habitual || 'S'
      categoriaPreferida.value = c.categoria_preferida || 'Corsetería & Tops'
      notas.value = c.notas || ''
    } else {
      nombre.value = ''
      tipo.value = 'Clienta Habitual'
      telefono.value = ''
      email.value = ''
      ciudad.value = 'Pereira'
      direccion.value = ''
      tallaHabitual.value = 'S'
      tallaSuperior.value = 'S'
      tallaInferior.value = 'S'
      categoriaPreferida.value = 'Corsetería & Tops'
      notas.value = ''
    }
  },
  { immediate: true },
)

function seleccionarTallaRapida(talla: string) {
  tallaHabitual.value = talla
  if (talla !== 'Sin Talla (Tote Bags)' && talla !== 'Talla Única / Surtido') {
    tallaSuperior.value = talla
    tallaInferior.value = talla
  }
}

function guardar() {
  if (!nombre.value.trim()) {
    showToast('warn', 'Nombre requerido', 'Ingresa el nombre de la clienta.')
    return
  }

  const esSinTalla = tallaHabitual.value.includes('Sin Talla') || categoriaPreferida.value.includes('Tote Bags')
  const tipoFrecuente = esSinTalla ? 'PRODUCTOS_SIN_TALLA' : 'PRENDAS_TALLAS'

  const payload: Partial<ClienteCRM> = {
    nombre: nombre.value.trim(),
    tipo: tipo.value,
    telefono: telefono.value.trim(),
    email: email.value.trim(),
    ciudad: ciudad.value.trim(),
    direccion: direccion.value.trim(),
    talla_habitual: tallaHabitual.value,
    talla_superior: tallaSuperior.value,
    talla_inferior: tallaInferior.value,
    categoria_preferida: categoriaPreferida.value,
    tipo_producto_frecuente: tipoFrecuente,
    notas: notas.value.trim(),
  }

  if (props.clienteEditar) {
    atelier.actualizarCliente(props.clienteEditar.id, payload)
    showToast('success', 'Clienta Actualizada', `${nombre.value} actualizada correctamente.`)
  } else {
    const c = atelier.crearCliente(payload)
    showToast('success', 'Clienta Registrada', `${c.nombre} registrada en el CRM con talla ${tallaHabitual.value}.`)
  }

  emit('update:visible', false)
}
</script>

<template>
  <Dialog
    :visible="visible"
    modal
    :header="clienteEditar ? `✏️ Editar Ficha • ${clienteEditar.nombre}` : '✨ Registrar Nueva Clienta (CRM Atelier)'"
    :style="{ width: '90vw', maxWidth: '680px' }"
    @update:visible="(v) => emit('update:visible', v)"
  >
    <div class="space-y-4 pt-1 text-xs text-stone-200">
      <!-- General Data -->
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 bg-stone-900/60 p-3.5 rounded-xl border border-stone-800">
        <div class="sm:col-span-2">
          <label class="block text-[11px] font-bold uppercase tracking-wider text-amber-300 mb-1">
            Nombre Completo de la Clienta *
          </label>
          <InputText v-model="nombre" placeholder="Ej: Gabriela Gómez" class="w-full text-xs" />
        </div>

        <div>
          <label class="block text-[11px] font-bold uppercase tracking-wider text-stone-400 mb-1">
            Tipo de Clienta
          </label>
          <Dropdown
            v-model="tipo"
            :options="tiposClientaOptions"
            option-label="label"
            option-value="value"
            class="w-full text-xs"
          />
        </div>

        <div>
          <label class="block text-[11px] font-bold uppercase tracking-wider text-stone-400 mb-1">
            Teléfono / WhatsApp
          </label>
          <InputText v-model="telefono" placeholder="+57 312 000 0000" class="w-full text-xs font-mono" />
        </div>

        <div>
          <label class="block text-[11px] font-bold uppercase tracking-wider text-stone-400 mb-1">
            Correo Electrónico
          </label>
          <InputText v-model="email" placeholder="cliente@arpia.com" class="w-full text-xs font-mono" />
        </div>

        <div>
          <label class="block text-[11px] font-bold uppercase tracking-wider text-stone-400 mb-1">
            Ciudad / Municipio
          </label>
          <InputText v-model="ciudad" placeholder="Pereira" class="w-full text-xs" />
        </div>

        <div class="sm:col-span-3">
          <label class="block text-[11px] font-bold uppercase tracking-wider text-stone-400 mb-1">
            Dirección de Envío / Entrega
          </label>
          <InputText v-model="direccion" placeholder="Cra 15 # 12-45, Barrio / Sector" class="w-full text-xs" />
        </div>
      </div>

      <!-- Sizing & Products Section -->
      <div class="border border-amber-500/30 rounded-xl p-4 bg-amber-950/20 space-y-3">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-amber-300 font-mono">
            <i class="pi pi-tag" />
            Talla Estándar de la Marca (Prendas XXS a XL & Productos Sin Talla)
          </div>
          <span class="text-[10px] text-amber-400/80 font-mono">Sin medidas a medida</span>
        </div>

        <div>
          <label class="block text-[11px] text-stone-300 font-bold mb-1.5">
            Seleccionar Talla Estándar Principal:
          </label>
          <div class="grid grid-cols-3 sm:grid-cols-6 gap-2">
            <button
              v-for="t in ['XXS', 'XS', 'S', 'M', 'L', 'XL']"
              :key="t"
              type="button"
              class="py-2 px-1 text-center font-mono font-bold rounded-lg border text-xs transition cursor-pointer"
              :class="tallaHabitual === t
                ? 'bg-amber-400 text-stone-950 border-amber-300 shadow-md font-extrabold'
                : 'bg-stone-900/80 text-stone-300 border-stone-800 hover:border-amber-500/50'"
              @click="seleccionarTallaRapida(t)"
            >
              {{ t }}
            </button>
          </div>

          <!-- Non-sized products selector button -->
          <div class="mt-2 flex flex-wrap gap-2">
            <button
              type="button"
              class="flex-1 py-1.5 px-3 rounded-lg border text-xs font-mono transition text-center cursor-pointer"
              :class="tallaHabitual.includes('Sin Talla')
                ? 'bg-amber-500/20 text-amber-300 border-amber-400 font-bold'
                : 'bg-stone-900/60 text-stone-400 border-stone-800 hover:text-stone-200'"
              @click="seleccionarTallaRapida('Sin Talla (Tote Bags)')"
            >
              👜 Sin Talla (Solo Tote Bags / Accesorios)
            </button>

            <button
              type="button"
              class="py-1.5 px-3 rounded-lg border text-xs font-mono transition text-center cursor-pointer"
              :class="tallaHabitual.includes('Talla Única')
                ? 'bg-amber-500/20 text-amber-300 border-amber-400 font-bold'
                : 'bg-stone-900/60 text-stone-400 border-stone-800 hover:text-stone-200'"
              @click="seleccionarTallaRapida('Talla Única / Surtido')"
            >
              ✨ Surtido / Talla Única
            </button>
          </div>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2 border-t border-amber-500/20">
          <div>
            <label class="block text-[10px] uppercase font-bold text-stone-400 mb-1">
              Talla Superior (Tops / Corsets)
            </label>
            <Dropdown
              v-model="tallaSuperior"
              :options="tallasPrenda"
              option-label="label"
              option-value="value"
              class="w-full text-xs"
            />
          </div>

          <div>
            <label class="block text-[10px] uppercase font-bold text-stone-400 mb-1">
              Talla Inferior (Faldas / Pantalones)
            </label>
            <Dropdown
              v-model="tallaInferior"
              :options="tallasPrenda"
              option-label="label"
              option-value="value"
              class="w-full text-xs"
            />
          </div>

          <div>
            <label class="block text-[10px] uppercase font-bold text-stone-400 mb-1">
              Categoría de Interés Principal
            </label>
            <Dropdown
              v-model="categoriaPreferida"
              :options="categoriasOptions"
              option-label="label"
              option-value="value"
              class="w-full text-xs"
            />
          </div>
        </div>
      </div>

      <!-- Notes / Delivery details -->
      <div class="bg-stone-900/60 p-3.5 rounded-xl border border-stone-800">
        <label class="block text-[11px] font-bold uppercase tracking-wider text-stone-400 mb-1">
          Notas de Preferencias, Calce de Prenda o Envíos
        </label>
        <Textarea
          v-model="notas"
          rows="2"
          class="w-full text-xs"
          placeholder="Ej: Prefiere corsets ajustados en talla S, fan de las Tote Bags ilustradas, envíos por Interrapidísimo..."
        />
      </div>

      <div class="flex justify-end gap-2 pt-2 border-t border-stone-800">
        <Button
          label="Cancelar"
          icon="pi pi-times"
          size="small"
          class="p-button-text p-button-secondary text-xs"
          @click="emit('update:visible', false)"
        />
        <Button
          :label="clienteEditar ? 'Guardar Cambios' : 'Registrar Clienta'"
          icon="pi pi-check"
          size="small"
          class="p-button-warning text-xs font-semibold px-4"
          @click="guardar"
        />
      </div>
    </div>
  </Dialog>
</template>
