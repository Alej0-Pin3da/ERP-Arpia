<script setup lang="ts">
/**
 * Usuario form (PR11, spec MOD-5 usuarios) — admin only.
 *
 * Dual-mode PrimeVue form over /usuarios:
 *  - create: POST UsuarioCreate {nombre, email, rol, password} — every field
 *    required; password must be at least 6 chars (backend schema
 *    min_length=6). The password is a secret: never trimmed, shown with the
 *    show-password toggle (Password toggleMask).
 *  - edit: ROL-ONLY — the module's edit action changes just the rol
 *    (prefilled from the row). A self-demote (own rol away from admin) is
 *    rejected server-side with 400 "Cannot change your own role away from
 *    admin" and surfaced by the view.
 *  The view owns the POST/PATCH, the admin-only gate and the refresh.
 */
import { computed, ref, watch } from 'vue'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Password from 'primevue/password'
import Select from 'primevue/select'

import { roleLabel } from '@/utils/menu'
import { showToast } from '@/utils/toast'
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

const rolOptions = computed(() => USUARIO_ROLES.map((r) => ({ label: roleLabel(r), value: r })))

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
      showToast('warn', 'Selecciona el rol.')
      return
    }
    emit('submit', buildUsuarioUpdatePayload(rol.value))
    return
  }

  if (nombre.value.trim() === '') {
    showToast('warn', 'Escribe el nombre del usuario.')
    return
  }
  if (email.value.trim() === '') {
    showToast('warn', 'Escribe el correo del usuario.')
    return
  }
  if (rol.value === null) {
    showToast('warn', 'Selecciona el rol.')
    return
  }
  if (password.value === '') {
    showToast('warn', 'Escribe la contraseña.')
    return
  }
  if (password.value.length < 6) {
    showToast('warn', 'La contraseña debe tener al menos 6 caracteres.')
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
  <form class="usuario-form" @submit.prevent="submit">
    <div class="form-grid">
      <div v-if="mode === 'create'" class="form-col" style="--md: 12">
        <div class="form-item">
          <label class="form-label">Nombre</label>
          <InputText v-model="nombre" placeholder="Ej: María Pérez" data-test="usuario-nombre-input" />
        </div>
      </div>
      <div v-if="mode === 'create'" class="form-col" style="--md: 12">
        <div class="form-item">
          <label class="form-label">Email</label>
          <InputText
            v-model="email"
            type="email"
            placeholder="Ej: maria@arpia.com.co"
            data-test="usuario-email-input"
          />
        </div>
      </div>
      <div class="form-col" style="--md: 12">
        <div class="form-item">
          <label class="form-label">Rol</label>
          <Select
            v-model="rol"
            :options="rolOptions"
            option-label="label"
            option-value="value"
            placeholder="Selecciona el rol"
            class="usuario-field"
            panel-class="usuario-rol-popper"
            data-test="usuario-rol-select"
          />
        </div>
      </div>
      <div v-if="mode === 'create'" class="form-col" style="--md: 12">
        <div class="form-item">
          <label class="form-label">Contraseña</label>
          <Password
            v-model="password"
            :toggle-mask="true"
            :feedback="false"
            placeholder="Mínimo 6 caracteres"
            class="usuario-field"
            data-test="usuario-password-input"
          />
        </div>
      </div>
    </div>
    <div class="submit-row">
      <Button type="submit" :loading="saving" data-test="submit-usuario">
        {{ mode === 'edit' ? 'Guardar cambios' : 'Crear usuario' }}
      </Button>
    </div>
  </form>
</template>

<style scoped>
.usuario-form {
  max-width: 48rem;
}

.usuario-field {
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

.submit-row {
  margin-top: 0.5rem;
}
</style>