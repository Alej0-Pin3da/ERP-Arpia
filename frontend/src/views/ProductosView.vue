<script setup lang="ts">
/**
 * Productos view (PR10, spec MOD-5).
 *
 * Three tabs:
 *  - Productos: the list from GET /productos?limit=1000 with a client join
 *    against GET /tipos-producto; create/edit form + Editar/Eliminar +
 *    "Variantes" (lazy GET /productos/{id}/variantes -> nested list with its
 *    own add/edit/delete form) are ADMIN ONLY (backend require_admin on every
 *    productos/variantes write — verified routes/productos.py).
 *  - BOM: pick a product -> GET /productos/{id}/bom/insumos +
 *    /bom/productos -> two sub-sections (insumo lines with the insumo name +
 *    unidad join; combo contents with the included product name join). All
 *    line writes (POST/PUT/DELETE) are admin only; a duplicate line surfaces
 *    the backend 409.
 *  - Costo: pick a product (+ optional variante) -> GET
 *    /productos/{id}/costo?variante_id -> buildCostoTree -> grouped tree with
 *    the grand total, es-CO. All roles read.
 *
 * Writes: admin only (canManage). Operador/consulta see read-only lists.
 */
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import { insumosApi, productosApi, tiposProductoApi } from '@/api/endpoints'
import { buildListParams } from '@/utils/pagination'
import BomInsumoForm from '@/components/productos/BomInsumoForm.vue'
import BomInsumosTable from '@/components/productos/BomInsumosTable.vue'
import BomProductoForm from '@/components/productos/BomProductoForm.vue'
import BomProductosTable from '@/components/productos/BomProductosTable.vue'
import CostoTree from '@/components/productos/CostoTree.vue'
import ProductoForm from '@/components/productos/ProductoForm.vue'
import ProductosTable from '@/components/productos/ProductosTable.vue'
import VarianteForm from '@/components/productos/VarianteForm.vue'
import VariantesTable from '@/components/productos/VariantesTable.vue'
import { useAuthStore } from '@/stores/auth'
import type {
  BomInsumoPayloadInput,
  BomInsumoRow,
  BomProductoPayloadInput,
  BomProductoRow,
  CostoTree as CostoTreeType,
  ProductoPayloadInput,
  ProductoRow,
  VariantePayloadInput,
} from '@/utils/productos'
import { buildBomInsumoRows, buildBomProductoRows, buildCostoTree, buildProductoRows } from '@/utils/productos'
import type {
  BomInsumoRead,
  BomProductoRead,
  CostoProduccionRead,
  InsumoRead,
  ProductoRead,
  TipoProductoRead,
  VarianteProductoRead,
} from '@/types/api.d'

const auth = useAuthStore()

/** MOD-5: EVERY productos/variantes/BOM write is require_admin (backend). */
const canManage = computed(() => auth.role === 'admin')

const activeTab = ref('productos')
const loading = ref(false)
const error = ref<string | null>(null)

// --- productos table: server-side pagination + filters ----------------------
const productos = ref<ProductoRead[]>([])
const productosTotal = ref(0)
const productosPage = ref(1)
const productosPageSize = ref(20)
const productoQ = ref('')
const filterTipoProductoId = ref<number | null>(null)

// --- lookups (full sets, limit:1000 — design D3) ---------------------------
const productosLookup = ref<ProductoRead[]>([])
const tipos = ref<TipoProductoRead[]>([])
const insumos = ref<InsumoRead[]>([])

const productoRows = computed(() => buildProductoRows(productos.value, tipos.value))

const savingProducto = ref(false)
const editingProducto = ref<ProductoRead | null>(null)

// Nested variantes: lazy per selected product (click "Variantes" on a row).
const selectedProducto = ref<ProductoRead | null>(null)
const variantes = ref<VarianteProductoRead[]>([])
const variantesLoading = ref(false)
const savingVariante = ref(false)
const editingVariante = ref<VarianteProductoRead | null>(null)

