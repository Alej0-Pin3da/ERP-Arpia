<script setup lang="ts">
/* eslint-disable @typescript-eslint/no-explicit-any */
// EditarInsumoModal — edits an existing insumo via PATCH /insumos/{id}.
// Field set mirrors NuevoInsumoModal (nombre, codigo, categoria_id, unidad,
// tipo, ubicacion, stock_actual, stock_minimo, costo_promedio_actual) so both
// modals stay consistent. Matches backend InsumoUpdate schema (all optional).
import { ref, computed, onMounted, watch } from 'vue'
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Dropdown from 'primevue/dropdown'
import Textarea from 'primevue/textarea'
import { useInsumos } from '@/composables/useInsumos'
import type { InsumoUpdatePayload } from '@/services/api/insumos'
import { client } from '@/api/client'
import { showToast } from '@/utils/toast'

/** Minimal insumo shape this modal reads (REAL display object from the caller). */
export interface InsumoEditarRef {
  id: number
  codigo?: string
  nombre: string
  descripcion?: string
  tipo?: 'Directo' | 'Indirecto'
  categoria?: string
  ubicacion?: string
  stock_actual: number
  stock_minimo: number
  unidad_medida: string
  costo_unitario?: number
}

const props = defineProps<{
  visible: boolean
  insumo: InsumoEditarRef | null
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
  (e: 'insumo-actualizado'): void
}>()

const insumosApi = useInsumos()

const codigo = ref('')
const nombre = ref('')
const descripcion = ref('')
const tipo = ref<'Directo' | 'Indirecto'>('Directo')
const categoria = ref('')
const categoriaId = ref<number | null>(null)
const categorias = ref<{ id: number; nombre: string }[]>([])
const ubicacion = ref('')
const stockActual = ref(0)
const stockMinimo = ref(0)
const unidadMedida = ref('m')
const costoUnitario = ref(0)
const guardando = ref(false)

async function cargarCategorias() {
  try {
    const { data } = await client.get<{ items: { id: number; nombre: string }[] }>('/categorias-insumos', { params: { limit: 100 } })
    categorias.value = data.items ?? []
  } catch { categorias.value = [] }
}
onMounted(() => { void cargarCategorias() })

const tiposOptions = [
  { label: 'Directo (Telas, Encajes, Forros, Copas)', value: 'Directo' },
  { label: 'Indirecto (Empaques, Hilos, Etiquetas, Cintas)', value: 'Indirecto' },
]

const categoriasOptions = computed(() => categorias.value.map((c) => ({ label: c.nombre, value: c.id })))

const unidadesOptions = [
  { label: 'Metros (m)', value: 'm' },
  { label: 'Unidades (un)', value: 'un' },
  { label: 'Centímetros (cm)', value: 'cm' },
  { label: 'Rollos (rll)', value: 'rll' },
]

function prefillFromRow(row: InsumoEditarRef) {
  codigo.value = row.codigo ?? ''
  nombre.value = row.nombre ?? ''
  descripcion.value = (row as any).descripcion ?? ''
  tipo.value = row.tipo ?? 'Directo'
  categoria.value = row.categoria ?? ''
  categoriaId.value = null
  ubicacion.value = row.ubicacion ?? ''
  stockActual.value = Number(row.stock_actual) || 0
  stockMinimo.value = Number(row.stock_minimo) || 0
  unidadMedida.value = row.unidad_medida ?? 'm'
  costoUnitario.value = Number((row as any).costo_unitario) || 0
}

async function prefillAuthoritative(id: number) {
  try {
    const full: any = await insumosApi.get(id)
    if (!full || full.id == null) return
    nombre.value = full.nombre ?? nombre.value
    codigo.value = full.codigo ?? ''
    descripcion.value = full.descripcion ?? ''
    tipo.value = full.tipo ?? tipo.value
    ubicacion.value = full.ubicacion ?? ''
    unidadMedida.value = full.unidad_medida ?? unidadMedida.value
    stockActual.value = Number(full.stock_actual) || 0
    stockMinimo.value = Number(full.stock_minimo) || 0
    costoUnitario.value = Number(full.costo_promedio_actual) || 0
    categoriaId.value = full.categoria_id ?? null
    if (full.nombre_categoria) categoria.value = full.nombre_categoria
  } catch { /* keep row values on fetch failure */ }
}

watch(
  () => [props.visible, props.insumo] as const,
  ([vis, row]) => {
    if (vis && row) {
      prefillFromRow(row)
      void prefillAuthoritative(row.id)
    }
  },
  { immediate: true },
)

