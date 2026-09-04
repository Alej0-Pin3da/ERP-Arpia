<script setup lang="ts">
/* eslint-disable @typescript-eslint/no-explicit-any */
import { ref, computed, watch } from 'vue'
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Dropdown from 'primevue/dropdown'
import Textarea from 'primevue/textarea'
import { useAtelierStore, type VentaAtelier } from '@/stores/atelier'
import { showToast } from '@/utils/toast'
import { useMode } from '@/composables/useMode'
import { useVentas } from '@/composables/useVentas'
import { useClientes } from '@/composables/useClientes'
import { client } from '@/api/client'
import type { CanalVenta, MetodoPago, VentaCreatePayload } from '@/services/api/ventas'
import { updateVenta } from '@/services/api/ventas'
import { listCanales, listMetodosPago } from '@/services/api/maestros'

const props = defineProps<{
  visible: boolean
  ventaEditar?: VentaAtelier | null
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
  (e: 'venta-guardada', venta: VentaAtelier): void
}>()

const atelier = useAtelierStore()
const { isMock } = useMode()
const ventasApi = useVentas()
const clientesApi = useClientes()

const clientesReal = ref<{ id: number; nombre: string; telefono?: string | null; ciudad?: string | null }[]>([])
const productosReal = ref<{ id: number; nombre: string; precio_venta_sugerido?: number; precio_base?: number }[]>([])
// P1-6: maestros-driven canal/metodo (con fallback a canónicos si la API falla)
const canalesReal = ref<{ codigo: string; nombre: string }[]>([])
const metodosReal = ref<{ codigo: string; nombre: string }[]>([])

async function cargarOpcionesReales() {
  if (isMock.value) return
  try {
    const [cliRes, prodRes, canRes, metRes] = await Promise.all([
      clientesApi.list({ limit: 100, offset: 0 }),
      client.get<{ items: { id: number; nombre: string; precio_venta_sugerido?: number }[] }>('/productos', { params: { limit: 100 } }),
      listCanales({ limit: 100 }).catch(() => ({ items: [], total: 0 })),
      listMetodosPago({ limit: 100 }).catch(() => ({ items: [], total: 0 })),
    ])
    clientesReal.value = (cliRes.items as unknown as typeof clientesReal.value) ?? []
    productosReal.value = (prodRes.data.items as unknown as typeof productosReal.value) ?? []
    if (canRes.items?.length) {
      canalesReal.value = canRes.items
        .filter((c) => c.activo !== false)
        .map((c) => ({ codigo: c.codigo, nombre: c.nombre }))
      // normaliza etiqueta legacy (mock) a codigo maestro para el submit
      canal.value = canalToCodigo(canal.value)
    }
    if (metRes.items?.length) {
      metodosReal.value = metRes.items
        .filter((m) => m.activo !== false)
        .map((m) => ({ codigo: m.codigo, nombre: m.nombre }))
      metodoPago.value = metodoToCodigo(metodoPago.value)
    }
  } catch {
    // keep mock fallback silent — will show empty placeholder and fallback producto_id 1
  }
}

const isEditing = computed(() => !!props.ventaEditar)

// Form fields
const codigo = ref('')
const fecha = ref(new Date().toISOString().split('T')[0])
const modoCliente = ref<'existente' | 'manual'>('existente')
const clienteId = ref<number | null>(null)
const clienteNombreManual = ref('')
const canal = ref('Showroom Pereira')
const metodoPago = ref('Transferencia Bancolombia')
const estado = ref<VentaAtelier['estado']>('COMPLETADA')
const descuentoPct = ref<number>(0)
const descuentoValManual = ref<number | null>(null)
const observaciones = ref('')
const descontarInventario = ref(true)

// Line items
interface LocalItem {
  id: number
  producto_id?: number | null
  variante_id?: number | null
  nombre_prenda: string
  talla: string
  color: string
  cantidad: number
  precio_unitario: number
  costo_unitario: number
}

