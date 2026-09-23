/**
 * Print helper with dynamic `@page` sizing and single active document.
 *
 * Static `@page` rules cannot be scoped per document: once any component's
 * print CSS is loaded in the SPA, its `@page` would leak into every other
 * print (e.g. the 80mm thermal size shrinking an A4 receipt). Components
 * therefore keep only visibility isolation in static CSS, while the page
 * size is injected dynamically right before printing: the injected <style>
 * is appended last to <head> so it wins, and it is removed on `afterprint`.
 *
 * The global print CSS reveals ONLY the active document
 * (`body[data-print-active="<id>"] #<id>`). This matters because several
 * print areas can coexist in the DOM: e.g. in Finanzas the `#print-balance`
 * page root is always rendered and `#print-acta-liquidacion` persists while
 * its object is set, even with the modal closed. Revealing all of them at
 * once used to stack overlapping documents across pages. Every caller must
 * therefore pass its own print-area id.
 */
export function printWithPage(pageRule: string, activeId: string): void {
  if (typeof window === 'undefined' || typeof document === 'undefined') return
  document.getElementById('dynamic-print-page')?.remove()
  const style = document.createElement('style')
  style.id = 'dynamic-print-page'
  style.textContent = `@page{${pageRule}}`
  document.head.appendChild(style)
  document.body.dataset.printActive = activeId
  const cleanup = () => {
    style.remove()
    delete document.body.dataset.printActive
    window.removeEventListener('afterprint', cleanup)
  }
  window.addEventListener('afterprint', cleanup)
  try {
    window.print()
  } catch {
    cleanup()
  }
  // Fallback: never leave a stale @page behind if afterprint misfires.
  window.setTimeout(() => {
    document.getElementById('dynamic-print-page')?.remove()
    delete document.body.dataset.printActive
  }, 60_000)
}

/** Standard A4 document (receipts, actas, balances). */
export function printDocument(activeId: string): void {
  printWithPage('size:A4;margin:12mm', activeId)
}

/** 80mm continuous thermal roll (garment tags). */
export function printThermal80mm(activeId = 'luxury-garment-tag'): void {
  printWithPage('size:80mm auto;margin:0', activeId)
}
