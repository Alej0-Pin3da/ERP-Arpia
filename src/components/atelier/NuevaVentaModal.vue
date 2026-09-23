<script setup lang="ts">
/* eslint-disable @typescript-eslint/no-explicit-any */
import { ref, computed, watch } from 'vue'
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Dropdown from 'primevue/dropdown'
import Textarea from 'primevue/textarea'
import { useVentas } from '@/composables/useVentas'
import { useClientes } from '@/composables/useClientes'
import NuevoClienteModal from '@/components/atelier/NuevoClienteModal.vue'
import { client } from '@/api/client'
import type { CanalVenta, MetodoPago, VentaCreatePayload, VentaRead } from '@/services/api/ventas'
import { updateVenta } from '@/services/api/ventas'
import { listCanales, listMetodosPago } from '@/services/api/maestros'
import { showToast } from '@/utils/toast'

/** Minimal venta shape this modal edits (REAL display object from the caller). */
export interface VentaEditar {
  id: number
  codigo: string
  fecha: string
  cliente_id: number | null
  cliente_nombre: string
  canal: string
  metodo_pago: string
  estado: string
  descuento_porcentaje: number
  descuento_valor: number
  observaciones?: string
  descontar_inventario?: boolean
  items: {
    id: number
    producto_id?: number | null
    variante_id?: number | null
    nombre_prenda: string
    talla: string
    color: string
    cantidad: number
    precio_unitario: number
    costo_unitario: number
  }[]
}

const props = defineProps<{
  visible: boolean
  ventaEditar?: VentaEditar | null
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
  (e: 'venta-guardada', venta: VentaRead): void
}>()

const ventasApi = useVentas()
const clientesApi = useClientes()

const clientes = ref<{ id: number; nombre: string; telefono?: string | null; ciudad?: string | null }[]>([])
const productos = ref<{ id: number; nombre: string; precio_venta_sugerido?: number; precio_base?: number }[]>([])
// Maestros-driven canal/metodo (con fallback a canónicos si la API falla)
const canales = ref<{ codigo: string; nombre: string }[]>([])
const metodos = ref<{ codigo: string; nombre: string }[]>([])

async function cargarOpciones() {
  try {
    const [cliRes, prodRes, canRes, metRes] = await Promise.all([
      clientesApi.list({ limit: 100, offset: 0 }),
      client.get<{ items: { id: number; nombre: string; precio_venta_sugerido?: number }[] }>('/productos', { params: { limit: 100 } }),
      listCanales({ limit: 100 }).catch(() => ({ items: [], total: 0 })),
      listMetodosPago({ limit: 100 }).catch(() => ({ items: [], total: 0 })),
    ])
    clientes.value = (cliRes.items as unknown as typeof clientes.value) ?? []
    productos.value = (prodRes.data.items as unknown as typeof productos.value) ?? []
    if (canRes.items?.length) {
      canales.value = canRes.items
        .filter((c) => c.activo !== false)
        .map((c) => ({ codigo: c.codigo, nombre: c.nombre }))
      // normaliza etiqueta legacy a codigo maestro para el submit
      canal.value = canalToCodigo(canal.value)
    }
    if (metRes.items?.length) {
      metodos.value = metRes.items
        .filter((m) => m.activo !== false)
        .map((m) => ({ codigo: m.codigo, nombre: m.nombre }))
      metodoPago.value = metodoToCodigo(metodoPago.value)
    }
  } catch {
    // keep silent — will show empty placeholder
  }
}

