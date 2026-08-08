<script setup lang="ts">
/**
 * Maestros view (PR11, spec MOD-5 maestros part).
 *
 * One config-driven CRUD screen per master-data entity — Clientes,
 * Proveedores, Tipos de producto, Categorías de insumos — as four tabs.
 * Every tab renders the SAME generic pattern (MaestroForm + MaestrosTable)
 * driven by its per-entity config (`MAESTRO_ENTITIES`), and every CRUD
 * round-trip shares one handler set keyed by entity:
 *
 *  - list: GET /{clientes,proveedores,tipos-producto,categorias-insumos}
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
import { ElMessage, ElMessageBox } from 'element-plus'

import {
  categoriasInsumosApi,
  clientesApi,
  proveedoresApi,
  tiposProductoApi,
} from '@/api/endpoints'
import MaestroForm from '@/components/maestros/MaestroForm.vue'
import MaestrosTable from '@/components/maestros/MaestrosTable.vue'
import { useAuthStore } from '@/stores/auth'
import {
  buildCategoriaInsumoPayload,
  buildCategoriaInsumoUpdatePayload,
  buildClientePayload,
  buildClienteUpdatePayload,
  buildProveedorPayload,
  buildProveedorUpdatePayload,
  buildTipoProductoPayload,
  buildTipoProductoUpdatePayload,
  MAESTRO_ENTITIES,
  maestroEntityConfig,
  type MaestroRow,
} from '@/utils/maestros'
const auth = useAuthStore()

/** MOD-5: every maestros write is admin-only server-side. */
const canManage = computed(() => auth.role === 'admin')

type EntityKey = (typeof MAESTRO_ENTITIES)[number]['key']

const activeTab = ref<EntityKey>('clientes')
const loading = ref(false)
const error = ref<string | null>(null)

const rows = ref<Record<EntityKey, MaestroRow[]>>({
  clientes: [],
  proveedores: [],
  'tipos-producto': [],
  'categorias-insumos': [],
})
const editing = ref<Record<EntityKey, MaestroRow | null>>({
  clientes: null,
  proveedores: null,
  'tipos-producto': null,
  'categorias-insumos': null,
})
const saving = ref<Record<EntityKey, boolean>>({
  clientes: false,
  proveedores: false,
  'tipos-producto': false,
  'categorias-insumos': false,
})

/** URL id param key per entity (backend path params). */
const ID_KEYS: Record<EntityKey, string> = {
  clientes: 'cliente_id',
  proveedores: 'proveedor_id',
  'tipos-producto': 'tipo_producto_id',
  'categorias-insumos': 'categoria_id',
}

/**
 * Uniform CRUD surface over the four APIs. The endpoints accept their own
 * generated body types (ClienteCreate etc.); the per-entity builders return
 * exactly those shapes, which are assignable to Record<string, string|null>
 * (all optionals are `string | null`), so the handlers stay generic.
 */
interface EntityCrud {
  list: (params?: { limit?: number }) => Promise<MaestroRow[]>
  create: (body: Record<string, string | null>) => Promise<MaestroRow>
  update: (params: Record<string, number>, body: Record<string, string | null>) => Promise<MaestroRow>
  delete: (params: Record<string, number>) => Promise<void>
}

const crudApis: Record<EntityKey, EntityCrud> = {
  clientes: clientesApi as unknown as EntityCrud,
  proveedores: proveedoresApi as unknown as EntityCrud,
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
  proveedores: { create: buildProveedorPayload, update: buildProveedorUpdatePayload },
  'tipos-producto': { create: buildTipoProductoPayload, update: buildTipoProductoUpdatePayload },
  'categorias-insumos': { create: buildCategoriaInsumoPayload, update: buildCategoriaInsumoUpdatePayload },
}