const items = ref<LocalItem[]>([])

const canalesOptionsLegacy = [
  { label: 'Showroom Pereira', value: 'Showroom Pereira' },
  { label: 'WhatsApp / DM', value: 'WhatsApp / DM' },
  { label: 'Feria / Evento NANA', value: 'Feria / Evento NANA' },
  { label: 'Feria Gótica', value: 'Feria Gótica' },
  { label: 'Tienda Online / Instagram', value: 'Tienda Online / Instagram' },
  { label: 'Encargo Personalizado', value: 'Encargo Personalizado' },
]

const metodosPagoOptionsLegacy = [
  { label: 'Transferencia Bancolombia', value: 'Transferencia Bancolombia' },
  { label: 'Transferencia Nequi / Daviplata', value: 'Transferencia Nequi' },
  { label: 'Efectivo Showroom', value: 'Efectivo Showroom' },
  { label: 'Datáfono / Tarjeta', value: 'Datáfono / Tarjeta' },
  { label: 'Contraentrega', value: 'Contraentrega' },
]

// P1-6: en REAL los dropdowns leen de maestros (value = codigo, incluye
// valores nuevos creados en Maestros); en MOCK o si falla la carga, fallback
// a las etiquetas legacy.
const canalesOptions = computed(() =>
  !isMock.value && canalesReal.value.length
    ? canalesReal.value.map((c) => ({ label: c.nombre, value: c.codigo }))
    : canalesOptionsLegacy,
)

const metodosPagoOptions = computed(() =>
  !isMock.value && metodosReal.value.length
    ? metodosReal.value.map((m) => ({ label: m.nombre, value: m.codigo }))
    : metodosPagoOptionsLegacy,
)

// Mappers from UI display values to backend Literal enums — keep UI labels intact, only translate payload
const canalToApi: Record<string, CanalVenta> = {
  'Showroom Pereira': 'showroom_pereira',
  'WhatsApp / DM': 'whatsapp',
  'Feria / Evento NANA': 'feria',
  'Feria Gótica': 'feria',
  'Tienda Online / Instagram': 'web',
  'Encargo Personalizado': 'web',
}

const metodoToApi: Record<string, MetodoPago> = {
  'Transferencia Bancolombia': 'transferencia',
  'Transferencia Nequi': 'transferencia',
  'Transferencia Nequi / Daviplata': 'transferencia',
  Transferencia: 'transferencia',
  'Efectivo Showroom': 'efectivo',
  Efectivo: 'efectivo',
  'Datáfono / Tarjeta': 'tarjeta',
  Tarjeta: 'tarjeta',
  Contraentrega: 'contraentrega',
}

// P1-6: resuelve el valor del dropdown a codigo maestro. Si ya es un codigo
// conocido (maestros cargados o canónicos) pasa directo — así los valores
// nuevos creados en Maestros llegan al backend sin 422; si es etiqueta legacy
// usa los mappers; último recurso, feria/efectivo.
function canalToCodigo(v: string): string {
  if (!v) return 'feria'
  if (canalesReal.value.some((c) => c.codigo === v)) return v
  if ((Object.values(canalToApi) as string[]).includes(v)) return v
  return canalToApi[v] ?? 'feria'
}

function metodoToCodigo(v: string): string {
  if (!v) return 'efectivo'
  if (metodosReal.value.some((m) => m.codigo === v)) return v
  if ((Object.values(metodoToApi) as string[]).includes(v)) return v
  return metodoToApi[v] ?? 'efectivo'
}

const estadosOptions = [
  { label: 'Completada / Entregada', value: 'COMPLETADA' },
  { label: 'Pendiente de Despacho', value: 'PENDIENTE' },
  { label: 'Anulada', value: 'ANULADA' },
]

const tallasOptions = ['XS', 'S', 'M', 'L', 'XL', 'A Medida', 'Única']

