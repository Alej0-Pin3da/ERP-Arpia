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
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'

import { formatMoney, parseDecimal } from '@/utils/format'
import {
  CANAL_VENTAS,
  buildVentaPayload,
  canalLabel,
  computeTotalPreview,
  createDetalleRow,
  hasValidDetalles,
  type CanalVenta,
  type VentaCreate,
  type VentasFormDetalle,
} from '@/utils/ventas'
import type { ClienteRead, ProductoRead, VarianteProductoRead } from '@/types/api.d'

const props = defineProps<{
  productos: ProductoRead[]
  clientes: ClienteRead[]
  /** Variante fetcher injected by the view (productosApi.listVariantes). */
  loadVariantes: (productoId: number) => Promise<VarianteProductoRead[]>
  /** True while the parent is POSTing — disables the submit button. */
  saving?: boolean
}>()

const emit = defineEmits<{ submit: [payload: VentaCreate] }>()

const clienteId = ref<number | null>(null)
const canalVenta = ref<CanalVenta>('web')
const descuento = ref(0)
const detalles = ref<VentasFormDetalle[]>([createDetalleRow()])
/** Variantes cached per product (lazy — only fetched for chosen products). */
const variantesPorProducto = ref<Record<number, VarianteProductoRead[]>>({})

const totalPreview = computed(() => computeTotalPreview(detalles.value, descuento.value))

/** Variantes available for a row's currently selected product. */
function variantesDe(row: VentasFormDetalle): VarianteProductoRead[] {
  return row.producto_id === null ? [] : (variantesPorProducto.value[row.producto_id] ?? [])
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

  if (variantesPorProducto.value[row.producto_id] === undefined) {
    const variantes = await props.loadVariantes(row.producto_id)
    variantesPorProducto.value = { ...variantesPorProducto.value, [row.producto_id]: variantes }
  }
}

function addRow(): void {
  detalles.value.push(createDetalleRow())
}

function removeRow(index: number): void {
  detalles.value.splice(index, 1)
}

/** MOD-1: block empty detalles (client-side) before emitting the payload. */
function submit(): void {
  if (!hasValidDetalles(detalles.value)) {
    ElMessage.warning('Agrega al menos un detalle con producto y cantidad mayor a cero.')
    return
  }
  emit('submit', buildVentaPayload({
    cliente_id: clienteId.value,
    canal_venta: canalVenta.value,
    descuento_porcentaje: descuento.value,
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
        :disabled="row.producto_id === null"
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
        Registrar venta
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
