<script setup lang="ts">
/**
 * Productos view (PR10, spec MOD-5).
 *
 * Three tabs:
 *  - Productos: table with CRUD + nested variantes (admin-only writes).
 *  - BOM: bill-of-materials editor (admin-only writes).
 *  - Costo: production cost breakdown (all roles read).
 *
 * All logic lives in the three composables; the view is a thin binding layer.
 */
import { computed, onMounted, ref } from 'vue'

import BomInsumoForm from '@/components/productos/BomInsumoForm.vue'
import BomInsumosTable from '@/components/productos/BomInsumosTable.vue'
import BomProductoForm from '@/components/productos/BomProductoForm.vue'
import BomProductosTable from '@/components/productos/BomProductosTable.vue'
import CostoTree from '@/components/productos/CostoTree.vue'
import ProductoForm from '@/components/productos/ProductoForm.vue'
import ProductosTable from '@/components/productos/ProductosTable.vue'
import VarianteForm from '@/components/productos/VarianteForm.vue'
import VariantesTable from '@/components/productos/VariantesTable.vue'
import Button from 'primevue/button'
import Paginator from 'primevue/paginator'
import Tab from 'primevue/tab'
import TabList from 'primevue/tablist'
import TabPanel from 'primevue/tabpanel'
import TabPanels from 'primevue/tabpanels'
import Tabs from 'primevue/tabs'
import { useProductosBom } from '@/composables/useProductosBom'
import { useProductosCatalog } from '@/composables/useProductosCatalog'
import { useProductosCosto } from '@/composables/useProductosCosto'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

/** MOD-5: EVERY productos/variantes/BOM write is require_admin (backend). */
const canManage = computed(() => auth.role === 'admin')

const activeTab = ref('productos')

const catalog = useProductosCatalog()
const bom = useProductosBom(catalog.insumos, catalog.productosLookup)
const costo = useProductosCosto()

// Flatten composable APIs into the template namespace for backward-compat.
const {
  loading, error,
  productosTotal, productosPage, productosPageSize,
  productoQ, filterTipoProductoId,
  productoRows, tipos, insumos, productosLookup,
  savingProducto, editingProducto, productoDialogVisible,
  selectedProducto, variantes, variantesLoading, savingVariante,
  editingVariante, varianteDialogVisible,
  load,
  onProductosSearch, onProductosFilterChange, onProductosTableSortChange,
  openCreateProducto, onEditProducto, resetProductoDialog, submitProducto, onDeleteProducto,
  onSelectVariantes, openCreateVariante, onEditVariante, resetVarianteDialog,
  onSubmitVariante, onDeleteVariante,
} = catalog

const {
  bomProductoId, bomInsumoRows, bomProductoRows, bomLoading,
  savingBomInsumo, savingBomProducto, editingBomInsumo, editingBomProducto,
  bomInsumoDialogVisible, bomProductoDialogVisible,
  onSelectBomProducto,
  openCreateBomInsumo, onEditBomInsumo, resetBomInsumoDialog,
  onSubmitBomInsumo, onDeleteBomInsumo,
  openCreateBomProducto, onEditBomProducto, resetBomProductoDialog,
  onSubmitBomProducto, onDeleteBomProducto,
} = bom

const {
  costoProductoId, costoVarianteId, costoProductoVariantes, costoTree, costoLoading,
  onSelectCostoProducto, onCostoVarianteChange,
} = costo

onMounted(load)
</script>