function extractDetail(e: unknown): string {
  const detail = (e as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail
  if (Array.isArray(detail)) return detail.map((d: any) => d.msg ?? JSON.stringify(d)).join('; ')
  if (typeof detail === 'string' && detail) return detail
  if (e instanceof Error && e.message) return e.message
  return 'No se pudo actualizar el insumo'
}

function isForbidden(e: unknown): boolean {
  return (e as { response?: { status?: number } })?.response?.status === 403
}

async function guardar() {
  if (!props.insumo) return
  if (!nombre.value.trim()) {
    showToast('warn', 'Nombre requerido', 'Ingresá el nombre del insumo o textil.')
    return
  }
  guardando.value = true
  try {
    const payload: InsumoUpdatePayload = {
      nombre: nombre.value.trim(),
      codigo: codigo.value.trim() || null,
      descripcion: descripcion.value.trim() || null,
      tipo: tipo.value,
      ubicacion: ubicacion.value.trim() || null,
      unidad_medida: unidadMedida.value,
      stock_actual: Number(stockActual.value) || 0,
      stock_minimo: Number(stockMinimo.value) || 0,
      costo_promedio_actual: Number(costoUnitario.value) || 0,
    }
    if (categoriaId.value != null) payload.categoria_id = categoriaId.value
    await insumosApi.update(props.insumo.id, payload)
    showToast('success', 'Insumo actualizado', `${nombre.value} guardado correctamente.`)
    emit('insumo-actualizado')
    emit('update:visible', false)
  } catch (e: unknown) {
    if (isForbidden(e)) {
      showToast('error', 'Sin permiso', 'Editar insumos requiere rol admin.')
    } else {
      showToast('error', 'No se pudo guardar', extractDetail(e))
    }
  } finally {
    guardando.value = false
  }
}
</script>

<template>
  <Dialog
    :visible="visible"
    modal
    :header="insumo ? `✏️ Editar Insumo • ${insumo.nombre}` : 'Editar Insumo'"
    :style="{ width: '90vw', maxWidth: '640px' }"
    :breakpoints="{ '640px': '95vw' }"
    :content-style="{ overflowX: 'hidden', maxWidth: '100%' }"
    @update:visible="(v) => emit('update:visible', v)"
  >
    <div v-if="insumo" class="min-w-0 max-w-full space-y-4 overflow-x-hidden pt-1">
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div class="min-w-0">
          <label class="block text-xs font-semibold uppercase tracking-wider text-stone-400 mb-1.5">Código Referencia</label>
          <InputText v-model="codigo" placeholder="Ej: TEL-TUL-200" class="w-full font-mono" />
        </div>
        <div class="min-w-0">
          <label class="block text-xs font-semibold uppercase tracking-wider text-stone-400 mb-1.5">Tipo de Insumo</label>
          <Dropdown v-model="tipo" :options="tiposOptions" option-label="label" option-value="value" class="w-full" />
        </div>
      </div>

      <div>
        <label class="block text-xs font-semibold uppercase tracking-wider text-stone-400 mb-1.5">Nombre del Insumo / Tela</label>
        <InputText v-model="nombre" placeholder="Ej: Ref 200 Encaje Chantilly Oro & Negro" class="w-full" />
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div class="min-w-0">
          <label class="block text-xs font-semibold uppercase tracking-wider text-stone-400 mb-1.5">Categoría</label>
          <Dropdown v-model="categoriaId" :options="categoriasOptions" option-label="label" option-value="value" placeholder="Seleccionar categoría..." class="w-full" />
        </div>
        <div class="min-w-0">
          <label class="block text-xs font-semibold uppercase tracking-wider text-stone-400 mb-1.5">Unidad de Medida</label>
          <Dropdown v-model="unidadMedida" :options="unidadesOptions" option-label="label" option-value="value" class="w-full" />
        </div>
      </div>

      <div>
        <label class="block text-xs font-semibold uppercase tracking-wider text-stone-400 mb-1.5">Ubicación en Taller</label>
        <InputText v-model="ubicacion" placeholder="Ej: Estante Telas Atenea A1" class="w-full" />
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div class="min-w-0">
          <label title="Stock Actual" class="block truncate text-xs font-semibold uppercase tracking-wider text-stone-400 mb-1.5">Stock Actual</label>
          <InputNumber v-model="stockActual" :min="0" :max-fraction-digits="2" class="w-full" input-class="w-full" />
        </div>
        <div class="min-w-0">
          <label title="Stock Mínimo (Alerta)" class="block truncate text-xs font-semibold uppercase tracking-wider text-stone-400 mb-1.5">Stock Mínimo (Alerta)</label>
          <InputNumber v-model="stockMinimo" :min="0" :max-fraction-digits="2" class="w-full" input-class="w-full" />
        </div>
        <div class="min-w-0">
          <label title="Costo Unitario ($)" class="block truncate text-xs font-semibold uppercase tracking-wider text-stone-400 mb-1.5">Costo Unitario ($)</label>
          <InputNumber v-model="costoUnitario" mode="currency" currency="COP" locale="es-CO" :min-fraction-digits="0" class="w-full" input-class="w-full" />
        </div>
      </div>

      <div>
        <label class="block text-xs font-semibold uppercase tracking-wider text-stone-400 mb-1.5">Descripción & Usos de Confección</label>
        <Textarea v-model="descripcion" rows="2" placeholder="Ej: Utilizado para copas de corsets y detalles de escote." class="w-full" />
      </div>

      <div class="flex justify-end gap-2 pt-2 border-t border-stone-800">
        <Button label="Cancelar" severity="secondary" text @click="emit('update:visible', false)" />
        <Button label="Guardar Cambios" icon="pi pi-check" class="p-button-warning font-semibold" :loading="guardando" @click="guardar" />
      </div>
    </div>
  </Dialog>
</template>