async function load(): Promise<void> {
  loading.value = true
  error.value = null
  try {
    const [clientes, proveedores, tipos, categorias] = await Promise.all([
      clientesApi.list({ limit: 1000 }), // backend GET /clientes defaults to limit=50
      proveedoresApi.list({ limit: 1000 }),
      tiposProductoApi.list({ limit: 1000 }),
      categoriasInsumosApi.list({ limit: 1000 }),
    ])
    rows.value.clientes = clientes
    rows.value.proveedores = proveedores
    rows.value['tipos-producto'] = tipos
    rows.value['categorias-insumos'] = categorias
  } catch {
    error.value = 'No se pudo cargar la información de maestros. Verifica la conexión con el servidor.'
  } finally {
    loading.value = false
  }
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
    ElMessage.success(`Se creó ${singularOf(entityKey)} correctamente`)
    await load()
  } catch (err) {
    ElMessage.error(serverDetail(err) ?? `No se pudo crear ${singularOf(entityKey).toLowerCase()}.`)
  } finally {
    saving.value[entityKey] = false
  }
}

function onEdit(entityKey: EntityKey, row: MaestroRow): void {
  editing.value[entityKey] = row
}

function cancelEdit(entityKey: EntityKey): void {
  editing.value[entityKey] = null
}

/** MOD-5: admin — PUT the entity row, then back to the create form. */
async function onUpdate(entityKey: EntityKey, values: Record<string, string>): Promise<void> {
  const row = editing.value[entityKey]
  if (row === null) return
  saving.value[entityKey] = true
  try {
    await crudApis[entityKey].update({ [ID_KEYS[entityKey]]: row.id }, BUILDERS[entityKey].update(values))
    ElMessage.success(`Se actualizó ${singularOf(entityKey)} correctamente`)
    editing.value[entityKey] = null
    await load()
  } catch (err) {
    ElMessage.error(serverDetail(err) ?? `No se pudo actualizar ${singularOf(entityKey).toLowerCase()}.`)
  } finally {
    saving.value[entityKey] = false
  }
}

/** MOD-5: admin — delete after a confirm dialog; DELETE answers 204. */
async function onDelete(entityKey: EntityKey, row: MaestroRow): Promise<void> {
  const singular = singularOf(entityKey)
  try {
    await ElMessageBox.confirm(`¿Eliminar ${singular.toLowerCase()} "${row.nombre}"?`, 'Confirmar eliminación', {
      type: 'warning',
      confirmButtonText: 'Eliminar',
      cancelButtonText: 'Cancelar',
    })
  } catch {
    return // cancelled
  }
  try {
    await crudApis[entityKey].delete({ [ID_KEYS[entityKey]]: row.id })
    ElMessage.success(`Se eliminó ${singular} correctamente`)
    await load()
  } catch (err) {
    ElMessage.error(serverDetail(err) ?? `No se pudo eliminar ${singular.toLowerCase()}.`)
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
      <el-button :loading="loading" data-test="refresh-maestros" @click="load">Actualizar</el-button>
    </header>

    <el-alert
      v-if="error"
      type="error"
      :title="error"
      show-icon
      :closable="false"
      class="maestros-error"
    />

    <el-tabs v-model="activeTab">
      <el-tab-pane v-for="entity in MAESTRO_ENTITIES" :key="entity.key" :label="entity.title" :name="entity.key">
        <div v-if="canManage" class="maestro-form-section">
          <template v-if="editing[entity.key] === null">
            <h3>Crear {{ entity.singular }}</h3>
            <MaestroForm
              mode="create"
              :fields="entity.fields"
              :singular="entity.singular"
              :saving="saving[entity.key]"
              @submit="(values) => onCreate(entity.key, values)"
            />
          </template>
          <template v-else>
            <h3>Editar {{ entity.singular }}</h3>
            <MaestroForm
              mode="edit"
              :fields="entity.fields"
              :singular="entity.singular"
              :initial="editing[entity.key]"
              :saving="saving[entity.key]"
              @submit="(values) => onUpdate(entity.key, values)"
            />
            <el-button size="small" :data-test="`cancel-edit-${entity.key}`" @click="cancelEdit(entity.key)">
              Cancelar edición
            </el-button>
          </template>
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
      </el-tab-pane>
    </el-tabs>
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

.maestro-form-section {
  margin-bottom: 1rem;
  max-width: 56rem;
}

.maestro-form-section h3 {
  margin: 0 0 0.5rem;
}
</style>
