/**
 * ConfirmDialog module singleton (task S4-T1, spec BEH-5).
 *
 * Bridges PrimeVue's ConfirmationService — which only exists inside a mounted
 * component (App.vue registers it in setup) — to component code that
 * previously awaited ElMessageBox.confirm. Until the app root registers the
 * live instance, confirmAction() resolves 'reject': a missing host must never
 * perform the destructive action (BEH-5 path), mirroring the user-cancel
 * branch of the old try/catch around ElMessageBox.confirm.
 *
 * Lifecycle: App.vue calls setConfirmInstance(useConfirm()) in its setup
 * before the router renders any view.
 */
import type { ConfirmationOptions } from 'primevue/confirmationoptions'
import type { ConfirmationServiceMethods } from 'primevue/confirmationservice'

export interface ConfirmActionOptions {
  /** Body text of the confirmation dialog. */
  message: string
  /** Header title of the confirmation dialog. */
  header?: string
  /** Label of the accept button (defaults to the PrimeVue locale). */
  acceptLabel?: string
  /** Label of the reject button (defaults to the PrimeVue locale). */
  rejectLabel?: string
}

let confirmInstance: ConfirmationServiceMethods | null = null

/** Register the live ConfirmationService instance captured from the app root. */
export function setConfirmInstance(instance: ConfirmationServiceMethods): void {
  confirmInstance = instance
}

/**
 * Ask the user to confirm a destructive action. Resolves 'reject' (no action)
 * until setConfirmInstance() has been called.
 *
 * @param opts message + optional header and accept/reject labels
 * @returns 'accept' when the user confirms, 'reject' on cancel or missing host
 */
export function confirmAction(opts: ConfirmActionOptions): Promise<'accept' | 'reject'> {
  return new Promise((resolve) => {
    if (!confirmInstance) {
      resolve('reject')
      return
    }
    const options: ConfirmationOptions = {
      message: opts.message,
      header: opts.header,
      acceptLabel: opts.acceptLabel,
      rejectLabel: opts.rejectLabel,
      accept: () => resolve('accept'),
      reject: () => resolve('reject'),
    }
    confirmInstance.require(options)
  })
}
