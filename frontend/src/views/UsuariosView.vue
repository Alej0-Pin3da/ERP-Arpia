<script setup lang="ts">
/**
 * Usuarios view (PR11, spec MOD-5 usuarios part) — ADMIN ONLY.
 *
 * The route already gates /usuarios via meta.roles ['admin'] (SHELL-4;
 * guards.spec covers the role block); every /usuarios endpoint is also
 * require_admin server-side. This view owns the CRUD:
 *  - list: GET /usuarios with limit=1000 (backend defaults to limit=50);
 *    the table shows id, nombre, email and the rol as an es-CO tag
 *  - create: POST UsuarioCreate {nombre, email, rol, password}; a 400
 *    "Email already registered" is surfaced
 *  - edit: PATCH the rol only (rol-only update form); a SELF-DEMOTE (own
 *    rol away from admin) is rejected server-side with 400 "Cannot change
 *    your own role away from admin" and surfaced — the account stays admin
 *  - delete: DELETE answers 204; the SELF row has no delete action in the
 *    table ("can't delete self"; the backend also rejects it with 400)
 */
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import { usuariosApi } from '@/api/endpoints'
import UsuarioForm from '@/components/usuarios/UsuarioForm.vue'
import UsuariosTable from '@/components/usuarios/UsuariosTable.vue'
import Button from 'primevue/button'
import Message from 'primevue/message'
import Paginator from 'primevue/paginator'
import { useAuthStore } from '@/stores/auth'
import { buildListParams } from '@/utils/pagination'
import type { UsuarioCreate, UsuarioRead, UsuarioUpdate } from '@/types/api.d'

const auth = useAuthStore()

/** Session user id — its own row loses the delete action in the table. */
const currentUserId = computed(() => auth.user?.id ?? null)

const loading = ref(false)
const error = ref<string | null>(null)

