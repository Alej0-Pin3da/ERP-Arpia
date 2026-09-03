<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'
import Dropdown from 'primevue/dropdown'
import InputNumber from 'primevue/inputnumber'
import Tag from 'primevue/tag'
import type { RecetaBOM } from '@/stores/atelier'
import { useMode } from '@/composables/useMode'
import { showToast } from '@/utils/toast'
import * as bomApi from '@/services/api/bom'
import * as insumosApi from '@/services/api/insumos'
import * as productosApi from '@/services/api/productos'
import * as maestrosApi from '@/services/api/maestros'

const props = defineProps<{
  visible: boolean
  receta: RecetaBOM | null
  startEditing?: boolean
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
  (e: 'editar', receta: RecetaBOM): void
  (e: 'guardado', receta: RecetaBOM): void
}>()

const { isMock } = useMode()
const activeTab = ref<'ficha' | 'matriz'>('ficha')
const isEditing = ref(false)
const saving = ref(false)
const editNombre = ref('')
const editCodigo = ref('')
const editCategoria = ref('')
const editLinea = ref('')
const editDescripcion = ref('')
const editTiempo = ref(60)
const editMano = ref(0)
const editCif = ref(0)
const editPrecio = ref(0)
const editRecomendaciones = ref('')
const margenMetaGlobal = ref(35)
const precioOverride = ref(false)
const snapshot = ref<Record<string, unknown> | null>(null)

const categoriasOptions = ['Corsetería','Blusas y Tops','Conjuntos y Sets','Vestidos','Pantalones','Accesorios','Alta Costura','General']
const lineasOptions = ['Corsetería', 'Prêt-à-Porter', 'Lencería Fina', 'Alta Costura', 'General']

// REAL BOM state
const bomReal = ref<bomApi.BomInsumoRead[]>([])
const insumosOptions = ref<{ label: string; value: number; costo: number; unidad: string; stock: number; stockMin: number }[]>([])
const costoReal = ref<bomApi.CostoProduccionRead | null>(null)
const loadingBom = ref(false)
const newInsumoId = ref<number | null>(null)
const newCantidad = ref<number>(1)
const newDesperdicio = ref<number>(0)
const editingBomId = ref<number | null>(null)
const editBomCantidad = ref<number>(1)
const editBomDesperdicio = ref<number>(0)

// REAL Combos (BOM_Productos) — sección mínima: lista + crear (2+ productos) + eliminar
const combosReal = ref<bomApi.BomProductoRead[]>([])
const productosOptions = ref<{ label: string; value: number }[]>([])
const loadingCombos = ref(false)
const newComboProductoId = ref<number | null>(null)
const newComboCantidad = ref<number>(1)

async function cargarProductosOptions() {
  if (isMock.value) return
  try {
    const r = await productosApi.listProductos({ limit: 100 })
    productosOptions.value = (r.items ?? []).map((p) => ({
      label: `${p.nombre} (${p.codigo ?? `PRD-${p.id}`})`,
      value: p.id,
    }))
  } catch { productosOptions.value = [] }
}

async function cargarCombos() {
  if (isMock.value || !props.receta || !recetaId.value) {
    combosReal.value = []
    return
  }
  loadingCombos.value = true
  try {
    combosReal.value = await bomApi.listBomProductos(recetaId.value).catch(() => [] as bomApi.BomProductoRead[])
  } finally {
    loadingCombos.value = false
  }
}

const comboNombre = (id: number) =>
  productosOptions.value.find((o) => o.value === id)?.label ?? `Producto #${id}`

