<script setup lang="ts">
/**
 * Maestros view (PR11, spec MOD-5 maestros part).
 *
 * One config-driven CRUD screen per master-data entity — Clientes,
 * Tipos de producto, Categorías de insumos — as three tabs.
 * Every tab renders the SAME generic pattern (MaestroForm + MaestrosTable)
 * driven by its per-entity config (`MAESTRO_ENTITIES`), and every CRUD
 * round-trip shares one handler set keyed by entity:
 *
 *  - list: GET /{clientes,tipos-producto,categorias-insumos}
 *    with limit=1000 (the backend defaults to limit=50)
 *  - create/edit: POST/PUT with the exact schema payload built by the
 *    per-entity builders (utils/maestros) — nombre required, empty optional
 *    fields serialize as null
 *  - delete: DELETE answers 204; tipos-producto additionally answers 409
 *    "in use" (IntegrityError), surfaced via serverDetail()
 *
 * Writes are ADMIN ONLY (backend require_admin on every POST/PUT/DELETE);
 * canManage = admin gates the forms + the table actions, so operador/
 * consulta see read-only lists (SHELL-4).
 */
import { computed, onMounted, ref } from 'vue'

import {
  categoriasInsumosApi,
  clientesApi,
  tiposProductoApi,
} from '@/api/endpoints'
import MaestroForm from '@/components/maestros/MaestroForm.vue'
import MaestrosTable from '@/components/maestros/MaestrosTable.vue'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Message from 'primevue/message'
import Paginator from 'primevue/paginator'
import Tab from 'primevue/tab'
import TabList from 'primevue/tablist'
import TabPanel from 'primevue/tabpanel'
import TabPanels from 'primevue/tabpanels'
import Tabs from 'primevue/tabs'
import { useAuthStore } from '@/stores/auth'
import { confirmAction } from '@/utils/confirm'
import { buildListParams } from '@/utils/pagination'
import {
  buildCategoriaInsumoPayload,
  buildCategoriaInsumoUpdatePayload,
  buildClientePayload,
  buildClienteUpdatePayload,
  buildTipoProductoPayload,
  buildTipoProductoUpdatePayload,
  MAESTRO_ENTITIES,
  maestroEntityConfig,
  type MaestroRow,
} from '@/utils/maestros'
import { showToast } from '@/utils/toast'
const auth = useAuthStore()

/** MOD-5: every maestros write is admin-only server-side. */
const canManage = computed(() => auth.role === 'admin')

type EntityKey = (typeof MAESTRO_ENTITIES)[number]['key']

const activeTab = ref<EntityKey>('clientes')
const loading = ref(false)
const error = ref<string | null>(null)

const rows = ref<Record<EntityKey, MaestroRow[]>>({
  clientes: [],
  'tipos-producto': [],
  'categorias-insumos': [],
})
/** Server totals per entity (FE-1: total comes from the API). */
const totals = ref<Record<EntityKey, number>>({
  clientes: 0,
  'tipos-producto': 0,
  'categorias-insumos': 0,
})
const pages = ref<Record<EntityKey, number>>({
  clientes: 1,
  'tipos-producto': 1,
  'categorias-insumos': 1,
})
const pageSize = 20
const searchQ = ref<Record<EntityKey, string>>({
  clientes: '',
  'tipos-producto': '',
  'categorias-insumos': '',
})
const editing = ref<Record<EntityKey, MaestroRow | null>>({
  clientes: null,
  'tipos-producto': null,
  'categorias-insumos': null,
})
const saving = ref<Record<EntityKey, boolean>>({
  clientes: false,
  'tipos-producto': false,
  'categorias-insumos': false,
})
/** T8/FE-DLG-1: one PrimeVue Dialog per entity, opened from the toolbar. */
const dialogVisible = ref<Record<EntityKey, boolean>>({
  clientes: false,
  'tipos-producto': false,
  'categorias-insumos': false,
})

/** URL id param key per entity (backend path params). */
const ID_KEYS: Record<EntityKey, string> = {
  clientes: 'cliente_id',
  'tipos-producto': 'tipo_producto_id',
  'categorias-insumos': 'categoria_id',
}

/**
 * Uniform CRUD surface over the three APIs. The endpoints accept their own
 * generated body types (ClienteCreate etc.); the per-entity builders return
 * exactly those shapes, which are assignable to Record<string, string|null>
 * (all optionals are `string | null`), so the handlers stay generic.
 */
interface EntityCrud {
  list: (params?: Record<string, unknown>) => Promise<{ items: MaestroRow[]; total: number }>
  create: (body: Record<string, string | null>) => Promise<MaestroRow>
  update: (params: Record<string, number>, body: Record<string, string | null>) => Promise<MaestroRow>
  delete: (params: Record<string, number>) => Promise<void>
}