const usuarios = ref<UsuarioRead[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const searchQ = ref('')
const filterRol = ref<'admin' | 'operador' | 'consulta' | null>(null)
const saving = ref(false)
const editing = ref<UsuarioRead | null>(null)

/** T8/FE-DLG-1: the form lives in an el-dialog opened from the toolbar button. */
const usuarioDialogVisible = ref(false)

async function load(): Promise<void> {
  loading.value = true
  error.value = null
  try {
    const result = await usuariosApi.list(
      buildListParams({
        page: page.value,
        pageSize,
        filtros: { rol: filterRol.value },
        q: searchQ.value,
      }),
    )
    usuarios.value = result.items
    total.value = result.total
  } catch {
    error.value = 'No se pudieron cargar los usuarios. Verifica la conexión con el servidor.'
  } finally {
    loading.value = false
  }
}

/** FE-2: filter/busqueda changes reset to page 1 and refetch. */
function onSearch(): void {
  page.value = 1
  load()
}

function onFilterChange(): void {
  page.value = 1
  load()
}

/** Surface the server validation detail (400/404) when present. */
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

/** POST /usuarios — 400 "Email already registered" surfaces. */
async function onCreate(payload: UsuarioCreate): Promise<void> {
  saving.value = true
  try {
    await usuariosApi.create(payload)
    ElMessage.success('Usuario creado correctamente')
    usuarioDialogVisible.value = false // FE-DLG-2: success closes the dialog
    await load()
  } catch (err) {
    ElMessage.error(serverDetail(err) ?? 'No se pudo crear el usuario.')
  } finally {
    saving.value = false
  }
}

/** T8: one @submit entry — route create vs edit by the dialog mode. */
function submitUsuario(payload: UsuarioCreate | UsuarioUpdate): void {
  if (editing.value === null) {
    void onCreate(payload as UsuarioCreate)
  } else {
    void onUpdate(payload as UsuarioUpdate)
  }
}

function onEdit(row: UsuarioRead): void {
  editing.value = row
  usuarioDialogVisible.value = true
}

/** FE-DLG-1: the toolbar button opens the dialog in create mode. */
function openCreateUsuario(): void {
  editing.value = null
  usuarioDialogVisible.value = true
}

/** FE-DLG-2/3: closing without saving discards the edit prefill. */
function resetUsuarioDialog(): void {
  editing.value = null
}

/** PATCH the rol — a self-demote 400 surfaces and the account stays admin. */
async function onUpdate(payload: UsuarioUpdate): Promise<void> {
  if (editing.value === null) return
  saving.value = true
  try {
    await usuariosApi.update({ usuario_id: editing.value.id }, payload)
    ElMessage.success('Usuario actualizado correctamente')
    usuarioDialogVisible.value = false // FE-DLG-2: success closes the dialog
    await load()
  } catch (err) {
    ElMessage.error(serverDetail(err) ?? 'No se pudo actualizar el usuario.')
  } finally {
    saving.value = false
  }
}

/** DELETE /usuarios/{id} (204). The self row never reaches here (hidden). */
async function onDelete(row: UsuarioRead): Promise<void> {
  try {
    await ElMessageBox.confirm(`¿Eliminar el usuario "${row.nombre}"?`, 'Confirmar eliminación', {
      type: 'warning',
      confirmButtonText: 'Eliminar',
      cancelButtonText: 'Cancelar',
    })
  } catch {
    return // cancelled
  }
  try {
    await usuariosApi.delete({ usuario_id: row.id })
    ElMessage.success('Usuario eliminado correctamente')
    await load()
  } catch (err) {
    ElMessage.error(serverDetail(err) ?? 'No se pudo eliminar el usuario.')
  }
}

onMounted(load)
</script>

<template>
  <section class="usuarios">
    <header class="usuarios-header">
      <h2>Usuarios</h2>
      <Button :loading="loading" data-test="refresh-usuarios" @click="load">Actualizar</Button>
    </header>

    <div v-if="error" class="usuarios-error">
      <Message severity="error" :closable="false" icon="pi pi-times-circle">{{ error }}</Message>
    </div>

    <div class="usuario-toolbar">
      <el-input
        v-model="searchQ"
        clearable
        placeholder="Buscar usuario…"
        data-test="usuario-search"
        class="usuario-search"
        @keyup.enter="onSearch"
        @clear="onSearch"
      />
      <el-select
        v-model="filterRol"
        clearable
        placeholder="Filtrar por rol"
        data-test="usuario-rol-filter"
        @change="onFilterChange"
      >
        <el-option label="Admin" value="admin" />
        <el-option label="Operador" value="operador" />
        <el-option label="Consulta" value="consulta" />
      </el-select>
      <Button data-test="nuevo-usuario" @click="openCreateUsuario">
        Nuevo usuario
      </Button>
    </div>

    <UsuariosTable
      :rows="usuarios"
      :loading="loading"
      :current-user-id="currentUserId"
      @edit="onEdit"
      @delete="onDelete"
    />
    <Paginator
      class="tabla-paginacion"
      :total-records="total"
      :rows="pageSize"
      :first="(page - 1) * pageSize"
      template="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink CurrentPageReport"
      @page="(e: { first: number; rows: number }) => { page = Math.floor(e.first / e.rows) + 1; load() }"
    />

    <el-dialog
      v-model="usuarioDialogVisible"
      :title="editing === null ? 'Crear usuario' : 'Editar usuario'"
      :close-on-click-modal="false"
      :close-on-press-escape="!saving"
      :show-close="!saving"
      width="560px"
      @closed="resetUsuarioDialog"
    >
      <UsuarioForm
        v-if="usuarioDialogVisible"
        :mode="editing === null ? 'create' : 'edit'"
        :initial="editing"
        :saving="saving"
        @submit="submitUsuario"
      />
    </el-dialog>
  </section>
</template>

<style scoped>
.usuarios-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
}

.usuarios-header h2 {
  margin: 0;
}

.usuarios-error {
  margin-bottom: 1rem;
}

.usuario-toolbar {
  display: flex;
  gap: 0.75rem;
  max-width: 42rem;
  margin-bottom: 1rem;
}

.usuario-search {
  width: 14rem;
}

.usuario-toolbar .el-select {
  width: 12rem;
}

.tabla-paginacion {
  margin-top: 1rem;
  justify-content: flex-end;
}
</style>
