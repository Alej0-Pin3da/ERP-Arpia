/**
 * Toast module singleton (task S0-T4, spec BEH-2).
 *
 * Bridges PrimeVue's ToastService — which only exists inside a mounted
 * component (App.vue registers it in setup) — to non-component code such as
 * the axios 403 interceptor in client.ts. Until the app root registers the
 * live instance, showToast() is a safe no-op (BEH-2 path), so early API
 * errors never crash on a missing service.
 *
 * Lifecycle: App.vue calls setToastInstance(useToast()) in its setup before
 * the router renders any view; client.ts imports showToast() only.
 */
import type { ToastMessageOptions } from 'primevue/toast'
import type { ToastServiceMethods } from 'primevue/toastservice'

let toastInstance: ToastServiceMethods | null = null

/** Register the live ToastService instance captured from the app root. */
export function setToastInstance(instance: ToastServiceMethods): void {
  toastInstance = instance
}

/**
 * Show a toast message. No-op until setToastInstance() has been called.
 *
 * @param severity success | info | warn | error (BEH-2 message mapping)
 * @param summary title of the message
 * @param detail body of the message
 * @param life auto-dismiss delay in milliseconds (default 3000)
 */
export function showToast(
  severity: NonNullable<ToastMessageOptions['severity']>,
  summary: string,
  detail?: string,
  life = 3000,
): void {
  toastInstance?.add({ severity, summary, detail, life })
}