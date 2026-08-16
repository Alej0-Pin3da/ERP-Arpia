import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import es from 'element-plus/es/locale/lang/es'
import 'element-plus/dist/index.css'

import PrimeVue from 'primevue/config'
import ToastService from 'primevue/toastservice'
import ConfirmationService from 'primevue/confirmationservice'
import Tooltip from 'primevue/tooltip'

import App from './App.vue'
import { router } from './router'
import { ArpiaPreset } from './styles/arpia-preset'
import esCO from './utils/locales/es-CO'
import './styles/main.css'

// Initialize the API client singleton (baseURL from VITE_API_BASE_URL,
// Bearer injection + single-flight refresh interceptors).
import '@/api/client'

const app = createApp(App)

// Order matters: Pinia first (the router guard reads the auth store during
// navigation), then the router, then Element Plus with the es locale (es-CO).
app.use(createPinia())
app.use(router)
app.use(ElementPlus, { locale: es })

// Hybrid dual-registration (MIG-2): Element Plus stays registered through
// slice 4; PrimeVue runs alongside from slice 0 with the Arpia dark preset
// (D1/D2 — Aura, 14px-calibrated, dark forced via darkModeSelector 'html'),
// the es-CO locale (BEH-7), and the Toast/ConfirmDialog services consumed
// by the App.vue hosts (D4). v-tooltip directive (D8).
app.use(PrimeVue, {
  theme: { preset: ArpiaPreset, options: { darkModeSelector: 'html' } },
  locale: esCO,
})
app.use(ToastService)
app.use(ConfirmationService)
app.directive('tooltip', Tooltip)

app.mount('#app')