const clientesOptions = computed(() => {
  const src = isMock.value ? atelier.clientes : clientesReal.value
  return (src as { id: number; nombre: string; telefono?: string | null; ciudad?: string | null }[]).map((c) => ({
    label: `${c.nombre} (${(c as unknown as { telefono?: string }).telefono || (c as unknown as { ciudad?: string }).ciudad || 'Cliente'})`,
    value: c.id,
  }))
})

const catalogoPrendasOptions = computed(() => {
  if (isMock.value) {
    return (isMock.value ? atelier.prendasListas : [] as any[]).map((p) => ({
      label: `${p.nombre} (PVP: $${p.precio_venta.toLocaleString('es-CO')} | Stock: ${p.disponible_total})`,
      value: p.id,
      prenda: p,
    }))
  }
  return productosReal.value.map((p) => ({
    label: `${p.nombre} (ID: ${p.id})`,
    value: p.id,
    prenda: p as unknown as (typeof atelier.prendasListas)[number],
  }))
})

// Financial calculations
const subtotalItems = computed(() => {
  return items.value.reduce((acc, it) => acc + (it.cantidad * it.precio_unitario), 0)
})

const costoTotalItems = computed(() => {
  return items.value.reduce((acc, it) => acc + (it.cantidad * it.costo_unitario), 0)
})

const valorDescuento = computed(() => {
  if (descuentoValManual.value !== null && descuentoValManual.value > 0) {
    return descuentoValManual.value
  }
  return Math.round(subtotalItems.value * ((descuentoPct.value || 0) / 100))
})

const totalVenta = computed(() => {
  return Math.max(0, subtotalItems.value - valorDescuento.value)
})

const gananciaNeta = computed(() => {
  return totalVenta.value - costoTotalItems.value
})

const margenPct = computed(() => {
  if (totalVenta.value === 0) return 0
  return Number(((gananciaNeta.value / totalVenta.value) * 100).toFixed(1))
})

const distribucion403030 = computed(() => {
  const g = gananciaNeta.value
  return {
    reinversion40: Math.round(g * 0.4),
    margara30: Math.round(g * 0.3),
    valqui30: Math.round(g * 0.3),
  }
})

function formatCOP(val: number) {
  return `$${Math.round(val).toLocaleString('es-CO')}`
}

function agregarItemVacio() {
  items.value.push({
    id: Date.now() + Math.random(),
    producto_id: null,
    variante_id: null,
    nombre_prenda: '',
    talla: 'S',
    color: 'Negro Satín',
    cantidad: 1,
    precio_unitario: 90000,
    costo_unitario: 25000,
  })
}

async function seleccionarPrendaCatalogo(it: LocalItem, prendaId: number | null) {
  if (!prendaId) return
  const src = isMock.value ? atelier.prendasListas : (productosReal.value as unknown as typeof atelier.prendasListas)
  const p = (src as typeof atelier.prendasListas).find((x) => x.id === prendaId)
  if (p) {
    it.producto_id = p.id
    it.nombre_prenda = p.nombre
    const precio = (p as unknown as { precio_venta?: number; precio_venta_sugerido?: number }).precio_venta ?? (p as unknown as { precio_venta_sugerido?: number }).precio_venta_sugerido ?? it.precio_unitario
    it.precio_unitario = precio
    it.costo_unitario = (p as unknown as { costo_unitario?: number }).costo_unitario ?? it.costo_unitario
    if ((p as unknown as { variantes?: { talla: string }[] }).variantes?.[0]) {
      it.talla = (p as unknown as { variantes: { talla: string }[] }).variantes[0].talla
    }
    // In REAL mode, if product has variantes, fetch and pick first variant
    if (!isMock.value) {
      try {
        const vare = await client.get<{ id: number; nombre_variante: string }[]>(`/productos/${prendaId}/variantes`)
        if (vare.data.length > 0) {
          it.variante_id = vare.data[0].id
          // try to map talla from variante nombre (e.g. "S", "M - Rojo")
          const rawTalla = vare.data[0].nombre_variante?.split(' - ')[0]?.trim()
          if (rawTalla) it.talla = rawTalla
        } else {
          it.variante_id = null
        }
      } catch {
        it.variante_id = null
      }
    }
  } else {
    it.producto_id = prendaId
  }
}

