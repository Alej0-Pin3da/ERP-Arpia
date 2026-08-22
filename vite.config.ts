import { fileURLToPath, URL } from 'node:url'
import type { Plugin } from 'vite'
import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vitest/config'
import { handleMockApiRequest } from './src/server/mockApi'

function mockApiPlugin(): Plugin {
  return {
    name: 'mock-api-middleware',
    configureServer(server) {
      server.middlewares.use(async (req, res, next) => {
        const url = req.url || ''
        if (url.startsWith('/api/v1') || url.startsWith('/api/')) {
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
        }
        next()
      })
    },
  }
}

// https://vite.dev/config/
export default defineConfig({
  base: '/',
  plugins: [vue(), mockApiPlugin()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./tests/setup.ts'],
  },
})