const crudApis: Record<EntityKey, EntityCrud> = {
  clientes: clientesApi as unknown as EntityCrud,
  'tipos-producto': tiposProductoApi as unknown as EntityCrud,
  'categorias-insumos': categoriasInsumosApi as unknown as EntityCrud,
}

const BUILDERS: Record<
  EntityKey,
  {
    create: (values: Record<string, string>) => Record<string, string | null>
    update: (values: Record<string, string>) => Record<string, string | null>
  }
> = {
  clientes: { create: buildClientePayload, update: buildClienteUpdatePayload },
  'tipos-producto': { create: buildTipoProductoPayload, update: buildTipoProductoUpdatePayload },
  'categorias-insumos': { create: buildCategoriaInsumoPayload, update: buildCategoriaInsumoUpdatePayload },
}

async function load(): Promise<void> {
  loading.value = true
  error.value = null
  try {
    const requests: Record<EntityKey, ReturnType<EntityCrud['list']>> = {
      clientes: clientesApi.list(
        buildListParams({ page: pages.value.clientes, pageSize, q: searchQ.value.clientes }),
      ),
      'tipos-producto': tiposProductoApi.list(
        buildListParams({ page: pages.value['tipos-producto'], pageSize, q: searchQ.value['tipos-producto'] }),
      ),
      'categorias-insumos': categoriasInsumosApi.list(
        buildListParams({ page: pages.value['categorias-insumos'], pageSize, q: searchQ.value['categorias-insumos'] }),
      ),
    }
    const [clientes, tipos, categorias] = await Promise.all([
      requests.clientes,
      requests['tipos-producto'],
      requests['categorias-insumos'],
    ])
    rows.value.clientes = clientes.items
    rows.value['tipos-producto'] = tipos.items
    rows.value['categorias-insumos'] = categorias.items
    totals.value.clientes = clientes.total
    totals.value['tipos-producto'] = tipos.total
    totals.value['categorias-insumos'] = categorias.total
  } catch {
    error.value = 'No se pudo cargar la información de maestros. Verifica la conexión con el servidor.'
  } finally {
    loading.value = false
  }
}

/** FE-2: a busqueda change resets that entity's table to page 1 and refetches. */
function onSearch(entityKey: EntityKey): void {
  pages.value[entityKey] = 1
  load()
}

/** Paginator @page: recompute the entity's 1-based page from the 0-based
 *  first index (typed handler; the template passes $event + the key). */
