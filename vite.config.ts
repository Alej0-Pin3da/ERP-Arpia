import { fileURLToPath, URL } from 'node:url'
import type { Plugin } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'
import { defineConfig } from 'vitest/config'
import { handleMockApiRequest } from './src/server/mockApi'

// Resolve whether the in-memory mock should handle /api in Vite dev server.
// Mirrors server.ts logic: explicit USE_MOCK=false or external VITE_API_BASE_URL or API_PROXY_TARGET => REAL.
function isExternalBaseUrl(url: string): boolean {
  return Boolean(url && (url.includes('http') || url.includes(':8000') || url.includes('backend')))
}

function shouldUseMock(): boolean {
  const rawUseMock = process.env.USE_MOCK
  if (rawUseMock === 'false') return false
  if (rawUseMock === 'true') return true
  const viteBase = (process.env.VITE_API_BASE_URL || '').trim()
  const proxyTarget = (process.env.API_PROXY_TARGET || '').trim()
  if (proxyTarget) return false
  if (isExternalBaseUrl(viteBase)) return false
  return true
}

function mockApiPlugin(): Plugin {
  return {
    name: 'mock-api-middleware',
    configureServer(server) {
      server.middlewares.use(async (req, res, next) => {
        const url = req.url || ''

        // Only intercept /api routes
        if (!(url.startsWith('/api/v1') || url.startsWith('/api/'))) {
          next()
          return
        }

        // Conditional: if mock is disabled, let Vite proxy / browser fetch reach the real backend
        if (!shouldUseMock()) {
          next()
          return
        }

        let body: Record<string, unknown> = {}
        if (['POST', 'PUT', 'PATCH'].includes(req.method || '')) {
          const chunks: Buffer[] = []
          for await (const chunk of req) {
            chunks.push(typeof chunk === 'string' ? Buffer.from(chunk) : chunk)
          }
          const rawBody = Buffer.concat(chunks).toString('utf-8')
          try {
            body = JSON.parse(rawBody)
          } catch {
            body = {}
          }
        }

        const urlObj = new URL(url, 'http://localhost')
        const queryParams: Record<string, unknown> = {}
        urlObj.searchParams.forEach((v, k) => {
          queryParams[k] = v
        })

        const result = handleMockApiRequest(
          req.method || 'GET',
          urlObj.pathname,
          body,
          queryParams,
          req.headers as Record<string, unknown>,
        )

        res.statusCode = result.status
        res.setHeader('Content-Type', 'application/json')
        res.end(JSON.stringify(result.data))
        return
      })
    },
  }
}

// Computed once at config load — also feeds Vite's proxy when mock is off
const useMockAtConfig = shouldUseMock()
const viteProxyTarget = (process.env.API_PROXY_TARGET || 'http://localhost:8000').replace(/\/$/, '')

// https://vite.dev/config/
export default defineConfig({
  base: '/',
  plugins: [vue(), tailwindcss(), mockApiPlugin()],
  build: {
    chunkSizeWarningLimit: 600,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['vue', 'vue-router', 'pinia'],
          primevue: ['primevue'],
        },
      },
    },
  },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: useMockAtConfig
    ? undefined
    : {
        proxy: {
          '/api': {
            target: viteProxyTarget,
            changeOrigin: true,
          },
        },
      },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./tests/setup.ts'],
  },
})
