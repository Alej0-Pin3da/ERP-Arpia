<script setup lang="ts">
/**
 * SPA shell — renders the active route through <router-view>.
 * The persistent layout (header + role-aware sidebar) is AppLayout (PR4);
 * the router wraps every authenticated route as its child, so /login stays
 * standalone and everything else renders inside the shell.
 *
 * D4 — Toast/ConfirmDialog hosts live at the true app root (not AppLayout):
 * the 403 interceptor in client.ts can fire before the shell mounts (e.g. on
 * /login), so the hosts must exist for the whole app lifetime. The captured
 * ToastService instance is handed to the toast.ts module singleton so
 * non-component code can call showToast() (BEH-2); ConfirmDialog needs no
 * module capture — client code uses useConfirm() where a choice is required.
 */
import Toast from 'primevue/toast'
import ConfirmDialog from 'primevue/confirmdialog'
import { useToast } from 'primevue/usetoast'

import { setToastInstance } from '@/utils/toast'

setToastInstance(useToast())
</script>

<template>
  <Toast position="top-right" />
  <ConfirmDialog />
  <router-view />
</template>