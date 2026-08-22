<script setup lang="ts">
import { ref } from 'vue'
import Button from 'primevue/button'
import { useAuthStore } from '@/stores/auth'
import { showToast } from '@/utils/toast'

const auth = useAuthStore()

const usuarios = ref([
  { id: 1, nombre: 'Valeria Arpía', email: 'admin@arpia.com.co', rol: 'admin', cargo: 'Directora Creativa & Socia', activo: true },
  { id: 2, nombre: 'Camila Modista', email: 'taller@arpia.com.co', rol: 'operador', cargo: 'Jefa de Taller & Patronista', activo: true },
  { id: 3, nombre: 'Elena Inversionista', email: 'socia@arpia.com.co', rol: 'consulta', cargo: 'Socia Auditora', activo: true },
])

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

    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div
        v-for="u in usuarios"
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
          <div class="text-xs text-stone-300 mt-2">{{ u.cargo }}</div>
        </div>
      </div>
    </div>
  </div>
</template>