async function onClienteGuardado(c: { id: number; nombre: string }) {
  // La clienta creada inline queda seleccionada sin salir del modal de venta
  try {
    const res = await clientesApi.list({ limit: 100, offset: 0 })
    clientes.value = (res.items as unknown as typeof clientes.value) ?? []
  } catch {
    // si falla el refresh, igual se selecciona con los datos del evento
  }
  modoCliente.value = 'existente'
  clienteId.value = c.id
  showNuevoCliente.value = false
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
const estado = ref<string>('COMPLETADA')
const descuentoPct = ref<number>(0)
const descuentoValManual = ref<number | null>(null)
const codigoDescuento = ref<string>('')
const motivoDescuento = ref<string>('')
const showNuevoCliente = ref(false)
const observaciones = ref('')
const MOTIVOS_DESCUENTO = [
  { value: '', label: 'Sin motivo' },
  { value: 'bono', label: 'Bono' },
  { value: 'aniversario', label: 'Aniversario' },
  { value: 'lanzamiento', label: 'Lanzamiento' },
  { value: 'rotacion', label: 'Rotación' },
  { value: 'otro', label: 'Otro' },
]

// Line items
interface LocalItem {
  id: number
  producto_id?: number | null
  variante_id?: number | null
  nombre_prenda: string
  talla: string
  cantidad: number
  precio_unitario: number
  costo_unitario: number
  variantes?: { id: number; nombre_variante: string }[]
  variantesLoading?: boolean
  stockTexto?: string
  stockDisponible?: number
}

const items = ref<LocalItem[]>([])
const guardando = ref(false)

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

// Los dropdowns leen de maestros (value = codigo, incluye
// valores nuevos creados en Maestros); si falla la carga, fallback
// a las etiquetas legacy.
const canalesOptions = computed(() =>
  canales.value.length
    ? canales.value.map((c) => ({ label: c.nombre, value: c.codigo }))
    : canalesOptionsLegacy,
)

const metodosPagoOptions = computed(() =>
  metodos.value.length
    ? metodos.value.map((m) => ({ label: m.nombre, value: m.codigo }))
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
  if (canales.value.some((c) => c.codigo === v)) return v
  if ((Object.values(canalToApi) as string[]).includes(v)) return v
  return canalToApi[v] ?? 'feria'
}

function metodoToCodigo(v: string): string {
  if (!v) return 'efectivo'
  if (metodos.value.some((m) => m.codigo === v)) return v
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
  const src = clientes.value
  return (src as { id: number; nombre: string; telefono?: string | null; ciudad?: string | null }[]).map((c) => ({
    label: `${c.nombre} (${(c as unknown as { telefono?: string }).telefono || (c as unknown as { ciudad?: string }).ciudad || 'Cliente'})`,
    value: c.id,
  }))
})

const catalogoPrendasOptions = computed(() => {
  return productos.value.map((p) => {
    const pvRaw = (p as unknown as { precio_venta_sugerido?: number | string }).precio_venta_sugerido
    const pv = Number(pvRaw ?? 0)
    return {
      label: Number.isFinite(pv) && pv > 0 ? `${p.nombre} (PVP: $${pv.toLocaleString('es-CO')})` : `${p.nombre} (ID: ${p.id})`,
      value: p.id,
      prenda: p as unknown as Record<string, unknown>,
    }
  })
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
    talla: '',
    cantidad: 1,
    precio_unitario: 0,
    costo_unitario: 0,
    variantes: [],
    stockTexto: '',
    stockDisponible: 0,
  })
}

function tallaDeVariante(nombre: string | undefined): string {
  if (!nombre) return ''
  return nombre.split(' - ')[0]?.trim() ?? ''
}