<template>
  <section class="productos">
    <header class="productos-header">
      <h2>Productos</h2>
      <Button :loading="loading" data-test="refresh-productos" @click="load">Actualizar</Button>
    </header>

    <el-alert
      v-if="error"
      type="error"
      :title="error"
      show-icon
      :closable="false"
      class="productos-error"
    />

    <Tabs v-model:value="activeTab">
      <TabList>
        <Tab value="productos">Productos</Tab>
        <Tab value="bom">BOM</Tab>
        <Tab value="costo">Costo</Tab>
      </TabList>
      <TabPanels>
        <TabPanel value="productos">
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
          <Button v-if="canManage" data-test="nuevo-producto" @click="openCreateProducto">
            Nuevo producto
          </Button>
        </div>

        <ProductosTable
          :rows="productoRows"
          :loading="loading"
          :can-edit="canManage"
          @edit="onEditProducto"
          @delete="onDeleteProducto"
          @select-variantes="onSelectVariantes"
          @sort-change="onProductosTableSortChange"
        />
        <Paginator
          class="tabla-paginacion"
          :total-records="productosTotal"
          :rows="productosPageSize"
          :first="(productosPage - 1) * productosPageSize"
          template="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink CurrentPageReport"
          @page="(e: { first: number; rows: number }) => { productosPage = Math.floor(e.first / e.rows) + 1; load() }"
        />

        <el-dialog
          v-model="productoDialogVisible"
          :title="editingProducto === null ? 'Crear producto' : 'Editar producto'"
          :close-on-click-modal="false"
          :close-on-press-escape="!savingProducto"
          :show-close="!savingProducto"
          width="560px"
          @closed="resetProductoDialog"
        >
          <ProductoForm
            v-if="productoDialogVisible"
            :mode="editingProducto === null ? 'create' : 'edit'"
            :initial="editingProducto"
            :tipos="tipos"
            :saving="savingProducto"
            @submit="submitProducto"
          />
        </el-dialog>

        <div v-if="selectedProducto !== null" class="variantes-section" data-test="variantes-section">
          <header class="variantes-header">
            <h3>Variantes de {{ selectedProducto.nombre }}</h3>
            <div class="variantes-actions">
              <Button v-if="canManage" size="small" data-test="nueva-variante" @click="openCreateVariante">
                Nueva variante
              </Button>
              <Button size="small" severity="secondary" data-test="close-variantes" @click="selectedProducto = null">
                Cerrar
              </Button>
            </div>
          </header>

          <VariantesTable
            :variantes="variantes"
            :loading="variantesLoading"
            :can-edit="canManage"
            @edit="onEditVariante"
            @delete="onDeleteVariante"
          />

          <el-dialog
            v-model="varianteDialogVisible"
            :title="editingVariante === null ? 'Nueva variante' : 'Editar variante'"
            :close-on-click-modal="false"
            :close-on-press-escape="!savingVariante"
            :show-close="!savingVariante"
            width="480px"
            @closed="resetVarianteDialog"
          >
            <VarianteForm
              v-if="varianteDialogVisible"
              :mode="editingVariante === null ? 'create' : 'edit'"
              :initial="editingVariante"
              :saving="savingVariante"
              @submit="onSubmitVariante"
            />
          </el-dialog>
        </div>
      </TabPanel>

      <TabPanel value="bom">
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
              <Button
                v-if="canManage"
                size="small"
                data-test="nueva-linea-insumo"
                @click="openCreateBomInsumo"
              >
                Nueva línea
              </Button>
            </header>
            <BomInsumosTable
              :rows="bomInsumoRows"
              :loading="bomLoading"
              :can-edit="canManage"
              @edit="onEditBomInsumo"
              @delete="onDeleteBomInsumo"
            />

            <el-dialog
              v-model="bomInsumoDialogVisible"
              :title="editingBomInsumo === null ? 'Nueva línea de insumo' : 'Editar línea de insumo'"
              :close-on-click-modal="false"
              :close-on-press-escape="!savingBomInsumo"
              :show-close="!savingBomInsumo"
              width="480px"
              @closed="resetBomInsumoDialog"
            >
              <BomInsumoForm
                v-if="bomInsumoDialogVisible"
                :mode="editingBomInsumo === null ? 'create' : 'edit'"
                :initial="editingBomInsumo"
                :insumos="insumos"
                :saving="savingBomInsumo"
                @submit="onSubmitBomInsumo"
              />
            </el-dialog>
          </section>

          <section class="bom-subsection">
            <header class="bom-subsection-header">
              <h3>Productos del combo</h3>
              <Button
                v-if="canManage"
                size="small"
                data-test="nueva-linea-combo"
                @click="openCreateBomProducto"
              >
                Nueva línea
              </Button>
            </header>
            <BomProductosTable
              :rows="bomProductoRows"
              :loading="bomLoading"
              :can-edit="canManage"
              @edit="onEditBomProducto"
              @delete="onDeleteBomProducto"
            />

            <el-dialog
              v-model="bomProductoDialogVisible"
              :title="editingBomProducto === null ? 'Nueva línea de combo' : 'Editar línea de combo'"
              :close-on-click-modal="false"
              :close-on-press-escape="!savingBomProducto"
              :show-close="!savingBomProducto"
              width="480px"
              @closed="resetBomProductoDialog"
            >
              <BomProductoForm
                v-if="bomProductoDialogVisible"
                :mode="editingBomProducto === null ? 'create' : 'edit'"
                :initial="editingBomProducto"
                :productos="productosLookup"
                :saving="savingBomProducto"
                @submit="onSubmitBomProducto"
              />
            </el-dialog>
          </section>
        </template>
      </TabPanel>

      <TabPanel value="costo">
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
      </TabPanel>
      </TabPanels>
    </Tabs>
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

.variantes-actions {
  display: flex;
  gap: 0.5rem;
}

.bom-select {
  max-width: 24rem;
  margin-bottom: 1rem;
}

.bom-subsection {
  margin-bottom: 1.5rem;
}

.bom-subsection-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.75rem;
}

.bom-subsection-header h3 {
  margin: 0;
}

.costo-selects {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(14rem, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}
</style>
