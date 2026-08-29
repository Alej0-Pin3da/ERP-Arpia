<script setup lang="ts">
import { ref } from 'vue'
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Dropdown from 'primevue/dropdown'
import Textarea from 'primevue/textarea'
import { useAtelierStore, type RecetaBOM } from '@/stores/atelier'
import { useMode } from '@/composables/useMode'
import { showToast } from '@/utils/toast'

defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
  (e: 'receta-creada', receta: RecetaBOM): void
}>()

const atelier = useAtelierStore()
const { isMock } = useMode()

const codigo = ref('')
const nombre = ref('')
const categoria = ref('Corsetería')
const linea = ref('Corsetería')
const descripcion = ref('')
const tiempoConfeccion = ref(120)
const costoInsumos = ref(25000)
const manoObra = ref(0)
const cifEnergia = ref(1500)
const precioVenta = ref(95000)
const recomendaciones = ref('')

const categoriasOptions = [
  'Corsetería',
  'Blusas y Tops',
  'Conjuntos y Sets',
  'Vestidos',
  'Pantalones',
  'Accesorios',
  'Alta Costura',
]

const lineasOptions = ['Corsetería', 'Prêt-à-Porter', 'Lencería Fina', 'Alta Costura']

function guardar() {
  if (!nombre.value.trim()) {
    showToast('warn', 'Nombre requerido', 'Por favor ingresa el nombre de la prenda o receta.')
    return
  }

  if (!isMock.value) { showToast('info','Modo REAL','Usá POST /productos y /bom para crear recetas.'); return }
  if (!isMock.value) { showToast('info','Modo REAL','La creación de recetas en modo REAL usa el catálogo de productos.'); return }
  const r = atelier.crearReceta({
    codigo: codigo.value.trim() || `REC-ARP-0${(isMock.value ? atelier.recetas.length : 0) + 1}`,
    nombre: nombre.value.trim(),
    categoria: categoria.value,
    linea: linea.value,
    descripcion: descripcion.value.trim() || 'Ficha técnica de confección en taller.',
    tiempo_confeccion_min: tiempoConfeccion.value,
    costo_insumos: costoInsumos.value,
    mano_obra: manoObra.value,
    cif_energia: cifEnergia.value,
    precio_venta: precioVenta.value,
    markup_pct: precioVenta.value ? Math.round(((precioVenta.value - (costoInsumos.value + manoObra.value + cifEnergia.value)) / precioVenta.value) * 100) : 60,
    recomendaciones_taller: recomendaciones.value.trim() || 'Seguir patrones anatómicos y pruebas de entalle.',
    items: [
      { id: 1, insumo_id: 1, nombre: 'Tela Principal', tipo: 'Directo', consumo_unitario: 1, unidad: 'm', merma_pct: 4, costo_unitario: costoInsumos.value, subtotal: costoInsumos.value },
    ],
  })

  showToast('success', 'Receta creada', `Ficha ${r.codigo} - ${r.nombre} guardada correctamente.`)
  emit('receta-creada', r)
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
    header="📋 Crear Nueva Receta / Ficha Técnica (BOM)"
    :style="{ width: '90vw', maxWidth: '680px' }"
    @update:visible="(v) => emit('update:visible', v)"
  >
    <div class="space-y-4 pt-1">
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div>
          <label class="block text-xs font-semibold uppercase tracking-wider text-stone-400 mb-1.5">Código Referencia</label>
          <InputText v-model="codigo" placeholder="Ej: REC-ARP-09" class="w-full font-mono" />
        </div>
        <div>
          <label class="block text-xs font-semibold uppercase tracking-wider text-stone-400 mb-1.5">Categoría</label>
          <Dropdown v-model="categoria" :options="categoriasOptions" class="w-full" />
        </div>
        <div>
          <label class="block text-xs font-semibold uppercase tracking-wider text-stone-400 mb-1.5">Línea</label>
          <Dropdown v-model="linea" :options="lineasOptions" class="w-full" />
        </div>
      </div>

      <div>
        <label class="block text-xs font-semibold uppercase tracking-wider text-stone-400 mb-1.5">Nombre del Modelo / Prenda</label>
        <InputText v-model="nombre" placeholder="Ej: Corset Noir de Satén con Encaje Francés" class="w-full" />
      </div>

      <div>
        <label class="block text-xs font-semibold uppercase tracking-wider text-stone-400 mb-1.5">Descripción del Diseño</label>
        <Textarea v-model="descripcion" rows="2" placeholder="Detalles de patronaje, copas, varillado y materiales." class="w-full" />
      </div>

      <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div>
          <label class="block text-xs font-semibold uppercase tracking-wider text-stone-400 mb-1.5">Tiempo (min)</label>
          <InputNumber v-model="tiempoConfeccion" :min="1" class="w-full font-mono" />
        </div>
        <div>
          <label class="block text-xs font-semibold uppercase tracking-wider text-stone-400 mb-1.5">Costo Insumos ($)</label>
          <InputNumber v-model="costoInsumos" mode="currency" currency="COP" locale="es-CO" :min-fraction-digits="0" class="w-full font-mono" />
        </div>
        <div>
          <label class="block text-xs font-semibold uppercase tracking-wider text-stone-400 mb-1.5">Mano Obra ($)</label>
          <InputNumber v-model="manoObra" mode="currency" currency="COP" locale="es-CO" :min-fraction-digits="0" class="w-full font-mono" />
        </div>
        <div>
          <label class="block text-xs font-semibold uppercase tracking-wider text-stone-400 mb-1.5">Precio Venta ($)</label>
          <InputNumber v-model="precioVenta" mode="currency" currency="COP" locale="es-CO" :min-fraction-digits="0" class="w-full font-mono" />
        </div>
      </div>

      <div>
        <label class="block text-xs font-semibold uppercase tracking-wider text-stone-400 mb-1.5">Recomendaciones para el Taller</label>
        <InputText v-model="recomendaciones" placeholder="Ej: Precaución con aguja fina en tul y remates dobles." class="w-full" />
      </div>

      <div class="flex justify-end gap-2 pt-2 border-t border-stone-800">
        <Button label="Cancelar" severity="secondary" text @click="emit('update:visible', false)" />
        <Button label="Guardar Ficha Técnica" icon="pi pi-check" class="p-button-warning font-semibold" @click="guardar" />
      </div>
    </div>
  </Dialog>
</template>
