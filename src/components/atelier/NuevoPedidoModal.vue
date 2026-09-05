<script setup lang="ts">
/* eslint-disable @typescript-eslint/no-explicit-any */
import { ref, computed, onMounted, watch } from 'vue'
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Dropdown from 'primevue/dropdown'
import Textarea from 'primevue/textarea'
import { useAtelierStore, type PedidoProduccion } from '@/stores/atelier'
import { useMode } from '@/composables/useMode'
import { useClientes } from '@/composables/useClientes'
import { useProductos } from '@/composables/useProductos'
import { useProduccion } from '@/composables/useProduccion'
import { client } from '@/api/client'
import { showToast } from '@/utils/toast'

defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
  (e: 'pedido-creado', pedido: PedidoProduccion): void
}>()

const atelier = useAtelierStore()
const { isMock } = useMode()
const clientesApi = useClientes()
const productosApi = useProductos()
const produccionService = useProduccion()

const clienteSeleccionado = ref<number | null>(null)
const nuevoClienteNombre = ref('')
const modoCliente = ref<'existente' | 'nuevo'>('existente')
const recetaSeleccionada = ref<number | null>(null)
const nombrePrendaManual = ref('')
const precioVenta = ref<number>(90000)
const costoEstimado = ref<number>(25000)
const estadoInicial = ref<PedidoProduccion['estado']>('COTIZADO')
const observaciones = ref('')
// REAL-only (POST /pedidos-produccion): producto + variante + cantidad + enums del backend.
const varianteReal = ref<number | null>(null)
const cantidadReal = ref<number>(1)
const estadoReal = ref<string>('pendiente')
const prioridadReal = ref<string>('normal')
const fechaEntregaReal = ref<string>('')

const clientesReal = ref<any[]>([])
const productosReal = ref<any[]>([])
const variantesReal = ref<{ id: number; nombre_variante: string }[]>([])
const guardando = ref(false)

async function cargarDatosReales() {
  if (isMock.value) return
  try {
    const [c, p] = await Promise.all([
      clientesApi.list({ limit: 100 }),
      productosApi.list({ limit: 100 }),
    ])
    clientesReal.value = (c.items as any) ?? []
    productosReal.value = (p.items as any) ?? []
  } catch {
    clientesReal.value = []
    productosReal.value = []
  }
}
onMounted(() => { void cargarDatosReales() })
watch(isMock, () => { void cargarDatosReales() })

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

const estadosOptionsReal = [
  { label: 'Pendiente', value: 'pendiente' },
  { label: 'En producción', value: 'en_produccion' },
]

const prioridadesOptions = [
  { label: 'Baja', value: 'baja' },
  { label: 'Normal', value: 'normal' },
  { label: 'Alta', value: 'alta' },
  { label: 'Urgente', value: 'urgente' },
]

const variantesOptions = computed(() => [
  { label: 'Sin variante (genérico)', value: null },
  ...variantesReal.value.map((v) => ({ label: v.nombre_variante, value: v.id })),
])

const clientesOptions = computed(() => {
  return (isMock.value ? atelier.clientes : clientesReal.value as any[]).map((c) => ({
    label: `${c.nombre} (${c.telefono || 'Sin tel'})`,
    value: c.id,
  }))
})

const recetasOptions = computed(() => {
  return (isMock.value ? (atelier as any).recetas : productosReal.value as any[]).map((r) => ({
    label: isMock.value
      ? `${r.nombre} (PVP Sugerido: $${Number(r.precio_venta ?? 0).toLocaleString('es-CO')})`
      : `${r.nombre} (${r.codigo ?? `PRD-${r.id}`})`,
    value: r.id,
  }))
})

async function onRecetaChange() {
  if (recetaSeleccionada.value) {
    const r = (isMock.value ? (atelier as any).recetas : productosReal.value as any[]).find((x) => x.id === recetaSeleccionada.value)
    if (r) {
      nombrePrendaManual.value = r.nombre
      const pv = Number(r.precio_venta_sugerido ?? r.precio_venta ?? 0)
      if (Number.isFinite(pv) && pv > 0) precioVenta.value = Math.round(pv)
      const ct = Number(r.costo_total_unitario ?? r.costos_operativos_fijos ?? r.costo_insumos ?? 0)
      if (Number.isFinite(ct) && ct > 0) costoEstimado.value = Math.round(ct)
    }
    if (!isMock.value) {
      varianteReal.value = null
      try {
        const { data } = await client.get<{ id: number; nombre_variante: string }[]>(`/productos/${recetaSeleccionada.value}/variantes`)
        variantesReal.value = data ?? []
      } catch { variantesReal.value = [] }
    }
  }
}

