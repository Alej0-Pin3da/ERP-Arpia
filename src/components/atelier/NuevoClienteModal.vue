<script setup lang="ts">
import { ref, watch } from 'vue'
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Dropdown from 'primevue/dropdown'
import { type ClienteRead } from '@/services/api/clientes'
import { showToast } from '@/utils/toast'
import { useClientes } from '@/composables/useClientes'

const props = defineProps<{
  visible: boolean
  clienteEditar?: ClienteRead | null
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
  (e: 'cliente-guardado', cliente: ClienteRead): void
}>()

const clientesApi = useClientes()

const guardando = ref(false)

const nombre = ref('')
const tipo = ref('Clienta Habitual')
const telefono = ref('')
const email = ref('')
const ciudad = ref('Pereira')
const direccion = ref('')
// Valores fuera del modal (tallas/notas): en edición se conservan tal cual
// para no borrar datos existentes; en alta van null (la talla real queda en
// cada venta y un regalo no debe dejar datos falsos en la ficha).
const conservar = ref<{
  talla_habitual: string | null
  talla_superior: string | null
  talla_inferior: string | null
  categoria_preferida: string | null
  tipo_producto_frecuente: string | null
  notas: string | null
}>({
  talla_habitual: null,
  talla_superior: null,
  talla_inferior: null,
  categoria_preferida: null,
  tipo_producto_frecuente: null,
  notas: null,
})

const tiposClientaOptions = [
  { label: 'Clienta Habitual', value: 'Clienta Habitual' },
  { label: 'Clienta VIP / Showroom', value: 'Clienta VIP' },
  { label: 'Compradora Showroom Pereira', value: 'Clienta Showroom' },
  { label: 'Feria / Stand Mayorista', value: 'Feria / Stand Mayorista' },
  { label: 'Clienta Online / Envíos', value: 'Clienta Online' },
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
      conservar.value = {
        talla_habitual: c.talla_habitual ?? null,
        talla_superior: c.talla_superior ?? null,
        talla_inferior: c.talla_inferior ?? null,
        categoria_preferida: c.categoria_preferida ?? null,
        tipo_producto_frecuente: (c as unknown as { tipo_producto_frecuente?: string }).tipo_producto_frecuente ?? null,
        notas: c.notas ?? null,
      }
    } else {
      nombre.value = ''
      tipo.value = 'Clienta Habitual'
      telefono.value = ''
      email.value = ''
      ciudad.value = 'Pereira'
      direccion.value = ''
      conservar.value = {
        talla_habitual: null,
        talla_superior: null,
        talla_inferior: null,
        categoria_preferida: null,
        tipo_producto_frecuente: null,
        notas: null,
      }
    }
  },
  { immediate: true },
)

async function guardar() {
  if (guardando.value) return
  if (!nombre.value.trim()) {
    showToast('warn', 'Nombre requerido', 'Ingresa el nombre de la clienta.')
    return
  }

  // Sin sección de tallas/notas en el modal: la talla real queda en cada
  // venta (un regalo no deja datos falsos en la ficha) y en edición se
  // conservan los valores existentes sin mostrarlos.
  const apiPayload = {
    nombre: nombre.value.trim(),
    tipo: tipo.value,
    telefono: telefono.value.trim() || null,
    email: email.value.trim() || null,
    ciudad: ciudad.value.trim() || null,
    direccion: direccion.value.trim() || null,
    talla_habitual: conservar.value.talla_habitual,
    talla_superior: conservar.value.talla_superior,
    talla_inferior: conservar.value.talla_inferior,
    categoria_preferida: conservar.value.categoria_preferida,
    tipo_producto_frecuente: conservar.value.tipo_producto_frecuente,
    notas: conservar.value.notas,
  }
  guardando.value = true
  try {
    if (props.clienteEditar) {
      const updated = await clientesApi.update(props.clienteEditar.id, apiPayload)
      showToast('success', 'Clienta Actualizada', `${nombre.value} actualizada.`)
      if (updated) emit('cliente-guardado', updated)
    } else {
      const created = await clientesApi.create(apiPayload)
      showToast('success', 'Clienta Registrada', `${nombre.value} registrada en BD.`)
      emit('cliente-guardado', created)
    }
    emit('update:visible', false)
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? 'Error al guardar clienta'
    showToast('error', 'Error', String(msg))
  } finally {
    guardando.value = false
  }
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
          :loading="guardando"
          @click="guardar"
        />
      </div>
    </div>
  </Dialog>
</template>