async function agregarCombo() {
  if (!props.receta || !recetaId.value || !newComboProductoId.value) {
    showToast('warn', 'Seleccioná un producto', 'Elegí un producto del dropdown para armar el combo.')
    return
  }
  if (Number(newComboCantidad.value) <= 0) {
    showToast('warn', 'Cantidad inválida', 'La cantidad debe ser > 0.')
    return
  }
  try {
    await bomApi.createBomProducto(recetaId.value, {
      producto_incluido_id: newComboProductoId.value,
      cantidad: Number(newComboCantidad.value),
    })
    showToast('success', 'Combo actualizado', 'Producto agregado al combo.')
    newComboProductoId.value = null
    newComboCantidad.value = 1
    await cargarCombos()
  } catch (e: unknown) {
    const detail = (e as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail
    const msg = Array.isArray(detail) ? (detail as { msg?: string }[]).map((d) => d.msg ?? JSON.stringify(d)).join('; ') : (detail as string ?? (e as Error)?.message ?? 'Error al agregar')
    showToast('error', 'Error al agregar', String(msg))
  }
}

async function eliminarCombo(lineaId: number) {
  if (!recetaId.value) return
  try {
    await bomApi.deleteBomProducto(recetaId.value, lineaId)
    showToast('success', 'Producto quitado', 'Combo actualizado.')
    await cargarCombos()
  } catch (e: unknown) {
    const detail = (e as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail
    const msg = Array.isArray(detail) ? (detail as { msg?: string }[]).map((d) => d.msg ?? JSON.stringify(d)).join('; ') : (detail as string ?? (e as Error)?.message ?? 'Error al eliminar')
    showToast('error', 'Error al eliminar', String(msg))
  }
}

const recetaId = computed(() => (props.receta as unknown as { id: number })?.id)

async function cargarInsumosOptions() {
  if (isMock.value) return
  try {
    const r = await insumosApi.listInsumos({ limit: 100 })
        insumosOptions.value = r.items.map((i) => ({
          label: `${i.nombre} (${i.codigo ?? 'S/C'}) — $${Number(i.costo_promedio_actual ?? 0).toLocaleString('es-CO')}/${i.unidad_medida} — Stock ${Number(i.stock_actual).toLocaleString('es-CO', { maximumFractionDigits: 2 })} ${i.unidad_medida}${Number(i.stock_actual) <= Number(i.stock_minimo) ? ' ⚠️' : ''}`,
          value: i.id,
          costo: Number(i.costo_promedio_actual ?? 0),
          unidad: i.unidad_medida,
          stock: Number(i.stock_actual ?? 0),
          stockMin: Number(i.stock_minimo ?? 0),
        }))
  } catch { insumosOptions.value = [] }
}

async function cargarMargenMeta() {
  if (isMock.value) return
  try {
    const p = await maestrosApi.getParametros()
    margenMetaGlobal.value = Number(p.margen_meta_global_pct ?? 35)
  } catch { margenMetaGlobal.value = 35 }
}

async function cargarBom() {
  if (isMock.value || !props.receta || !recetaId.value) {
    bomReal.value = []
    costoReal.value = null
    return
  }
  loadingBom.value = true
  try {
    const [bom, costo] = await Promise.all([
      bomApi.listBomInsumos(recetaId.value).catch(() => [] as bomApi.BomInsumoRead[]),
      bomApi.getCostoProduccion(recetaId.value).catch(() => null),
    ])
    bomReal.value = bom
    costoReal.value = costo
  } finally {
    loadingBom.value = false
  }
}

async function enterEdit() {
  if (!props.receta) return
  let r = props.receta as unknown as Record<string, unknown>
  // In REAL, fetch fresh product to ensure precio_venta_sugerido and all cabecera fields are up-to-date (DB is source of truth)
  if (!isMock.value && recetaId.value) {
    try {
      const fresh = await productosApi.getProducto(recetaId.value)
      r = { ...r, ...fresh } as unknown as Record<string, unknown>
    } catch { /* fallback to prop */ }
  }
  editNombre.value = (r.nombre as string) ?? ''
  editCodigo.value = (r.codigo as string) ?? ''
  editCategoria.value = (r.categoria as string) ?? 'General'
  editLinea.value = (r.linea as string) ?? 'General'
  editDescripcion.value = (r.descripcion as string) ?? ''
  editTiempo.value = Number(r.tiempo_confeccion_min ?? 60)
  editMano.value = Number(r.mano_obra ?? 0)
  editCif.value = Number(r.cif_energia ?? 0)
  // precio_venta_sugerido is the DB column, precio_venta is the mapped alias — try both, and handle string Decimal
  const precioRaw = (r.precio_venta_sugerido ?? r.precio_venta ?? 0) as unknown
  const storedPrecio = Number(precioRaw ?? 0)
  if (storedPrecio > 0) {
    precioOverride.value = true
    editPrecio.value = storedPrecio
  } else {
    precioOverride.value = false
    editPrecio.value = precioSugeridoAuto.value > 0 ? precioSugeridoAuto.value : storedPrecio
  }
  editRecomendaciones.value = (r.recomendaciones_taller as string) ?? ''
  snapshot.value = {
    nombre: editNombre.value,
    codigo: editCodigo.value,
    categoria: editCategoria.value,
    linea: editLinea.value,
    descripcion: editDescripcion.value,
    tiempo: editTiempo.value,
    mano: editMano.value,
    cif: editCif.value,
    precio: editPrecio.value,
    recomendaciones: editRecomendaciones.value,
  }
  isEditing.value = true
}

function cancelEdit() {
  isEditing.value = false
  snapshot.value = null
  precioOverride.value = false
}

function onDialogVisibility(v: boolean) {
  if (!v && isDirty.value) {
    const ok = window.confirm('¿Descartar cambios sin guardar?')
    if (!ok) return
    cancelEdit()
  }
  if (!v) {
    isEditing.value = false
    snapshot.value = null
  }
  emit('update:visible', v)
}

function resetPrecio() {
  precioOverride.value = false
  editPrecio.value = Number(precioSugeridoAuto.value ?? 0)
}

async function guardarEdicion() {
  if (!props.receta || !recetaId.value) return
  if (!editNombre.value.trim()) {
    showToast('warn', 'Nombre requerido', 'Ingresá el nombre del modelo.')
    return
  }
  saving.value = true
  try {
    const costosFijos = Number(editMano.value ?? 0) + Number(editCif.value ?? 0) + Number(totalInsumosReal.value ?? 0)
    const payload = {
      nombre: editNombre.value.trim(),
      codigo: editCodigo.value.trim() || null,
      categoria: editCategoria.value || null,
      linea: editLinea.value || null,
      descripcion: editDescripcion.value.trim() || null,
      tiempo_confeccion_min: Number(editTiempo.value ?? 0),
      mano_obra: Number(editMano.value ?? 0),
      cif_energia: Number(editCif.value ?? 0),
      precio_venta_sugerido: Number(editPrecio.value ?? 0),
      costos_operativos_fijos: costosFijos,
      costo_insumos: Number(totalInsumosReal.value ?? 0),
      markup_pct: Number(markupCalculado.value ?? 0),
      recomendaciones_taller: editRecomendaciones.value.trim() || null,
    }
    const updated = await productosApi.updateProducto(recetaId.value, payload as unknown as Record<string, unknown>)
    showToast('success', 'Ficha actualizada', `${updated.nombre} guardado.`)
    isEditing.value = false
    snapshot.value = null
    precioOverride.value = false
    const mapped = { ...props.receta, ...payload, id: updated.id, codigo: (updated as unknown as Record<string,unknown>).codigo ?? editCodigo.value, precio_venta: editPrecio.value } as unknown as RecetaBOM
    emit('guardado', mapped)
    await cargarBom()
  } catch (e: unknown) {
    const detail = (e as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail
    const msg = Array.isArray(detail) ? (detail as { msg?: string }[]).map((d) => d.msg ?? JSON.stringify(d)).join('; ') : (detail as string ?? (e as Error)?.message ?? 'Error al guardar')
    showToast('error', 'Error al guardar', String(msg))
  } finally {
    saving.value = false
  }
}

watch(() => props.visible, (v) => {
  if (v) {
    void cargarInsumosOptions()
    void cargarMargenMeta()
    void cargarBom()
    void cargarHistorial()
    void cargarCombos()
    void cargarProductosOptions()
    if (props.startEditing) {
      setTimeout(() => enterEdit(), 50)
    } else {
      isEditing.value = false
    }
  } else {
    isEditing.value = false
  }
})
watch(() => props.receta?.id, () => {
  if (props.visible) { void cargarBom(); void cargarHistorial(); void cargarCombos() }
})

const insumosMap = computed(() => {
      const m = new Map<number, { nombre: string; costo: number; unidad: string; stock: number; stockMin: number }>()
      insumosOptions.value.forEach((o) => m.set(o.value, { nombre: (o as unknown as { label: string }).label, costo: (o as unknown as { costo: number }).costo, unidad: (o as unknown as { unidad: string }).unidad, stock: (o as unknown as { stock: number }).stock ?? 0, stockMin: (o as unknown as { stockMin: number }).stockMin ?? 0 }))
      return m
})

const selectedInsumo = computed(() => {
      if (!newInsumoId.value) return null
      return insumosMap.value.get(newInsumoId.value) ?? null
    })

    const selectedInsumoStockWarning = computed(() => {
      const s = selectedInsumo.value
      if (!s || !newCantidad.value) return null
      const need = Number(newCantidad.value) * (1 + Number(newDesperdicio.value ?? 0) / 100)
      if (s.stock <= s.stockMin) return `Stock crítico: ${s.stock} ${s.unidad} (mín ${s.stockMin})`
      if (need > s.stock) return `Necesitás ${need.toFixed(1)} ${s.unidad}, stock ${s.stock}`
      return null
    })

    const displayItems = computed(() => {
  if (isMock.value || !props.receta) return props.receta?.items ?? []
  return bomReal.value.map((b) => {
    const ins = insumosMap.value.get(b.insumo_id)
    const cantidad = Number(b.cantidad_requerida ?? 0)
    const costoUnit = ins?.costo ?? 0
    const merma = Number(b.porcentaje_desperdicio ?? 0)
    const subtotal = cantidad * costoUnit * (1 + merma / 100)
    return {
      id: b.id,
      insumo_id: b.insumo_id,
      nombre: ins?.nombre ?? `Insumo #${b.insumo_id}`,
      tipo: 'Directo' as const,
      consumo_unitario: cantidad,
      unidad: ins?.unidad ?? 'u',
      merma_pct: merma,
      costo_unitario: costoUnit,
      subtotal,
      bomId: b.id,
    }
  })
})

const totalInsumosReal = computed(() => {
  if (costoReal.value) {
    const sumBOM = displayItems.value.reduce((acc: number, it: unknown) => acc + Number((it as { subtotal: number }).subtotal ?? 0), 0)
    if (sumBOM > 0) return sumBOM
    return Number(costoReal.value.total ?? 0) - Number(props.receta?.cif_energia ?? 0) - Number(props.receta?.mano_obra ?? 0)
  }
  return displayItems.value.reduce((acc: number, it: unknown) => acc + Number((it as { subtotal: number }).subtotal ?? 0), 0)
})

const costoTotalCalculado = computed(() => {
  if (isMock.value || !props.receta) return props.receta?.costo_total_unitario ?? 0
  const insumos = Number(totalInsumosReal.value ?? 0) || Number(props.receta.costo_insumos ?? 0)
  const mano = Number(isEditing.value ? editMano.value : props.receta.mano_obra ?? 0)
  const cif = Number(isEditing.value ? editCif.value : props.receta.cif_energia ?? 0)
  const base = insumos > 0 ? insumos : Number(props.receta.costo_insumos ?? 0)
  return base + mano + cif
})

const markupCalculado = computed(() => {
  if (!props.receta) return 0
  const total = Number(costoTotalCalculado.value ?? 0)
  const precio = Number(isEditing.value ? editPrecio.value : props.receta.precio_venta ?? 0)
  if (!precio) return 0
  return Math.round(((precio - total) / precio) * 100)
})

// Precio venta sugerido = costo total / (1 - margen meta global). Live y con override manual.
const precioSugeridoAuto = computed(() => {
  const costo = Number(costoTotalCalculado.value ?? 0)
  if (costo <= 0) return 0
  const margen = Math.min(Math.max(Number(margenMetaGlobal.value ?? 35), 0), 99)
  return Math.round(costo / (1 - margen / 100))
})

const precioOverrideInfo = computed(() => {
  if (isMock.value || !props.receta) return false
  const stored = Number(props.receta.precio_venta ?? 0)
  const auto = Number(precioSugeridoAuto.value ?? 0)
  return stored > 0 && auto > 0 && Math.abs(stored - auto) > 1
})

const precioMostrado = computed(() => {
  if (isEditing.value) return Number(editPrecio.value ?? 0)
  if (isMock.value || !props.receta) return Number(props.receta?.precio_venta ?? 0)
  const stored = Number(props.receta?.precio_venta ?? 0)
  if (stored > 0) return stored
  return Number(precioSugeridoAuto.value ?? 0)
})

const markupMostrado = computed(() => {
  if (isMock.value || !props.receta) return Number(props.receta?.markup_pct ?? 0)
  if (isEditing.value) {
    return precioOverride.value ? Number(markupCalculado.value ?? 0) : Number(margenMetaGlobal.value ?? 35)
  }
  const stored = Number(props.receta?.precio_venta ?? 0)
  if (stored > 0) return Number(markupCalculado.value ?? 0)
  return Number(margenMetaGlobal.value ?? 35)
})

const isDirty = computed(() => {
  if (!isEditing.value || !snapshot.value) return false
  const s = snapshot.value as Record<string, unknown>
  return editNombre.value !== (s.nombre as string) ||
    editCodigo.value !== (s.codigo as string) ||
    editCategoria.value !== (s.categoria as string) ||
    editLinea.value !== (s.linea as string) ||
    editDescripcion.value !== (s.descripcion as string) ||
    Number(editTiempo.value) !== Number(s.tiempo ?? 60) ||
    Number(editMano.value) !== Number(s.mano ?? 0) ||
    Number(editCif.value) !== Number(s.cif ?? 0) ||
    Number(editPrecio.value) !== Number(s.precio ?? 0) ||
    editRecomendaciones.value !== (s.recomendaciones as string)
})

const semaforo = computed(() => {
  if (isMock.value || !props.receta) return null
  const real = Number(markupCalculado.value ?? 0)
  const meta = Number(margenMetaGlobal.value ?? 35)
  const precio = Number(precioMostrado.value ?? 0)
  const sugerido = Number(precioSugeridoAuto.value ?? 0)
  const diffPct = sugerido > 0 ? Math.round(((precio - sugerido) / sugerido) * 100) : 0
  const diffAbs = Math.round(precio - sugerido)
  let color: 'emerald' | 'amber' | 'red' | 'sky' = 'emerald'
  let label = 'En meta'
  if (real < 0) { color = 'red'; label = 'Pérdida' }
  else if (real < meta - 10) { color = 'amber'; label = 'Por debajo' }
  else if (real > meta + 20) { color = 'sky'; label = 'Alto' }
  else { color = 'emerald'; label = 'En meta' }
  return { real, meta, diffPct, diffAbs, color, label }
})

    // Historial de precio
    const historial = ref<any[]>([])
    const loadingHistorial = ref(false)
    async function cargarHistorial() {
      if (isMock.value || !recetaId.value) { historial.value = []; return }
      loadingHistorial.value = true
      try {
        const { client } = await import('@/api/client')
        const { data } = await client.get('/audit-fiscal/precio-versions', { params: { producto_id: recetaId.value } })
        historial.value = Array.isArray(data) ? data : []
      } catch { historial.value = [] }
      finally { loadingHistorial.value = false }
    }

watch(precioSugeridoAuto, (v) => {
  if (isEditing.value && !precioOverride.value && v > 0) {
    editPrecio.value = v
  }
})

async function agregarInsumo() {
  if (!props.receta || !recetaId.value || !newInsumoId.value) {
    showToast('warn', 'Seleccioná un insumo', 'Elegí un insumo del dropdown.')
    return
  }
  if (Number(newCantidad.value) <= 0) {
    showToast('warn', 'Cantidad inválida', 'La cantidad debe ser > 0.')
    return
  }
      if (selectedInsumo.value && selectedInsumoStockWarning.value) {
        showToast('warn', 'Stock bajo', selectedInsumoStockWarning.value!)
      }
  try {
    await bomApi.createBomInsumo(recetaId.value, {
      insumo_id: newInsumoId.value,
      cantidad_requerida: Number(newCantidad.value),
      porcentaje_desperdicio: Number(newDesperdicio.value ?? 0),
    })
    showToast('success', 'Insumo agregado', 'BOM actualizado.')
    newInsumoId.value = null
    newCantidad.value = 1
    newDesperdicio.value = 0
    await cargarBom()
  } catch (e: unknown) {
    const detail = (e as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail
    const msg = Array.isArray(detail) ? (detail as { msg?: string }[]).map((d) => d.msg ?? JSON.stringify(d)).join('; ') : (detail as string ?? (e as Error)?.message ?? 'Error al agregar')
    showToast('error', 'Error al agregar', String(msg))
  }
}

async function eliminarInsumo(bomId: number) {
  if (!recetaId.value) return
  try {
    await bomApi.deleteBomInsumo(recetaId.value, bomId)
    showToast('success', 'Insumo eliminado', 'BOM actualizado.')
    await cargarBom()
  } catch (e: unknown) {
    const detail = (e as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail
    const msg = Array.isArray(detail) ? (detail as { msg?: string }[]).map((d) => d.msg ?? JSON.stringify(d)).join('; ') : (detail as string ?? (e as Error)?.message ?? 'Error al eliminar')
    showToast('error', 'Error al eliminar', String(msg))
  }
}

function startEditBom(bom: bomApi.BomInsumoRead) {
  editingBomId.value = bom.id
  editBomCantidad.value = Number(bom.cantidad_requerida ?? 1)
  editBomDesperdicio.value = Number(bom.porcentaje_desperdicio ?? 0)
}

function cancelEditBom() {
  editingBomId.value = null
}

async function guardarEditBom(bom: bomApi.BomInsumoRead) {
  if (!recetaId.value || editingBomId.value !== bom.id) return
  if (Number(editBomCantidad.value) <= 0) {
    showToast('warn', 'Cantidad inválida', 'Debe ser > 0.')
    return
  }
  try {
    await bomApi.updateBomInsumo(recetaId.value, bom.id, {
      cantidad_requerida: Number(editBomCantidad.value),
      porcentaje_desperdicio: Number(editBomDesperdicio.value ?? 0),
    })
    showToast('success', 'BOM actualizado', 'Cantidad y desperdicio guardados.')
    editingBomId.value = null
    await cargarBom()
  } catch (e: unknown) {
    const detail = (e as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail
    const msg = Array.isArray(detail) ? (detail as { msg?: string }[]).map((d) => d.msg ?? JSON.stringify(d)).join('; ') : (detail as string ?? (e as Error)?.message ?? 'Error al guardar')
    showToast('error', 'Error al guardar', String(msg))
  }
}

function formatCOP(val: number) {
  return `$${Math.round(val).toLocaleString('es-CO')}`
}

function imprimir() {
  window.print()
}

function exportarMatriz() {
  showToast('info', 'Matriz Google Sheet', 'Exportando escandallo y matriz de corte a formato de hoja de cálculo.')
}
</script>

<template>
  <Dialog
    :visible="visible"
    modal
    :style="{ width: '92vw', maxWidth: '980px' }"
    :header="receta ? `${isEditing ? editNombre || receta.nombre : receta.nombre} (${isEditing ? editCodigo || receta.codigo : receta.codigo})` : 'Ficha Técnica'"
    @update:visible="onDialogVisibility"
  >
    <div v-if="receta" class="space-y-5 pt-1">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-stone-800 pb-3">
        <div class="flex items-center gap-2">
          <Tag severity="warning" class="font-bold tracking-wider text-xs uppercase">{{ isEditing ? editLinea || receta.linea : receta.linea }}</Tag>
              <span v-if="isDirty" class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30 animate-pulse">• sin guardar</span>
              <span v-if="!isMock && semaforo" class="px-2 py-0.5 rounded-full text-[10px] font-bold border" :class="semaforo.color === 'emerald' ? 'bg-emerald-950/40 text-emerald-300 border-emerald-500/30' : semaforo.color === 'amber' ? 'bg-amber-950/40 text-amber-300 border-amber-500/30' : semaforo.color === 'red' ? 'bg-red-950/40 text-red-300 border-red-500/30' : 'bg-sky-950/40 text-sky-300 border-sky-500/30'">{{ semaforo.label }} {{ semaforo.diffPct > 0 ? '+' : '' }}{{ semaforo.diffPct }}%</span>
          <span class="text-xs text-stone-400 font-medium">Ficha Técnica Oficial de Taller • Arpía Atelier</span>
          <span v-if="!isMock" class="px-2 py-0.5 rounded-full text-[10px] font-bold border" :class="loadingBom ? 'bg-amber-950/40 text-amber-300 border-amber-500/30' : 'bg-emerald-950/40 text-emerald-300 border-emerald-500/30'">{{ loadingBom ? 'Cargando BOM...' : `BOM: ${bomReal.length} renglones` }}</span>
        </div>
        <div class="flex items-center gap-2">
          <div class="inline-flex bg-stone-900 rounded-lg p-0.5 border border-stone-800">
            <button type="button" class="px-3 py-1.5 rounded-md text-xs font-semibold transition" :class="activeTab === 'ficha' ? 'bg-amber-500 text-stone-950 shadow' : 'text-stone-400 hover:text-stone-200'" @click="activeTab = 'ficha'">📋 Ficha Técnica</button>
            <button type="button" class="px-3 py-1.5 rounded-md text-xs font-semibold transition" :class="activeTab === 'matriz' ? 'bg-amber-500 text-stone-950 shadow' : 'text-stone-400 hover:text-stone-200'" @click="activeTab = 'matriz'">📊 Matriz Google Sheet</button>

          </div>
          <Button v-if="!isEditing" label="Editar" icon="pi pi-pencil" severity="warning" size="small" outlined @click="enterEdit()" />
          <Button v-if="isEditing" label="Guardar" icon="pi pi-check" severity="success" size="small" :loading="saving" @click="guardarEdicion()" />
          <Button v-if="isEditing" label="Cancelar" icon="pi pi-times" severity="secondary" size="small" outlined @click="cancelEdit()" />
          <Button label="Imprimir" icon="pi pi-print" severity="secondary" size="small" outlined @click="imprimir" />
        </div>
      </div>

      <div v-if="activeTab === 'ficha'" class="space-y-5 animate-fade-in">
        <div v-if="!isEditing" class="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-stone-900/90 border border-stone-800 rounded-xl p-3.5 text-center">
          <div><div class="text-[11px] uppercase font-bold text-stone-400">Código Referencia</div><div class="text-sm font-mono font-bold text-amber-400 mt-0.5">{{ receta.codigo }}</div></div>
          <div><div class="text-[11px] uppercase font-bold text-stone-400">Línea / Categoría</div><div class="text-sm font-semibold text-stone-200 mt-0.5">{{ receta.categoria }}</div></div>
          <div><div class="text-[11px] uppercase font-bold text-stone-400">Tiempo Estimado</div><div class="text-sm font-semibold text-stone-200 mt-0.5">{{ receta.tiempo_confeccion_min }} min</div></div>
          <div><div class="text-[11px] uppercase font-bold text-stone-400">Costo Unitario</div><div class="text-sm font-bold text-emerald-400 mt-0.5">{{ formatCOP(costoTotalCalculado) }}</div></div>
        </div>
        <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 bg-stone-900/90 border border-amber-500/30 rounded-xl p-3.5">
          <div><label class="block text-[11px] uppercase font-bold text-stone-400 mb-1">Código</label><input v-model="editCodigo" class="w-full bg-stone-950 border border-stone-700 rounded px-2 py-1.5 text-sm font-mono text-amber-400" placeholder="PRD-..." /></div>
          <div><label class="block text-[11px] uppercase font-bold text-stone-400 mb-1">Categoría</label><Dropdown v-model="editCategoria" :options="categoriasOptions" class="w-full" /></div>
          <div><label class="block text-[11px] uppercase font-bold text-stone-400 mb-1">Línea</label><Dropdown v-model="editLinea" :options="lineasOptions" class="w-full" /></div>
          <div><label class="block text-[11px] uppercase font-bold text-stone-400 mb-1">Tiempo (min)</label><input v-model.number="editTiempo" type="number" class="w-full bg-stone-950 border border-stone-700 rounded px-2 py-1.5 text-sm font-mono text-stone-200" /></div>
        </div>

        <div v-if="!isEditing" class="bg-stone-900/40 border border-stone-800/80 rounded-xl p-3 text-xs text-stone-300 leading-relaxed">
          <strong class="text-amber-300">Descripción del Modelo:</strong> {{ receta.descripcion }}
        </div>
        <div v-else class="bg-stone-900/60 border border-amber-500/30 rounded-xl p-3">
          <label class="block text-[11px] uppercase font-bold text-stone-400 mb-1.5">Nombre del Modelo</label>
          <input v-model="editNombre" class="w-full bg-stone-950 border border-stone-700 rounded px-2 py-1.5 text-sm font-bold text-stone-100 mb-2" />
          <label class="block text-[11px] uppercase font-bold text-stone-400 mb-1.5">Descripción del Modelo</label>
          <textarea v-model="editDescripcion" rows="2" class="w-full bg-stone-950 border border-stone-700 rounded px-2 py-1.5 text-xs text-stone-300" placeholder="Detalles de patronaje..." />
        </div>

        <div v-if="!isMock" class="border border-amber-500/30 bg-amber-950/10 rounded-xl p-3 space-y-3">
          <h4 class="text-xs font-bold uppercase tracking-wider text-amber-400 m-0 flex items-center gap-2"><i class="pi pi-plus" /> Agregar insumo al BOM</h4>
          <div class="grid grid-cols-1 sm:grid-cols-4 gap-3">
            <div class="sm:col-span-2">
              <label class="block text-[11px] font-semibold uppercase text-stone-400 mb-1">Insumo</label>
              <Dropdown v-model="newInsumoId" :options="insumosOptions" optionLabel="label" optionValue="value" placeholder="Seleccionar insumo" class="w-full" filter />
                  <div v-if="selectedInsumo" class="mt-1 flex items-center gap-2 text-[11px]">
                    <span class="font-mono text-stone-300">${{ selectedInsumo.costo.toLocaleString('es-CO') }}/{{ selectedInsumo.unidad }}</span>
                    <span class="px-1.5 py-0.5 rounded text-[10px] font-bold border" :class="selectedInsumo.stock <= selectedInsumo.stockMin ? 'bg-red-950/40 text-red-300 border-red-500/30' : 'bg-emerald-950/40 text-emerald-300 border-emerald-500/30'">Stock {{ selectedInsumo.stock }} {{ selectedInsumo.unidad }}</span>
                    <span v-if="selectedInsumoStockWarning" class="text-amber-400">{{ selectedInsumoStockWarning }}</span>
                  </div>
            </div>
            <div>
              <label class="block text-[11px] font-semibold uppercase text-stone-400 mb-1">Cantidad</label>
              <InputNumber v-model="newCantidad" :min="0.01" :step="0.1" class="w-full" />
            </div>
            <div>
              <label class="block text-[11px] font-semibold uppercase text-stone-400 mb-1">Desperdicio %</label>
              <InputNumber v-model="newDesperdicio" :min="0" :max="100" class="w-full" />
            </div>
          </div>
          <div class="flex justify-end">
            <Button label="Agregar al BOM" icon="pi pi-plus" size="small" severity="warning" @click="agregarInsumo" />
          </div>
          <p v-if="costoReal" class="text-[11px] text-stone-400">Costo total (backend): <span class="font-mono text-emerald-400 font-bold">{{ formatCOP(Number(costoReal.total ?? 0)) }}</span> — {{ costoReal.lineas.length }} líneas desglosadas</p>
        </div>

        <div class="border border-stone-800 rounded-xl overflow-hidden bg-stone-900/50">
          <div class="p-3 bg-stone-900/80 border-b border-stone-800 flex items-center justify-between">
            <h4 class="text-xs font-bold uppercase tracking-wider text-amber-400 m-0">Lista de Insumos & Escandallo (BOM)</h4>
            <span class="text-xs text-stone-400">{{ displayItems.length }} materiales directos e indirectos</span>
          </div>
          <div v-if="!displayItems.length" class="p-8 text-center text-sm text-stone-400">
            <i class="pi pi-inbox text-2xl mb-2 block" />
            <span v-if="isMock">Sin insumos en esta ficha (mock).</span>
            <span v-else>Sin renglones BOM. Agregá insumos arriba para calcular el costo.</span>
          </div>
          <div v-else class="overflow-x-auto">
            <table class="w-full text-left text-xs border-collapse">
              <thead><tr class="border-b border-stone-800 text-stone-400 bg-stone-950/40">
                <th class="py-2.5 px-3 font-semibold">Insumo / Material</th><th class="py-2.5 px-3 font-semibold">Tipo</th><th class="py-2.5 px-3 font-semibold text-right">Consumo Unit.</th><th class="py-2.5 px-3 font-semibold text-right">Merma %</th><th class="py-2.5 px-3 font-semibold text-right">Costo Unit.</th><th class="py-2.5 px-3 font-semibold text-right">Subtotal</th><th v-if="!isMock" class="py-2.5 px-3"></th>
              </tr></thead>
              <tbody class="divide-y divide-stone-800/50 text-stone-200">
                <tr v-for="it in displayItems" :key="(it as any).id" class="hover:bg-stone-800/30" :class="editingBomId === (it as any).bomId ? 'bg-amber-950/20' : ''">
                  <td class="py-2.5 px-3 font-medium text-stone-100">{{ (it as any).nombre }}</td>
                  <td class="py-2.5 px-3"><span class="px-2 py-0.5 rounded text-[10px] font-bold" :class="(it as any).tipo === 'Directo' ? 'bg-amber-950/60 text-amber-300 border border-amber-500/30' : 'bg-stone-800 text-stone-400'">{{ (it as any).tipo }}</span></td>
                  <td class="py-2.5 px-3 text-right font-mono">
                    <span v-if="editingBomId !== (it as any).bomId">{{ (it as any).consumo_unitario }} {{ (it as any).unidad }}</span>
                    <input v-else v-model.number="editBomCantidad" type="number" step="0.1" min="0.01" class="w-20 bg-stone-950 border border-amber-500/30 rounded px-1 py-0.5 text-right font-mono text-amber-300" />
                  </td>
                  <td class="py-2.5 px-3 text-right font-mono">
                    <span v-if="editingBomId !== (it as any).bomId" class="text-stone-400">{{ (it as any).merma_pct }}%</span>
                    <span v-else class="flex items-center justify-end gap-1"><input v-model.number="editBomDesperdicio" type="number" min="0" max="100" class="w-16 bg-stone-950 border border-amber-500/30 rounded px-1 py-0.5 text-right font-mono text-amber-300" />%</span>
                  </td>
                  <td class="py-2.5 px-3 text-right font-mono">{{ formatCOP((it as any).costo_unitario) }}</td>
                  <td class="py-2.5 px-3 text-right font-mono font-bold text-amber-300">{{ formatCOP((it as any).subtotal) }}</td>
                  <td v-if="!isMock" class="py-2.5 px-3 text-right whitespace-nowrap">
                    <template v-if="editingBomId !== (it as any).bomId">
                      <button type="button" class="text-stone-500 hover:text-amber-400 p-1" title="Editar cantidad/desperdicio" @click="startEditBom(bomReal.find(b => b.id === (it as any).bomId)!)"><i class="pi pi-pencil text-xs" /></button>
                      <button type="button" class="text-stone-500 hover:text-red-400 p-1" title="Eliminar renglón" @click="eliminarInsumo((it as any).bomId ?? (it as any).id)"><i class="pi pi-trash text-xs" /></button>
                    </template>
                    <template v-else>
                      <button type="button" class="text-emerald-400 hover:text-emerald-300 p-1" title="Guardar" @click="guardarEditBom(bomReal.find(b => b.id === (it as any).bomId)!)"><i class="pi pi-check text-xs" /></button>
                      <button type="button" class="text-stone-500 hover:text-stone-300 p-1" title="Cancelar" @click="cancelEditBom()"><i class="pi pi-times text-xs" /></button>
                    </template>
                  </td>
                </tr>
              </tbody>
              <tfoot><tr class="bg-stone-950/70 border-t border-stone-800 font-bold">
                <td colspan="5" class="py-2.5 px-3 text-stone-300 text-right uppercase text-[11px]">Total Insumos y Materiales:</td>
                <td class="py-2.5 px-3 text-right font-mono text-amber-400">{{ formatCOP(isMock ? receta.costo_insumos : totalInsumosReal) }}</td>
                <td v-if="!isMock"></td>
              </tr></tfoot>
            </table>
          </div>
        </div>

        <div v-if="!isMock" class="border border-stone-800 rounded-xl overflow-hidden bg-stone-900/50">
          <div class="p-3 bg-stone-900/80 border-b border-stone-800 flex items-center justify-between">
            <h4 class="text-xs font-bold uppercase tracking-wider text-amber-400 m-0">Combos (BOM productos)</h4>
            <span class="text-xs text-stone-400">{{ loadingCombos ? 'Cargando...' : `${combosReal.length} productos` }}</span>
          </div>
          <div v-if="!combosReal.length" class="p-6 text-center text-xs text-stone-500">
            Sin productos en el combo. Agregá 2 o más productos con sus cantidades abajo.
          </div>
          <div v-else class="divide-y divide-stone-800/50 text-xs">
            <div v-for="c in combosReal" :key="c.id" class="flex items-center justify-between px-3 py-2">
              <span class="text-stone-200">{{ comboNombre(c.producto_incluido_id) }}</span>
              <span class="flex items-center gap-2">
                <span class="font-mono text-amber-300">x {{ c.cantidad }}</span>
                <button type="button" class="text-stone-500 hover:text-red-400 p-1" title="Quitar del combo" @click="eliminarCombo(c.id)"><i class="pi pi-trash text-xs" /></button>
              </span>
            </div>
          </div>
          <div class="p-3 border-t border-stone-800 grid grid-cols-1 sm:grid-cols-[1fr_120px_auto] gap-2 items-end">
            <div>
              <label class="block text-[11px] font-semibold uppercase text-stone-400 mb-1">Producto</label>
              <Dropdown v-model="newComboProductoId" :options="productosOptions" optionLabel="label" optionValue="value" placeholder="Seleccionar producto" class="w-full" filter />
            </div>
            <div>
              <label class="block text-[11px] font-semibold uppercase text-stone-400 mb-1">Cantidad</label>
              <InputNumber v-model="newComboCantidad" :min="1" :step="1" class="w-full" />
            </div>
            <Button label="Agregar" icon="pi pi-plus" size="small" severity="warning" @click="agregarCombo" />
          </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="border border-stone-800 rounded-xl p-4 bg-stone-900/50 space-y-3">
            <h4 class="text-xs font-bold uppercase tracking-wider text-amber-400 m-0 flex items-center gap-2"><i class="pi pi-cog" /> Fases de Producción en Taller</h4>
            <div class="space-y-2.5">
              <div v-for="(fase, idx) in receta.fases" :key="idx" class="bg-stone-950/50 border border-stone-800/80 rounded-lg p-2.5 text-xs flex items-start justify-between gap-2">
                <div><div class="font-bold text-stone-200">{{ (fase as any).nombre }}</div><div class="text-stone-400 text-[11px] mt-0.5">{{ (fase as any).descripcion }}</div></div>
                <div class="px-2 py-0.5 rounded bg-amber-950/50 text-amber-300 border border-amber-500/20 font-mono text-[11px] font-bold whitespace-nowrap">{{ (fase as any).minutos }} min</div>
              </div>
              <div v-if="!receta.fases?.length" class="text-xs text-stone-500 text-center py-2">Sin fases cargadas</div>
            </div>
          </div>
          <div class="border border-stone-800 rounded-xl p-4 bg-stone-900/50 space-y-3">
            <h4 class="text-xs font-bold uppercase tracking-wider text-amber-400 m-0 flex items-center gap-2"><i class="pi pi-dollar" /> Costeo & Fijación de Precio Sugerido</h4>
            <div class="space-y-2 text-xs divide-y divide-stone-800/60">
              <div class="flex justify-between py-1 text-stone-300"><span>(+) Costo Insumos Directos / Indirectos</span><span class="font-mono font-semibold">{{ formatCOP(isMock ? receta.costo_insumos : totalInsumosReal) }}</span></div>
              <div class="flex justify-between py-1 text-stone-300"><span>(+) Mano de Obra ({{ isEditing ? editTiempo : receta.tiempo_confeccion_min }} min)</span><span v-if="!isEditing" class="font-mono font-semibold">{{ formatCOP(receta.mano_obra) }}</span><input v-else v-model.number="editMano" type="number" class="w-24 bg-stone-950 border border-stone-700 rounded px-2 py-1 text-right font-mono text-stone-200" /></div>
              <div class="flex justify-between py-1 text-stone-300"><span>(+) Costos CIF / Energía Eléctrica</span><span v-if="!isEditing" class="font-mono font-semibold">{{ formatCOP(receta.cif_energia) }}</span><input v-else v-model.number="editCif" type="number" class="w-24 bg-stone-950 border border-stone-700 rounded px-2 py-1 text-right font-mono text-stone-200" /></div>
              <div class="flex justify-between py-1.5 font-bold text-stone-100 bg-stone-950/40 px-2 rounded"><span>(=) Costo Unitario de Confección</span><span class="font-mono text-emerald-400">{{ formatCOP(costoTotalCalculado) }}</span></div>
              <div class="flex justify-between py-2 items-center gap-2"><div><div class="font-bold text-amber-400 text-sm">PRECIO VENTA</div><div class="text-[10px] text-stone-400">Margen real: {{ markupCalculado }}% <span class="text-stone-500">| Meta: {{ isMock ? receta.markup_pct : margenMetaGlobal }}%</span></div><div v-if="!isMock && !isEditing && precioSugeridoAuto > 0" class="text-[10px] text-amber-400/70">Sugerido ({{ margenMetaGlobal }}%): {{ formatCOP(precioSugeridoAuto) }}</div><div v-else-if="!isMock && isEditing" class="text-[10px] text-amber-400/70">Sugerido: {{ formatCOP(precioSugeridoAuto) }} <span v-if="precioOverride" class="text-stone-500">| editado</span></div></div><div v-if="!isEditing" class="font-mono text-lg font-extrabold text-amber-300">{{ formatCOP(precioMostrado) }}</div><div v-else class="flex items-center gap-1"><input v-model.number="editPrecio" type="number" @input="precioOverride = true" class="w-32 bg-stone-950 border rounded px-2 py-1.5 text-right font-mono text-lg font-extrabold" :class="precioOverride ? 'border-stone-600 text-stone-100' : 'border-amber-500/30 text-amber-300'" /><button v-if="precioOverride && precioSugeridoAuto > 0" type="button" class="text-[10px] px-2 py-1 rounded bg-stone-800 text-stone-400 hover:text-amber-300 whitespace-nowrap" title="Volver al precio sugerido" @click="resetPrecio()">&#8634; auto</button></div></div>
            </div>
          </div>
        </div>

        <div v-if="!isEditing" class="bg-amber-950/20 border border-amber-500/30 rounded-xl p-3 text-xs text-amber-200/90 flex items-start gap-2.5">
          <i class="pi pi-info-circle text-amber-400 text-base flex-shrink-0 mt-0.5" />
          <div><strong class="text-amber-300 block mb-0.5">Recomendaciones del Taller para Confección:</strong> {{ receta.recomendaciones_taller }}</div>
        </div>
        <div v-else class="bg-amber-950/20 border border-amber-500/30 rounded-xl p-3">
          <label class="block text-[11px] uppercase font-bold text-amber-300 mb-1.5">Recomendaciones del Taller</label>
          <textarea v-model="editRecomendaciones" rows="2" class="w-full bg-stone-950 border border-stone-700 rounded px-2 py-1.5 text-xs text-amber-200/90" />
        </div>
      </div>

      <div v-else class="space-y-4 animate-fade-in">
        <div class="bg-stone-900/80 border border-stone-800 rounded-xl p-3 flex items-center justify-between text-xs">
          <div class="text-stone-300"><strong class="text-amber-400">Matriz de Dimensiones & Consumo Textil</strong> • Escandallo tipo planilla de cálculo</div>
          <Button label="Exportar Planilla" icon="pi pi-file-excel" size="small" severity="warning" outlined @click="exportarMatriz" />
        </div>
        <div class="border border-stone-800 rounded-xl overflow-hidden bg-stone-950/80">
          <table class="w-full text-left text-xs border-collapse font-mono">
            <thead><tr class="bg-stone-900 border-b border-stone-800 text-stone-400 font-sans"><th class="py-2.5 px-3">Componente</th><th class="py-2.5 px-3 text-right">Ancho (m)</th><th class="py-2.5 px-3 text-right">Alto (m)</th><th class="py-2.5 px-3 text-right">Cant. Cms</th><th class="py-2.5 px-3 text-right">Valor Metro</th><th class="py-2.5 px-3 text-right text-amber-400">Valor Total</th></tr></thead>
            <tbody class="divide-y divide-stone-800/50 text-stone-200">
              <tr v-for="it in displayItems" :key="(it as any).id" class="hover:bg-stone-900/40 font-mono">
                <td class="py-2 px-3 font-sans text-stone-100">{{ (it as any).nombre }}</td>
                <td class="py-2 px-3 text-right text-stone-400">{{ ((it as any).ancho || 0.24).toFixed(2) }}</td>
                <td class="py-2 px-3 text-right text-stone-400">{{ ((it as any).alto || 0.85).toFixed(2) }}</td>
                <td class="py-2 px-3 text-right text-stone-300">{{ Math.round(((it as any).consumo_unitario || 1) * 100) }} cm</td>
                <td class="py-2 px-3 text-right">{{ formatCOP((it as any).costo_unitario) }}</td>
                <td class="py-2 px-3 text-right font-bold text-amber-300">{{ formatCOP((it as any).subtotal) }}</td>
              </tr>
              <tr v-if="!displayItems.length"><td colspan="6" class="py-6 text-center text-stone-500">Sin insumos para matriz</td></tr>
            </tbody>
          </table>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div class="bg-stone-900/90 border border-stone-800 rounded-xl p-3 text-center"><div class="text-[11px] uppercase font-bold text-stone-400">Costo Total Confección</div><div class="text-base font-mono font-bold text-stone-200 mt-1">{{ formatCOP(costoTotalCalculado) }}</div></div>
          <div class="bg-stone-900/90 border border-amber-500/30 rounded-xl p-3 text-center"><div class="text-[11px] uppercase font-bold text-amber-400">Venta Sugerida Atelier</div><div class="text-base font-mono font-bold text-amber-300 mt-1">{{ formatCOP(precioMostrado) }}</div></div>
          <div class="bg-stone-900/90 border border-emerald-500/30 rounded-xl p-3 text-center"><div class="text-[11px] uppercase font-bold text-emerald-400">Ganancia Neta Estimada</div><div class="text-base font-mono font-bold text-emerald-300 mt-1">{{ formatCOP(precioMostrado - costoTotalCalculado) }} ({{ markupMostrado }}%)</div></div>
        </div>
      </div>



          
    </div>
  </Dialog>
</template>
