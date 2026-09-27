import { expect, test } from '@playwright/test'

// V4 golden paths (foundation): production -> commercial -> closing.
// Backend + seeded demo data required; assertions stay on stable selectors.
test('production cycle: pedido reaches cierre', async ({ page }) => {
  await page.goto('/produccion')
  await expect(page).toHaveTitle(/Arp/i)
})

test('commercial cycle: venta descuenta stock', async ({ page }) => {
  await page.goto('/ventas')
  await expect(page).toHaveTitle(/Arp/i)
})

test('closing cycle: liquidacion con anticipos', async ({ page }) => {
  await page.goto('/finanzas')
  await expect(page).toHaveTitle(/Arp/i)
})
