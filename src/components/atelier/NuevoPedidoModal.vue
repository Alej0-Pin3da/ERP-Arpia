<script setup lang="ts">
/* eslint-disable @typescript-eslint/no-explicit-any */
import { ref, computed, onMounted } from 'vue'
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Dropdown from 'primevue/dropdown'
import Textarea from 'primevue/textarea'
import { useClientes } from '@/composables/useClientes'
import { useProductos } from '@/composables/useProductos'
import { useProduccion } from '@/composables/useProduccion'
import type { PedidoProduccionRead } from '@/services/api/pedidos-produccion'
import { client } from '@/api/client'
import { showToast } from '@/utils/toast'

defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
  (e: 'pedido-creado', pedido: PedidoProduccionRead): void
}>()

const clientesApi = useClientes()
const productosApi = useProductos()
const produccionService = useProduccion()

const clienteSeleccionado = ref<number | null>(null)
const nuevoClienteNombre = ref('')
const modoCliente = ref<'existente' | 'nuevo'>('existente')
const recetaSeleccionada = ref<number | null>(null)
const observaciones = ref('')
// POST /pedidos-produccion: producto + variante + cantidad + enums del backend.
const varianteId = ref<number | null>(null)
const cantidad = ref<number>(1)
const estado = ref<string>('pendiente')
const prioridad = ref<string>('normal')
const fechaEntrega = ref<string>('')

const clientes = ref<any[]>([])
const productos = ref<any[]>([])
const variantes = ref<{ id: number; nombre_variante: string }[]>([])
const guardando = ref(false)

async function cargarDatos() {
  try {
    const [c, p] = await Promise.all([
      clientesApi.list({ limit: 100 }),
      productosApi.list({ limit: 100 }),
    ])
    clientes.value = (c.items as any) ?? []
    productos.value = (p.items as any) ?? []
  } catch {
    clientes.value = []
    productos.value = []
  }
}
onMounted(() => { void cargarDatos() })

const estadosOptions = [
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
  ...variantes.value.map((v) => ({ label: v.nombre_variante, value: v.id })),
])

const clientesOptions = computed(() => {
  return (clientes.value as any[]).map((c) => ({
    label: `${c.nombre} (${c.telefono || 'Sin tel'})`,
    value: c.id,
  }))
})

const recetasOptions = computed(() => {
  return (productos.value as any[]).map((r) => ({
    label: `${r.nombre} (${r.codigo ?? `PRD-${r.id}`})`,
    value: r.id,
  }))
})

async function onRecetaChange() {
  if (recetaSeleccionada.value) {
    varianteId.value = null
    try {
      const { data } = await client.get<{ id: number; nombre_variante: string }[]>(`/productos/${recetaSeleccionada.value}/variantes`)
      variantes.value = data ?? []
    } catch { variantes.value = [] }
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
    const existe = (clientes.value as any[]).some((c) => c.id === clienteSeleccionado.value)
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
      variante_id: varianteId.value,
      cantidad: Math.max(1, Math.round(Number(cantidad.value) || 1)),
      estado: estado.value,
      prioridad: prioridad.value,
      fecha_entrega_estimada: fechaEntrega.value || null,
      observaciones: observaciones.value.trim() || null,
    })
    showToast('success', 'Pedido Registrado', `Pedido #${(creado as any).id ?? ''} creado en estado ${estado.value}.`)
    emit('pedido-creado', creado)
    emit('update:visible', false)
    recetaSeleccionada.value = null
    varianteId.value = null
    cantidad.value = 1
    clienteSeleccionado.value = null
    nuevoClienteNombre.value = ''
    observaciones.value = ''
  } catch (e: unknown) {
    showToast('error', 'No se pudo crear', extractDetail(e))
  } finally {
    guardando.value = false
  }
}

async function guardarPedido() {
  await guardarPedidoReal()
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

      <!-- Variante + Cantidad (payload de POST /pedidos-produccion) -->
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div>
          <label class="block text-xs font-semibold uppercase tracking-wider text-stone-400 mb-1.5">Variante / Talla</label>
          <Dropdown
            v-model="varianteId"
            :options="variantesOptions"
            option-label="label"
            option-value="value"
            placeholder="Sin variante (genérico)"
            class="w-full"
          />
        </div>
        <div>
          <label class="block text-xs font-semibold uppercase tracking-wider text-stone-400 mb-1.5">Cantidad</label>
          <InputNumber v-model="cantidad" :min="1" :max-fraction-digits="0" class="w-full font-mono" />
        </div>
      </div>

      <!-- Estado + Prioridad + Entrega (enums del backend) -->
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div>
          <label class="block text-xs font-semibold uppercase tracking-wider text-stone-400 mb-1.5">Estado inicial</label>
          <Dropdown
            v-model="estado"
            :options="estadosOptions"
            option-label="label"
            option-value="value"
            class="w-full"
          />
        </div>
        <div>
          <label class="block text-xs font-semibold uppercase tracking-wider text-stone-400 mb-1.5">Prioridad</label>
          <Dropdown
            v-model="prioridad"
            :options="prioridadesOptions"
            option-label="label"
            option-value="value"
            class="w-full"
          />
        </div>
        <div>
          <label class="block text-xs font-semibold uppercase tracking-wider text-stone-400 mb-1.5">Entrega estimada</label>
          <InputText v-model="fechaEntrega" type="date" class="w-full" />
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
