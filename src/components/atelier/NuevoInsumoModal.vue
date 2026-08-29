<script setup lang="ts">
import { ref } from 'vue'
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Dropdown from 'primevue/dropdown'
import Textarea from 'primevue/textarea'
import { useAtelierStore, type InsumoAtelier } from '@/stores/atelier'
import { useMode } from '@/composables/useMode'
import { showToast } from '@/utils/toast'

defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
  (e: 'insumo-creado', insumo: InsumoAtelier): void
}>()

const atelier = useAtelierStore()
const { isMock } = useMode()

const codigo = ref('')
const nombre = ref('')
const descripcion = ref('')
const tipo = ref<'Directo' | 'Indirecto'>('Directo')
const categoria = ref('Telas Principales')
const ubicacion = ref('Estante Telas A1')
const proveedor = ref('Atenea Bordados y Encajes')
const stockActual = ref(10)
const stockMinimo = ref(5)
const unidadMedida = ref('m')
const costoUnitario = ref(15000)

const tiposOptions = [
  { label: 'Directo (Telas, Encajes, Forros, Copas)', value: 'Directo' },
  { label: 'Indirecto (Empaques, Hilos, Etiquetas, Cintas)', value: 'Indirecto' },
]

const categoriasOptions = [
  'Telas Principales',
  'Forros y Entretelas',
  'Herrajes y Varillas',
  'Empaques y Avíos',
  'Elásticos y Sesgos',
]

const unidadesOptions = [
  { label: 'Metros (m)', value: 'm' },
  { label: 'Unidades (un)', value: 'un' },
  { label: 'Centímetros (cm)', value: 'cm' },
  { label: 'Rollos (rll)', value: 'rll' },
]

function guardar() {
  if (!nombre.value.trim()) {
    showToast('warn', 'Nombre requerido', 'Ingresa el nombre del insumo o textil.')
    return
  }

  const item = atelier.crearInsumo({
    codigo: codigo.value.trim() || `TEL-AUTO-${Date.now().toString().slice(-4)}`,
    nombre: nombre.value.trim(),
    descripcion: descripcion.value.trim(),
    tipo: tipo.value,
    categoria: categoria.value,
    ubicacion: ubicacion.value.trim(),
    proveedor: proveedor.value.trim(),
    stock_actual: stockActual.value,
    stock_minimo: stockMinimo.value,
    unidad_medida: unidadMedida.value,
    costo_unitario: costoUnitario.value,
  })

  showToast('success', 'Insumo creado', `${item.nombre} registrado en el inventario.`)
  emit('insumo-creado', item)
  emit('update:visible', false)

  // Reset
  nombre.value = ''
  codigo.value = ''
  descripcion.value = ''
}
</script>

<template>
  <Dialog
    :visible="visible"
    modal
    header="🧵 Registrar Nuevo Insumo / Materia Prima"
    :style="{ width: '90vw', maxWidth: '640px' }"
    @update:visible="(v) => emit('update:visible', v)"
  >
    <div class="space-y-4 pt-1">
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div>
          <label class="block text-xs font-semibold uppercase tracking-wider text-stone-400 mb-1.5">Código Referencia</label>
          <InputText v-model="codigo" placeholder="Ej: TEL-TUL-200" class="w-full font-mono" />
        </div>
        <div>
          <label class="block text-xs font-semibold uppercase tracking-wider text-stone-400 mb-1.5">Tipo de Insumo</label>
          <Dropdown v-model="tipo" :options="tiposOptions" option-label="label" option-value="value" class="w-full" />
        </div>
      </div>

      <div>
        <label class="block text-xs font-semibold uppercase tracking-wider text-stone-400 mb-1.5">Nombre del Insumo / Tela</label>
        <InputText v-model="nombre" placeholder="Ej: Ref 200 Encaje Chantilly Oro & Negro" class="w-full" />
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div>
          <label class="block text-xs font-semibold uppercase tracking-wider text-stone-400 mb-1.5">Categoría</label>
          <Dropdown v-model="categoria" :options="categoriasOptions" class="w-full" />
        </div>
        <div>
          <label class="block text-xs font-semibold uppercase tracking-wider text-stone-400 mb-1.5">Unidad de Medida</label>
          <Dropdown v-model="unidadMedida" :options="unidadesOptions" option-label="label" option-value="value" class="w-full" />
        </div>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div>
          <label class="block text-xs font-semibold uppercase tracking-wider text-stone-400 mb-1.5">Ubicación en Taller</label>
          <InputText v-model="ubicacion" placeholder="Ej: Estante Telas Atenea A1" class="w-full" />
        </div>
        <div>
          <label class="block text-xs font-semibold uppercase tracking-wider text-stone-400 mb-1.5">Proveedor Habitual</label>
          <InputText v-model="proveedor" placeholder="Ej: Atenea Bordados y Encajes" class="w-full" />
        </div>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div>
          <label class="block text-xs font-semibold uppercase tracking-wider text-stone-400 mb-1.5">Stock Inicial</label>
          <InputNumber v-model="stockActual" :min="0" :max-fraction-digits="2" class="w-full" />
        </div>
        <div>
          <label class="block text-xs font-semibold uppercase tracking-wider text-stone-400 mb-1.5">Stock Mínimo (Alerta)</label>
          <InputNumber v-model="stockMinimo" :min="0" :max-fraction-digits="2" class="w-full" />
        </div>
        <div>
          <label class="block text-xs font-semibold uppercase tracking-wider text-stone-400 mb-1.5">Costo Unitario ($)</label>
          <InputNumber v-model="costoUnitario" mode="currency" currency="COP" locale="es-CO" :min-fraction-digits="0" class="w-full" />
        </div>
      </div>

      <div>
        <label class="block text-xs font-semibold uppercase tracking-wider text-stone-400 mb-1.5">Descripción & Usos de Confección</label>
        <Textarea v-model="descripcion" rows="2" placeholder="Ej: Utilizado para copas de corsets y detalles de escote." class="w-full" />
      </div>

      <div class="flex justify-end gap-2 pt-2 border-t border-stone-800">
        <Button label="Cancelar" severity="secondary" text @click="emit('update:visible', false)" />
        <Button label="Guardar Insumo" icon="pi pi-check" class="p-button-warning font-semibold" @click="guardar" />
      </div>
    </div>
  </Dialog>
</template>
