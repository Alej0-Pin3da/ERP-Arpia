<script setup lang="ts">
/**
 * Usuario form (PR11, spec MOD-5 usuarios) — admin only.
 *
 * Dual-mode Element Plus form over /usuarios:
 *  - create: POST UsuarioCreate {nombre, email, rol, password} — every field
 *    required; password must be at least 6 chars (backend schema
 *    min_length=6). The password is a secret: never trimmed, shown with the
 *    show-password toggle.
 *  - edit: ROL-ONLY — the module's edit action changes just the rol
 *    (prefilled from the row). A self-demote (own rol away from admin) is
 *    rejected server-side with 400 "Cannot change your own role away from
 *    admin" and surfaced by the view.
 *  The view owns the POST/PATCH, the admin-only gate and the refresh.
 */
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'

import { roleLabel } from '@/utils/menu'
import {
  buildUsuarioPayload,
  buildUsuarioUpdatePayload,
  USUARIO_ROLES,
} from '@/utils/usuarios'
import type { UsuarioCreate, UsuarioRead, UsuarioUpdate } from '@/types/api.d'

const props = defineProps<{
  mode: 'create' | 'edit'
  /** The row being edited — prefills the rol select in edit mode. */
  initial?: UsuarioRead | null
  /** True while the parent is POSTing/PATCHing — disables the submit button. */
  saving?: boolean
}>()

const emit = defineEmits<{ submit: [payload: UsuarioCreate | UsuarioUpdate] }>()

const nombre = ref('')
const email = ref('')
const rol = ref<string | null>(null)
const password = ref('')

/** Edit mode prefills the rol (the only editable field). */
watch(
  () => props.initial,
  (user) => {
    if (user) {
      nombre.value = user.nombre
      email.value = user.email
      rol.value = user.rol
    }
  },
  { immediate: true },
)

function submit(): void {
  if (props.mode === 'edit') {
    if (rol.value === null) {
      ElMessage.warning('Selecciona el rol.')
      return
    }
    emit('submit', buildUsuarioUpdatePayload(rol.value))
    return
  }

  if (nombre.value.trim() === '') {
    ElMessage.warning('Escribe el nombre del usuario.')
    return
  }
  if (email.value.trim() === '') {
    ElMessage.warning('Escribe el correo del usuario.')
    return
  }
  if (rol.value === null) {
    ElMessage.warning('Selecciona el rol.')
    return
  }
  if (password.value === '') {
    ElMessage.warning('Escribe la contraseña.')
    return
  }
  if (password.value.length < 6) {
    ElMessage.warning('La contraseña debe tener al menos 6 caracteres.')
    return
  }
  emit(
    'submit',
    buildUsuarioPayload({
      nombre: nombre.value,
      email: email.value,
      rol: rol.value,
      password: password.value,
    }),
  )
}
</script>

<template>
  <el-form label-position="top" class="usuario-form" @submit.prevent="submit">
    <el-row :gutter="16">
      <el-col v-if="mode === 'create'" :xs="24" :md="12">
        <el-form-item label="Nombre">
          <el-input v-model="nombre" placeholder="Ej: María Pérez" data-test="usuario-nombre-input" />
        </el-form-item>
      </el-col>
      <el-col v-if="mode === 'create'" :xs="24" :md="12">
        <el-form-item label="Email">
          <el-input
            v-model="email"
            type="email"
            placeholder="Ej: maria@arpia.com.co"
            data-test="usuario-email-input"
          />
        </el-form-item>
      </el-col>
      <el-col :xs="24" :md="12">
        <el-form-item label="Rol">
          <el-select
            v-model="rol"
            placeholder="Selecciona el rol"
            class="usuario-field"
            popper-class="usuario-rol-popper"
            data-test="usuario-rol-select"
          >
            <el-option v-for="r in USUARIO_ROLES" :key="r" :label="roleLabel(r)" :value="r" />
          </el-select>
        </el-form-item>
      </el-col>
      <el-col v-if="mode === 'create'" :xs="24" :md="12">
        <el-form-item label="Contraseña">
          <el-input
            v-model="password"
            type="password"
            show-password
            placeholder="Mínimo 6 caracteres"
            data-test="usuario-password-input"
          />
        </el-form-item>
      </el-col>
    </el-row>
    <el-button type="primary" native-type="submit" :loading="saving" data-test="submit-usuario">
      {{ mode === 'edit' ? 'Guardar cambios' : 'Crear usuario' }}
    </el-button>
  </el-form>
</template>

<style scoped>
.usuario-form {
  max-width: 48rem;
}

.usuario-field {
  width: 100%;
}
</style>
