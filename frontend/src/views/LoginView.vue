<script setup lang="ts">
/**
 * Login view (task 1.8, spec SHELL-3).
 *
 * Manual validation (D7/BEH-3): blur-triggered checks for email
 * required/type and password required, with the exact current messages
 * ("Ingrese su correo electrónico", "El correo no es válido", "Ingrese su
 * contraseña"); submission is blocked while the form is invalid. A 401
 * surfaces inline as incorrect credentials via a PrimeVue Message
 * (el-alert -> Message); other failures as a connection message.
 */
import { computed, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Message from 'primevue/message'
import Password from 'primevue/password'

import { isUnauthorized } from '@/api/errors'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const loading = ref(false)
const errorMessage = ref('')
const emailTouched = ref(false)
const passwordTouched = ref(false)

const form = reactive({
  email: '',
  password: '',
})

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

/** Blur-triggered email error: required first, then format (BEH-3). */
const emailError = computed(() => {
  if (!emailTouched.value) return ''
  if (form.email.trim() === '') return 'Ingrese su correo electrónico'
  if (!EMAIL_RE.test(form.email)) return 'El correo no es válido'
  return ''
})

/** Blur-triggered password error: required only (BEH-3). */
const passwordError = computed(() => {
  if (!passwordTouched.value) return ''
  if (form.password === '') return 'Ingrese su contraseña'
  return ''
})

const invalid = computed(() => emailError.value !== '' || passwordError.value !== '')

function onEmailBlur(): void {
  emailTouched.value = true
}

function onPasswordBlur(): void {
  passwordTouched.value = true
}

async function onSubmit(): Promise<void> {
  // Touching both fields on submit surfaces every error at once; the request
  // is blocked while any field is invalid (BEH-3).
  emailTouched.value = true
  passwordTouched.value = true
  if (invalid.value) return

  errorMessage.value = ''
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

      <Message
        v-if="errorMessage"
        severity="error"
        :closable="false"
        icon="pi pi-times-circle"
        class="login-error"
      >
        {{ errorMessage }}
      </Message>

      <form class="login-form" novalidate @submit.prevent="onSubmit">
        <div class="login-field">
          <label class="login-label" for="login-email">Correo electrónico</label>
          <InputText
            id="login-email"
            v-model="form.email"
            type="email"
            name="email"
            autocomplete="username"
            placeholder="usuario@arpia.com.co"
            :invalid="emailError !== ''"
            aria-describedby="login-email-error"
            @blur="onEmailBlur"
          />
          <p v-if="emailError" id="login-email-error" class="login-field__error">
            {{ emailError }}
          </p>
        </div>

        <div class="login-field">
          <label class="login-label" for="login-password">Contraseña</label>
          <Password
            id="login-password"
            v-model="form.password"
            name="password"
            autocomplete="current-password"
            placeholder="••••••••"
            :toggle-mask="true"
            :feedback="false"
            :invalid="passwordError !== ''"
            aria-describedby="login-password-error"
            @blur="onPasswordBlur"
          />
          <p v-if="passwordError" id="login-password-error" class="login-field__error">
            {{ passwordError }}
          </p>
        </div>

        <Button
          class="login-submit"
          type="submit"
          :loading="loading"
          :disabled="loading"
          label="Iniciar sesión"
        />
      </form>
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

.login-form {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.login-field {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.login-field__error {
  margin: 0;
  font-size: 0.8rem;
  color: var(--arpia-danger);
}

.login-submit {
  width: 100%;
  margin-top: 0.5rem;
}
</style>