function onEntityPage(e: { first: number; rows: number }, entityKey: EntityKey): void {
  pages.value[entityKey] = Math.floor(e.first / e.rows) + 1
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

/** MOD-5: admin — POST the entity row (exact schema payload). */
async function onCreate(entityKey: EntityKey, values: Record<string, string>): Promise<void> {
  saving.value[entityKey] = true
  try {
    await crudApis[entityKey].create(BUILDERS[entityKey].create(values))
    showToast('success', `Se creó ${singularOf(entityKey)} correctamente`)
    dialogVisible.value[entityKey] = false // FE-DLG-2: success closes the dialog
    await load()
  } catch (err) {
    showToast('error', serverDetail(err) ?? `No se pudo crear ${singularOf(entityKey).toLowerCase()}.`)
  } finally {
    saving.value[entityKey] = false
  }
}

/** T8: one @submit entry — route create vs edit by the dialog mode. */
function submitEntity(entityKey: EntityKey, values: Record<string, string>): void {
  if (editing.value[entityKey] === null) {
    void onCreate(entityKey, values)
  } else {
    void onUpdate(entityKey, values)
  }
}

function onEdit(entityKey: EntityKey, row: MaestroRow): void {
  editing.value[entityKey] = row
  dialogVisible.value[entityKey] = true
}

/** FE-DLG-1: the toolbar button opens the dialog in create mode. */
function openCreate(entityKey: EntityKey): void {
  editing.value[entityKey] = null
  dialogVisible.value[entityKey] = true
}

/** FE-DLG-2/3: closing without saving discards the edit prefill. */
function resetDialog(entityKey: EntityKey): void {
  editing.value[entityKey] = null
}

/** MOD-5: admin — PUT the entity row, then back to the create form. */
async function onUpdate(entityKey: EntityKey, values: Record<string, string>): Promise<void> {
  const row = editing.value[entityKey]
  if (row === null) return
  saving.value[entityKey] = true
  try {
    await crudApis[entityKey].update({ [ID_KEYS[entityKey]]: row.id }, BUILDERS[entityKey].update(values))
    showToast('success', `Se actualizó ${singularOf(entityKey)} correctamente`)
    dialogVisible.value[entityKey] = false // FE-DLG-2: success closes the dialog
    await load()
  } catch (err) {
    showToast('error', serverDetail(err) ?? `No se pudo actualizar ${singularOf(entityKey).toLowerCase()}.`)
  } finally {
    saving.value[entityKey] = false
  }
}

/** MOD-5: admin — delete after a confirm dialog; DELETE answers 204. */
async function onDelete(entityKey: EntityKey, row: MaestroRow): Promise<void> {
  const singular = singularOf(entityKey)
  const choice = await confirmAction({
    message: `¿Eliminar ${singular.toLowerCase()} "${row.nombre}"?`,
    header: 'Confirmar eliminación',
    acceptLabel: 'Eliminar',
    rejectLabel: 'Cancelar',
  })
  if (choice !== 'accept') return // cancelled
  try {
    await crudApis[entityKey].delete({ [ID_KEYS[entityKey]]: row.id })
    showToast('success', `Se eliminó ${singular} correctamente`)
    await load()
  } catch (err) {
    showToast('error', serverDetail(err) ?? `No se pudo eliminar ${singular.toLowerCase()}.`)
  }
}

function singularOf(key: EntityKey): string {
  return maestroEntityConfig(key)?.singular ?? 'Registro'
}

onMounted(load)
</script>

<template>
  <section class="maestros">
    <header class="maestros-header">
      <h2>Maestros</h2>
      <Button :loading="loading" data-test="refresh-maestros" @click="load">Actualizar</Button>
    </header>

    <div v-if="error" class="maestros-error">
      <Message severity="error" :closable="false" icon="pi pi-times-circle">{{ error }}</Message>
    </div>

    <Tabs v-model:value="activeTab">
      <TabList>
        <Tab v-for="entity in MAESTRO_ENTITIES" :key="entity.key" :value="entity.key">
          {{ entity.title }}
        </Tab>
      </TabList>
      <TabPanels>
        <TabPanel v-for="entity in MAESTRO_ENTITIES" :key="entity.key" :value="entity.key">
        <div class="maestro-toolbar">
          <InputText
            v-model="searchQ[entity.key]"
            :placeholder="`Buscar ${entity.singular.toLowerCase()}…`"
            :data-test="`maestro-search-${entity.key}`"
            class="maestro-search"
            @keyup.enter="onSearch(entity.key)"
          />
          <Button
            v-if="canManage"
            :data-test="`nuevo-${entity.key}`"
            @click="openCreate(entity.key)"
          >
            Nuevo {{ entity.singular }}
          </Button>
        </div>

        <MaestrosTable
          :rows="rows[entity.key]"
          :columns="entity.columns"
          :empty-text="entity.emptyText"
          :loading="loading"
          :can-edit="canManage"
          @edit="(row) => onEdit(entity.key, row)"
          @delete="(row) => onDelete(entity.key, row)"
        />
        <Paginator
          class="tabla-paginacion"
          :total-records="totals[entity.key]"
          :rows="pageSize"
          :first="(pages[entity.key] - 1) * pageSize"
          template="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink CurrentPageReport"
          @page="onEntityPage($event, entity.key)"
        />

        <Dialog
          v-model:visible="dialogVisible[entity.key]"
          :header="editing[entity.key] === null ? `Crear ${entity.singular}` : `Editar ${entity.singular}`"
          modal
          position="top"
          style="width: 560px"
          :dismissable-mask="false"
          :close-on-escape="!saving[entity.key]"
          :closable="!saving[entity.key]"
          @after-hide="resetDialog(entity.key)"
        >
          <MaestroForm
            v-if="dialogVisible[entity.key]"
            :mode="editing[entity.key] === null ? 'create' : 'edit'"
            :fields="entity.fields"
            :singular="entity.singular"
            :initial="editing[entity.key]"
            :saving="saving[entity.key]"
            @submit="(values) => submitEntity(entity.key, values)"
          />
        </Dialog>
      </TabPanel>
      </TabPanels>
    </Tabs>
  </section>
</template>

<style scoped>
.maestros-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
}

.maestros-header h2 {
  margin: 0;
}

.maestros-error {
  margin-bottom: 1rem;
}

.maestro-toolbar {
  display: flex;
  gap: 0.75rem;
  max-width: 42rem;
  margin-bottom: 1rem;
}

.maestro-search {
  width: 14rem;
}

.tabla-paginacion {
  margin-top: 1rem;
  justify-content: flex-end;
}
</style>