// BOM tab: the product whose recipe is being edited.
const bomProductoId = ref<number | null>(null)
const bomInsumos = ref<BomInsumoRead[]>([])
const bomProductos = ref<BomProductoRead[]>([])
const bomInsumoRows = computed(() => buildBomInsumoRows(bomInsumos.value, insumos.value))
const bomProductoRows = computed(() => buildBomProductoRows(bomProductos.value, productosLookup.value))
const bomLoading = ref(false)
const savingBomInsumo = ref(false)
const savingBomProducto = ref(false)
const editingBomInsumo = ref<BomInsumoRow | null>(null)
const editingBomProducto = ref<BomProductoRow | null>(null)

// Costo tab.
const costoProductoId = ref<number | null>(null)
const costoVarianteId = ref<number | null>(null)
const costoProductoVariantes = ref<VarianteProductoRead[]>([])
const costoTree = ref<CostoTreeType | null>(null)
const costoLoading = ref(false)

async function load(): Promise<void> {
  loading.value = true
  error.value = null
  try {
    const [productosList, tiposList, insumosList, productosLookup_] = await Promise.all([
      // Table page: real server-side pagination + filters (T6).
      productosApi.list(
        buildListParams({
          page: productosPage.value,
          pageSize: productosPageSize.value,
          filtros: { tipo_producto_id: filterTipoProductoId.value },
          q: productoQ.value,
        }),
      ),
      tiposProductoApi.list({ limit: 1000 }), // tipo label join + form options
      insumosApi.list({ limit: 1000 }), // BOM insumo name/unidad join + form options
      // D3: join fetches keep the full set (BOM/Costo selects, combo names).
      productosApi.list({ limit: 1000 }),
    ])
    productos.value = productosList.items
    productosTotal.value = productosList.total
    tipos.value = tiposList.items
    insumos.value = insumosList.items
    productosLookup.value = productosLookup_.items
  } catch {
    error.value = 'No se pudo cargar la información de productos. Verifica la conexión con el servidor.'
  } finally {
    loading.value = false
  }
}

/** FE-2: filter/busqueda changes reset to page 1 and refetch. */
function onProductosSearch(): void {
  productosPage.value = 1
  load()
}

function onProductosFilterChange(): void {
  productosPage.value = 1
  load()
}

/** Surface the server validation detail (400/404/409) when present. */
function serverDetail(err: unknown): string | null {
  if (typeof err === 'object' && err !== null && 'response' in err) {
    const data = (err as { response?: { data?: unknown } }).response?.data
    if (
      typeof data === 'object' &&
      data !== null &&
      'detail' in data &&
      typeof (data as { detail: unknown }).detail === 'string'
    ) {
      return (data as { detail: string }).detail
    }
  }
  return null
}

// ---------------------------------------------------------------------------
// Productos CRUD (admin)
// ---------------------------------------------------------------------------

async function onCreateProducto(payload: ProductoPayloadInput): Promise<void> {
  savingProducto.value = true
  try {
    await productosApi.create(payload)
    ElMessage.success('Producto creado correctamente')
    await load()
  } catch (err) {
    ElMessage.error(serverDetail(err) ?? 'No se pudo crear el producto.')
  } finally {
    savingProducto.value = false
  }
}

function onEditProducto(row: ProductoRow): void {
  const producto = productos.value.find((p) => p.id === row.id)
  if (producto) editingProducto.value = producto
}

function cancelEditProducto(): void {
  editingProducto.value = null
}

async function onUpdateProducto(payload: ProductoPayloadInput): Promise<void> {
  if (editingProducto.value === null) return
  savingProducto.value = true
  try {
    await productosApi.update({ producto_id: editingProducto.value.id }, payload)
    ElMessage.success('Producto actualizado correctamente')
    editingProducto.value = null
    await load()
  } catch (err) {
    ElMessage.error(serverDetail(err) ?? 'No se pudo actualizar el producto.')
  } finally {
    savingProducto.value = false
  }
}

/** MOD-5: delete answers 204; a 409 (in use) is surfaced via server detail. */
async function onDeleteProducto(row: ProductoRow): Promise<void> {
  try {
    await ElMessageBox.confirm(
      `¿Eliminar el producto "${row.nombre}"?`,
      'Confirmar eliminación',
      { type: 'warning', confirmButtonText: 'Eliminar', cancelButtonText: 'Cancelar' },
    )
  } catch {
    return // cancelled
  }
  try {
    await productosApi.delete({ producto_id: row.id })
    ElMessage.success('Producto eliminado correctamente')
    await load()
  } catch (err) {
    ElMessage.error(serverDetail(err) ?? 'No se pudo eliminar el producto.')
  }
}

