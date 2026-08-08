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
import { useAuthStore } from '@/stores/auth'
import type { UsuarioCreate, UsuarioRead, UsuarioUpdate } from '@/types/api.d'

const auth = useAuthStore()

/** Session user id — its own row loses the delete action in the table. */
const currentUserId = computed(() => auth.user?.id ?? null)

const loading = ref(false)
const error = ref<string | null>(null)

const usuarios = ref<UsuarioRead[]>([])
const saving = ref(false)
const editing = ref<UsuarioRead | null>(null)

async function load(): Promise<void> {
  loading.value = true
  error.value = null
  try {
    usuarios.value = await usuariosApi.list({ limit: 1000 }) // backend GET /usuarios defaults to limit=50
  } catch {
    error.value = 'No se pudieron cargar los usuarios. Verifica la conexión con el servidor.'
  } finally {
    loading.value = false
  }
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
    await load()
  } catch (err) {
    ElMessage.error(serverDetail(err) ?? 'No se pudo crear el usuario.')
  } finally {
    saving.value = false
  }
}

function onEdit(row: UsuarioRead): void {
  editing.value = row
}

function cancelEdit(): void {
  editing.value = null
}

/** PATCH the rol — a self-demote 400 surfaces and the account stays admin. */
async function onUpdate(payload: UsuarioUpdate): Promise<void> {
  if (editing.value === null) return
  saving.value = true
  try {
    await usuariosApi.update({ usuario_id: editing.value.id }, payload)
    ElMessage.success('Usuario actualizado correctamente')
    editing.value = null
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
      <el-button :loading="loading" data-test="refresh-usuarios" @click="load">Actualizar</el-button>
    </header>

    <el-alert
      v-if="error"
      type="error"
      :title="error"
      show-icon
      :closable="false"
      class="usuarios-error"
    />

    <div v-if="editing === null" class="usuario-form-section">
      <h3>Crear usuario</h3>
      <UsuarioForm mode="create" :saving="saving" @submit="onCreate" />
    </div>
    <div v-else class="usuario-form-section">
      <h3>Editar usuario</h3>
      <UsuarioForm mode="edit" :initial="editing" :saving="saving" @submit="onUpdate" />
      <el-button size="small" data-test="cancel-edit-usuario" @click="cancelEdit">
        Cancelar edición
      </el-button>
    </div>

    <UsuariosTable
      :rows="usuarios"
      :loading="loading"
      :current-user-id="currentUserId"
      @edit="onEdit"
      @delete="onDelete"
    />
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

.usuario-form-section {
  margin-bottom: 1rem;
  max-width: 56rem;
}

.usuario-form-section h3 {
  margin: 0 0 0.5rem;
}
</style>
