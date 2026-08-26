<script setup lang="ts">
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
  nombre_prenda: string
  talla: string
  color: string
  cantidad: number
  precio_unitario: number
  costo_unitario: number
}

const items = ref<LocalItem[]>([])

const canalesOptions = [
  { label: 'Showroom Pereira', value: 'Showroom Pereira' },
  { label: 'WhatsApp / DM', value: 'WhatsApp / DM' },
  { label: 'Feria / Evento NANA', value: 'Feria / Evento NANA' },
  { label: 'Feria Gótica', value: 'Feria Gótica' },
  { label: 'Tienda Online / Instagram', value: 'Tienda Online / Instagram' },
  { label: 'Encargo Personalizado', value: 'Encargo Personalizado' },
]

const metodosPagoOptions = [
  { label: 'Transferencia Bancolombia', value: 'Transferencia Bancolombia' },
  { label: 'Transferencia Nequi / Daviplata', value: 'Transferencia Nequi' },
  { label: 'Efectivo Showroom', value: 'Efectivo Showroom' },
  { label: 'Datáfono / Tarjeta', value: 'Datáfono / Tarjeta' },
  { label: 'Contraentrega', value: 'Contraentrega' },
]

const estadosOptions = [
  { label: 'Completada / Entregada', value: 'COMPLETADA' },
  { label: 'Pendiente de Despacho', value: 'PENDIENTE' },
  { label: 'Anulada', value: 'ANULADA' },
]

const tallasOptions = ['XS', 'S', 'M', 'L', 'XL', 'A Medida', 'Única']

const clientesOptions = computed(() => {
  return atelier.clientes.map((c) => ({
    label: `${c.nombre} (${c.telefono || c.ciudad || 'Cliente'})`,
    value: c.id,
  }))
})

const catalogoPrendasOptions = computed(() => {
  return atelier.prendasListas.map((p) => ({
    label: `${p.nombre} (PVP: $${p.precio_venta.toLocaleString('es-CO')} | Stock: ${p.disponible_total})`,
    value: p.id,
    prenda: p,
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
    nombre_prenda: '',
    talla: 'S',
    color: 'Negro Satín',
    cantidad: 1,
    precio_unitario: 90000,
    costo_unitario: 25000,
  })
}

function seleccionarPrendaCatalogo(it: LocalItem, prendaId: number | null) {
  if (!prendaId) return
  const p = atelier.prendasListas.find((x) => x.id === prendaId)
  if (p) {
    it.producto_id = p.id
    it.nombre_prenda = p.nombre
    it.precio_unitario = p.precio_venta
    it.costo_unitario = p.costo_unitario
    if (p.variantes && p.variantes.length > 0) {
      it.talla = p.variantes[0].talla
    }
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
      nombre_prenda: it.nombre_prenda,
      talla: it.talla,
      color: it.color,
      cantidad: it.cantidad,
      precio_unitario: it.precio_unitario,
      costo_unitario: it.costo_unitario,
    }))
  } else {
    // New sale default
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
    if (val) initForm()
  },
  { immediate: true },
)

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
    const c = atelier.clientes.find((x) => x.id === clienteId.value)
    if (c) {
      nombreClienteFinal = c.nombre
      cidFinal = c.id
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

  // Real API — map to /ventas canonical enums (canal_venta, metodo_pago)
  const canalMap: Record<string, string> = {
    'Showroom Pereira': 'showroom_pereira',
    'WhatsApp / DM': 'whatsapp',
    'Feria / Evento NANA': 'feria',
    'Feria Gótica': 'feria',
    'Tienda Online / Instagram': 'web',
    'Encargo Personalizado': 'web',
  }
  const pagoMap: Record<string, string> = {
    'Transferencia Bancolombia': 'transferencia',
    'Transferencia Nequi': 'transferencia',
    'Transferencia Nequi / Daviplata': 'transferencia',
    'Efectivo Showroom': 'efectivo',
    'Datáfono / Tarjeta': 'tarjeta',
    'Contraentrega': 'contraentrega',
  }
  const apiPayload = {
    cliente_id: cidFinal,
    canal_venta: (canalMap[canal.value] ?? 'showroom_pereira') as never,
    metodo_pago: (pagoMap[metodoPago.value] ?? 'transferencia') as never,
    descuento_porcentaje: Number(descuentoPct.value) || 0,
    es_regalo: false,
    detalles: items.value.map((it) => ({
      producto_id: it.producto_id ?? 1,
      variante_id: null,
      cantidad: it.cantidad,
      precio_unitario: it.precio_unitario,
    })),
  }
  try {
    const creada = await ventasApi.create(apiPayload as never)
    showToast('success', 'Venta Registrada', `Venta ${(creada as unknown as Record<string, unknown>).codigo ?? 'creada'} guardada en BD.`)
    emit('venta-guardada', creada as unknown as VentaAtelier)
    emit('update:visible', false)
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? 'Error al guardar venta'
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
