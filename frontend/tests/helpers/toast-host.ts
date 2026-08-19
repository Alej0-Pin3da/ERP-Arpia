/**
 * Test helper: fake PrimeVue <Toast/> host for the toast.ts module singleton
 * (design D4, BEH-2/BEH-5).
 *
 * Component specs mount views/forms that call showToast(); without a live
 * ToastService instance the singleton is a safe no-op and message assertions
 * on document.body would fail. This helper registers a fake host whose add()
 * appends the message text to <body> — the same surface ElMessage used when it
 * teleported messages there — so `expect(document.body.textContent)
 * .toContain('...')` assertions keep working after the ElMessage sweep
 * (slice 4a).
 */
import type { ToastMessageOptions } from 'primevue/toast'
import type { ToastServiceMethods } from 'primevue/toastservice'

import { setToastInstance } from '@/utils/toast'

const toastMessages: HTMLElement[] = []

/** Register a fake Toast host that renders messages into <body>. */
export function mountToastHost(): void {
  setToastInstance({
    add: (message: ToastMessageOptions) => {
      const el = document.createElement('div')
      el.className = 'p-toast-message'
      el.textContent = [message.summary, message.detail].filter(Boolean).join(' ')
      document.body.appendChild(el)
      toastMessages.push(el)
    },
  } as unknown as ToastServiceMethods)
}

/** Remove the fake toast nodes appended by mountToastHost(). */
export function clearToastHost(): void {
  toastMessages.forEach((el) => el.remove())
  toastMessages.length = 0
}