async function cargarVariantesYStock(it: LocalItem, prendaId: number, opts: { preservePrecio?: boolean } = {}) {
  it.variantesLoading = true
  try {
    const vare = await client.get<{ id: number; nombre_variante: string }[]>(`/productos/${prendaId}/variantes`)
    it.variantes = vare.data ?? []
  } catch {
    it.variantes = []
  }
  // Stock visible: prendas disponibles de este producto (por talla/variante)
  try {
    const stockRes = await client.get<{ items: { producto_id?: number | null; variante_id: number | null; estado: string; talla?: string | null }[] }>(
      '/prendas-confeccionadas',
      { params: { estado: 'disponible', limit: 200 } },
    )
    const rows = (stockRes.data.items ?? []).filter((r) => r.producto_id === prendaId)
    const porVariante = new Map<number, number>()
    let genericas = 0
    for (const r of rows) {
      if (r.variante_id != null) porVariante.set(r.variante_id, (porVariante.get(r.variante_id) ?? 0) + 1)
      else genericas += 1
    }
    const total = rows.length
    it.stockDisponible = total
    if (it.variantes?.length) {
      const detalle = it.variantes
        .map((v) => `${tallaDeVariante(v.nombre_variante)}: ${porVariante.get(v.id) ?? 0}`)
        .join(' · ')
      it.stockTexto = total > 0 ? `${total} uds en perchero (${detalle})` : 'Sin stock en perchero'
    } else {
      it.stockTexto = total > 0 ? `${total} uds disponibles (genérica)` : 'Sin stock en perchero'
    }
  } catch {
    it.stockTexto = ''
    it.stockDisponible = 0
  } finally {
    it.variantesLoading = false
  }
  if (!opts.preservePrecio) {
    // El llamador ya resolvió precio/costo; aquí solo se asegura sync inicial
    // cuando hay una única variante o la talla actual no matchea.
    if (it.variantes?.length === 1 && it.variante_id == null) {
      it.variante_id = it.variantes[0].id
      it.talla = tallaDeVariante(it.variantes[0].nombre_variante)
    }
  }
}

function onVarianteChange(it: LocalItem, varianteId: number | null) {
  it.variante_id = varianteId
  if (varianteId == null) {
    if (!it.talla) it.talla = 'Única'
    return
  }
  const v = it.variantes?.find((x) => x.id === varianteId)
  if (v) it.talla = tallaDeVariante(v.nombre_variante)
}

function onTallaChange(it: LocalItem, talla: string) {
  it.talla = talla
  // Sincroniza variante cuando la talla matchea exactamente una variante;
  // texto libre => variante null (genérica), evita vender talla errada.
  const match = (it.variantes ?? []).filter((v) => tallaDeVariante(v.nombre_variante) === talla)
  it.variante_id = match.length === 1 ? match[0].id : null
}

