<script setup lang="ts">
/**
 * Ventas register form (task 2.2, spec MOD-1).
 *
 * Element Plus form that maps to POST /ventas (VentaCreate): optional
 * cliente, canal_venta select, descuento_porcentaje, and dynamic line items
 * (producto, optional variante, cantidad > 0, precio_unitario >= 0 defaulted
 * from producto.precio_venta_sugerido). The client blocks empty detalles
 * before any network call; the view owns the actual POST, the success
 * message and the list refresh. The total preview mirrors the server
 * calculation: subtotal * (1 - descuento/100).
 */
import { computed, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'

import { formatMoney, parseDecimal } from '@/utils/format'
import {
  CANAL_VENTAS,
  buildVentaPayload,
  canalLabel,
  computeTotalPreview,
  createDetalleRow,
  detallesSinVariante,
  hasValidDetalles,
  type CanalVenta,
  type VentaCreate,
  type VentasFormDetalle,
} from '@/utils/ventas'
import type { components } from '@/types/api.d'

type ClienteRead = components['schemas']['ClienteRead']
type ProductoRead = components['schemas']['ProductoRead']
type VarianteProductoRead = components['schemas']['VarianteProductoRead']
type VentaRead = components['schemas']['VentaRead']

const props = withDefaults(
  defineProps<{
    productos: ProductoRead[]
    clientes: ClienteRead[]
    /** Variante fetcher injected by the view (productosApi.listVariantes). */
    loadVariantes: (productoId: number) => Promise<VarianteProductoRead[]>
    /** 'create' POSTs; 'edit' PUTs with `initial` as the prefill. */
    mode?: 'create' | 'edit'
    /** The venta being edited (prefills every editable field in edit mode). */
    initial?: VentaRead | null
    /** True while the parent is POSTing — disables the submit button. */
    saving?: boolean
  }>(),
  { mode: 'create', initial: null, saving: false },
)

const emit = defineEmits<{ submit: [payload: VentaCreate] }>()

const clienteId = ref<number | null>(null)
const canalVenta = ref<CanalVenta>('web')
const descuento = ref(0)
const esRegalo = ref(false)
const detalles = ref<VentasFormDetalle[]>([createDetalleRow()])
/** Variantes cached per product (lazy — only fetched for chosen products). */
const variantesPorProducto = ref<Record<number, VarianteProductoRead[]>>({})

const totalPreview = computed(() =>
  esRegalo.value ? 0 : computeTotalPreview(detalles.value, descuento.value),
)

/** Variantes available for a row's currently selected product. */
function variantesDe(row: VentasFormDetalle): VarianteProductoRead[] {
  return row.producto_id === null ? [] : (variantesPorProducto.value[row.producto_id] ?? [])
}

/** In-flight variant loads per product — concurrent callers share the same
 *  promise so submit() can await the load that `onProductoChange` started
 *  (D6: closes the submit-before-load race, VV-4). */
const variantesEnVuelo = new Map<number, Promise<void>>()

/** Lazy-load (and cache) the variantes of a product; idempotent per product. */
function loadVariantesFor(productoId: number): Promise<void> {
  if (variantesPorProducto.value[productoId] !== undefined) return Promise.resolve()
  const enVuelo = variantesEnVuelo.get(productoId)
  if (enVuelo) return enVuelo
  const carga = props
    .loadVariantes(productoId)
    .then((variantes) => {
      variantesPorProducto.value = { ...variantesPorProducto.value, [productoId]: variantes }
    })
    .finally(() => {
      variantesEnVuelo.delete(productoId)
    })
  variantesEnVuelo.set(productoId, carga)
  return carga
}

/**
 * On product selection: reset the variante, default the unit price from the
 * product's suggested price, and lazily load the product's variantes.
 */
async function onProductoChange(row: VentasFormDetalle): Promise<void> {
  row.variante_id = null
  if (row.producto_id === null) return

  const producto = props.productos.find((p) => p.id === row.producto_id)
  if (producto) {
    row.precio_unitario = parseDecimal(producto.precio_venta_sugerido) ?? 0
  }

  await loadVariantesFor(row.producto_id)
}

/** Edit mode: prefill every field from the `initial` venta (T9 pattern). */
watch(
  () => props.initial,
  async (venta) => {
    if (!venta) return
    clienteId.value = venta.cliente_id
    canalVenta.value = venta.canal_venta as CanalVenta
    descuento.value = Number.parseFloat(venta.descuento_porcentaje)
    esRegalo.value = venta.es_regalo
    detalles.value = venta.detalles.map((d) => ({
      producto_id: d.producto_id,
      variante_id: d.variante_id,
      cantidad: Number.parseFloat(d.cantidad),
      precio_unitario: Number.parseFloat(d.precio_unitario_aplicado),
    }))
    // Preload the variantes of the prefilled products so the variant selects
    // render their labels immediately.
    const ids = [...new Set(venta.detalles.map((d) => d.producto_id))]
    await Promise.all(ids.map(loadVariantesFor))
  },
  { immediate: true },
)

function addRow(): void {
  detalles.value.push(createDetalleRow())
}

function removeRow(index: number): void {
  detalles.value.splice(index, 1)
}

/**
 * MOD-1: block empty detalles (client-side) before emitting the payload.
 * VV-1/D6: wait for any in-flight variant loads, then block (warning, no
 * emit) while any sized row still lacks its variant — same path for create
 * and edit (edit prefill feeds `detalles`, so a sized line prefilled with
 * `variante_id: null` is blocked until a variant is chosen).
 */
async function submit(): Promise<void> {
  if (!hasValidDetalles(detalles.value)) {
    ElMessage.warning('Agrega al menos un detalle con producto y cantidad mayor a cero.')
    return
  }

  const ids = [
    ...new Set(
      detalles.value
        .map((d) => d.producto_id)
        .filter((id): id is number => id !== null),
    ),
  ]
  await Promise.all(ids.map(loadVariantesFor))

  if (detallesSinVariante(detalles.value, variantesPorProducto.value).length > 0) {
    ElMessage.warning('Los productos con talla requieren seleccionar una variante.')
    return
  }
  emit('submit', buildVentaPayload({
    cliente_id: clienteId.value,
    canal_venta: canalVenta.value,
    descuento_porcentaje: descuento.value,
    es_regalo: esRegalo.value,
    detalles: detalles.value,
  }))
}
</script>

<template>
  <el-form label-position="top" class="venta-form" @submit.prevent="submit">
    <el-row :gutter="16">
      <el-col :xs="24" :md="10">
        <el-form-item label="Cliente">
          <el-select
            v-model="clienteId"
            clearable
            filterable
            placeholder="Sin cliente"
            class="venta-field"
            data-test="cliente-select"
          >
            <el-option v-for="c in clientes" :key="c.id" :label="c.nombre" :value="c.id" />
          </el-select>
        </el-form-item>
      </el-col>
      <el-col :xs="24" :md="7">
        <el-form-item label="Canal de venta">
          <el-select v-model="canalVenta" class="venta-field" data-test="canal-select">
            <el-option
              v-for="canal in CANAL_VENTAS"
              :key="canal"
              :label="canalLabel(canal)"
              :value="canal"
            />
          </el-select>
        </el-form-item>
      </el-col>
      <el-col :xs="24" :md="7">
        <el-form-item label="Descuento (%)">
          <el-input-number
            v-model="descuento"
            :min="0"
            :max="100"
            :step="1"
            class="venta-field"
            data-test="descuento-input"
          />
        </el-form-item>
      </el-col>
      <el-col :xs="24" :md="7">
        <el-form-item label="Es regalo" data-test="es-regalo-field">
          <el-switch
            v-model="esRegalo"
            data-test="es-regalo-toggle"
            inline-prompt
            active-text="Sí"
            inactive-text="No"
          />
        </el-form-item>
      </el-col>
    </el-row>

    <div class="detalles-header">
      <span>Detalles de la venta</span>
      <el-button size="small" type="primary" plain data-test="add-detalle" @click="addRow">
        Agregar producto
      </el-button>
    </div>

    <div v-for="(row, index) in detalles" :key="index" class="detalle-row" data-test="detalle-row">
      <el-select
        v-model="row.producto_id"
        filterable
        placeholder="Producto"
        class="venta-field"
        data-test="producto-select"
        @change="onProductoChange(row)"
      >
        <el-option v-for="p in productos" :key="p.id" :label="p.nombre" :value="p.id" />
      </el-select>

      <el-select
        v-model="row.variante_id"
        clearable
        placeholder="Variante (opcional)"
        :disabled="variantesDe(row).length === 0"
        class="venta-field"
        data-test="variante-select"
      >
        <el-option v-for="v in variantesDe(row)" :key="v.id" :label="v.nombre_variante" :value="v.id" />
      </el-select>

      <el-input-number
        v-model="row.cantidad"
        :min="1"
        :step="1"
        class="venta-field"
        data-test="cantidad-input"
      />

      <el-input-number
        v-model="row.precio_unitario"
        :min="0"
        :step="100"
        class="venta-field"
        data-test="precio-input"
      />

      <el-button size="small" type="danger" plain data-test="remove-detalle" @click="removeRow(index)">
        Quitar
      </el-button>
    </div>

    <div class="form-footer">
      <span class="total-preview" data-test="total-preview">Total: {{ formatMoney(totalPreview) }}</span>
      <el-button type="primary" native-type="submit" :loading="saving" data-test="submit-venta">
        {{ mode === 'edit' ? 'Guardar cambios' : 'Registrar venta' }}
      </el-button>
    </div>
  </el-form>
</template>

<style scoped>
.venta-form {
  max-width: 56rem;
}

.venta-field {
  width: 100%;
}

.detalles-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: 0.5rem 0;
  font-weight: 600;
}

.detalle-row {
  display: grid;
  grid-template-columns: 2fr 1.6fr 0.7fr 1fr auto;
  gap: 0.5rem;
  align-items: center;
  margin-bottom: 0.5rem;
}

.form-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 1rem;
}

.total-preview {
  font-size: 1.05rem;
  font-weight: 600;
}
</style>
