<script setup lang="ts">
import { ref, watch } from 'vue'
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'
import InputText from 'primevue/inputText'
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
const telefono = ref('')
const email = ref('')
const busto = ref<number | string>('')
const cintura = ref<number | string>('')
const cadera = ref<number | string>('')
const espalda = ref<number | string>('')
const talle = ref<number | string>('')
const largo = ref<number | string>('')

watch(
  () => props.clienteEditar,
  (c) => {
    if (c) {
      nombre.value = c.nombre
      telefono.value = c.telefono
      email.value = c.email
      busto.value = c.medidas?.busto ?? ''
      cintura.value = c.medidas?.cintura ?? ''
      cadera.value = c.medidas?.cadera ?? ''
      espalda.value = c.medidas?.espalda ?? ''
      talle.value = c.medidas?.talle ?? ''
      largo.value = c.medidas?.largo ?? ''
    } else {
      nombre.value = ''
      telefono.value = ''
      email.value = ''
      busto.value = ''
      cintura.value = ''
      cadera.value = ''
      espalda.value = ''
      talle.value = ''
      largo.value = ''
    }
  },
  { immediate: true },
)

function guardar() {
  if (!nombre.value.trim()) {
    showToast('warn', 'Nombre requerido', 'Ingresa el nombre de la clienta.')
    return
  }

  const medidas = {
    busto: busto.value || '-',
    cintura: cintura.value || '-',
    cadera: cadera.value || '-',
    espalda: espalda.value || '-',
    talle: talle.value || '-',
    largo: largo.value || '-',
  }

  if (props.clienteEditar) {
    atelier.actualizarCliente(props.clienteEditar.id, {
      nombre: nombre.value.trim(),
      telefono: telefono.value.trim(),
      email: email.value.trim(),
      medidas,
    })
    showToast('success', 'Cliente actualizado', `${nombre.value} actualizado correctamente.`)
  } else {
    const c = atelier.crearCliente({
      nombre: nombre.value.trim(),
      telefono: telefono.value.trim(),
      email: email.value.trim(),
      medidas,
    })
    showToast('success', 'Cliente creado', `${c.nombre} registrado en el CRM.`)
  }

  emit('update:visible', false)
}
</script>

<template>
  <Dialog
    :visible="visible"
    modal
    :header="clienteEditar ? `✏️ Editar Ficha • ${clienteEditar.nombre}` : '✨ Registrar Nueva Clienta (CRM)'"
    :style="{ width: '90vw', maxWidth: '640px' }"
    @update:visible="(v) => emit('update:visible', v)"
  >
    <div class="space-y-4 pt-1">
      <div>
        <label class="block text-xs font-semibold uppercase tracking-wider text-stone-400 mb-1.5">Nombre Completo</label>
        <InputText v-model="nombre" placeholder="Ej: Gabriela Gómez" class="w-full" />
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div>
          <label class="block text-xs font-semibold uppercase tracking-wider text-stone-400 mb-1.5">Teléfono / WhatsApp</label>
          <InputText v-model="telefono" placeholder="+57 312 000 0000" class="w-full" />
        </div>
        <div>
          <label class="block text-xs font-semibold uppercase tracking-wider text-stone-400 mb-1.5">Correo Electrónico</label>
          <InputText v-model="email" placeholder="cliente@arpia.com" class="w-full" />
        </div>
      </div>

      <div class="border border-stone-800 rounded-xl p-3 bg-stone-900/60 space-y-2.5">
        <div class="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-amber-400">
          <i class="pi pi-pencil" /> Medidas Anatómicas (cm)
        </div>

        <div class="grid grid-cols-3 sm:grid-cols-6 gap-2">
          <div>
            <label class="block text-[11px] text-stone-400 mb-1 text-center">Busto</label>
            <InputText v-model="busto" class="w-full text-center font-mono text-sm" placeholder="-" />
          </div>
          <div>
            <label class="block text-[11px] text-stone-400 mb-1 text-center">Cintura</label>
            <InputText v-model="cintura" class="w-full text-center font-mono text-sm" placeholder="-" />
          </div>
          <div>
            <label class="block text-[11px] text-stone-400 mb-1 text-center">Cadera</label>
            <InputText v-model="cadera" class="w-full text-center font-mono text-sm" placeholder="-" />
          </div>
          <div>
            <label class="block text-[11px] text-stone-400 mb-1 text-center">Espalda</label>
            <InputText v-model="espalda" class="w-full text-center font-mono text-sm" placeholder="-" />
          </div>
          <div>
            <label class="block text-[11px] text-stone-400 mb-1 text-center">Talle</label>
            <InputText v-model="talle" class="w-full text-center font-mono text-sm" placeholder="-" />
          </div>
          <div>
            <label class="block text-[11px] text-stone-400 mb-1 text-center">Largo</label>
            <InputText v-model="largo" class="w-full text-center font-mono text-sm" placeholder="-" />
          </div>
        </div>
      </div>

      <div class="flex justify-end gap-2 pt-2 border-t border-stone-800">
        <Button label="Cancelar" severity="secondary" text @click="emit('update:visible', false)" />
        <Button label="Guardar Clienta" icon="pi pi-check" class="p-button-warning font-semibold" @click="guardar" />
      </div>
    </div>
  </Dialog>
</template>
