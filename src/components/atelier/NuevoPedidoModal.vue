<script setup lang="ts">
import { ref, computed } from 'vue'
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Dropdown from 'primevue/dropdown'
import Textarea from 'primevue/textarea'
import { useAtelierStore, type PedidoProduccion } from '@/stores/atelier'
import { showToast } from '@/utils/toast'

defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
  (e: 'pedido-creado', pedido: PedidoProduccion): void
}>()

const atelier = useAtelierStore()

const clienteSeleccionado = ref<number | null>(null)
const nuevoClienteNombre = ref('')
const modoCliente = ref<'existente' | 'nuevo'>('existente')
const recetaSeleccionada = ref<number | null>(null)
const nombrePrendaManual = ref('')
const precioVenta = ref<number>(90000)
const costoEstimado = ref<number>(25000)
const estadoInicial = ref<PedidoProduccion['estado']>('COTIZADO')
const observaciones = ref('')

const estadosOptions = [
  { label: '1. Cotizado', value: 'COTIZADO' },
  { label: '2. Reservado / Abono', value: 'RESERVADO' },
  { label: '3. Corte & Trazado', value: 'CORTE' },
  { label: '4. Costura & Confección', value: 'COSTURA' },
  { label: '5. Acabados & Varillaje', value: 'ACABADOS' },
  { label: '6. Control de Calidad', value: 'CALIDAD' },
  { label: '7. Listo para Entrega', value: 'LISTO' },
  { label: '8. Entregado al Cliente', value: 'ENTREGADO' },
]

const clientesOptions = computed(() => {
  return atelier.clientes.map((c) => ({
    label: `${c.nombre} (${c.telefono || 'Sin tel'})`,
    value: c.id,
  }))
})

const recetasOptions = computed(() => {
  return atelier.recetas.map((r) => ({
    label: `${r.nombre} (PVP Sugerido: $${r.precio_venta.toLocaleString('es-CO')})`,
    value: r.id,
  }))
})

function onRecetaChange() {
  if (recetaSeleccionada.value) {
    const r = atelier.recetas.find((x) => x.id === recetaSeleccionada.value)
    if (r) {
      nombrePrendaManual.value = r.nombre
      precioVenta.value = r.precio_venta
      costoEstimado.value = r.costo_total_unitario
    }
  }
}

function guardarPedido() {
  let clienteId = clienteSeleccionado.value
  let clienteNombre = 'Cliente'

  if (modoCliente.value === 'nuevo' && nuevoClienteNombre.value.trim()) {
    const c = atelier.crearCliente({ nombre: nuevoClienteNombre.value.trim() })
    clienteId = c.id
    clienteNombre = c.nombre
  } else if (clienteId) {
    const c = atelier.clientes.find((x) => x.id === clienteId)
    if (c) clienteNombre = c.nombre
  } else {
    showToast('warn', 'Seleccione un cliente', 'Debe seleccionar o ingresar el nombre de la clienta.')
    return
  }

  const prenda = nombrePrendaManual.value.trim() || 'Prenda a Medida Atelier'
  const p = atelier.crearPedido({
    cliente_id: clienteId || 1,
    cliente_nombre: clienteNombre,
    prenda_nombre: prenda,
    precio_venta: precioVenta.value || 0,
    costo_produccion: costoEstimado.value || 0,
    estado: estadoInicial.value,
    observaciones: observaciones.value,
  })

  showToast('success', 'Pedido Registrado', `Orden ${p.codigo} creada correctamente en fase ${p.estado}.`)
  emit('pedido-creado', p)
  emit('update:visible', false)

  // Reset form
  recetaSeleccionada.value = null
  nombrePrendaManual.value = ''
  observaciones.value = ''
}
</script>

