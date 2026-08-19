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
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Message from 'primevue/message'
import Paginator from 'primevue/paginator'
import Select from 'primevue/select'
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

    <div v-if="error" class="productos-error">
      <Message severity="error" :closable="false" icon="pi pi-times-circle">{{ error }}</Message>
    </div>

    <Tabs v-model:value="activeTab">
      <TabList>
        <Tab value="productos">Productos</Tab>
        <Tab value="bom">BOM</Tab>
        <Tab value="costo">Costo</Tab>
      </TabList>
      <TabPanels>
        <TabPanel value="productos">
        <div class="producto-toolbar">
          <InputText
            v-model="productoQ"
            placeholder="Buscar producto…"
            data-test="producto-search"
            class="producto-search"
            @keyup.enter="onProductosSearch"
          />
          <Select
            v-model="filterTipoProductoId"
            :options="tipos"
            optionLabel="nombre"
            optionValue="id"
            placeholder="Filtrar por tipo"
            filter
            :show-clear="true"
            data-test="producto-tipo-filter"
            class="producto-tipo-filter"
            @change="onProductosFilterChange"
          />
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

        <Dialog
          v-model:visible="productoDialogVisible"
          :header="editingProducto === null ? 'Crear producto' : 'Editar producto'"
          modal
          position="top"
          style="width: 560px"
          :dismissable-mask="false"
          :close-on-escape="!savingProducto"
          :closable="!savingProducto"
          @after-hide="resetProductoDialog"
        >
          <ProductoForm
            v-if="productoDialogVisible"
            :mode="editingProducto === null ? 'create' : 'edit'"
            :initial="editingProducto"
            :tipos="tipos"
            :saving="savingProducto"
            @submit="submitProducto"
          />
        </Dialog>

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

          <Dialog
            v-model:visible="varianteDialogVisible"
            :header="editingVariante === null ? 'Nueva variante' : 'Editar variante'"
            modal
            position="top"
            style="width: 480px"
            :dismissable-mask="false"
            :close-on-escape="!savingVariante"
            :closable="!savingVariante"
            @after-hide="resetVarianteDialog"
          >
            <VarianteForm
              v-if="varianteDialogVisible"
              :mode="editingVariante === null ? 'create' : 'edit'"
              :initial="editingVariante"
              :saving="savingVariante"
              @submit="onSubmitVariante"
            />
          </Dialog>
        </div>
      </TabPanel>

      <TabPanel value="bom">
        <div class="bom-select">
          <Select
            v-model="bomProductoId"
            :options="productosLookup"
            optionLabel="nombre"
            optionValue="id"
            placeholder="Selecciona un producto para ver su receta"
            filter
            data-test="bom-product-select"
            panelClass="bom-product-popper"
            style="width: 100%"
            @change="(e: { value: number }) => onSelectBomProducto(e.value)"
          />
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

            <Dialog
              v-model:visible="bomInsumoDialogVisible"
              :header="editingBomInsumo === null ? 'Nueva línea de insumo' : 'Editar línea de insumo'"
              modal
              position="top"
              style="width: 480px"
              :dismissable-mask="false"
              :close-on-escape="!savingBomInsumo"
              :closable="!savingBomInsumo"
              @after-hide="resetBomInsumoDialog"
            >
              <BomInsumoForm
                v-if="bomInsumoDialogVisible"
                :mode="editingBomInsumo === null ? 'create' : 'edit'"
                :initial="editingBomInsumo"
                :insumos="insumos"
                :saving="savingBomInsumo"
                @submit="onSubmitBomInsumo"
              />
            </Dialog>
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

            <Dialog
              v-model:visible="bomProductoDialogVisible"
              :header="editingBomProducto === null ? 'Nueva línea de combo' : 'Editar línea de combo'"
              modal
              position="top"
              style="width: 480px"
              :dismissable-mask="false"
              :close-on-escape="!savingBomProducto"
              :closable="!savingBomProducto"
              @after-hide="resetBomProductoDialog"
            >
              <BomProductoForm
                v-if="bomProductoDialogVisible"
                :mode="editingBomProducto === null ? 'create' : 'edit'"
                :initial="editingBomProducto"
                :productos="productosLookup"
                :saving="savingBomProducto"
                @submit="onSubmitBomProducto"
              />
            </Dialog>
          </section>
        </template>
      </TabPanel>

      <TabPanel value="costo">
        <div class="costo-selects">
          <Select
            v-model="costoProductoId"
            :options="productosLookup"
            optionLabel="nombre"
            optionValue="id"
            placeholder="Selecciona un producto"
            filter
            data-test="costo-product-select"
            panelClass="costo-product-popper"
            style="width: 100%"
            @change="(e: { value: number }) => onSelectCostoProducto(e.value)"
          />
          <Select
            v-model="costoVarianteId"
            :options="costoProductoVariantes"
            optionLabel="nombre_variante"
            optionValue="id"
            placeholder="Variante (opcional)"
            :show-clear="true"
            data-test="costo-variante-select"
            panelClass="costo-variante-popper"
            style="width: 100%"
            @change="onCostoVarianteChange"
          />
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

.producto-tipo-filter {
  width: 12rem;
}

.tabla-paginacion {
  margin-top: 1rem;
  justify-content: flex-end;
}

.variantes-section {
  margin-top: 1rem;
  padding: 1rem;
  border: 1px solid var(--arpia-border-subtle);
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
