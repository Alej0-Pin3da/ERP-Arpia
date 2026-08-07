import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import es from 'element-plus/es/locale/lang/es'
import 'element-plus/dist/index.css'

import App from './App.vue'
import { router } from './router'
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

app.mount('#app')