<template>
  <Dialog
    :visible="visible"
    modal
    header="✂️ Registrar Nuevo Pedido & Confección"
    :style="{ width: '90vw', maxWidth: '640px' }"
    @update:visible="(v) => emit('update:visible', v)"
  >
    <div class="space-y-4 pt-1">
      <!-- Client Selector -->
      <div>
        <div class="flex items-center justify-between mb-1.5">
          <label class="text-xs font-semibold uppercase tracking-wider text-stone-400">Cliente / Destinatario</label>
          <div class="text-xs space-x-2">
            <button
              type="button"
              class="hover:underline"
              :class="modoCliente === 'existente' ? 'text-amber-400 font-bold' : 'text-stone-400'"
              @click="modoCliente = 'existente'"
            >
              Existente
            </button>
            <span class="text-stone-600">|</span>
            <button
              type="button"
              class="hover:underline"
              :class="modoCliente === 'nuevo' ? 'text-amber-400 font-bold' : 'text-stone-400'"
              @click="modoCliente = 'nuevo'"
            >
              + Nuevo Cliente
            </button>
          </div>
        </div>

        <Dropdown
          v-if="modoCliente === 'existente'"
          v-model="clienteSeleccionado"
          :options="clientesOptions"
          option-label="label"
          option-value="value"
          placeholder="Seleccionar cliente registrado..."
          class="w-full"
        />
        <InputText
          v-else
          v-model="nuevoClienteNombre"
          placeholder="Nombre completo de la clienta..."
          class="w-full"
        />
      </div>

      <!-- Garment Recipe Selector -->
      <div>
        <label class="block text-xs font-semibold uppercase tracking-wider text-stone-400 mb-1.5">Cargar desde Receta / Ficha BOM (Opcional)</label>
        <Dropdown
          v-model="recetaSeleccionada"
          :options="recetasOptions"
          option-label="label"
          option-value="value"
          placeholder="-- Seleccionar prenda del catálogo o escribir manual --"
          class="w-full"
          @change="onRecetaChange"
        />
      </div>

      <!-- Garment Name -->
      <div>
        <label class="block text-xs font-semibold uppercase tracking-wider text-stone-400 mb-1.5">Nombre o Descripción de la Prenda</label>
        <InputText
          v-model="nombrePrendaManual"
          placeholder="Ej: Corset Nocturna en Tul Bordado Negro Talla S"
          class="w-full"
        />
      </div>

      <!-- Pricing & Costs -->
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div>
          <label class="block text-xs font-semibold uppercase tracking-wider text-stone-400 mb-1.5">Precio de Venta ($ COP)</label>
          <InputNumber
            v-model="precioVenta"
            mode="currency"
            currency="COP"
            locale="es-CO"
            :min-fraction-digits="0"
            class="w-full"
          />
        </div>
        <div>
          <label class="block text-xs font-semibold uppercase tracking-wider text-stone-400 mb-1.5">Costo Estimado Producción ($ COP)</label>
          <InputNumber
            v-model="costoEstimado"
            mode="currency"
            currency="COP"
            locale="es-CO"
            :min-fraction-digits="0"
            class="w-full"
          />
        </div>
      </div>

      <!-- Stage Selection -->
      <div>
        <label class="block text-xs font-semibold uppercase tracking-wider text-stone-400 mb-1.5">Fase Inicial del Flujo</label>
        <Dropdown
          v-model="estadoInicial"
          :options="estadosOptions"
          option-label="label"
          option-value="value"
          class="w-full"
        />
      </div>

      <!-- Notes -->
      <div>
        <label class="block text-xs font-semibold uppercase tracking-wider text-stone-400 mb-1.5">Observaciones & Medidas Especiales</label>
        <Textarea
          v-model="observaciones"
          rows="2"
          placeholder="Ej: Ajustar 2cm en talle de espalda, forro en powernet negro, entrega sábado."
          class="w-full"
        />
      </div>

      <!-- Footer Buttons -->
      <div class="flex justify-end gap-2 pt-2 border-t border-stone-800">
        <Button
          label="Cancelar"
          severity="secondary"
          text
          @click="emit('update:visible', false)"
        />
        <Button
          label="Crear Pedido"
          icon="pi pi-check"
          class="p-button-warning font-semibold"
          @click="guardarPedido"
        />
      </div>
    </div>
  </Dialog>
</template>