function eliminarItem(index: number) {
  items.value.splice(index, 1)
  if (items.value.length === 0) {
    agregarItemVacio()
  }
}

function initForm() {
  if (props.ventaEditar) {
    const v = props.ventaEditar
    codigo.value = v.codigo
    fecha.value = v.fecha
    clienteId.value = v.cliente_id || null
    clienteNombreManual.value = v.cliente_nombre
    modoCliente.value = v.cliente_id ? 'existente' : 'manual'
    canal.value = v.canal
    metodoPago.value = v.metodo_pago
    estado.value = v.estado
    descuentoPct.value = v.descuento_porcentaje
    descuentoValManual.value = v.descuento_valor
    observaciones.value = v.observaciones || ''
    descontarInventario.value = v.descontar_inventario ?? true
    items.value = v.items.map((it) => ({
      id: it.id,
      producto_id: it.producto_id,
      variante_id: (it as unknown as { variante_id?: number }).variante_id ?? null,
      nombre_prenda: it.nombre_prenda,
      talla: it.talla,
      color: it.color,
      cantidad: it.cantidad,
      precio_unitario: it.precio_unitario,
      costo_unitario: it.costo_unitario,
    }))
  } else {
    // New sale default
    if (!isMock.value) return // real uses server id
    const nextNum = (atelier.ventas.length ? Math.max(...atelier.ventas.map((v) => v.id)) : 0) + 1
    codigo.value = `VEN-ARP-${String(nextNum).padStart(3, '0')}`
    fecha.value = new Date().toISOString().split('T')[0]
    modoCliente.value = 'existente'
    clienteId.value = null
    clienteNombreManual.value = ''
    canal.value = 'Showroom Pereira'
    metodoPago.value = 'Transferencia Bancolombia'
    estado.value = 'COMPLETADA'
    descuentoPct.value = 0
    descuentoValManual.value = null
    observaciones.value = ''
    descontarInventario.value = true
    items.value = [
      {
        id: Date.now(),
        producto_id: null,
        variante_id: null,
        nombre_prenda: 'Corset Estructurado "Garras"',
        talla: 'S',
        color: 'Negro Satín',
        cantidad: 1,
        precio_unitario: 95000,
        costo_unitario: 29826,
      },
    ]
  }
}

watch(
  () => props.visible,
  (val) => {
    if (val) {
      initForm()
      void cargarOpcionesReales()
    }
  },
  { immediate: true },
)
watch(isMock, () => {
  if (props.visible) void cargarOpcionesReales()
})

