<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Dropdown from 'primevue/dropdown'
import { useAuthStore } from '@/stores/auth'
import { useMode } from '@/composables/useMode'
import { showToast } from '@/utils/toast'
import * as usuariosApi from '@/services/api/usuarios'

const auth = useAuthStore()
const { isMock } = useMode()

// MOCK: lista local mínima (no rompe, sin mutar atelier — no hay colección de usuarios ahí)
const usuariosMock = ref([
  { id: 1, nombre: 'Valeria Arpía', email: 'admin@arpia.com.co', rol: 'admin' },
  { id: 2, nombre: 'Camila Modista', email: 'taller@arpia.com.co', rol: 'operador' },
  { id: 3, nombre: 'Elena Inversionista', email: 'socia@arpia.com.co', rol: 'consulta' },
])

const usuariosReal = ref<usuariosApi.UsuarioRead[]>([])
const cargando = ref(false)
const search = ref('')
const filterRol = ref('TODOS')
const rolOptions = [
  { label: 'Todos', value: 'TODOS' },
  { label: 'Admin', value: 'admin' },
  { label: 'Operador', value: 'operador' },
  { label: 'Consulta', value: 'consulta' },
]
const formRolOptions = [
  { label: 'Administrador', value: 'admin' },
  { label: 'Operador de taller', value: 'operador' },
  { label: 'Auditor / Consulta', value: 'consulta' },
]

async function cargarUsuarios() {
  if (isMock.value) return
  cargando.value = true
  try {
    const r = await usuariosApi.listUsuarios({
      limit: 100,
      offset: 0,
      ...(search.value.trim() ? { q: search.value.trim() } : {}),
      ...(filterRol.value !== 'TODOS' ? { rol: filterRol.value as 'admin' | 'operador' | 'consulta' } : {}),
    })
    usuariosReal.value = r.items ?? []
  } catch {
    usuariosReal.value = []
  } finally {
    cargando.value = false
  }
}

onMounted(() => { void cargarUsuarios() })
watch(isMock, () => { void cargarUsuarios() })

const usuariosDisplay = computed(() => (isMock.value ? usuariosMock.value : usuariosReal.value))

// --- Crear / editar ---
const showFormDialog = ref(false)
const isEditing = ref(false)
const editId = ref<number | null>(null)
const saving = ref(false)
const formNombre = ref('')
const formEmail = ref('')
const formRol = ref('consulta')
const formPassword = ref('')

function openCreate() {
  isEditing.value = false
  editId.value = null
  formNombre.value = ''
  formEmail.value = ''
  formRol.value = 'consulta'
  formPassword.value = ''
  showFormDialog.value = true
}

function openEdit(u: { id: number; nombre: string; email: string; rol: string }) {
  isEditing.value = true
  editId.value = u.id
  formNombre.value = u.nombre
  formEmail.value = u.email
  formRol.value = u.rol
  formPassword.value = ''
  showFormDialog.value = true
}