// ---------------------------------------------------------------------------
// Nested variantes (admin writes; list lazy per selected product)
// ---------------------------------------------------------------------------

async function onSelectVariantes(row: ProductoRow): Promise<void> {
  selectedProducto.value = productos.value.find((p) => p.id === row.id) ?? null
  editingVariante.value = null
  await loadVariantes(row.id)
}

async function loadVariantes(productoId: number): Promise<void> {
  variantesLoading.value = true
  try {
    variantes.value = await productosApi.listVariantes({ producto_id: productoId })
  } catch {
    ElMessage.error('No se pudieron cargar las variantes del producto.')
  } finally {
    variantesLoading.value = false
  }
}

function onEditVariante(variante: VarianteProductoRead): void {
  editingVariante.value = variante
}

function cancelEditVariante(): void {
  editingVariante.value = null
}

async function onSubmitVariante(payload: VariantePayloadInput): Promise<void> {
  if (selectedProducto.value === null) return
  savingVariante.value = true
  try {
    if (editingVariante.value !== null) {
      await productosApi.updateVariante(
        { producto_id: selectedProducto.value.id, variante_id: editingVariante.value.id },
        payload,
      )
      ElMessage.success('Variante actualizada correctamente')
      editingVariante.value = null
    } else {
      await productosApi.createVariante({ producto_id: selectedProducto.value.id }, payload)
      ElMessage.success('Variante creada correctamente')
    }
    await loadVariantes(selectedProducto.value.id)
  } catch (err) {
    ElMessage.error(serverDetail(err) ?? 'No se pudo guardar la variante.')
  } finally {
    savingVariante.value = false
  }
}

async function onDeleteVariante(variante: VarianteProductoRead): Promise<void> {
  if (selectedProducto.value === null) return
  try {
    await ElMessageBox.confirm(
      `¿Eliminar la variante "${variante.nombre_variante}"?`,
      'Confirmar eliminación',
      { type: 'warning', confirmButtonText: 'Eliminar', cancelButtonText: 'Cancelar' },
    )
  } catch {
    return
  }
  try {
    await productosApi.deleteVariante({ producto_id: selectedProducto.value.id, variante_id: variante.id })
    ElMessage.success('Variante eliminada correctamente')
    await loadVariantes(selectedProducto.value.id)
  } catch (err) {
    ElMessage.error(serverDetail(err) ?? 'No se pudo eliminar la variante.')
  }
}

// ---------------------------------------------------------------------------
// BOM tab
// ---------------------------------------------------------------------------

async function onSelectBomProducto(productoId: number): Promise<void> {
  bomProductoId.value = productoId
  editingBomInsumo.value = null
  editingBomProducto.value = null
  await loadBom(productoId)
}

async function loadBom(productoId: number): Promise<void> {
  bomLoading.value = true
  try {
    const [insumosList, productosList] = await Promise.all([
      productosApi.listBomInsumos({ producto_id: productoId }),
      productosApi.listBomProductos({ producto_id: productoId }),
    ])
    bomInsumos.value = insumosList
    bomProductos.value = productosList
  } catch {
    ElMessage.error('No se pudo cargar la receta del producto.')
  } finally {
    bomLoading.value = false
  }
}

function onEditBomInsumo(row: BomInsumoRow): void {
  editingBomInsumo.value = row
}

function cancelEditBomInsumo(): void {
  editingBomInsumo.value = null
}

