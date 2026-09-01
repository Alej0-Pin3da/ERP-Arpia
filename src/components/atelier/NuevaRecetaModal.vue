<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Dropdown from 'primevue/dropdown'
import Textarea from 'primevue/textarea'
import { useAtelierStore, type RecetaBOM } from '@/stores/atelier'
import { useMode } from '@/composables/useMode'
import { showToast } from '@/utils/toast'
import * as productosApi from '@/services/api/productos'

const props = defineProps<{
  visible: boolean
  receta?: RecetaBOM | null
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
  (e: 'receta-creada', receta: RecetaBOM): void
  (e: 'receta-actualizada', receta: RecetaBOM): void
}>()

const atelier = useAtelierStore()
const { isMock } = useMode()

const isEditing = computed(() => !!props.receta)

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
const tipoProductoId = ref<number | null>(null)
const tiposOptions = ref<{ label: string; value: number }[]>([])
const saving = ref(false)

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

async function cargarTipos() {
  if (isMock.value) return
  try {
    const r = await productosApi.listTiposProducto({ limit: 50 })
    tiposOptions.value = r.items.map((t) => ({ label: t.nombre, value: t.id }))
    if (!tipoProductoId.value && tiposOptions.value.length) {
      tipoProductoId.value = tiposOptions.value[0].value
    }
  } catch { /* ignore */ }
}

watch(() => props.visible, (v) => {
  if (v) {
    void cargarTipos()
    if (props.receta) {
      // Prefill for editing
      codigo.value = props.receta.codigo ?? ''
      nombre.value = props.receta.nombre ?? ''
      categoria.value = props.receta.categoria ?? 'Corsetería'
      linea.value = props.receta.linea ?? 'Corsetería'
      descripcion.value = props.receta.descripcion ?? ''
      tiempoConfeccion.value = props.receta.tiempo_confeccion_min ?? 120
      costoInsumos.value = props.receta.costo_insumos ?? 25000
      manoObra.value = props.receta.mano_obra ?? 0
      cifEnergia.value = props.receta.cif_energia ?? 1500
      precioVenta.value = props.receta.precio_venta ?? 95000
      recomendaciones.value = (props.receta as any).recomendaciones_taller ?? ''
      // try to extract tipo_producto_id from mapped product if available
      const raw = props.receta as any
      if (raw.tipo_producto_id) tipoProductoId.value = raw.tipo_producto_id
    } else {
      // Reset for create
      codigo.value = ''
      nombre.value = ''
      descripcion.value = ''
      // keep defaults for costs
    }
  }
})

watch(() => props.receta, (r) => {
  if (props.visible && r) {
    codigo.value = r.codigo ?? ''
    nombre.value = r.nombre ?? ''
    categoria.value = r.categoria ?? 'Corsetería'
    linea.value = r.linea ?? 'Corsetería'
    descripcion.value = r.descripcion ?? ''
    tiempoConfeccion.value = (r as any).tiempo_confeccion_min ?? 120
    costoInsumos.value = (r as any).costo_insumos ?? 25000
    manoObra.value = (r as any).mano_obra ?? 0
    cifEnergia.value = (r as any).cif_energia ?? 1500
    precioVenta.value = (r as any).precio_venta ?? (r as any).precio_venta_sugerido ?? 95000
    recomendaciones.value = (r as any).recomendaciones_taller ?? ''
  }
})

