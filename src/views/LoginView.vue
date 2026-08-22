<script setup lang="ts">
/**
 * Executive Atelier Login view.
 *
 * Implements Arpía (arpia.com.co) luxury aesthetic:
 * - Haute couture corset & wings emblem with burnished gold gradients
 * - Authentic Colombian slow-fashion atelier branding ("Hecho por Garras Colombianas")
 * - Deep Noir & Velvet Obsidian glassmorphism container
 * - Role-switching chips with gold badges
 * - Robust error handling and session redirect
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

/** Blur-triggered email error: required first, then format */
const emailError = computed(() => {
  if (!emailTouched.value) return ''
  if (form.email.trim() === '') return 'Ingrese su correo electrónico'
  if (!EMAIL_RE.test(form.email)) return 'El correo no es válido'
  return ''
})

/** Blur-triggered password error: required only */
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

function setQuickUser(email: string, pass: string): void {
  form.email = email
  form.password = pass
  emailTouched.value = false
  passwordTouched.value = false
  errorMessage.value = ''
}

async function onSubmit(): Promise<void> {
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
      ? 'Credenciales no autorizadas. Verifique usuario o contraseña.'
      : 'No se pudo conectar con el servidor. Intente nuevamente.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <!-- Atmospheric gold and noir radial lighting -->
    <div class="ambient-glow ambient-glow--gold"></div>
    <div class="ambient-glow ambient-glow--burgundy"></div>

    <div class="login-card">
      <div class="login-header">
        <!-- Luxury Golden Arpía Atelier Crest -->
        <div class="login-brand-icon">
          <svg viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg" class="login-brand-svg">
            <path d="M16 2L5 8V16C5 22.8 9.7 29.2 16 31C22.3 29.2 27 22.8 27 16V8L16 2Z" fill="url(#gold-grad-bg)" fill-opacity="0.2" stroke="url(#gold-grad)" stroke-width="1.6" />
            <!-- Corset / Wings Geometry -->
            <path d="M16 6L11 12H14V22H18V12H21L16 6Z" fill="url(#gold-grad)" />
            <path d="M11 15L7 18M21 15L25 18M11 19L8 22M21 19L24 22" stroke="url(#gold-grad)" stroke-width="1.4" stroke-linecap="round" />
            <defs>
              <linearGradient id="gold-grad" x1="5" y1="2" x2="27" y2="31" gradientUnits="userSpaceOnUse">
                <stop stop-color="#F3E5AB" />
                <stop offset="0.5" stop-color="#C5A059" />
                <stop offset="1" stop-color="#DFB15B" />
              </linearGradient>
              <linearGradient id="gold-grad-bg" x1="5" y1="2" x2="27" y2="31" gradientUnits="userSpaceOnUse">
                <stop stop-color="#DFB15B" stop-opacity="0.3" />
                <stop offset="1" stop-color="#9E7D3B" stop-opacity="0.05" />
              </linearGradient>
            </defs>
          </svg>
        </div>

        <div class="brand-eyebrow-text">ATELIER DE CORSETERÍA & LENCERÍA</div>
        <h1 class="login-title">
          ARPÍA
        </h1>
        <p class="login-motto">« Hecho por Garras Colombianas »</p>
        <div class="header-divider"></div>
        <p class="login-subtitle">Sistema Integrado de Taller, Producción & Finanzas</p>
      </div>

      <Message
        v-if="errorMessage"
        severity="error"
        :closable="false"
        icon="pi pi-exclamation-circle"
        class="login-error"
      >
        {{ errorMessage }}
      </Message>

      <form class="login-form" novalidate @submit.prevent="onSubmit">
        <div class="login-field">
          <label class="login-label" for="login-email">Correo Corporativo</label>
          <div class="input-with-icon">
            <i class="pi pi-envelope field-icon" />
            <InputText
              id="login-email"
              v-model="form.email"
              type="email"
              name="email"
              autocomplete="username"
              placeholder="atelier@arpia.com.co"
              :invalid="emailError !== ''"
              aria-describedby="login-email-error"
              class="w-full pl-9"
              @blur="onEmailBlur"
            />
          </div>
          <p v-if="emailError" id="login-email-error" class="login-field__error">
            {{ emailError }}
          </p>
        </div>

        <div class="login-field">
          <div class="field-label-row">
            <label class="login-label" for="login-password">Contraseña de Seguridad</label>
          </div>
          <div class="input-with-icon">
            <i class="pi pi-lock field-icon" />
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
              class="w-full"
              input-class="w-full pl-9"
              @blur="onPasswordBlur"
            />
          </div>
          <p v-if="passwordError" id="login-password-error" class="login-field__error">
            {{ passwordError }}
          </p>
        </div>

        <Button
          class="login-submit"
          type="submit"
          :loading="loading"
          :disabled="loading"
          label="Ingresar al Atelier"
          icon="pi pi-arrow-right"
          icon-pos="right"
        />

        <!-- Quick Access Switcher for fast evaluation -->
        <div class="quick-access-box">
          <span class="quick-access-title">Perfiles de Demostración:</span>
          <div class="quick-buttons-row">
            <button
              type="button"
              class="quick-pill-btn"
              @click="setQuickUser('admin@arpia.com', 'admin123')"
            >
              <span class="pill-dot pill-dot--gold"></span>
              Admin / Dirección
            </button>
            <button
              type="button"
              class="quick-pill-btn"
              @click="setQuickUser('operador@arpia.com', 'operador123')"
            >
              <span class="pill-dot pill-dot--copper"></span>
              Operador Taller
            </button>
            <button
              type="button"
              class="quick-pill-btn"
              @click="setQuickUser('consulta@arpia.com', 'consulta123')"
            >
              <span class="pill-dot pill-dot--silver"></span>
              Auditor / Finanzas
            </button>
          </div>
        </div>
      </form>

      <div class="login-footer">
        <span class="footer-badge">Pereira, Colombia</span>
        <span class="footer-sep">•</span>
        <span>Moda Lenta & Alta Costura</span>
      </div>
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
  padding: 1.5rem;
  background-color: var(--arpia-dark-bg);
  background-image: radial-gradient(ellipse at 50% 20%, #17161f 0%, #08080a 75%);
  overflow: hidden;
}

.ambient-glow {
  position: absolute;
  border-radius: 50%;
  filter: blur(100px);
  pointer-events: none;
  opacity: 0.18;
}

.ambient-glow--gold {
  width: 550px;
  height: 550px;
  top: 5%;
  left: 20%;
  background: radial-gradient(circle, #dfb15b 0%, rgba(197, 160, 89, 0) 70%);
}

.ambient-glow--burgundy {
  width: 500px;
  height: 500px;
  bottom: 5%;
  right: 20%;
  background: radial-gradient(circle, #9f1239 0%, rgba(159, 18, 57, 0) 70%);
}

.login-card {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 27.5rem;
  padding: 2.5rem 2.25rem;
  background: rgba(19, 19, 24, 0.88);
  border: 1px solid rgba(197, 160, 89, 0.25);
  border-radius: var(--arpia-radius-xl);
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.8), 0 0 30px rgba(197, 160, 89, 0.08);
  backdrop-filter: blur(24px);
}

.login-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  margin-bottom: 1.75rem;
}

.login-brand-icon {
  width: 58px;
  height: 58px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 16px;
  background: rgba(197, 160, 89, 0.08);
  border: 1px solid rgba(197, 160, 89, 0.35);
  box-shadow: 0 0 25px rgba(197, 160, 89, 0.18);
  margin-bottom: 1.1rem;
}

.login-brand-svg {
  width: 36px;
  height: 36px;
}

.brand-eyebrow-text {
  font-family: var(--arpia-font-heading);
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: var(--arpia-primary);
  margin-bottom: 0.25rem;
}

.login-title {
  margin: 0;
  font-family: var(--arpia-font-display);
  font-weight: 800;
  font-size: 2.25rem;
  letter-spacing: 0.18em;
  background: var(--arpia-gold-text);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

.login-motto {
  margin: 0.35rem 0 0;
  font-family: var(--arpia-font-serif);
  font-style: italic;
  font-size: 0.95rem;
  color: var(--arpia-text-regular);
  letter-spacing: 0.03em;
}

.header-divider {
  width: 48px;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(197, 160, 89, 0.5), transparent);
  margin: 0.85rem 0;
}

.login-subtitle {
  margin: 0;
  font-size: 0.8rem;
  color: var(--arpia-text-muted);
}

.login-error {
  margin-bottom: 1.25rem;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 1.1rem;
}

.login-field {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.field-label-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.login-label {
  font-family: var(--arpia-font-heading);
  font-size: 0.76rem;
  font-weight: 600;
  color: var(--arpia-text-regular);
  letter-spacing: 0.02em;
}

.input-with-icon {
  position: relative;
  display: flex;
  align-items: center;
}

.field-icon {
  position: absolute;
  left: 0.85rem;
  color: var(--arpia-primary);
  font-size: 0.85rem;
  pointer-events: none;
  z-index: 2;
  opacity: 0.8;
}

.login-field__error {
  margin: 0.25rem 0 0;
  font-size: 0.72rem;
  color: var(--arpia-danger);
}

.login-submit {
  width: 100%;
  margin-top: 0.5rem;
  padding: 0.8rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  color: #09090b !important;
  background: linear-gradient(135deg, #f3e5ab 0%, #c5a059 60%, #dfb15b 100%) !important;
  border: 1px solid rgba(243, 229, 171, 0.6) !important;
  box-shadow: 0 4px 20px rgba(197, 160, 89, 0.35) !important;
}

.login-submit:hover {
  background: linear-gradient(135deg, #ffffff 0%, #dfb15b 60%, #c5a059 100%) !important;
  box-shadow: 0 6px 25px rgba(197, 160, 89, 0.5) !important;
}

.quick-access-box {
  margin-top: 0.85rem;
  padding: 0.85rem;
  background: rgba(197, 160, 89, 0.03);
  border: 1px solid rgba(197, 160, 89, 0.15);
  border-radius: var(--arpia-radius);
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.quick-access-title {
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--arpia-primary);
  text-align: center;
}

.quick-buttons-row {
  display: flex;
  gap: 0.4rem;
  justify-content: center;
  flex-wrap: wrap;
}

.quick-pill-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(197, 160, 89, 0.2);
  color: var(--arpia-text-regular);
  font-size: 0.72rem;
  font-weight: 500;
  padding: 0.3rem 0.65rem;
  border-radius: 9999px;
  cursor: pointer;
  transition: all 180ms ease;
}

.quick-pill-btn:hover {
  background: rgba(197, 160, 89, 0.15);
  border-color: rgba(197, 160, 89, 0.5);
  color: #fafaf9;
  transform: translateY(-1px);
}

.pill-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.pill-dot--gold { background: #dfb15b; }
.pill-dot--copper { background: #e11d48; }
.pill-dot--silver { background: #38bdf8; }

.login-footer {
  margin-top: 1.75rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  font-size: 0.72rem;
  color: var(--arpia-text-faint);
  letter-spacing: 0.03em;
}

.footer-badge {
  color: var(--arpia-primary);
  font-weight: 600;
}

.footer-sep {
  opacity: 0.4;
}
</style>