/** MOD-5: admin line create/edit; a duplicate line surfaces the backend 409. */
async function onSubmitBomInsumo(payload: BomInsumoPayloadInput): Promise<void> {
  if (bomProductoId.value === null) return
  savingBomInsumo.value = true
  try {
    if (editingBomInsumo.value !== null) {
      await productosApi.updateBomInsumo(
        { producto_id: bomProductoId.value, linea_id: editingBomInsumo.value.id },
        payload,
      )
      ElMessage.success('Línea de BOM actualizada correctamente')
      editingBomInsumo.value = null
    } else {
      await productosApi.createBomInsumo({ producto_id: bomProductoId.value }, payload)
      ElMessage.success('Línea de BOM agregada correctamente')
    }
    await loadBom(bomProductoId.value)
  } catch (err) {
    ElMessage.error(serverDetail(err) ?? 'No se pudo guardar la línea de BOM.')
  } finally {
    savingBomInsumo.value = false
  }
}

async function onDeleteBomInsumo(row: BomInsumoRow): Promise<void> {
  if (bomProductoId.value === null) return
  try {
    await ElMessageBox.confirm(
      `¿Eliminar la línea de insumo "${row.insumo}"?`,
      'Confirmar eliminación',
      { type: 'warning', confirmButtonText: 'Eliminar', cancelButtonText: 'Cancelar' },
    )
  } catch {
    return
  }
  try {
    await productosApi.deleteBomInsumo({ producto_id: bomProductoId.value, linea_id: row.id })
    ElMessage.success('Línea de BOM eliminada correctamente')
    await loadBom(bomProductoId.value)
  } catch (err) {
    ElMessage.error(serverDetail(err) ?? 'No se pudo eliminar la línea de BOM.')
  }
}

function onEditBomProducto(row: BomProductoRow): void {
  editingBomProducto.value = row
}

function cancelEditBomProducto(): void {
  editingBomProducto.value = null
}

async function onSubmitBomProducto(payload: BomProductoPayloadInput): Promise<void> {
  if (bomProductoId.value === null) return
  savingBomProducto.value = true
  try {
    if (editingBomProducto.value !== null) {
      await productosApi.updateBomProducto(
        { producto_id: bomProductoId.value, linea_id: editingBomProducto.value.id },
        payload,
      )
      ElMessage.success('Línea de combo actualizada correctamente')
      editingBomProducto.value = null
    } else {
      await productosApi.createBomProducto({ producto_id: bomProductoId.value }, payload)
      ElMessage.success('Línea de combo agregada correctamente')
    }
    await loadBom(bomProductoId.value)
  } catch (err) {
    ElMessage.error(serverDetail(err) ?? 'No se pudo guardar la línea de combo.')
  } finally {
    savingBomProducto.value = false
  }
}

async function onDeleteBomProducto(row: BomProductoRow): Promise<void> {
  if (bomProductoId.value === null) return
  try {
    await ElMessageBox.confirm(
      `¿Eliminar la línea de combo "${row.producto}"?`,
      'Confirmar eliminación',
      { type: 'warning', confirmButtonText: 'Eliminar', cancelButtonText: 'Cancelar' },
    )
  } catch {
    return
  }
  try {
    await productosApi.deleteBomProducto({ producto_id: bomProductoId.value, linea_id: row.id })
    ElMessage.success('Línea de combo eliminada correctamente')
    await loadBom(bomProductoId.value)
  } catch (err) {
    ElMessage.error(serverDetail(err) ?? 'No se pudo eliminar la línea de combo.')
  }
}

// ---------------------------------------------------------------------------
// Costo tab
// ---------------------------------------------------------------------------

/** Load the selected product's variantes (feeds the optional variante select). */
async function loadCostoVariantes(productoId: number): Promise<void> {
  try {
    costoProductoVariantes.value = await productosApi.listVariantes({ producto_id: productoId })
  } catch {
    costoProductoVariantes.value = []
  }
}

async function onSelectCostoProducto(productoId: number): Promise<void> {
  costoProductoId.value = productoId
  costoVarianteId.value = null
  costoTree.value = null
  await loadCostoVariantes(productoId)
  await loadCosto()
}

async function loadCosto(): Promise<void> {
  if (costoProductoId.value === null) return
  costoLoading.value = true
  try {
    const costo: CostoProduccionRead = await productosApi.costo(
      { producto_id: costoProductoId.value },
      costoVarianteId.value === null ? undefined : { variante_id: costoVarianteId.value },
    )
    costoTree.value = buildCostoTree(costo)
  } catch {
    costoTree.value = null
    ElMessage.error('No se pudo calcular el costo de producción.')
  } finally {
    costoLoading.value = false
  }
}