async function guardar() {
  if (items.value.length === 0) {
    showToast('warn', 'Items requeridos', 'Debe agregar al menos una prenda o producto a la venta.')
    return
  }

  for (const it of items.value) {
    if (!it.nombre_prenda.trim()) {
      showToast('warn', 'Nombre de prenda requerido', 'Complete el nombre de todas las prendas.')
      return
    }
  }

  let nombreClienteFinal = 'Cliente General'
  let cidFinal: number | null = null

  if (modoCliente.value === 'existente' && clienteId.value) {
    const srcCli = isMock.value ? atelier.clientes : (clientesReal.value as unknown as typeof atelier.clientes)
    const c = (srcCli as typeof atelier.clientes).find((x) => x.id === clienteId.value)
    if (c) {
      nombreClienteFinal = c.nombre
      cidFinal = c.id
    } else {
      // clienteId viene de un cliente que ya no existe en la fuente activa — evita mandar id fantasma
      cidFinal = null
    }
  } else if (clienteNombreManual.value.trim()) {
    nombreClienteFinal = clienteNombreManual.value.trim()
  }

  if (isMock.value) {
    const payload: Partial<VentaAtelier> = {
      codigo: codigo.value || `VEN-ARP-${Date.now().toString().slice(-4)}`,
      cliente_id: cidFinal,
      cliente_nombre: nombreClienteFinal,
      fecha: fecha.value,
      canal: canal.value,
      metodo_pago: metodoPago.value,
      estado: estado.value,
      items: items.value.map((it, idx) => ({
        id: idx + 1,
        producto_id: it.producto_id || null,
        nombre_prenda: it.nombre_prenda,
        talla: it.talla,
        color: it.color,
        cantidad: it.cantidad,
        precio_unitario: it.precio_unitario,
        costo_unitario: it.costo_unitario,
        subtotal: it.cantidad * it.precio_unitario,
        costo_subtotal: it.cantidad * it.costo_unitario,
      })),
      subtotal: subtotalItems.value,
      descuento_porcentaje: Number(descuentoPct.value) || 0,
      descuento_valor: valorDescuento.value,
      total_venta: totalVenta.value,
      costo_total: costoTotalItems.value,
      ganancia_neta: gananciaNeta.value,
      margen_pct: margenPct.value,
      reinversion_40: distribucion403030.value.reinversion40,
      margarita_30: distribucion403030.value.margara30,
      valqui_30: distribucion403030.value.valqui30,
      observaciones: observaciones.value,
      descontar_inventario: descontarInventario.value,
    }
    if (isEditing.value && props.ventaEditar) {
      const act = atelier.actualizarVenta(props.ventaEditar.id, payload)
      if (act) {
        showToast('success', 'Venta Actualizada', `La venta ${act.codigo} ha sido actualizada con éxito.`)
        emit('venta-guardada', act)
      }
    } else {
      const nueva = atelier.crearVenta(payload)
      showToast('success', 'Venta Registrada', `Venta ${nueva.codigo} guardada por ${formatCOP(nueva.total_venta)}.`)
      emit('venta-guardada', nueva)
    }
    emit('update:visible', false)
    return
  }

  // Real API — P1-6: valores resueltos a codigo maestro (ver canalToCodigo)
  const apiPayload: VentaCreatePayload = {
    cliente_id: cidFinal,
    canal_venta: canalToCodigo(canal.value),
    metodo_pago: metodoToCodigo(metodoPago.value),
    descuento_porcentaje: Number(descuentoPct.value) || 0,
    es_regalo: false,
    detalles: items.value.map((it) => ({
      producto_id: it.producto_id ?? 1,
      variante_id: it.variante_id ?? null,
      cantidad: it.cantidad,
      precio_unitario: it.precio_unitario,
    })),
  }
  try {
    if (isEditing.value && props.ventaEditar) {
      const actualizada = await updateVenta(props.ventaEditar.id, apiPayload)
      showToast('success', 'Venta Actualizada', `Venta ${(actualizada as unknown as Record<string, unknown>).codigo ?? props.ventaEditar.codigo} actualizada en BD.`)
      emit('venta-guardada', actualizada as unknown as VentaAtelier)
    } else {
      const creada = await ventasApi.create(apiPayload)
      showToast('success', 'Venta Registrada', `Venta ${(creada as unknown as Record<string, unknown>).codigo ?? 'creada'} guardada en BD.`)
      emit('venta-guardada', creada as unknown as VentaAtelier)
    }
    emit('update:visible', false)
  } catch (e: unknown) {
    const axiosDetail = (e as { response?: { data?: { detail?: string }; status?: number } })?.response?.data?.detail
    const status = (e as { response?: { status?: number } })?.response?.status
    let msg = axiosDetail ?? (e instanceof Error ? e.message : 'Error al guardar venta')
    if (status === 409) {
      msg = axiosDetail ? `Stock insuficiente: ${axiosDetail}` : 'Stock insuficiente para los insumos de esa prenda (409). Revisá el inventario o elegí otro producto con stock.'
    }
    showToast('error', 'Error', String(msg))
  }
}
</script>

