// @ts-nocheck — optional dep: installed only when running `npm run test:e2e`.
import { defineConfig, devices } from '@playwright/test'

// V4 Eje 4.1 foundation: golden-path E2E scaffold (production, commercial,
// closing cycles). Requires: backend up + `npx playwright install`.
// Run with `npm run test:e2e`. Not part of `npm test` (vitest).
export default defineConfig({
  testDir: './e2e',
  testMatch: '**/*.playwright.ts',
  fullyParallel: true,
  reporter: 'list',
  use: {
    baseURL: process.env.E2E_BASE_URL || 'http://localhost:5173',
    trace: 'on-first-retry',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
})