function onCostoVarianteChange(): void {
  loadCosto()
}

onMounted(load)
</script>

<template>
  <section class="productos">
    <header class="productos-header">
      <h2>Productos</h2>
      <el-button :loading="loading" data-test="refresh-productos" @click="load">Actualizar</el-button>
    </header>

    <el-alert
      v-if="error"
      type="error"
      :title="error"
      show-icon
      :closable="false"
      class="productos-error"
    />

    <el-tabs v-model="activeTab">
      <el-tab-pane label="Productos" name="productos">
        <div class="producto-toolbar">
          <el-input
            v-model="productoQ"
            clearable
            placeholder="Buscar producto…"
            data-test="producto-search"
            class="producto-search"
            @keyup.enter="onProductosSearch"
            @clear="onProductosSearch"
          />
          <el-select
            v-model="filterTipoProductoId"
            clearable
            filterable
            placeholder="Filtrar por tipo"
            data-test="producto-tipo-filter"
            @change="onProductosFilterChange"
          >
            <el-option v-for="t in tipos" :key="t.id" :label="t.nombre" :value="t.id" />
          </el-select>
        </div>

        <div v-if="canManage" class="producto-form-section">
          <template v-if="editingProducto === null">
            <h3>Crear producto</h3>
            <ProductoForm mode="create" :tipos="tipos" :saving="savingProducto" @submit="onCreateProducto" />
          </template>
          <template v-else>
            <h3>Editar producto</h3>
            <ProductoForm
              mode="edit"
              :initial="editingProducto"
              :tipos="tipos"
              :saving="savingProducto"
              @submit="onUpdateProducto"
            />
            <el-button size="small" data-test="cancel-edit-producto" @click="cancelEditProducto">
              Cancelar edición
            </el-button>
          </template>
        </div>

        <ProductosTable
          :rows="productoRows"
          :loading="loading"
          :can-edit="canManage"
          @edit="onEditProducto"
          @delete="onDeleteProducto"
          @select-variantes="onSelectVariantes"
        />
        <el-pagination
          class="tabla-paginacion"
          background
          layout="total, prev, pager, next"
          :total="productosTotal"
          :page-size="productosPageSize"
          :current-page="productosPage"
          @current-change="(p: number) => { productosPage = p; load() }"
        />

        <div v-if="selectedProducto !== null" class="variantes-section" data-test="variantes-section">
          <header class="variantes-header">
            <h3>Variantes de {{ selectedProducto.nombre }}</h3>
            <el-button size="small" data-test="close-variantes" @click="selectedProducto = null">
              Cerrar
            </el-button>
          </header>

          <template v-if="canManage">
            <template v-if="editingVariante === null">
              <VarianteForm mode="create" :saving="savingVariante" class="variante-form" @submit="onSubmitVariante" />
            </template>
            <template v-else>
              <VarianteForm
                mode="edit"
                :initial="editingVariante"
                :saving="savingVariante"
                class="variante-form"
                @submit="onSubmitVariante"
              />
              <el-button size="small" data-test="cancel-edit-variante" @click="cancelEditVariante">
                Cancelar edición
              </el-button>
            </template>
          </template>

          <VariantesTable
            :variantes="variantes"
            :loading="variantesLoading"
            :can-edit="canManage"
            @edit="onEditVariante"
            @delete="onDeleteVariante"
          />
        </div>
      </el-tab-pane>

      <el-tab-pane label="BOM" name="bom">
        <div class="bom-select">
          <el-select
            v-model="bomProductoId"
            filterable
            placeholder="Selecciona un producto para ver su receta"
            data-test="bom-product-select"
            popper-class="bom-product-popper"
            style="width: 100%"
            @change="onSelectBomProducto"
          >
            <el-option v-for="p in productosLookup" :key="p.id" :label="p.nombre" :value="p.id" />
          </el-select>
        </div>

        <template v-if="bomProductoId !== null">
          <section class="bom-subsection">
            <header class="bom-subsection-header">
              <h3>Insumos</h3>
            </header>
            <template v-if="canManage">
              <template v-if="editingBomInsumo === null">
                <BomInsumoForm
                  mode="create"
                  :insumos="insumos"
                  :saving="savingBomInsumo"
                  class="bom-form"
                  @submit="onSubmitBomInsumo"
                />
              </template>
              <template v-else>
                <BomInsumoForm
                  mode="edit"
                  :initial="editingBomInsumo"
                  :insumos="insumos"
                  :saving="savingBomInsumo"
                  class="bom-form"
                  @submit="onSubmitBomInsumo"
                />
                <el-button size="small" data-test="cancel-edit-bom-insumo" @click="cancelEditBomInsumo">
                  Cancelar edición
                </el-button>
              </template>
            </template>
            <BomInsumosTable
              :rows="bomInsumoRows"
              :loading="bomLoading"
              :can-edit="canManage"
              @edit="onEditBomInsumo"
              @delete="onDeleteBomInsumo"
            />
          </section>

          <section class="bom-subsection">
            <header class="bom-subsection-header">
              <h3>Productos del combo</h3>
            </header>
            <template v-if="canManage">
              <template v-if="editingBomProducto === null">
                <BomProductoForm
                  mode="create"
                  :productos="productosLookup"
                  :saving="savingBomProducto"
                  class="bom-form"
                  @submit="onSubmitBomProducto"
                />
              </template>
              <template v-else>
                <BomProductoForm
                  mode="edit"
                  :initial="editingBomProducto"
                  :productos="productosLookup"
                  :saving="savingBomProducto"
                  class="bom-form"
                  @submit="onSubmitBomProducto"
                />
                <el-button size="small" data-test="cancel-edit-bom-producto" @click="cancelEditBomProducto">
                  Cancelar edición
                </el-button>
              </template>
            </template>
            <BomProductosTable
              :rows="bomProductoRows"
              :loading="bomLoading"
              :can-edit="canManage"
              @edit="onEditBomProducto"
              @delete="onDeleteBomProducto"
            />
          </section>
        </template>
      </el-tab-pane>

      <el-tab-pane label="Costo" name="costo">
        <div class="costo-selects">
          <el-select
            v-model="costoProductoId"
            filterable
            placeholder="Selecciona un producto"
            data-test="costo-product-select"
            popper-class="costo-product-popper"
            style="width: 100%"
            @change="onSelectCostoProducto"
          >
            <el-option v-for="p in productosLookup" :key="p.id" :label="p.nombre" :value="p.id" />
          </el-select>
          <el-select
            v-model="costoVarianteId"
            clearable
            placeholder="Variante (opcional)"
            data-test="costo-variante-select"
            popper-class="costo-variante-popper"
            style="width: 100%"
            @change="onCostoVarianteChange"
          >
            <el-option v-for="v in costoProductoVariantes" :key="v.id" :label="v.nombre_variante" :value="v.id" />
          </el-select>
        </div>

        <CostoTree :tree="costoTree" :loading="costoLoading" />
      </el-tab-pane>
    </el-tabs>
  </section>
</template>

<style scoped>
.productos-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
}

.productos-header h2 {
  margin: 0;
}

.productos-error {
  margin-bottom: 1rem;
}

.producto-form-section {
  margin-bottom: 1rem;
  max-width: 56rem;
}

.producto-form-section h3 {
  margin: 0 0 0.5rem;
}

.producto-toolbar {
  display: flex;
  gap: 0.75rem;
  max-width: 42rem;
  margin-bottom: 1rem;
}

.producto-search {
  width: 14rem;
}

.producto-toolbar .el-select {
  width: 12rem;
}

.tabla-paginacion {
  margin-top: 1rem;
  justify-content: flex-end;
}

.variantes-section {
  margin-top: 1rem;
  padding: 1rem;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 0.375rem;
}

.variantes-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.75rem;
}

.variantes-header h3 {
  margin: 0;
}

.bom-select {
  max-width: 24rem;
  margin-bottom: 1rem;
}

.bom-subsection {
  margin-bottom: 1.5rem;
}

.bom-subsection-header h3 {
  margin: 0 0 0.75rem;
}

.bom-form {
  margin-bottom: 0.75rem;
  max-width: 40rem;
}

.costo-selects {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(14rem, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}
</style>