<template>
  <Dialog
    :visible="visible"
    modal
    :header="isEditing ? `✏️ Editar Venta: ${ventaEditar?.codigo}` : '✨ Registrar Nueva Venta Realizada'"
    :style="{ width: '92vw', maxWidth: '820px' }"
    @update:visible="(v) => emit('update:visible', v)"
  >
    <div class="space-y-5 pt-1 text-xs text-stone-200">
      <!-- Row 1: Code, Date, Status -->
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 bg-stone-900/60 p-3.5 rounded-xl border border-stone-800">
        <div>
          <label class="block text-[11px] font-bold text-amber-300 uppercase tracking-wider mb-1">
            Código Venta
          </label>
          <InputText v-model="codigo" class="w-full text-xs font-mono" placeholder="VEN-ARP-021" />
        </div>

        <div>
          <label class="block text-[11px] font-bold text-stone-400 uppercase tracking-wider mb-1">
            Fecha de Venta
          </label>
          <InputText v-model="fecha" type="date" class="w-full text-xs font-mono" />
        </div>

        <div>
          <label class="block text-[11px] font-bold text-stone-400 uppercase tracking-wider mb-1">
            Estado
          </label>
          <Dropdown
            v-model="estado"
            :options="estadosOptions"
            option-label="label"
            option-value="value"
            class="w-full text-xs"
          />
        </div>
      </div>

      <!-- Row 2: Client, Channel & Payment -->
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 bg-stone-900/60 p-3.5 rounded-xl border border-stone-800">
        <!-- Client selector -->
        <div class="sm:col-span-1">
          <div class="flex items-center justify-between mb-1">
            <label class="text-[11px] font-bold text-amber-300 uppercase tracking-wider">Cliente</label>
            <div class="text-[10px] space-x-1.5 font-mono">
              <button
                type="button"
                :class="modoCliente === 'existente' ? 'text-amber-400 font-bold underline' : 'text-stone-400'"
                @click="modoCliente = 'existente'"
              >
                CRM
              </button>
              <span class="text-stone-600">|</span>
              <button
                type="button"
                :class="modoCliente === 'manual' ? 'text-amber-400 font-bold underline' : 'text-stone-400'"
                @click="modoCliente = 'manual'"
              >
                Manual
              </button>
            </div>
          </div>

          <Dropdown
            v-if="modoCliente === 'existente'"
            v-model="clienteId"
            :options="clientesOptions"
            option-label="label"
            option-value="value"
            placeholder="Seleccionar clienta..."
            class="w-full text-xs"
            filter
          />
          <InputText
            v-else
            v-model="clienteNombreManual"
            placeholder="Nombre clienta / Comprador feria..."
            class="w-full text-xs"
          />
        </div>

        <!-- Channel -->
        <div>
          <label class="block text-[11px] font-bold text-stone-400 uppercase tracking-wider mb-1">
            Canal de Venta
          </label>
          <Dropdown
            v-model="canal"
            :options="canalesOptions"
            option-label="label"
            option-value="value"
            class="w-full text-xs"
          />
        </div>

        <!-- Payment -->
        <div>
          <label class="block text-[11px] font-bold text-stone-400 uppercase tracking-wider mb-1">
            Método de Pago
          </label>
          <Dropdown
            v-model="metodoPago"
            :options="metodosPagoOptions"
            option-label="label"
            option-value="value"
            class="w-full text-xs"
          />
        </div>
      </div>

      <!-- Row 3: Items Table & Line Builder -->
      <div class="bg-stone-900/90 p-4 rounded-xl border border-stone-800 space-y-3">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <span class="text-xs font-bold text-amber-400 uppercase tracking-wider font-mono">
              Prendas & Artículos ({{ items.length }})
            </span>
          </div>
          <Button
            label="Agregar Prenda"
            icon="pi pi-plus"
            size="small"
            class="p-button-outlined p-button-warning text-[11px] py-1 px-2.5"
            @click="agregarItemVacio"
          />
        </div>

        <!-- Items List -->
        <div class="space-y-3">
          <div
            v-for="(it, idx) in items"
            :key="it.id"
            class="bg-stone-950/80 p-3 rounded-lg border border-stone-800/80 relative group"
          >
            <div class="grid grid-cols-1 sm:grid-cols-12 gap-2.5 items-end">
              <!-- Quick Select from Inventory (Optional) -->
              <div class="sm:col-span-4">
                <label class="block text-[10px] text-stone-400 mb-0.5">Prenda / Modelo</label>
                <div class="space-y-1">
                  <Dropdown
                    :model-value="it.producto_id"
                    :options="catalogoPrendasOptions"
                    option-label="label"
                    option-value="value"
                    placeholder="Elegir del perchero..."
                    class="w-full text-xs mb-1"
                    show-clear
                    @update:model-value="(val) => seleccionarPrendaCatalogo(it, val)"
                  />
                  <InputText
                    v-model="it.nombre_prenda"
                    placeholder="O escribe nombre personalizado..."
                    class="w-full text-xs font-serif font-semibold"
                  />
                </div>
              </div>

              <!-- Talla -->
              <div class="sm:col-span-2">
                <label class="block text-[10px] text-stone-400 mb-0.5">Talla</label>
                <Dropdown
                  v-model="it.talla"
                  :options="tallasOptions"
                  editable
                  class="w-full text-xs"
                />
              </div>

              <!-- Color / Detalle -->
              <div class="sm:col-span-2">
                <label class="block text-[10px] text-stone-400 mb-0.5">Color / Acabado</label>
                <InputText v-model="it.color" placeholder="Ej: Negro Satín" class="w-full text-xs" />
              </div>

              <!-- Cantidad -->
              <div class="sm:col-span-1">
                <label class="block text-[10px] text-stone-400 mb-0.5">Cant.</label>
                <InputNumber v-model="it.cantidad" :min="1" class="w-full text-xs font-mono" />
              </div>

              <!-- Precio Unitario -->
              <div class="sm:col-span-2">
                <label class="block text-[10px] text-stone-400 mb-0.5">Precio Venta ($)</label>
                <InputNumber v-model="it.precio_unitario" mode="currency" currency="COP" locale="es-CO" :min="0" class="w-full text-xs font-mono" />
              </div>

              <!-- Actions & Cost -->
              <div class="sm:col-span-1 flex items-center justify-end gap-1">
                <Button
                  icon="pi pi-trash"
                  size="small"
                  class="p-button-danger p-button-text text-xs p-1"
                  title="Eliminar prenda"
                  @click="eliminarItem(idx)"
                />
              </div>
            </div>

            <!-- Item Footer with Cost & Subtotal info -->
            <div class="mt-2 pt-2 border-t border-stone-800/60 flex flex-wrap items-center justify-between text-[11px] text-stone-400 font-mono">
              <div class="flex items-center gap-2">
                <span>Costo Unitario Taller:</span>
                <InputNumber
                  v-model="it.costo_unitario"
                  mode="currency"
                  currency="COP"
                  locale="es-CO"
                  :min="0"
                  class="w-28 text-[11px]"
                />
              </div>
              <div class="flex items-center gap-3">
                <span>Subtotal: <strong class="text-stone-100">{{ formatCOP(it.cantidad * it.precio_unitario) }}</strong></span>
                <span class="text-emerald-400">Margen: {{ it.precio_unitario > 0 ? (((it.precio_unitario - it.costo_unitario) / it.precio_unitario) * 100).toFixed(0) : 0 }}%</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Row 4: Discount & Financial Summary -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <!-- Left: Discounts & Notes -->
        <div class="space-y-3 bg-stone-900/60 p-3.5 rounded-xl border border-stone-800">
          <div class="grid grid-cols-2 gap-2">
            <div>
              <label class="block text-[11px] font-bold text-stone-400 uppercase tracking-wider mb-1">
                Descuento (%)
              </label>
              <InputNumber
                v-model="descuentoPct"
                :min="0"
                :max="100"
                suffix="%"
                class="w-full text-xs font-mono"
              />
            </div>
            <div>
              <label class="block text-[11px] font-bold text-stone-400 uppercase tracking-wider mb-1">
                Descuento Valor ($)
              </label>
              <div class="p-2 bg-stone-950 border border-stone-800 rounded font-mono text-amber-400 font-bold text-right">
                -{{ formatCOP(valorDescuento) }}
              </div>
            </div>
          </div>

          <div>
            <label class="block text-[11px] font-bold text-stone-400 uppercase tracking-wider mb-1">
              Observaciones & Notas
            </label>
            <Textarea
              v-model="observaciones"
              rows="2"
              placeholder="Ej: Descuento 25% socia, empaque regalo cumpleaños, entrega personalizada..."
              class="w-full text-xs"
            />
          </div>
        </div>

        <!-- Right: Partner 40/30/30 Distribution Card -->
        <div class="bg-gradient-to-br from-stone-950 via-stone-900 to-amber-950/30 p-4 rounded-xl border border-amber-500/30 space-y-2.5 font-mono shadow-inner">
          <div class="flex items-center justify-between text-xs border-b border-stone-800 pb-1.5">
            <span class="text-stone-400 uppercase font-bold tracking-wider">Subtotal:</span>
            <span class="text-stone-200 font-bold">{{ formatCOP(subtotalItems) }}</span>
          </div>

          <div v-if="valorDescuento > 0" class="flex items-center justify-between text-xs border-b border-stone-800 pb-1.5 text-rose-400">
            <span>Descuento aplicado:</span>
            <span>-{{ formatCOP(valorDescuento) }}</span>
          </div>

          <div class="flex items-center justify-between text-sm font-bold border-b border-amber-500/30 pb-2">
            <span class="text-amber-300">TOTAL FACTURADO:</span>
            <span class="text-amber-400 text-base">{{ formatCOP(totalVenta) }}</span>
          </div>

          <div class="grid grid-cols-2 gap-2 text-[11px] pt-1">
            <div class="text-stone-400">
              Costo Producción: <span class="text-stone-200">{{ formatCOP(costoTotalItems) }}</span>
            </div>
            <div class="text-right text-emerald-400 font-bold">
              Utilidad: {{ formatCOP(gananciaNeta) }} ({{ margenPct }}%)
            </div>
          </div>

          <!-- Formula 40/30/30 Breakdown -->
          <div class="pt-2 border-t border-stone-800/80 space-y-1 text-[11px]">
            <div class="text-[10px] text-amber-500 font-bold tracking-wider uppercase">
              Liquidación Socias (40% / 30% / 30%)
            </div>
            <div class="flex justify-between text-stone-300">
              <span>🏛️ Fondo Reinversión Atelier (40%):</span>
              <span class="font-bold text-amber-400">{{ formatCOP(distribucion403030.reinversion40) }}</span>
            </div>
            <div class="flex justify-between text-stone-300">
              <span>🪡 Margara Confección (30%):</span>
              <span class="font-bold text-stone-100">{{ formatCOP(distribucion403030.margara30) }}</span>
            </div>
            <div class="flex justify-between text-stone-300">
              <span>🎨 Valqui Diseño (30%):</span>
              <span class="font-bold text-stone-100">{{ formatCOP(distribucion403030.valqui30) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="flex items-center justify-end gap-2 pt-3 border-t border-stone-800">
        <Button
          label="Cancelar"
          icon="pi pi-times"
          size="small"
          class="p-button-text p-button-secondary text-xs"
          @click="emit('update:visible', false)"
        />
        <Button
          :label="isEditing ? 'Guardar Cambios' : 'Registrar Venta'"
          icon="pi pi-check"
          size="small"
          class="p-button-warning text-xs font-semibold px-4"
          @click="guardar"
        />
      </div>
    </template>
  </Dialog>
</template>
