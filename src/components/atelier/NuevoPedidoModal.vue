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
import { useMaestros } from '@/composables/useMaestros'
import { listVariantes, createVariante } from '@/services/api/productos'
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
const maestrosApi = useMaestros()

const clienteSeleccionado = ref<number | null>(null)
const nuevoClienteNombre = ref('')
const modoCliente = ref<'existente' | 'nuevo' | 'stock'>('stock')
const recetaSeleccionada = ref<number | null>(null)
const observaciones = ref('')
// POST /pedidos-produccion: producto + variante + cantidad + enums del backend.
// varianteKey: 'none' | 'v:<id>' (propia) | 'm:<nombre>' (matriz, se crea sola).
const cantidad = ref<number>(1)
const estado = ref<string>('pendiente')
const prioridad = ref<string>('normal')
const fechaEntrega = ref<string>('')

const clientes = ref<any[]>([])
const productos = ref<any[]>([])
const variantes = ref<{ id: number; nombre_variante: string }[]>([])
const matrizTallas = ref<string[]>([])

async function cargarMatrizTallas() {
  try {
    const r = await maestrosApi.listTallas({ limit: 100 })
    matrizTallas.value = ((r.items ?? []) as unknown as Record<string, unknown>[])
      .filter((t) => t.activo !== false)
      .map((t) => String(t.talla ?? '').trim())
      .filter((n) => n.length > 0)
  } catch { matrizTallas.value = [] }
}
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
onMounted(() => { void cargarDatos(); void cargarMatrizTallas() })

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

const variantesOptions = computed(() => {
  const propias = variantes.value.map((v) => ({ label: v.nombre_variante, value: `v:${v.id}` }))
  const nombres = new Set(variantes.value.map((v) => v.nombre_variante))
  const deMatriz = matrizTallas.value
    .filter((n) => !nombres.has(n))
    .map((n) => ({ label: `${n} (nueva)`, value: `m:${n}` }))
  return [{ label: 'Sin variante (genérico)', value: 'none' }, ...propias, ...deMatriz]
})
const varianteKey = ref<string>('none')

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
    varianteKey.value = 'none'
    try {
      variantes.value = await listVariantes(recetaSeleccionada.value)
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
    // Talla de matriz que el producto aún no tiene: se crea como variante.
    let varianteIdFinal: number | null = null
    if (varianteKey.value !== 'none') {
      if (varianteKey.value.startsWith('m:')) {
        try {
          const creada = await createVariante(
            recetaSeleccionada.value as number,
            varianteKey.value.slice(2),
          )
          varianteIdFinal = creada.id
        } catch (e: unknown) {
          showToast('error', 'No se pudo crear la talla', extractDetail(e))
          return
        }
      } else if (varianteKey.value.startsWith('v:')) {
        varianteIdFinal = Number(varianteKey.value.slice(2)) || null
      }
    }
    const creado = await produccionService.create({
      producto_id: recetaSeleccionada.value,
      cliente_id: clienteIdFinal,
      variante_id: varianteIdFinal,
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
    varianteKey.value = 'none'
    cantidad.value = 1
    modoCliente.value = 'stock'
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
          <label class="text-xs font-semibold uppercase tracking-wider text-stone-400">Cliente / Destinatario <span class="normal-case font-normal">(opcional: producción a stock)</span></label>
          <div class="text-xs space-x-2">
            <button
              type="button"
              class="hover:underline"
              :class="modoCliente === 'stock' ? 'text-amber-400 font-bold' : 'text-stone-400'"
              @click="modoCliente = 'stock'"
            >
              Para stock
            </button>
            <span class="text-stone-600">|</span>
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

        <div v-if="modoCliente === 'stock'" class="text-[11px] text-stone-500 bg-stone-900/60 border border-stone-800 rounded-lg px-3 py-2">
          Se produce para stock (1–2 por talla): al venderse se repone. Sin clienta asociada.
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
          v-else-if="modoCliente === 'nuevo'"
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
          <label class="block text-xs font-semibold uppercase tracking-wider text-stone-400 mb-1.5">Variante / Talla (matriz + propias)</label>
          <Dropdown
            v-model="varianteKey"
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
