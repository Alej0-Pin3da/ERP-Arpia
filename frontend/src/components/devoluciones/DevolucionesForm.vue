<script setup lang="ts">
/**
 * Devoluciones create form (task 2.3, spec MOD-2).
 *
 * PrimeVue form that maps to POST /devoluciones (DevolucionCreate):
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
import Button from 'primevue/button'
import InputNumber from 'primevue/inputnumber'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'

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
import { showToast } from '@/utils/toast'
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

const tipoOptions = computed(() => TIPO_DEVOLUCION.map((t) => ({ label: tipoLabel(t), value: t })))

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
    showToast('warn', 'Indica el número de la venta a devolver.')
    return
  }
  if (isParcial.value && !hasValidDevolucionItems(items.value)) {
    showToast('warn', 'Una devolución parcial requiere al menos un item con producto y cantidad mayor a cero.')
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
  <form class="devolucion-form" @submit.prevent="submit">
    <div class="form-grid">
      <div class="form-col" style="--md: 8">
        <div class="form-item">
          <label class="form-label">Número de venta</label>
          <InputNumber
            v-model="ventaId"
            :min="1"
            :step="1"
            :use-grouping="false"
            :show-buttons="false"
            class="devolucion-field"
            data-test="venta-id-input"
          />
        </div>
      </div>
      <div class="form-col" style="--md: 8">
        <div class="form-item">
          <label class="form-label">Tipo de devolución</label>
          <Select
            v-model="tipo"
            :options="tipoOptions"
            option-label="label"
            option-value="value"
            class="devolucion-field"
            data-test="tipo-select"
          />
        </div>
      </div>
      <div class="form-col" style="--md: 8">
        <div class="form-item">
          <label class="form-label">Motivo</label>
          <InputText v-model="motivo" placeholder="Opcional" data-test="motivo-input" />
        </div>
      </div>
    </div>

    <div v-if="isParcial" class="items-section">
      <div class="items-header">
        <span>Items a devolver</span>
        <Button size="small" text data-test="add-item" @click="addItem">
          Agregar item
        </Button>
      </div>

      <div v-for="(row, index) in items" :key="index" class="item-row" data-test="devolucion-item">
        <Select
          v-model="row.producto_id"
          :options="productos"
          option-label="nombre"
          option-value="id"
          filter
          placeholder="Producto"
          class="devolucion-field"
          data-test="producto-select"
          @change="onProductoChange(row)"
        />

        <Select
          v-model="row.variante_id"
          :options="variantesDe(row)"
          option-label="nombre_variante"
          option-value="id"
          show-clear
          placeholder="Variante (opcional)"
          :disabled="row.producto_id === null"
          class="devolucion-field"
          data-test="variante-select"
        />

        <InputNumber
          v-model="row.cantidad"
          :min="1"
          :step="1"
          :use-grouping="false"
          class="devolucion-field"
          data-test="cantidad-input"
        />

        <InputNumber
          v-model="row.precio_unitario"
          :min="0"
          :step="100"
          :use-grouping="false"
          class="devolucion-field"
          data-test="precio-input"
        />

        <Button size="small" text severity="danger" data-test="remove-item" @click="removeItem(index)">
          Quitar
        </Button>
      </div>

      <p class="price-note">
        El precio de cada item se toma de la venta original; el valor aquí no afecta el reembolso.
      </p>
    </div>

    <div class="form-footer">
      <span class="form-hint">La devolución total anula la venta completa.</span>
      <Button type="submit" :loading="saving" data-test="submit-devolucion">
        Registrar devolución
      </Button>
    </div>
  </form>
</template>

<style scoped>
.devolucion-form {
  max-width: 56rem;
}

.devolucion-field {
  width: 100%;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(24, 1fr);
  gap: 0.5rem 1rem;
}

.form-col {
  grid-column: span 24;
}

@media (min-width: 768px) {
  .form-col {
    grid-column: span var(--md, 24);
  }
}

.form-item {
  display: flex;
  flex-direction: column;
}

.form-label {
  margin-bottom: 0.25rem;
  font-size: 0.875rem;
  color: var(--el-text-color-primary);
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