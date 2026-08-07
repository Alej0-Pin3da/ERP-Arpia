import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import es from 'element-plus/es/locale/lang/es'
import 'element-plus/dist/index.css'

import App from './App.vue'
import './styles/main.css'

const app = createApp(App)

app.use(createPinia())
// Element Plus with the es locale (es-CO UX). Router is wired here in
// task 1.6 (router + guards) — PR3 of the frontend-dashboard change.
app.use(ElementPlus, { locale: es })

app.mount('#app')
