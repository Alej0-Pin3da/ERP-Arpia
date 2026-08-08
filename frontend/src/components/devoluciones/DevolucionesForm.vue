<script setup lang="ts">
/**
 * Devoluciones create form (task 2.3, spec MOD-2).
 *
 * Element Plus form that maps to POST /devoluciones (DevolucionCreate):
 * required venta_id, tipo select (total|parcial), optional motivo, and —
 * ONLY for tipo 'parcial' — dynamic line items (producto, optional variante,
 * cantidad > 0, precio_unitario). CRITICAL rules from MOD-2:
 *  - 'total' needs NO items (items section hidden; POST returns 201 with an
 *    empty payload — the backend ignores items for a total return).
 *  - 'parcial' REQUIRES items (server 422 otherwise); the client blocks an
 *    empty parcial submit before any network call.
 *  - `precio_unitario` is required by the schema but NEVER trusted: the
 *    backend prices every return from the sale-time snapshot and ignores the
 *    client value (note shown under the items).
 * The view owns the actual POST, the success message and the list refresh.
 */
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'

import {
  TIPO_DEVOLUCION,
  buildDevolucionPayload,
  createDevolucionItemRow,
  hasValidDevolucionItems,
  tipoLabel,
  type DevolucionCreate,
  type DevolucionFormItem,
  type DevolucionTipo,
} from '@/utils/devoluciones'
import { parseDecimal } from '@/utils/format'
import type { ProductoRead, VarianteProductoRead } from '@/types/api.d'

const props = defineProps<{
  productos: ProductoRead[]
  /** Variante fetcher injected by the view (productosApi.listVariantes). */
  loadVariantes: (productoId: number) => Promise<VarianteProductoRead[]>
  /** True while the parent is POSTing — disables the submit button. */
  saving?: boolean
}>()

const emit = defineEmits<{ submit: [payload: DevolucionCreate] }>()

const ventaId = ref<number | null>(null)
const tipo = ref<DevolucionTipo>('total')
const motivo = ref('')
const items = ref<DevolucionFormItem[]>([createDevolucionItemRow()])
/** Variantes cached per product (lazy — only fetched for chosen products). */
const variantesPorProducto = ref<Record<number, VarianteProductoRead[]>>({})

/** MOD-2: items are only relevant (and only rendered) for a parcial return. */
const isParcial = computed(() => tipo.value === 'parcial')

/** Variantes available for a row's currently selected product. */
function variantesDe(row: DevolucionFormItem): VarianteProductoRead[] {
  return row.producto_id === null ? [] : (variantesPorProducto.value[row.producto_id] ?? [])
}

/**
 * On product selection: reset the variante, default the (schema-required,
 * server-ignored) unit price from the product's suggested price, and lazily
 * load the product's variantes.
 */
async function onProductoChange(row: DevolucionFormItem): Promise<void> {
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

function addItem(): void {
  items.value.push(createDevolucionItemRow())
}

function removeItem(index: number): void {
  items.value.splice(index, 1)
}

/** MOD-2: client-side gates — venta_id required; parcial requires items. */
function submit(): void {
  if (ventaId.value === null) {
    ElMessage.warning('Indica el número de la venta a devolver.')
    return
  }
  if (isParcial.value && !hasValidDevolucionItems(items.value)) {
    ElMessage.warning('Una devolución parcial requiere al menos un item con producto y cantidad mayor a cero.')
    return
  }
  emit('submit', buildDevolucionPayload({
    venta_id: ventaId.value,
    tipo: tipo.value,
    motivo: motivo.value,
    items: items.value,
  }))
}
</script>

<template>
  <el-form label-position="top" class="devolucion-form" @submit.prevent="submit">
    <el-row :gutter="16">
      <el-col :xs="24" :md="8">
        <el-form-item label="Número de venta">
          <el-input-number
            v-model="ventaId"
            :min="1"
            :step="1"
            :controls="false"
            class="devolucion-field"
            data-test="venta-id-input"
          />
        </el-form-item>
      </el-col>
      <el-col :xs="24" :md="8">
        <el-form-item label="Tipo de devolución">
          <el-select v-model="tipo" class="devolucion-field" data-test="tipo-select">
            <el-option
              v-for="t in TIPO_DEVOLUCION"
              :key="t"
              :label="tipoLabel(t)"
              :value="t"
            />
          </el-select>
        </el-form-item>
      </el-col>
      <el-col :xs="24" :md="8">
        <el-form-item label="Motivo">
          <el-input v-model="motivo" placeholder="Opcional" data-test="motivo-input" />
        </el-form-item>
      </el-col>
    </el-row>

    <div v-if="isParcial" class="items-section">
      <div class="items-header">
        <span>Items a devolver</span>
        <el-button size="small" type="primary" plain data-test="add-item" @click="addItem">
          Agregar item
        </el-button>
      </div>

      <div v-for="(row, index) in items" :key="index" class="item-row" data-test="devolucion-item">
        <el-select
          v-model="row.producto_id"
          filterable
          placeholder="Producto"
          class="devolucion-field"
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
          class="devolucion-field"
          data-test="variante-select"
        >
          <el-option v-for="v in variantesDe(row)" :key="v.id" :label="v.nombre_variante" :value="v.id" />
        </el-select>

        <el-input-number
          v-model="row.cantidad"
          :min="1"
          :step="1"
          class="devolucion-field"
          data-test="cantidad-input"
        />

        <el-input-number
          v-model="row.precio_unitario"
          :min="0"
          :step="100"
          class="devolucion-field"
          data-test="precio-input"
        />

        <el-button size="small" type="danger" plain data-test="remove-item" @click="removeItem(index)">
          Quitar
        </el-button>
      </div>

      <p class="price-note">
        El precio de cada item se toma de la venta original; el valor aquí no afecta el reembolso.
      </p>
    </div>

    <div class="form-footer">
      <span class="form-hint">La devolución total anula la venta completa.</span>
      <el-button type="primary" native-type="submit" :loading="saving" data-test="submit-devolucion">
        Registrar devolución
      </el-button>
    </div>
  </el-form>
</template>

<style scoped>
.devolucion-form {
  max-width: 56rem;
}

.devolucion-field {
  width: 100%;
}

.items-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: 0.5rem 0;
  font-weight: 600;
}

.item-row {
  display: grid;
  grid-template-columns: 2fr 1.6fr 0.7fr 1fr auto;
  gap: 0.5rem;
  align-items: center;
  margin-bottom: 0.5rem;
}

.price-note {
  margin: 0 0 1rem;
  color: var(--el-text-color-secondary);
  font-size: 0.8rem;
}

.form-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 1rem;
}

.form-hint {
  color: var(--el-text-color-secondary);
  font-size: 0.85rem;
}
</style>