async function seleccionarPrendaCatalogo(it: LocalItem, prendaId: number | null) {
  if (!prendaId) return
  const src = productos.value as unknown as Record<string, any>[]
  const p = src.find((x) => x.id === prendaId)
  if (p) {
    it.producto_id = p.id
    it.nombre_prenda = p.nombre
    const rawPrecio = (p as unknown as { precio_venta?: number | string; precio_venta_sugerido?: number | string }).precio_venta ?? (p as unknown as { precio_venta_sugerido?: number | string }).precio_venta_sugerido
    // Backend Numeric serializa como string ("83000.0000"): normalizar a number.
    // Precio default SIEMPRE del producto (fix 95000 fijo): si no hay precio
    // válido, queda en 0 para no vender con precio fantasma.
    const numPrecio = Number(rawPrecio ?? NaN)
    it.precio_unitario = Number.isFinite(numPrecio) && numPrecio > 0 ? numPrecio : 0
    const rawCosto = (p as unknown as { costo_unitario?: number | string; costos_operativos_fijos?: number | string; costo_insumos?: number | string }).costo_unitario ?? (p as unknown as { costos_operativos_fijos?: number | string }).costos_operativos_fijos ?? (p as unknown as { costo_insumos?: number | string }).costo_insumos
    const numCosto = Number(rawCosto ?? NaN)
    it.costo_unitario = Number.isFinite(numCosto) && numCosto > 0 ? numCosto : 0
    await cargarVariantesYStock(it, prendaId)
    // Sync inicial: primera variante por defecto (antes era auto sin talla
    // sincronizada); ahora variante+talla quedan atados y con stock visible.
    if (it.variantes?.length) {
      it.variante_id = it.variantes[0].id
      it.talla = tallaDeVariante(it.variantes[0].nombre_variante)
    } else {
      it.variante_id = null
      it.talla = 'Única'
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
    codigoDescuento.value = (v as unknown as Record<string, unknown>).codigo_descuento as string ?? ''
    motivoDescuento.value = (v as unknown as Record<string, unknown>).motivo_descuento as string ?? ''
    observaciones.value = v.observaciones || ''
    items.value = v.items.map((it) => ({
      id: it.id,
      producto_id: it.producto_id,
      variante_id: (it as unknown as { variante_id?: number }).variante_id ?? null,
      nombre_prenda: it.nombre_prenda,
      talla: it.talla,
      cantidad: it.cantidad,
      precio_unitario: it.precio_unitario,
      costo_unitario: it.costo_unitario,
      variantes: [],
      stockTexto: '',
      stockDisponible: 0,
    }))
    // Carga variantes+stock sin pisar precio/cantidad editados
    for (const it of items.value) {
      if (it.producto_id != null) void cargarVariantesYStock(it, it.producto_id, { preservePrecio: true })
    }
  } else {
    // New sale default (real uses server id)
    codigo.value = ''
    fecha.value = new Date().toISOString().split('T')[0]
    modoCliente.value = 'existente'
    clienteId.value = null
    clienteNombreManual.value = ''
    canal.value = 'Showroom Pereira'
    metodoPago.value = 'Transferencia Bancolombia'
    estado.value = 'COMPLETADA'
    descuentoPct.value = 0
    descuentoValManual.value = null
    codigoDescuento.value = ''
    motivoDescuento.value = ''
    observaciones.value = ''
    items.value = [
      {
        id: Date.now(),
        producto_id: null,
        variante_id: null,
        nombre_prenda: '',
        talla: '',
        cantidad: 1,
        precio_unitario: 0,
        costo_unitario: 0,
        variantes: [],
        stockTexto: '',
        stockDisponible: 0,
      },
    ]
  }
}

watch(
  () => props.visible,
  (val) => {
    if (val) {
      initForm()
      void cargarOpciones()
    }
  },
  { immediate: true },
)

async function guardar() {
  if (guardando.value) return
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

  // Sincronía variante/talla + precio default: evita vender talla errada o a precio fantasma
  for (let i = 0; i < items.value.length; i++) {
    const it = items.value[i]
    if (it.producto_id != null && !String(it.talla ?? '').trim()) {
      showToast('warn', 'Talla requerida', `La fila ${i + 1} ("${it.nombre_prenda || 'sin nombre'}") no tiene talla. Elegí variante o talla.`)
      return
    }
    if ((it.variantes?.length ?? 0) > 0 && it.variante_id == null) {
      showToast('warn', 'Variante requerida', `La fila ${i + 1} ("${it.nombre_prenda}") tiene ${it.variantes?.length} variantes: elegí una para no vender la talla errada.`)
      return
    }
    if (!(it.precio_unitario > 0)) {
      showToast('warn', 'Precio requerido', `La fila ${i + 1} ("${it.nombre_prenda || 'sin nombre'}") quedó en $0. Elegí el producto del catálogo para traer su precio.`)
      return
    }
  }

  let nombreClienteFinal = 'Cliente General'
  let cidFinal: number | null = null

  if (modoCliente.value === 'existente' && clienteId.value) {
    const c = (clientes.value as { id: number; nombre: string }[]).find((x) => x.id === clienteId.value)
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

  // Real API — valores resueltos a codigo maestro (ver canalToCodigo)
  // producto_id es requerido por el backend; se prohibe el fantasma.
  const sinProducto = items.value.findIndex((it) => it.producto_id == null)
  if (sinProducto !== -1) {
    showToast('warn', 'Producto requerido', `La fila ${sinProducto + 1} ("${items.value[sinProducto].nombre_prenda || 'sin nombre'}") no tiene producto del catálogo. Elegilo del dropdown para vender en modo REAL.`)
    return
  }
  guardando.value = true
  const apiPayload: VentaCreatePayload = {
    cliente_id: cidFinal,
    canal_venta: canalToCodigo(canal.value),
    metodo_pago: metodoToCodigo(metodoPago.value),
    descuento_porcentaje: Number(descuentoPct.value) || 0,
    codigo_descuento: codigoDescuento.value.trim() || null,
    motivo_descuento: motivoDescuento.value || null,
    observaciones: observaciones.value.trim() || null,
    es_regalo: false,
    detalles: items.value.map((it) => ({
      producto_id: it.producto_id as number,
      variante_id: it.variante_id ?? null,
      cantidad: it.cantidad,
      precio_unitario: it.precio_unitario,
    })),
  }
  try {
    if (isEditing.value && props.ventaEditar) {
      const actualizada = await updateVenta(props.ventaEditar.id, apiPayload)
      showToast('success', 'Venta Actualizada', `Venta ${(actualizada as unknown as Record<string, unknown>).codigo ?? props.ventaEditar.codigo} actualizada en BD.`)
      emit('venta-guardada', actualizada as unknown as VentaRead)
    } else {
      const creada = await ventasApi.create(apiPayload)
      showToast('success', 'Venta Registrada', `Venta ${(creada as unknown as Record<string, unknown>).codigo ?? 'creada'} guardada en BD.`)
      emit('venta-guardada', creada as unknown as VentaRead)
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
  } finally {
    guardando.value = false
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
      <!-- Row 1: Code, Date, Status (solo lectura: los define el backend) -->
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 bg-stone-900/60 p-3.5 rounded-xl border border-stone-800">
        <div>
          <label class="block text-[11px] font-bold text-amber-300 uppercase tracking-wider mb-1">
            Código Venta · auto
          </label>
          <InputText v-model="codigo" class="w-full text-xs font-mono" placeholder="Se genera al guardar (VEN-...)" disabled />
        </div>

        <div>
          <label class="block text-[11px] font-bold text-stone-400 uppercase tracking-wider mb-1">
            Fecha de Venta · auto
          </label>
          <InputText v-model="fecha" type="date" class="w-full text-xs font-mono" disabled title="La pone el servidor al guardar" />
        </div>

        <div>
          <label class="block text-[11px] font-bold text-stone-400 uppercase tracking-wider mb-1">
            Estado · auto
          </label>
          <Dropdown
            v-model="estado"
            :options="estadosOptions"
            option-label="label"
            option-value="value"
            class="w-full text-xs"
            disabled
            title="Toda venta nueva nace confirmada; anular es otra acción"
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
              <span class="text-stone-600">|</span>
              <button
                type="button"
                class="text-emerald-400 font-bold"
                title="Crear clienta sin salir de la venta"
                @click="showNuevoCliente = true"
              >
                + Nueva
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

      <!-- Alta de clienta inline: sin salir de la venta -->
      <NuevoClienteModal
        :visible="showNuevoCliente"
        @update:visible="(v) => (showNuevoCliente = v)"
        @cliente-guardado="onClienteGuardado"
      />

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
            <div class="grid grid-cols-1 sm:grid-cols-12 gap-2.5">
              <!-- Quick Select from Inventory (Optional) -->
              <div class="sm:col-span-6">
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

              <!-- Variante + Talla sincronizadas con stock visible -->
              <div class="sm:col-span-6">
                <label class="block text-[10px] text-stone-400 mb-0.5">Variante / Talla</label>
                <Dropdown
                  v-if="it.variantes?.length"
                  :model-value="it.variante_id"
                  :options="(it.variantes ?? []).map((v) => ({ label: v.nombre_variante, value: v.id }))"
                  option-label="label"
                  option-value="value"
                  placeholder="Elegir variante..."
                  class="w-full text-xs"
                  show-clear
                  :loading="it.variantesLoading"
                  @update:model-value="(val) => onVarianteChange(it, val)"
                />
                <Dropdown
                  :model-value="it.talla"
                  :options="tallasOptions"
                  editable
                  placeholder="Talla..."
                  class="w-full text-xs mt-1"
                  @update:model-value="(val) => onTallaChange(it, val)"
                />
                <div v-if="it.stockTexto" class="mt-1 text-[10px] font-mono" :class="(it.stockDisponible ?? 0) > 0 ? 'text-emerald-400' : 'text-rose-400'">
                  📦 {{ it.stockTexto }}
                </div>
              </div>
            </div>

            <div class="grid grid-cols-2 sm:grid-cols-12 gap-2.5 items-end mt-2.5">
              <!-- Cantidad -->
              <div class="sm:col-span-2">
                <label class="block text-[10px] text-stone-400 mb-0.5">Cant.</label>
                <InputNumber v-model="it.cantidad" mode="decimal" locale="es-CO" :min="1" :min-fraction-digits="0" :max-fraction-digits="0" class="w-full text-xs font-mono" />
              </div>

              <!-- Precio Unitario -->
              <div class="sm:col-span-4">
                <label class="block text-[10px] text-stone-400 mb-0.5">Precio Venta ($)</label>
                <InputNumber v-model="it.precio_unitario" mode="currency" currency="COP" locale="es-CO" :min="0" :min-fraction-digits="0" :max-fraction-digits="0" class="w-full text-xs font-mono" />
              </div>

              <!-- Actions -->
              <div class="sm:col-span-6 flex items-center justify-end gap-1">
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
              <div class="flex items-center gap-2" title="Lo calcula el backend al guardar (snapshot de costo)">
                <span>Costo Taller:</span>
                <strong class="text-stone-100">{{ formatCOP(it.costo_unitario) }}</strong>
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
                mode="decimal"
                locale="es-CO"
                :min="0"
                :max="100"
                :min-fraction-digits="0"
                :max-fraction-digits="2"
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

          <div class="grid grid-cols-2 gap-2">
            <div>
              <label class="block text-[11px] font-bold text-stone-400 uppercase tracking-wider mb-1">
                Código descuento
              </label>
              <InputText
                v-model="codigoDescuento"
                placeholder="Ej: ANIV2026"
                class="w-full text-xs font-mono"
              />
            </div>
            <div>
              <label class="block text-[11px] font-bold text-stone-400 uppercase tracking-wider mb-1">
                Motivo
              </label>
              <select
                v-model="motivoDescuento"
                class="w-full bg-stone-950 border border-stone-700 text-stone-200 text-xs rounded-lg px-2 py-2 font-mono focus:border-amber-400 focus:outline-none"
              >
                <option v-for="m in MOTIVOS_DESCUENTO" :key="m.value" :value="m.value">{{ m.label }}</option>
              </select>
            </div>
          </div>

          <div>
            <label class="block text-[11px] font-bold text-stone-400 uppercase tracking-wider mb-1">
              Observaciones & Notas
            </label>
            <Textarea
              v-model="observaciones"
              rows="2"
              placeholder="Ej: empaque regalo cumpleaños, entrega personalizada..."
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

          <!-- Formula 40/30/30 Breakdown (estimado cliente — solo Finanzas es oficial) -->
          <div class="pt-2 border-t border-stone-800/80 space-y-1 text-[11px]">
            <div class="text-[10px] text-amber-500 font-bold tracking-wider uppercase">
              Liquidación Socias (40% / 30% / 30% — estimado, no oficial)
            </div>
            <div class="flex justify-between text-stone-300">
              <span>🏛️ Fondo de Reinversión (40% estimado):</span>
              <span class="font-bold text-amber-400">{{ formatCOP(distribucion403030.reinversion40) }}</span>
            </div>
            <div class="flex justify-between text-stone-300">
              <span>🪡 Socia Confección (30% estimado):</span>
              <span class="font-bold text-stone-100">{{ formatCOP(distribucion403030.margara30) }}</span>
            </div>
            <div class="flex justify-between text-stone-300">
              <span>🎨 Socia Diseño (30% estimado):</span>
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
          :loading="guardando"
          @click="guardar"
        />
      </div>
    </template>
  </Dialog>
</template>
