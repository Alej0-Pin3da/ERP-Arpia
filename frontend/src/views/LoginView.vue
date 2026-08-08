<script setup lang="ts">
/**
 * Login view (task 1.8, spec SHELL-3).
 *
 * Element Plus form (email + password) -> authStore.login -> redirect to the
 * intended route (`?redirect=`, set by the guard) or /dashboard. A 401
 * surfaces inline as incorrect credentials; other failures as a connection
 * message (design refresh-algorithm step 5 wording).
 */
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { FormInstance, FormRules } from 'element-plus'

import { isUnauthorized } from '@/api/errors'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const formRef = ref<FormInstance>()
const loading = ref(false)
const errorMessage = ref('')

const form = reactive({
  email: '',
  password: '',
})

const rules: FormRules = {
  email: [
    { required: true, message: 'Ingrese su correo electrónico', trigger: 'blur' },
    { type: 'email', message: 'El correo no es válido', trigger: 'blur' },
  ],
  password: [{ required: true, message: 'Ingrese su contraseña', trigger: 'blur' }],
}

async function onSubmit(): Promise<void> {
  errorMessage.value = ''
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await authStore.login(form.email, form.password)
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/dashboard'
    await router.push(redirect)
  } catch (err) {
    errorMessage.value = isUnauthorized(err)
      ? 'Correo o contraseña incorrectos'
      : 'No se pudo conectar con el servidor. Intente nuevamente.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <div class="login-card">
      <h1 class="login-title">
        ERP <span class="login-title__gold">Arpia</span>
      </h1>
      <p class="login-eyebrow arpia-eyebrow">Sistema de gestión</p>
      <p class="login-subtitle">Inicie sesión para continuar</p>

      <el-alert
        v-if="errorMessage"
        :title="errorMessage"
        type="error"
        show-icon
        :closable="false"
        class="login-error"
      />

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-position="top"
        size="large"
        @submit.prevent="onSubmit"
      >
        <el-form-item label="Correo electrónico" prop="email">
          <el-input
            v-model="form.email"
            type="email"
            name="email"
            autocomplete="username"
            placeholder="usuario@arpia.com.co"
          />
        </el-form-item>

        <el-form-item label="Contraseña" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            name="password"
            autocomplete="current-password"
            placeholder="••••••••"
            show-password
          />
        </el-form-item>

        <el-button
          class="login-submit"
          type="primary"
          native-type="submit"
          :loading="loading"
          :disabled="loading"
        >
          Iniciar sesión
        </el-button>
      </el-form>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 2rem;
  background: var(--arpia-bg-gradient);
  overflow: hidden;
}

/* Editorial top bar — brand gradient signature. */
.login-page::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: var(--arpia-brand-gradient);
}

/* Soft brand glow behind the card. */
.login-page::after {
  content: '';
  position: absolute;
  width: 560px;
  height: 560px;
  border-radius: 50%;
  background: radial-gradient(
    circle at center,
    rgba(140, 108, 161, 0.28) 0%,
    rgba(41, 151, 170, 0.14) 45%,
    transparent 70%
  );
  filter: blur(20px);
  pointer-events: none;
}

.login-card {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 24rem;
  padding: 2.5rem 2rem;
  background: var(--arpia-card);
  border: 1px solid var(--arpia-border);
  border-radius: 8px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.45);
}

.login-title {
  margin: 0;
  font-family: var(--arpia-font-heading);
  font-weight: 600;
  font-size: 1.75rem;
  text-align: center;
  color: var(--arpia-text-primary);
}

.login-title__gold {
  font-family: var(--arpia-font-heading);
  font-weight: 600;
  color: var(--arpia-gold);
}

.login-eyebrow {
  margin: 0.75rem 0 0;
  text-align: center;
}

.login-subtitle {
  margin: 0.25rem 0 1.5rem;
  color: var(--arpia-text-muted);
  text-align: center;
}

.login-error {
  margin-bottom: 1rem;
}

.login-submit {
  width: 100%;
  margin-top: 0.5rem;
}
</style>