function extractDetail(e: unknown): string {
  const d = (e as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail
  if (Array.isArray(d)) return d.map((x: unknown) => (x as { msg?: string }).msg ?? JSON.stringify(x)).join('; ')
  if (typeof d === 'string' && d) return d
  if (e instanceof Error && e.message) return e.message
  return 'Operación no completada'
}

async function submitForm() {
  if (!formNombre.value.trim() || !formEmail.value.trim()) {
    showToast('warn', 'Campos requeridos', 'Nombre y email son obligatorios.')
    return
  }
  if (!isEditing.value && formPassword.value.length < 6) {
    showToast('warn', 'Contraseña requerida', 'La contraseña debe tener al menos 6 caracteres.')
    return
  }
  saving.value = true
  try {
    if (isMock.value) {
      if (isEditing.value && editId.value != null) {
        const idx = usuariosMock.value.findIndex((u) => u.id === editId.value)
        if (idx !== -1) {
          usuariosMock.value[idx] = { id: editId.value, nombre: formNombre.value.trim(), email: formEmail.value.trim(), rol: formRol.value }
        }
      } else {
        const nextId = usuariosMock.value.length ? Math.max(...usuariosMock.value.map((u) => u.id)) + 1 : 1
        usuariosMock.value.unshift({ id: nextId, nombre: formNombre.value.trim(), email: formEmail.value.trim(), rol: formRol.value })
      }
      showToast('success', 'Usuario guardado', 'Guardado en lista local (modo MOCK).')
    } else if (isEditing.value && editId.value != null) {
      const payload: usuariosApi.UsuarioUpdate = { nombre: formNombre.value.trim(), email: formEmail.value.trim(), rol: formRol.value }
      if (formPassword.value) payload.password = formPassword.value
      await usuariosApi.updateUsuario(editId.value, payload)
      showToast('success', 'Usuario actualizado', `${formNombre.value.trim()} actualizado.`)
      await cargarUsuarios()
    } else {
      await usuariosApi.createUsuario({ nombre: formNombre.value.trim(), email: formEmail.value.trim(), rol: formRol.value, password: formPassword.value })
      showToast('success', 'Usuario creado', `${formNombre.value.trim()} creado.`)
      await cargarUsuarios()
    }
    showFormDialog.value = false
  } catch (e: unknown) {
    showToast('error', 'Error al guardar', extractDetail(e))
  } finally {
    saving.value = false
  }
}

// --- Desactivar (baja: el backend no tiene campo activo → DELETE) ---
const showDeleteDialog = ref(false)
const deleteTarget = ref<{ id: number; nombre: string } | null>(null)

function askDelete(u: { id: number; nombre: string }) {
  deleteTarget.value = u
  showDeleteDialog.value = true
}

async function confirmDelete() {
  if (!deleteTarget.value) return
  try {
    if (isMock.value) {
      usuariosMock.value = usuariosMock.value.filter((u) => u.id !== deleteTarget.value!.id)
      showToast('info', 'Usuario eliminado', 'Eliminado de la lista local (modo MOCK).')
    } else {
      await usuariosApi.deleteUsuario(deleteTarget.value.id)
      showToast('info', 'Usuario eliminado', `${deleteTarget.value.nombre} dado de baja.`)
      await cargarUsuarios()
    }
    showDeleteDialog.value = false
    deleteTarget.value = null
  } catch (e: unknown) {
    showToast('error', 'Error al eliminar', extractDetail(e))
  }
}

// --- Cambio de contraseña ---
const showPassDialog = ref(false)
const passTarget = ref<{ id: number; nombre: string } | null>(null)
const passCurrent = ref('')
const passNew = ref('')

function openPassword(u: { id: number; nombre: string }) {
  passTarget.value = u
  passCurrent.value = ''
  passNew.value = ''
  showPassDialog.value = true
}

async function submitPassword() {
  if (!passTarget.value) return
  if (passNew.value.length < 6) {
    showToast('warn', 'Contraseña inválida', 'La nueva contraseña debe tener al menos 6 caracteres.')
    return
  }
  if (isMock.value) {
    showToast('success', 'Contraseña actualizada', 'Cambio simulado en modo MOCK.')
    showPassDialog.value = false
    return
  }
  try {
    await usuariosApi.changePassword(passTarget.value.id, { current_password: passCurrent.value, new_password: passNew.value })
    showToast('success', 'Contraseña actualizada', `Contraseña de ${passTarget.value.nombre} actualizada.`)
    showPassDialog.value = false
  } catch (e: unknown) {
    showToast('error', 'Error al actualizar', extractDetail(e))
  }
}

function cambiarRol(rol: 'admin' | 'operador' | 'consulta') {
  auth.changeRole(rol)
  showToast('info', 'Rol Activo Modificado', `Sesión ejecutando ahora como: ${rol.toUpperCase()}`)
}
</script>

<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-stone-800 pb-4">
      <div>
        <h1 class="text-2xl font-serif font-bold text-amber-300 tracking-wide">
          Gestión de Usuarios & Roles de Atelier
        </h1>
        <p class="text-xs text-stone-400 mt-1 font-mono">
          Control de accesos y permisos por rol (Administrador, Operador de Taller, Auditor/Consulta).
        </p>
      </div>
      <div class="flex items-center gap-2">
        <span class="text-xs text-stone-400 font-mono">Cambio rápido de rol:</span>
        <Button
          label="Admin"
          size="small"
          :class="auth.role === 'admin' ? 'p-button-warning' : 'p-button-outlined p-button-secondary'"
          class="text-xs"
          @click="cambiarRol('admin')"
        />
        <Button
          label="Operador"
          size="small"
          :class="auth.role === 'operador' ? 'p-button-warning' : 'p-button-outlined p-button-secondary'"
          class="text-xs"
          @click="cambiarRol('operador')"
        />
        <Button
          label="Consulta"
          size="small"
          :class="auth.role === 'consulta' ? 'p-button-warning' : 'p-button-outlined p-button-secondary'"
          class="text-xs"
          @click="cambiarRol('consulta')"
        />
      </div>
    </div>

    <div class="flex flex-col sm:flex-row items-center justify-between gap-3 bg-stone-900/60 p-3.5 rounded-xl border border-stone-800">
      <div class="flex items-center gap-2 w-full sm:w-auto">
        <InputText v-model="search" placeholder="Buscar por nombre o email..." class="text-xs w-64" @change="cargarUsuarios" />
        <Dropdown v-model="filterRol" :options="rolOptions" option-label="label" option-value="value" class="text-xs w-36" @change="cargarUsuarios" />
      </div>
      <Button label="Nuevo usuario" icon="pi pi-plus" size="small" class="p-button-warning text-xs font-semibold" @click="openCreate" />
    </div>

    <div v-if="isMock" class="rounded-xl border border-amber-500/30 bg-amber-950/20 p-3 text-xs text-amber-200/90 font-mono">
      Modo MOCK: lista local mínima. En modo REAL los datos vienen de <code>GET /api/v1/usuarios</code> (solo admin).
    </div>

    <div v-if="!usuariosDisplay.length" class="text-center py-12 bg-stone-900/40 border border-stone-800 rounded-2xl">
      <i class="pi pi-inbox text-3xl text-stone-500 mb-3 block" />
      <p class="text-sm font-bold text-stone-300">Sin usuarios en modo {{ isMock ? 'MOCK' : 'REAL' }}</p>
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div
        v-for="u in usuariosDisplay"
        :key="u.id"
        class="rounded-xl border border-stone-800 bg-stone-900/40 p-5 flex flex-col justify-between"
      >
        <div>
          <div class="flex items-center justify-between">
            <span class="text-[10px] font-mono px-2 py-0.5 rounded bg-stone-800 uppercase text-amber-300 font-bold">
              {{ u.rol }}
            </span>
            <span class="w-2 h-2 rounded-full bg-emerald-500" />
          </div>
          <div class="font-serif font-bold text-stone-100 text-lg mt-3">{{ u.nombre }}</div>
          <div class="text-xs text-stone-400 font-mono mt-1">{{ u.email }}</div>
        </div>
        <div class="flex items-center gap-1 mt-4 pt-3 border-t border-stone-800">
          <Button icon="pi pi-pencil" size="small" text rounded class="p-button-secondary text-amber-300 hover:bg-stone-800" title="Editar usuario" @click="openEdit(u)" />
          <Button icon="pi pi-key" size="small" text rounded class="p-button-secondary text-stone-300 hover:bg-stone-800" title="Cambiar contraseña" @click="openPassword(u)" />
          <Button icon="pi pi-trash" size="small" text rounded class="p-button-danger text-rose-400 hover:bg-rose-950/40" title="Dar de baja" @click="askDelete(u)" />
        </div>
      </div>
    </div>

    <Dialog v-model:visible="showFormDialog" modal :header="isEditing ? 'Editar usuario' : 'Nuevo usuario'" :style="{ width: '90vw', maxWidth: '440px' }">
      <div class="space-y-3 pt-2 text-xs">
        <div class="flex flex-col gap-1">
          <label class="font-semibold text-stone-300">Nombre *</label>
          <InputText v-model="formNombre" placeholder="Nombre completo" class="text-xs" />
        </div>
        <div class="flex flex-col gap-1">
          <label class="font-semibold text-stone-300">Email *</label>
          <InputText v-model="formEmail" placeholder="usuario@arpia.com.co" class="text-xs" />
        </div>
        <div class="flex flex-col gap-1">
          <label class="font-semibold text-stone-300">Rol *</label>
          <Dropdown v-model="formRol" :options="formRolOptions" option-label="label" option-value="value" class="text-xs w-full" />
        </div>
        <div class="flex flex-col gap-1">
          <label class="font-semibold text-stone-300">{{ isEditing ? 'Nueva contraseña (vacío = no cambia)' : 'Contraseña * (mín. 6)' }}</label>
          <InputText v-model="formPassword" type="password" placeholder="••••••" class="text-xs" />
        </div>
      </div>
      <template #footer>
        <div class="flex items-center justify-end gap-2 pt-3 border-t border-stone-800">
          <Button label="Cancelar" icon="pi pi-times" size="small" class="p-button-text p-button-secondary text-xs" :disabled="saving" @click="showFormDialog = false" />
          <Button label="Guardar" icon="pi pi-check" size="small" class="p-button-warning text-xs font-semibold" :loading="saving" @click="submitForm" />
        </div>
      </template>
    </Dialog>

    <Dialog v-model:visible="showDeleteDialog" modal header="Confirmar baja de usuario" :style="{ width: '90vw', maxWidth: '420px' }">
      <div class="pt-1 text-xs text-stone-200">
        <p>¿Dar de baja a <strong class="text-amber-300">{{ deleteTarget?.nombre }}</strong>? Esta acción no se puede deshacer.</p>
      </div>
      <template #footer>
        <div class="flex items-center justify-end gap-2 pt-2 border-t border-stone-800">
          <Button label="Cancelar" icon="pi pi-times" size="small" class="p-button-text p-button-secondary text-xs" @click="showDeleteDialog = false" />
          <Button label="Dar de baja" icon="pi pi-trash" size="small" class="p-button-danger text-xs font-semibold" @click="confirmDelete" />
        </div>
      </template>
    </Dialog>

    <Dialog v-model:visible="showPassDialog" modal header="Cambiar contraseña" :style="{ width: '90vw', maxWidth: '420px' }">
      <div class="space-y-3 pt-2 text-xs">
        <p class="text-stone-400 font-mono text-[11px]">Usuario: <strong class="text-amber-300">{{ passTarget?.nombre }}</strong>. Si cambiás tu propia contraseña se verifica la actual; para otros usuarios el admin puede indicar cualquiera.</p>
        <div class="flex flex-col gap-1">
          <label class="font-semibold text-stone-300">Contraseña actual</label>
          <InputText v-model="passCurrent" type="password" placeholder="••••••" class="text-xs" />
        </div>
        <div class="flex flex-col gap-1">
          <label class="font-semibold text-stone-300">Nueva contraseña * (mín. 6)</label>
          <InputText v-model="passNew" type="password" placeholder="••••••" class="text-xs" />
        </div>
      </div>
      <template #footer>
        <div class="flex items-center justify-end gap-2 pt-3 border-t border-stone-800">
          <Button label="Cancelar" icon="pi pi-times" size="small" class="p-button-text p-button-secondary text-xs" @click="showPassDialog = false" />
          <Button label="Actualizar" icon="pi pi-check" size="small" class="p-button-warning text-xs font-semibold" @click="submitPassword" />
        </div>
      </template>
    </Dialog>
  </div>
</template>