function extractDetail(e: unknown): string {
  const detail = (e as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail
  if (Array.isArray(detail)) return detail.map((d: any) => d.msg ?? JSON.stringify(d)).join('; ')
  if (typeof detail === 'string' && detail) return detail
  if (e instanceof Error && e.message) return e.message
  return 'No se pudo crear el pedido'
}

async function guardarPedidoReal() {
  if (guardando.value) return
  if (recetaSeleccionada.value == null) {
    showToast('warn', 'Seleccioná un producto', 'Elegí el modelo del catálogo para crear el pedido de producción.')
    return
  }
  // Clienta del pedido: existente de CRM o alta rápida por nombre.
  let clienteIdFinal: number | null = null
  if (modoCliente.value === 'nuevo' && nuevoClienteNombre.value.trim()) {
    try {
      const creada = await clientesApi.create({ nombre: nuevoClienteNombre.value.trim() })
      clienteIdFinal = (creada as unknown as { id: number }).id ?? null
    } catch (e: unknown) {
      showToast('error', 'No se pudo crear la clienta', extractDetail(e))
      return
    }
  } else if (modoCliente.value === 'existente' && clienteSeleccionado.value) {
    const existe = (clientesReal.value as any[]).some((c) => c.id === clienteSeleccionado.value)
    if (!existe) {
      showToast('warn', 'Clienta inválida', 'La clienta seleccionada ya no existe. Elegí otra o cargá el nombre manual.')
      return
    }
    clienteIdFinal = clienteSeleccionado.value
  }
  guardando.value = true
  try {
    const creado = await produccionService.create({
      producto_id: recetaSeleccionada.value,
      cliente_id: clienteIdFinal,
      variante_id: varianteReal.value,
      cantidad: Math.max(1, Math.round(Number(cantidadReal.value) || 1)),
      estado: estadoReal.value,
      prioridad: prioridadReal.value,
      fecha_entrega_estimada: fechaEntregaReal.value || null,
      observaciones: observaciones.value.trim() || null,
    }) as unknown as PedidoProduccion
    showToast('success', 'Pedido Registrado', `Pedido #${(creado as any).id ?? ''} creado en estado ${estadoReal.value}.`)
    emit('pedido-creado', creado)
    emit('update:visible', false)
    recetaSeleccionada.value = null
    varianteReal.value = null
    cantidadReal.value = 1
    clienteSeleccionado.value = null
    nuevoClienteNombre.value = ''
    observaciones.value = ''
  } catch (e: unknown) {
    showToast('error', 'No se pudo crear', extractDetail(e))
  } finally {
    guardando.value = false
  }
}

function guardarPedido() {
  if (!isMock.value) { void guardarPedidoReal(); return }
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
      <div v-if="isMock">
        <label class="block text-xs font-semibold uppercase tracking-wider text-stone-400 mb-1.5">Nombre o Descripción de la Prenda</label>
        <InputText
          v-model="nombrePrendaManual"
          placeholder="Ej: Corset Nocturna en Tul Bordado Negro Talla S"
          class="w-full"
        />
      </div>

      <!-- Variante + Cantidad (REAL: payload de POST /pedidos-produccion) -->
      <div v-if="!isMock" class="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div>
          <label class="block text-xs font-semibold uppercase tracking-wider text-stone-400 mb-1.5">Variante / Talla</label>
          <Dropdown
            v-model="varianteReal"
            :options="variantesOptions"
            option-label="label"
            option-value="value"
            placeholder="Sin variante (genérico)"
            class="w-full"
          />
        </div>
        <div>
          <label class="block text-xs font-semibold uppercase tracking-wider text-stone-400 mb-1.5">Cantidad</label>
          <InputNumber v-model="cantidadReal" :min="1" :max-fraction-digits="0" class="w-full font-mono" />
        </div>
      </div>

      <!-- Pricing & Costs (MOCK only: el backend no guarda precios en el pedido) -->
      <div v-if="isMock" class="grid grid-cols-1 sm:grid-cols-2 gap-3">
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
      <div v-if="isMock">
        <label class="block text-xs font-semibold uppercase tracking-wider text-stone-400 mb-1.5">Fase Inicial del Flujo</label>
        <Dropdown
          v-model="estadoInicial"
          :options="estadosOptions"
          option-label="label"
          option-value="value"
          class="w-full"
        />
      </div>

      <!-- Estado + Prioridad + Entrega (REAL: enums del backend) -->
      <div v-if="!isMock" class="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div>
          <label class="block text-xs font-semibold uppercase tracking-wider text-stone-400 mb-1.5">Estado inicial</label>
          <Dropdown
            v-model="estadoReal"
            :options="estadosOptionsReal"
            option-label="label"
            option-value="value"
            class="w-full"
          />
        </div>
        <div>
          <label class="block text-xs font-semibold uppercase tracking-wider text-stone-400 mb-1.5">Prioridad</label>
          <Dropdown
            v-model="prioridadReal"
            :options="prioridadesOptions"
            option-label="label"
            option-value="value"
            class="w-full"
          />
        </div>
        <div>
          <label class="block text-xs font-semibold uppercase tracking-wider text-stone-400 mb-1.5">Entrega estimada</label>
          <InputText v-model="fechaEntregaReal" type="date" class="w-full" />
        </div>
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
          :loading="guardando"
          @click="guardarPedido"
        />
      </div>
    </div>
  </Dialog>
</template>
