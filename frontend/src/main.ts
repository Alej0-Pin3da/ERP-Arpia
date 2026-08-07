import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import es from 'element-plus/es/locale/lang/es'
import 'element-plus/dist/index.css'

import App from './App.vue'
import './styles/main.css'

// Initialize the API client singleton (baseURL from VITE_API_BASE_URL,
// Bearer injection + single-flight refresh interceptors). The auth store
// (PR3) will drive session state through storage.
import '@/api/client'

const app = createApp(App)

app.use(createPinia())
// Element Plus with the es locale (es-CO UX). Router is wired here in
// task 1.6 (router + guards) — PR3 of the frontend-dashboard change.
app.use(ElementPlus, { locale: es })

app.mount('#app')
