import express from 'express'
import cors from 'cors'
import path from 'path'
import { fileURLToPath } from 'url'
import { createServer as createViteServer } from 'vite'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

const app = express()
const PORT = Number(process.env.PORT) || 3000

// --- REAL-only backend proxy ---
// Every /api request is proxied to the FastAPI backend. There is no
// in-memory mock DB anymore. Required backend: FastAPI listening on
// API_PROXY_TARGET (default http://localhost:8000).
// NOTE: USE_MOCK is no longer read — the server always proxies.
const proxyTarget = ((process.env.API_PROXY_TARGET || '').trim() || 'http://localhost:8000').replace(/\/$/, '')

app.use(cors())
app.use(express.json())

// --- API proxy (real backend) using native fetch (Node 20+) ---
async function apiProxyMiddleware(
  req: express.Request,
  res: express.Response,
): Promise<void> {
  const targetUrl = `${proxyTarget}${req.originalUrl}`
  try {
    const headers: Record<string, string> = {}
    for (const [k, v] of Object.entries(req.headers)) {
      if (!v) continue
      if (k.toLowerCase() === 'host' || k.toLowerCase() === 'connection') continue
      if (Array.isArray(v)) headers[k] = v.join(', ')
      else if (typeof v === 'string') headers[k] = v
    }
    // Let fetch set content-length / host correctly
    delete headers['content-length']
    delete headers['Content-Length']

    const fetchOpts: RequestInit & { duplex?: string } = {
      method: req.method,
      headers,
    }

    if (req.method !== 'GET' && req.method !== 'HEAD') {
      const hasBody = req.body !== undefined && req.body !== null
      const isJsonContent =
        typeof req.headers['content-type'] === 'string' &&
        String(req.headers['content-type']).includes('application/json')
      if (hasBody) {
        if (isJsonContent || (typeof req.body === 'object' && !(req.body instanceof Buffer))) {
          // Express json parser already produced an object
          const isEmptyObject =
            typeof req.body === 'object' &&
            !Array.isArray(req.body) &&
            Object.keys(req.body as Record<string, unknown>).length === 0
          if (!isEmptyObject) {
            fetchOpts.body = JSON.stringify(req.body)
            if (!headers['content-type'] && !headers['Content-Type']) {
              ;(fetchOpts.headers as Record<string, string>)['content-type'] = 'application/json'
            }
          }
        } else if (typeof req.body === 'string') {
          fetchOpts.body = req.body
        } else if (req.body instanceof Buffer) {
          fetchOpts.body = req.body as unknown as BodyInit
        } else {
          fetchOpts.body = JSON.stringify(req.body)
        }
        // Required for Node fetch with streaming body
        if (fetchOpts.body !== undefined) (fetchOpts as { duplex?: string }).duplex = 'half'
      }
    }

    const proxyRes = await fetch(targetUrl, fetchOpts as RequestInit)

    res.status(proxyRes.status)
    proxyRes.headers.forEach((value, key) => {
      const lower = key.toLowerCase()
      if (['transfer-encoding', 'content-encoding', 'content-length', 'connection'].includes(lower))
        return
      res.setHeader(key, value)
    })

    const buf = Buffer.from(await proxyRes.arrayBuffer())
    // Preserve empty 204
    if (proxyRes.status === 204 || buf.length === 0) {
      res.end()
      return
    }
    res.send(buf)
  } catch (err) {
    console.error(`[proxy] failed ${req.method} ${req.originalUrl} -> ${targetUrl}:`, err)
    res.status(502).json({
      detail: 'Bad gateway: unable to reach backend',
      target: proxyTarget,
      error: String((err as Error)?.message || err),
    })
  }
}

// Mode probe — always REAL (kept for ApiModeBadge compat)
app.get('/api/__mode', (_req, res) => {
  res.json({
    mode: 'real',
    proxyTarget,
    time: new Date().toISOString(),
  })
})

// Proxy all /api traffic to the real FastAPI backend
app.use('/api', apiProxyMiddleware)

// Vite & Static Asset Handling
async function start() {
  if (process.env.NODE_ENV !== 'production') {
    const vite = await createViteServer({
      server: {
        middlewareMode: true,
        host: '0.0.0.0',
        port: PORT,
      },
      appType: 'spa',
    })
    app.use(vite.middlewares)
  } else {
    const distPath = __dirname.endsWith('dist') ? __dirname : path.resolve(process.cwd(), 'dist')
    app.use(express.static(distPath))
    app.get('*', (_req, res) => {
      res.sendFile(path.join(distPath, 'index.html'))
    })
  }

  app.listen(PORT, '0.0.0.0', () => {
    console.log(
      `ERP Arpía server listening on http://0.0.0.0:${PORT} — proxying /api to ${proxyTarget}`,
    )
  })
}

start().catch((err) => {
  console.error('Failed to start server:', err)
  process.exit(1)
})