async function guardar() {
  if (!nombre.value.trim()) {
    showToast('warn', 'Nombre requerido', 'Por favor ingresa el nombre de la prenda o receta.')
    return
  }

  // MOCK branch
  if (isMock.value) {
    if (isEditing.value && props.receta) {
      const idx = atelier.recetas.findIndex((x) => x.id === props.receta!.id)
      if (idx !== -1) {
        const updated = {
          ...atelier.recetas[idx],
          codigo: codigo.value.trim() || atelier.recetas[idx].codigo,
          nombre: nombre.value.trim(),
          categoria: categoria.value,
          linea: linea.value,
          descripcion: descripcion.value.trim() || 'Ficha técnica de confección en taller.',
          tiempo_confeccion_min: tiempoConfeccion.value,
          costo_insumos: costoInsumos.value,
          mano_obra: manoObra.value,
          cif_energia: cifEnergia.value,
          precio_venta: precioVenta.value,
          costo_total_unitario: costoInsumos.value + manoObra.value + cifEnergia.value,
          precio_venta_sugerido: precioVenta.value,
          markup_pct: precioVenta.value ? Math.round(((precioVenta.value - (costoInsumos.value + manoObra.value + cifEnergia.value)) / precioVenta.value) * 100) : 60,
          recomendaciones_taller: recomendaciones.value.trim() || 'Seguir patrones anatómicos y pruebas de entalle.',
        }
        atelier.recetas[idx] = updated as RecetaBOM
        showToast('success', 'Receta actualizada', `Ficha ${updated.codigo} - ${updated.nombre} actualizada.`)
        emit('receta-actualizada', updated as RecetaBOM)
        emit('update:visible', false)
        return
      }
    }
    const r = atelier.crearReceta({
      codigo: codigo.value.trim() || `REC-ARP-0${atelier.recetas.length + 1}`,
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
    nombre.value = ''
    codigo.value = ''
    descripcion.value = ''
    return
  }

  // REAL branch — POST / PUT /productos
  saving.value = true
  try {
    // Ensure tipo_producto_id
    let tid = tipoProductoId.value
    if (!tid) {
      // try to fetch first available
      try {
        const r = await productosApi.listTiposProducto({ limit: 1 })
        tid = r.items[0]?.id ?? 1
      } catch { tid = 1 }
    }
    const costosFijos = Number(costoInsumos.value ?? 0) + Number(manoObra.value ?? 0) + Number(cifEnergia.value ?? 0)
    const markupCalc = precioVenta.value ? Math.round(((Number(precioVenta.value) - costosFijos) / Number(precioVenta.value)) * 100) : 0
    const basePayload = {
      nombre: nombre.value.trim(),
      tipo_producto_id: tid!,
      precio_venta_sugerido: Number(precioVenta.value ?? 0),
      costos_operativos_fijos: costosFijos,
      requiere_fabricacion: true,
      codigo: codigo.value.trim() || null,
      categoria: categoria.value || null,
      linea: linea.value || null,
      descripcion: descripcion.value.trim() || null,
      tiempo_confeccion_min: Number(tiempoConfeccion.value ?? 0),
      costo_insumos: Number(costoInsumos.value ?? 0),
      mano_obra: Number(manoObra.value ?? 0),
      cif_energia: Number(cifEnergia.value ?? 0),
      markup_pct: markupCalc,
      recomendaciones_taller: recomendaciones.value.trim() || null,
    } as const
    if (isEditing.value && props.receta) {
      const updated = await productosApi.updateProducto(props.receta.id, basePayload)
      showToast('success', 'Producto actualizado', `${updated.nombre} actualizado correctamente.`)
      // Map to RecetaBOM for emit
      const mapped: RecetaBOM = {
        id: updated.id,
        codigo: `PRD-${updated.id}`,
        nombre: updated.nombre,
        categoria: categoria.value,
        linea: linea.value,
        descripcion: descripcion.value.trim() || updated.nombre,
        tiempo_confeccion_min: tiempoConfeccion.value,
        costo_insumos: costoInsumos.value,
        mano_obra: manoObra.value,
        cif_energia: cifEnergia.value,
        costo_total_unitario: costosFijos,
        precio_venta: Number(updated.precio_venta_sugerido ?? precioVenta.value),
        markup_pct: 0,
        recomendaciones_taller: recomendaciones.value.trim(),
        items: [],
        fases: [],
      } as unknown as RecetaBOM
      emit('receta-actualizada', mapped)
    } else {
      const created = await productosApi.createProducto(basePayload)
      showToast('success', 'Producto creado', `${created.nombre} creado correctamente.`)
      const mapped: RecetaBOM = {
        id: created.id,
        codigo: `PRD-${created.id}`,
        nombre: created.nombre,
        categoria: categoria.value,
        linea: linea.value,
        descripcion: descripcion.value.trim() || created.nombre,
        tiempo_confeccion_min: tiempoConfeccion.value,
        costo_insumos: costoInsumos.value,
        mano_obra: manoObra.value,
        cif_energia: cifEnergia.value,
        costo_total_unitario: costosFijos,
        precio_venta: Number(created.precio_venta_sugerido ?? precioVenta.value),
        markup_pct: 0,
        recomendaciones_taller: recomendaciones.value.trim(),
        items: [],
        fases: [],
      } as unknown as RecetaBOM
      emit('receta-creada', mapped)
    }
    emit('update:visible', false)
    if (!isEditing.value) {
      nombre.value = ''
      codigo.value = ''
      descripcion.value = ''
    }
  } catch (e: any) {
    const detail = e?.response?.data?.detail
    const msg = Array.isArray(detail) ? detail.map((d: any) => d.msg ?? JSON.stringify(d)).join('; ') : (detail ?? e?.message ?? 'Error al guardar')
    showToast('error', 'Error al guardar', String(msg))
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <Dialog
    :visible="visible"
    modal
    :header="isEditing ? '✏️ Editar Receta / Ficha Técnica (BOM)' : '📋 Crear Nueva Receta / Ficha Técnica (BOM)'"
    :style="{ width: '90vw', maxWidth: '680px' }"
    @update:visible="(v) => emit('update:visible', v)"
  >
    <div class="space-y-4 pt-1">
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div>
          <label class="block text-xs font-semibold uppercase tracking-wider text-stone-400 mb-1.5">Código Referencia</label>
          <InputText v-model="codigo" placeholder="Ej: REC-ARP-09" class="w-full font-mono" />
          <span class="text-[10px] text-stone-500">Código único (opcional)</span>
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

      <div v-if="!isMock" class="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div>
          <label class="block text-xs font-semibold uppercase tracking-wider text-stone-400 mb-1.5">Tipo de Producto *</label>
          <Dropdown v-model="tipoProductoId" :options="tiposOptions" optionLabel="label" optionValue="value" placeholder="Seleccionar tipo" class="w-full" />
          <span v-if="!tiposOptions.length" class="text-[10px] text-amber-400">Cargando tipos... si falla, usará ID 1</span>
        </div>
      </div>

      <div>
        <label class="block text-xs font-semibold uppercase tracking-wider text-stone-400 mb-1.5">Nombre del Modelo / Prenda *</label>
        <InputText v-model="nombre" placeholder="Ej: Corset Noir de Satén con Encaje Francés" class="w-full" />
      </div>

      <div>
        <label class="block text-xs font-semibold uppercase tracking-wider text-stone-400 mb-1.5">Descripción del Diseño</label>
        <Textarea v-model="descripcion" rows="2" placeholder="Detalles de patronaje, copas, varillado y materiales." class="w-full" />
      </div>

      <div class="grid grid-cols-2 sm:grid-cols-5 gap-3">
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
          <label class="block text-xs font-semibold uppercase tracking-wider text-stone-400 mb-1.5">CIF / Energía ($)</label>
          <InputNumber v-model="cifEnergia" mode="currency" currency="COP" locale="es-CO" :min-fraction-digits="0" class="w-full font-mono" />
        </div>
        <div>
          <label class="block text-xs font-semibold uppercase tracking-wider text-stone-400 mb-1.5">Precio Venta ($)</label>
          <InputNumber v-model="precioVenta" mode="currency" currency="COP" locale="es-CO" :min-fraction-digits="0" class="w-full font-mono" />
        </div>
      </div>
      <div class="bg-stone-900/60 border border-stone-800 rounded-lg p-2.5 flex items-center justify-between text-xs">
        <span class="text-stone-400 font-semibold uppercase tracking-wider">Costo total (Insumos + Mano + CIF)</span>
        <span class="font-mono font-bold text-emerald-400 text-sm">$ {{ (Number(costoInsumos||0) + Number(manoObra||0) + Number(cifEnergia||0)).toLocaleString('es-CO') }}</span>
      </div>

      <div>
        <label class="block text-xs font-semibold uppercase tracking-wider text-stone-400 mb-1.5">Recomendaciones para el Taller</label>
        <InputText v-model="recomendaciones" placeholder="Ej: Precaución con aguja fina en tul y remates dobles." class="w-full" />
      </div>

      <div class="flex justify-end gap-2 pt-2 border-t border-stone-800">
        <Button label="Cancelar" severity="secondary" text @click="emit('update:visible', false)" />
        <Button :label="isEditing ? 'Actualizar Ficha Técnica' : 'Guardar Ficha Técnica'" icon="pi pi-check" class="p-button-warning font-semibold" :loading="saving" @click="guardar" />
      </div>
    </div>
  </Dialog>
</template>
