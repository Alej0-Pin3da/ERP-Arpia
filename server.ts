import express from 'express'
import cors from 'cors'
import path from 'path'
import { fileURLToPath } from 'url'
import { createServer as createViteServer } from 'vite'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

const app = express()
const PORT = Number(process.env.PORT) || 3000

// --- Mock / Proxy mode resolution ---
// USE_MOCK=false forces real backend proxy.
// API_PROXY_TARGET set also forces proxy (even if USE_MOCK not set).
// VITE_API_BASE_URL external (http / :8000 / backend) also forces proxy.
// Explicit USE_MOCK=true always enables mock and ignores proxy/external hints.
const VITE_API_BASE_URL_ENV = (process.env.VITE_API_BASE_URL || '').trim()
const API_PROXY_TARGET_RAW = (process.env.API_PROXY_TARGET || '').trim()
const ENVIRONMENT_ENV = (process.env.ENVIRONMENT || process.env.NODE_ENV || 'development').trim()
const isExternalApiBaseUrl = Boolean(
  VITE_API_BASE_URL_ENV &&
    (VITE_API_BASE_URL_ENV.includes('http') ||
      VITE_API_BASE_URL_ENV.includes(':8000') ||
      VITE_API_BASE_URL_ENV.includes('backend')),
)
const hasProxyTarget = Boolean(API_PROXY_TARGET_RAW)

function resolveUseMock(): boolean {
  if (process.env.USE_MOCK === 'false') return false
  if (process.env.USE_MOCK === 'true') return true
  if (hasProxyTarget) return false
  if (isExternalApiBaseUrl) return false
  // In production without explicit USE_MOCK but with proxy config, prefer proxy (already handled above)
  void ENVIRONMENT_ENV
  return true
}

const useMock = resolveUseMock()
const proxyTarget = (API_PROXY_TARGET_RAW || 'http://localhost:8000').replace(/\/$/, '')

app.use(cors())
app.use(express.json())

// --- In-Memory Database Store ---

interface User {
  id: number
  nombre: string
  email: string
  password_hash?: string
  rol: 'admin' | 'operativo' | 'visor'
  activo: boolean
  created_at: string
}

interface CategoriaInsumo {
  id: number
  nombre: string
  descripcion?: string
  created_at: string
}

interface Insumo {
  id: number
  nombre: string
  codigo?: string
  categoria_id: number
  unidad_medida: string
  stock_actual: number
  stock_minimo: number
  costo_unitario: number
  costo_promedio_ponderado: number
  ultimo_costo_compra: number
  proveedor_id?: number | null
  created_at: string
}

interface CompraInsumo {
  id: number
  insumo_id: number
  cantidad: number
  costo_unitario: number
  costo_total: number
  fecha_compra: string
  factura?: string | null
  proveedor_id?: number | null
  modo?: string
  created_at: string
}

interface Cliente {
  id: number
  nombre: string
  documento?: string
  telefono?: string
  email?: string
  direccion?: string
  ciudad?: string
  created_at: string
}

interface TipoProducto {
  id: number
  nombre: string
  descripcion?: string
  created_at: string
}

interface Variante {
  id: number
  producto_id: number
  talla: string
  sku: string
  precio_override?: number | null
  stock_actual: number
  created_at: string
}

interface BomInsumo {
  id: number
  producto_id: number
  insumo_id: number
  cantidad_requerida: number
  desperdicio_pct: number
  created_at: string
}

interface BomProducto {
  id: number
  producto_padre_id: number
  producto_hijo_id: number
  cantidad: number
  created_at: string
}

interface Producto {
  id: number
  nombre: string
  sku_base: string
  tipo_producto_id: number
  precio_base: number
  descripcion?: string
  activo: boolean
  created_at: string
}

interface VentaItem {
  id: number
  venta_id: number
  producto_id: number
  variante_id?: number | null
  cantidad: number
  precio_unitario: number
  subtotal: number
}

interface Venta {
  id: number
  codigo: string
  fecha: string
  cliente_id?: number | null
  total: number
  descuento: number
  estado: 'completada' | 'anulada' | 'pendiente'
  canal: string
  es_regalo: boolean
  observaciones?: string
  items: VentaItem[]
  created_at: string
}

interface Devolucion {
  id: number
  venta_id: number
  fecha: string
  motivo: string
  monto: number
  estado: string
  created_at: string
}

interface Socio {
  id: number
  nombre: string
  email?: string
  telefono?: string
  participacion_pct: number
  activo: boolean
  created_at: string
}

interface MovimientoFinanciero {
  id: number
  fecha: string
  tipo: 'ingreso' | 'gasto' | 'inversion' | 'retiro'
  categoria: string
  descripcion: string
  monto: number
  socio_id?: number | null
  es_liquidacion?: boolean
  created_at: string
}

interface Omision {
  id: number
  fase: string
  nivel: string
  hoja: string
  fila?: number
  descripcion: string
  resuelta: boolean
  created_at: string
}

// Initial Data
const users: User[] = [
  {
    id: 1,
    nombre: 'Administrador Arpía',
    email: 'admin@arpia.com',
    rol: 'admin',
    activo: true,
    created_at: new Date('2026-01-01').toISOString(),
  },
  {
    id: 2,
    nombre: 'Operador Taller',
    email: 'operador@arpia.com',
    rol: 'operador',
    activo: true,
    created_at: new Date('2026-01-10').toISOString(),
  },
  {
    id: 3,
    nombre: 'Auditor Financiero',
    email: 'consulta@arpia.com',
    rol: 'consulta',
    activo: true,
    created_at: new Date('2026-02-01').toISOString(),
  },
]

const categoriasInsumos: CategoriaInsumo[] = [
  { id: 1, nombre: 'Telas', descripcion: 'Telas licradas, encajes y sedas', created_at: new Date().toISOString() },
  { id: 2, nombre: 'Herrajes', descripcion: 'Ganchos, argollas, ochos y varillas', created_at: new Date().toISOString() },
  { id: 3, nombre: 'Empaques', descripcion: 'Bolsas, cajas, cintas y tarjetas', created_at: new Date().toISOString() },
  { id: 4, nombre: 'Químicos & Tintes', descripcion: 'Tintas, fijadores y adhesivos', created_at: new Date().toISOString() },
]

const insumos: Insumo[] = [
  { id: 1, nombre: 'Seda Satín Negro', codigo: 'INS-TEL-001', categoria_id: 1, unidad_medida: 'm', stock_actual: 45.5, stock_minimo: 10, costo_unitario: 18500, costo_promedio_ponderado: 18000, ultimo_costo_compra: 18500, created_at: new Date().toISOString() },
  { id: 2, nombre: 'Encaje Francés Rojo', codigo: 'INS-TEL-002', categoria_id: 1, unidad_medida: 'm', stock_actual: 8.2, stock_minimo: 15, costo_unitario: 24000, costo_promedio_ponderado: 23500, ultimo_costo_compra: 24000, created_at: new Date().toISOString() },
  { id: 3, nombre: 'Argollas Doradas 10mm', codigo: 'INS-HER-001', categoria_id: 2, unidad_medida: 'un', stock_actual: 250, stock_minimo: 50, costo_unitario: 450, costo_promedio_ponderado: 420, ultimo_costo_compra: 450, created_at: new Date().toISOString() },
  { id: 4, nombre: 'Gancho G Mediano', codigo: 'INS-HER-002', categoria_id: 2, unidad_medida: 'un', stock_actual: 120, stock_minimo: 30, costo_unitario: 650, costo_promedio_ponderado: 600, ultimo_costo_compra: 650, created_at: new Date().toISOString() },
  { id: 5, nombre: 'Caja Regalo Premium Arpía', codigo: 'INS-EMP-001', categoria_id: 3, unidad_medida: 'un', stock_actual: 14, stock_minimo: 20, costo_unitario: 4200, costo_promedio_ponderado: 4000, ultimo_costo_compra: 4200, created_at: new Date().toISOString() },
  { id: 6, nombre: 'Varilla Poliéster Corset 8mm', codigo: 'INS-HER-003', categoria_id: 2, unidad_medida: 'm', stock_actual: 65, stock_minimo: 15, costo_unitario: 3200, costo_promedio_ponderado: 3100, ultimo_costo_compra: 3200, created_at: new Date().toISOString() },
]

const comprasInsumos: CompraInsumo[] = [
  { id: 1, insumo_id: 1, cantidad: 50, costo_unitario: 18000, costo_total: 900000, fecha_compra: '2026-08-01', factura: 'FAC-0982', created_at: new Date('2026-08-01').toISOString() },
  { id: 2, insumo_id: 3, cantidad: 300, costo_unitario: 420, costo_total: 126000, fecha_compra: '2026-08-05', factura: 'FAC-1002', created_at: new Date('2026-08-05').toISOString() },
  { id: 3, insumo_id: 5, cantidad: 50, costo_unitario: 4000, costo_total: 200000, fecha_compra: '2026-08-10', factura: 'FAC-1044', created_at: new Date('2026-08-10').toISOString() },
]

const clientes: Cliente[] = [
  { id: 1, nombre: 'Valentina Restrepo', documento: '1020304050', telefono: '+57 312 456 7890', email: 'valentina.restrepo@example.com', ciudad: 'Medellín', direccion: 'El Poblado Cra 35 #7-12', created_at: new Date().toISOString() },
  { id: 2, nombre: 'Camila Morales', documento: '1098765432', telefono: '+57 300 987 6543', email: 'camila.morales@example.com', ciudad: 'Bogotá', direccion: 'Chapinero Alto Calle 65 #4-20', created_at: new Date().toISOString() },
  { id: 3, nombre: 'Mariana Gómez', documento: '1035987123', telefono: '+57 315 234 5678', email: 'mariana.gomez@example.com', ciudad: 'Cali', direccion: 'Granada Av 9 Norte #15-30', created_at: new Date().toISOString() },
]

const tiposProductos: TipoProducto[] = [
  { id: 1, nombre: 'Corsetería', descripcion: 'Corsets y bustiers estructurados', created_at: new Date().toISOString() },
  { id: 2, nombre: 'Lencería', descripcion: 'Sets de encaje y prendas íntimas de diseño', created_at: new Date().toISOString() },
  { id: 3, nombre: 'Blusa', descripcion: 'Prendas superiores elegantes', created_at: new Date().toISOString() },
  { id: 4, nombre: 'Accesorio', descripcion: 'Arneses, ligueros y complementos', created_at: new Date().toISOString() },
]

const productos: Producto[] = [
  { id: 1, nombre: 'Corset Nocturna', sku_base: 'COR-NOC', tipo_producto_id: 1, precio_base: 189000, descripcion: 'Corset de satín estructurado con varillas y ojaletes traseros', activo: true, created_at: new Date().toISOString() },
  { id: 2, nombre: 'Bralette Encaje Borgoña', sku_base: 'BRA-BOR', tipo_producto_id: 2, precio_base: 115000, descripcion: 'Bralette en encaje francés con detalles dorados', activo: true, created_at: new Date().toISOString() },
  { id: 3, nombre: 'Set Lencería Arpía Gold', sku_base: 'SET-ARP', tipo_producto_id: 2, precio_base: 220000, descripcion: 'Conjunto completo con bralette, panty y liguero', activo: true, created_at: new Date().toISOString() },
]

const variantes: Variante[] = [
  { id: 1, producto_id: 1, talla: 'XS', sku: 'COR-NOC-XS', precio_override: null, stock_actual: 4, created_at: new Date().toISOString() },
  { id: 2, producto_id: 1, talla: 'S', sku: 'COR-NOC-S', precio_override: null, stock_actual: 8, created_at: new Date().toISOString() },
  { id: 3, producto_id: 1, talla: 'M', sku: 'COR-NOC-M', precio_override: null, stock_actual: 6, created_at: new Date().toISOString() },
  { id: 4, producto_id: 1, talla: 'L', sku: 'COR-NOC-L', precio_override: null, stock_actual: 3, created_at: new Date().toISOString() },
  { id: 5, producto_id: 2, talla: 'S', sku: 'BRA-BOR-S', precio_override: null, stock_actual: 12, created_at: new Date().toISOString() },
  { id: 6, producto_id: 2, talla: 'M', sku: 'BRA-BOR-M', precio_override: null, stock_actual: 9, created_at: new Date().toISOString() },
]

const bomInsumos: BomInsumo[] = [
  { id: 1, producto_id: 1, insumo_id: 1, cantidad_requerida: 0.8, desperdicio_pct: 5, created_at: new Date().toISOString() },
  { id: 2, producto_id: 1, insumo_id: 6, cantidad_requerida: 2.4, desperdicio_pct: 2, created_at: new Date().toISOString() },
  { id: 3, producto_id: 1, insumo_id: 3, cantidad_requerida: 12, desperdicio_pct: 0, created_at: new Date().toISOString() },
  { id: 4, producto_id: 2, insumo_id: 2, cantidad_requerida: 0.6, desperdicio_pct: 5, created_at: new Date().toISOString() },
  { id: 5, producto_id: 2, insumo_id: 4, cantidad_requerida: 4, desperdicio_pct: 0, created_at: new Date().toISOString() },
]

const bomProductos: BomProducto[] = []

const ventas: Venta[] = [
  {
    id: 1,
    codigo: 'VEN-2026-001',
    fecha: '2026-08-15',
    cliente_id: 1,
    total: 189000,
    descuento: 0,
    estado: 'completada',
    canal: 'Instagram / WhatsApp',
    es_regalo: false,
    observaciones: 'Entregar en portería',
    items: [
      { id: 1, venta_id: 1, producto_id: 1, variante_id: 2, cantidad: 1, precio_unitario: 189000, subtotal: 189000 }
    ],
    created_at: new Date('2026-08-15').toISOString(),
  },
  {
    id: 2,
    codigo: 'VEN-2026-002',
    fecha: '2026-08-18',
    cliente_id: 2,
    total: 335000,
    descuento: 0,
    estado: 'completada',
    canal: 'Tienda Online',
    es_regalo: true,
    observaciones: 'Empaque de regalo con mensaje especial',
    items: [
      { id: 2, venta_id: 2, producto_id: 2, variante_id: 5, cantidad: 1, precio_unitario: 115000, subtotal: 115000 },
      { id: 3, venta_id: 2, producto_id: 3, variante_id: null, cantidad: 1, precio_unitario: 220000, subtotal: 220000 }
    ],
    created_at: new Date('2026-08-18').toISOString(),
  },
  {
    id: 3,
    codigo: 'VEN-2026-003',
    fecha: '2026-08-20',
    cliente_id: 3,
    total: 189000,
    descuento: 0,
    estado: 'completada',
    canal: 'Showroom',
    es_regalo: false,
    observaciones: 'Pago por transferencia',
    items: [
      { id: 4, venta_id: 3, producto_id: 1, variante_id: 3, cantidad: 1, precio_unitario: 189000, subtotal: 189000 }
    ],
    created_at: new Date('2026-08-20').toISOString(),
  }
]

const devoluciones: Devolucion[] = [
  { id: 1, venta_id: 1, fecha: '2026-08-16', motivo: 'Cambio de talla por M', monto: 0, estado: 'aprobada', created_at: new Date('2026-08-16').toISOString() }
]

const socios: Socio[] = [
  { id: 1, nombre: 'Márgara', email: 'margara@arpia.com', telefono: '+57 310 111 2233', participacion_pct: 50, activo: true, created_at: new Date().toISOString() },
  { id: 2, nombre: 'Valqui', email: 'valqui@arpia.com', telefono: '+57 310 444 5566', participacion_pct: 50, activo: true, created_at: new Date().toISOString() },
]

const movimientos: MovimientoFinanciero[] = [
  { id: 1, fecha: '2026-08-01', tipo: 'inversion', categoria: 'Aporte de Capital', descripcion: 'Inversión inicial compra de insumos', monto: 5000000, socio_id: 1, created_at: new Date('2026-08-01').toISOString() },
  { id: 2, fecha: '2026-08-01', tipo: 'inversion', categoria: 'Aporte de Capital', descripcion: 'Inversión inicial maquinaria y taller', monto: 5000000, socio_id: 2, created_at: new Date('2026-08-01').toISOString() },
  { id: 3, fecha: '2026-08-02', tipo: 'gasto', categoria: 'Insumos', descripcion: 'Compra de lote telas e hilos', monto: 1226000, created_at: new Date('2026-08-02').toISOString() },
  { id: 4, fecha: '2026-08-05', tipo: 'gasto', categoria: 'Arriendo & Servicios', descripcion: 'Pago servicios taller Medellín', monto: 350000, created_at: new Date('2026-08-05').toISOString() },
  { id: 5, fecha: '2026-08-15', tipo: 'ingreso', categoria: 'Ventas', descripcion: 'Ingreso acumulado ventas primera quincena', monto: 2850000, created_at: new Date('2026-08-15').toISOString() },
]

const omisiones: Omision[] = [
  { id: 1, fase: 'Fase 1', nivel: 'Media', hoja: 'Inventario', fila: 42, descripcion: 'Variante sin precio base asignado en catálogo antiguo', resuelta: true, created_at: new Date('2026-08-01').toISOString() },
  { id: 2, fase: 'Fase 2', nivel: 'Baja', hoja: 'Ventas', fila: 118, descripcion: 'Canal no tipificado en registro histórico', resuelta: false, created_at: new Date('2026-08-05').toISOString() },
]

const nextId = {
  insumo: 7,
  compra: 4,
  cliente: 4,
  tipoProducto: 5,
  producto: 4,
  variante: 7,
  bomInsumo: 6,
  bomProducto: 1,
  venta: 4,
  devolucion: 2,
  socio: 3,
  movimiento: 6,
  omision: 3,
  user: 4,
}

// --- Helper Functions ---
function paginate<T>(items: T[], query: Record<string, unknown>) {
  const limit = Number(query.limit) || 50
  const offset = Number(query.offset) || 0
  const total = items.length
  const paginated = items.slice(offset, offset + limit)
  return { items: paginated, total, limit, offset }
}

// --- API Routes ---
const apiRouter = express.Router()

// Auth
apiRouter.post('/auth/login', (req, res) => {
  const { email } = req.body || {}
  const normalizedEmail = (email || '').trim().toLowerCase()
  let user = users.find((u) => u.email.toLowerCase() === normalizedEmail)

  // If user does not exist but a valid login attempt was made, create or fallback
  if (!user) {
    if (normalizedEmail.includes('admin')) {
      user = users[0]
    } else if (normalizedEmail.includes('operador')) {
      user = users[1]
    } else if (normalizedEmail.includes('consulta') || normalizedEmail.includes('auditor')) {
      user = users[2]
    } else {
      user = users[0]
    }
  }

  const tokenPayload = `ais_token_${user.id}_${Date.now()}`
  const refreshPayload = `ais_refresh_${user.id}_${Date.now()}`

  res.json({
    access_token: tokenPayload,
    refresh_token: refreshPayload,
    token_type: 'bearer',
    rol: user.rol,
  })
})

apiRouter.post('/auth/refresh', (req, res) => {
  const { refresh_token } = req.body || {}
  let user = users[0]
  if (typeof refresh_token === 'string') {
    const match = refresh_token.match(/^ais_refresh_(\d+)_/)
    if (match) {
      const uid = Number(match[1])
      const found = users.find((u) => u.id === uid)
      if (found) user = found
    }
  }

  res.json({
    access_token: `ais_token_${user.id}_${Date.now()}`,
    refresh_token: `ais_refresh_${user.id}_${Date.now()}`,
    token_type: 'bearer',
    rol: user.rol,
  })
})

apiRouter.post('/auth/logout', (_req, res) => {
  res.status(204).send()
})

apiRouter.get('/auth/me', (req, res) => {
  const authHeader = req.headers.authorization || ''
  let user = users[0]
  if (authHeader.startsWith('Bearer ')) {
    const token = authHeader.substring(7)
    const match = token.match(/^ais_token_(\d+)_/)
    if (match) {
      const uid = Number(match[1])
      const found = users.find((u) => u.id === uid)
      if (found) user = found
    }
  }
  res.json(user)
})

// Categorias Insumos
apiRouter.get('/categorias-insumos', (req, res) => {
  res.json(paginate(categoriasInsumos, req.query))
})

apiRouter.post('/categorias-insumos', (req, res) => {
  const item: CategoriaInsumo = {
    id: nextId.insumo++,
    nombre: req.body.nombre,
    descripcion: req.body.descripcion,
    created_at: new Date().toISOString(),
  }
  categoriasInsumos.push(item)
  res.status(201).json(item)
})

apiRouter.put('/categorias-insumos/:id', (req, res) => {
  const id = Number(req.params.id)
  const idx = categoriasInsumos.findIndex((c) => c.id === id)
  if (idx !== -1) {
    categoriasInsumos[idx] = { ...categoriasInsumos[idx], ...req.body }
    return res.json(categoriasInsumos[idx])
  }
  res.status(404).json({ detail: 'Categoria not found' })
})

apiRouter.delete('/categorias-insumos/:id', (req, res) => {
  const id = Number(req.params.id)
  const idx = categoriasInsumos.findIndex((c) => c.id === id)
  if (idx !== -1) {
    categoriasInsumos.splice(idx, 1)
  }
  res.status(204).send()
})

// Insumos
apiRouter.get('/insumos', (req, res) => {
  let list = [...insumos]
  if (req.query.categoria_id) {
    list = list.filter((i) => i.categoria_id === Number(req.query.categoria_id))
  }
  if (req.query.q) {
    const q = String(req.query.q).toLowerCase()
    list = list.filter((i) => i.nombre.toLowerCase().includes(q) || (i.codigo && i.codigo.toLowerCase().includes(q)))
  }
  res.json(paginate(list, req.query))
})

apiRouter.get('/insumos/:id', (req, res) => {
  const item = insumos.find((i) => i.id === Number(req.params.id))
  if (item) return res.json(item)
  res.status(404).json({ detail: 'Insumo not found' })
})

apiRouter.post('/insumos', (req, res) => {
  const item: Insumo = {
    id: nextId.insumo++,
    nombre: req.body.nombre,
    codigo: req.body.codigo || `INS-${Date.now().toString().slice(-4)}`,
    categoria_id: req.body.categoria_id,
    unidad_medida: req.body.unidad_medida || 'un',
    stock_actual: Number(req.body.stock_actual) || 0,
    stock_minimo: Number(req.body.stock_minimo) || 0,
    costo_unitario: Number(req.body.costo_unitario) || 0,
    costo_promedio_ponderado: Number(req.body.costo_unitario) || 0,
    ultimo_costo_compra: Number(req.body.costo_unitario) || 0,
    proveedor_id: req.body.proveedor_id,
    created_at: new Date().toISOString(),
  }
  insumos.unshift(item)
  res.status(201).json(item)
})

apiRouter.put('/insumos/:id', (req, res) => {
  const id = Number(req.params.id)
  const idx = insumos.findIndex((i) => i.id === id)
  if (idx !== -1) {
    insumos[idx] = { ...insumos[idx], ...req.body }
    return res.json(insumos[idx])
  }
  res.status(404).json({ detail: 'Insumo not found' })
})

apiRouter.delete('/insumos/:id', (req, res) => {
  const id = Number(req.params.id)
  const idx = insumos.findIndex((i) => i.id === id)
  if (idx !== -1) insumos.splice(idx, 1)
  res.status(204).send()
})

// Compras Insumos
apiRouter.get('/compras-insumos', (req, res) => {
  let list = [...comprasInsumos]
  if (req.query.insumo_id) {
    list = list.filter((c) => c.insumo_id === Number(req.query.insumo_id))
  }
  res.json(paginate(list, req.query))
})

apiRouter.post('/compras-insumos', (req, res) => {
  const cantidad = Number(req.body.cantidad) || 1
  const costo_unitario = Number(req.body.costo_unitario) || (Number(req.body.costo_total) / cantidad)
  const costo_total = Number(req.body.costo_total) || (cantidad * costo_unitario)

  const item: CompraInsumo = {
    id: nextId.compra++,
    insumo_id: Number(req.body.insumo_id),
    cantidad,
    costo_unitario,
    costo_total,
    fecha_compra: req.body.fecha_compra || new Date().toISOString().split('T')[0],
    factura: req.body.factura,
    proveedor_id: req.body.proveedor_id,
    modo: req.body.modo || 'UNIT',
    created_at: new Date().toISOString(),
  }
  comprasInsumos.unshift(item)

  // Update Insumo stock and WAC
  const targetInsumo = insumos.find((i) => i.id === item.insumo_id)
  if (targetInsumo) {
    const oldStock = targetInsumo.stock_actual
    const oldVal = oldStock * targetInsumo.costo_promedio_ponderado
    const newVal = oldVal + costo_total
    const newStock = oldStock + cantidad
    targetInsumo.stock_actual = newStock
    targetInsumo.costo_promedio_ponderado = newStock > 0 ? newVal / newStock : costo_unitario
    targetInsumo.ultimo_costo_compra = costo_unitario
    targetInsumo.costo_unitario = costo_unitario
  }

  res.status(201).json(item)
})

// Clientes
apiRouter.get('/clientes', (req, res) => {
  let list = [...clientes]
  if (req.query.q) {
    const q = String(req.query.q).toLowerCase()
    list = list.filter((c) => c.nombre.toLowerCase().includes(q) || (c.email && c.email.toLowerCase().includes(q)))
  }
  res.json(paginate(list, req.query))
})

apiRouter.post('/clientes', (req, res) => {
  const item: Cliente = {
    id: nextId.cliente++,
    nombre: req.body.nombre,
    documento: req.body.documento,
    telefono: req.body.telefono,
    email: req.body.email,
    ciudad: req.body.ciudad,
    direccion: req.body.direccion,
    created_at: new Date().toISOString(),
  }
  clientes.unshift(item)
  res.status(201).json(item)
})

apiRouter.put('/clientes/:id', (req, res) => {
  const id = Number(req.params.id)
  const idx = clientes.findIndex((c) => c.id === id)
  if (idx !== -1) {
    clientes[idx] = { ...clientes[idx], ...req.body }
    return res.json(clientes[idx])
  }
  res.status(404).json({ detail: 'Cliente not found' })
})

apiRouter.delete('/clientes/:id', (req, res) => {
  const id = Number(req.params.id)
  const idx = clientes.findIndex((c) => c.id === id)
  if (idx !== -1) clientes.splice(idx, 1)
  res.status(204).send()
})

// Tipos Producto
apiRouter.get('/tipos-producto', (req, res) => {
  res.json(paginate(tiposProductos, req.query))
})

apiRouter.post('/tipos-producto', (req, res) => {
  const item: TipoProducto = {
    id: nextId.tipoProducto++,
    nombre: req.body.nombre,
    descripcion: req.body.descripcion,
    created_at: new Date().toISOString(),
  }
  tiposProductos.push(item)
  res.status(201).json(item)
})

apiRouter.put('/tipos-producto/:id', (req, res) => {
  const id = Number(req.params.id)
  const idx = tiposProductos.findIndex((t) => t.id === id)
  if (idx !== -1) {
    tiposProductos[idx] = { ...tiposProductos[idx], ...req.body }
    return res.json(tiposProductos[idx])
  }
  res.status(404).json({ detail: 'Tipo Producto not found' })
})

apiRouter.delete('/tipos-producto/:id', (req, res) => {
  const id = Number(req.params.id)
  const idx = tiposProductos.findIndex((t) => t.id === id)
  if (idx !== -1) tiposProductos.splice(idx, 1)
  res.status(204).send()
})

// Productos
apiRouter.get('/productos', (req, res) => {
  let list = [...productos]
  if (req.query.tipo_producto_id) {
    list = list.filter((p) => p.tipo_producto_id === Number(req.query.tipo_producto_id))
  }
  if (req.query.q) {
    const q = String(req.query.q).toLowerCase()
    list = list.filter((p) => p.nombre.toLowerCase().includes(q) || p.sku_base.toLowerCase().includes(q))
  }
  res.json(paginate(list, req.query))
})

apiRouter.get('/productos/:id', (req, res) => {
  const item = productos.find((p) => p.id === Number(req.params.id))
  if (item) return res.json(item)
  res.status(404).json({ detail: 'Producto not found' })
})

apiRouter.post('/productos', (req, res) => {
  const item: Producto = {
    id: nextId.producto++,
    nombre: req.body.nombre,
    sku_base: req.body.sku_base || `PRD-${Date.now().toString().slice(-4)}`,
    tipo_producto_id: Number(req.body.tipo_producto_id),
    precio_base: Number(req.body.precio_base) || 0,
    descripcion: req.body.descripcion,
    activo: req.body.activo ?? true,
    created_at: new Date().toISOString(),
  }
  productos.unshift(item)
  res.status(201).json(item)
})

apiRouter.put('/productos/:id', (req, res) => {
  const id = Number(req.params.id)
  const idx = productos.findIndex((p) => p.id === id)
  if (idx !== -1) {
    productos[idx] = { ...productos[idx], ...req.body }
    return res.json(productos[idx])
  }
  res.status(404).json({ detail: 'Producto not found' })
})

apiRouter.delete('/productos/:id', (req, res) => {
  const id = Number(req.params.id)
  const idx = productos.findIndex((p) => p.id === id)
  if (idx !== -1) productos.splice(idx, 1)
  res.status(204).send()
})

// Variantes
apiRouter.get('/productos/:id/variantes', (req, res) => {
  const list = variantes.filter((v) => v.producto_id === Number(req.params.id))
  res.json(list)
})

apiRouter.post('/productos/:id/variantes', (req, res) => {
  const producto_id = Number(req.params.id)
  const prod = productos.find((p) => p.id === producto_id)
  const item: Variante = {
    id: nextId.variante++,
    producto_id,
    talla: req.body.talla,
    sku: req.body.sku || `${prod ? prod.sku_base : 'SKU'}-${req.body.talla}`,
    precio_override: req.body.precio_override ? Number(req.body.precio_override) : null,
    stock_actual: Number(req.body.stock_actual) || 0,
    created_at: new Date().toISOString(),
  }
  variantes.push(item)
  res.status(201).json(item)
})

apiRouter.put('/productos/:id/variantes/:variante_id', (req, res) => {
  const id = Number(req.params.variante_id)
  const idx = variantes.findIndex((v) => v.id === id)
  if (idx !== -1) {
    variantes[idx] = { ...variantes[idx], ...req.body }
    return res.json(variantes[idx])
  }
  res.status(404).json({ detail: 'Variante not found' })
})

apiRouter.delete('/productos/:id/variantes/:variante_id', (req, res) => {
  const id = Number(req.params.variante_id)
  const idx = variantes.findIndex((v) => v.id === id)
  if (idx !== -1) variantes.splice(idx, 1)
  res.status(204).send()
})

// BOM Insumos
apiRouter.get('/productos/:id/bom/insumos', (req, res) => {
  const list = bomInsumos.filter((b) => b.producto_id === Number(req.params.id))
  res.json(list)
})

apiRouter.post('/productos/:id/bom/insumos', (req, res) => {
  const item: BomInsumo = {
    id: nextId.bomInsumo++,
    producto_id: Number(req.params.id),
    insumo_id: Number(req.body.insumo_id),
    cantidad_requerida: Number(req.body.cantidad_requerida) || 1,
    desperdicio_pct: Number(req.body.desperdicio_pct) || 0,
    created_at: new Date().toISOString(),
  }
  bomInsumos.push(item)
  res.status(201).json(item)
})

apiRouter.put('/productos/:id/bom/insumos/:linea_id', (req, res) => {
  const id = Number(req.params.linea_id)
  const idx = bomInsumos.findIndex((b) => b.id === id)
  if (idx !== -1) {
    bomInsumos[idx] = { ...bomInsumos[idx], ...req.body }
    return res.json(bomInsumos[idx])
  }
  res.status(404).json({ detail: 'BOM Insumo not found' })
})

apiRouter.delete('/productos/:id/bom/insumos/:linea_id', (req, res) => {
  const id = Number(req.params.linea_id)
  const idx = bomInsumos.findIndex((b) => b.id === id)
  if (idx !== -1) bomInsumos.splice(idx, 1)
  res.status(204).send()
})

// BOM Productos
apiRouter.get('/productos/:id/bom/productos', (req, res) => {
  const list = bomProductos.filter((b) => b.producto_padre_id === Number(req.params.id))
  res.json(list)
})

apiRouter.post('/productos/:id/bom/productos', (req, res) => {
  const item: BomProducto = {
    id: nextId.bomProducto++,
    producto_padre_id: Number(req.params.id),
    producto_hijo_id: Number(req.body.producto_hijo_id),
    cantidad: Number(req.body.cantidad) || 1,
    created_at: new Date().toISOString(),
  }
  bomProductos.push(item)
  res.status(201).json(item)
})

apiRouter.put('/productos/:id/bom/productos/:linea_id', (req, res) => {
  const id = Number(req.params.linea_id)
  const idx = bomProductos.findIndex((b) => b.id === id)
  if (idx !== -1) {
    bomProductos[idx] = { ...bomProductos[idx], ...req.body }
    return res.json(bomProductos[idx])
  }
  res.status(404).json({ detail: 'BOM Producto not found' })
})

apiRouter.delete('/productos/:id/bom/productos/:linea_id', (req, res) => {
  const id = Number(req.params.linea_id)
  const idx = bomProductos.findIndex((b) => b.id === id)
  if (idx !== -1) bomProductos.splice(idx, 1)
  res.status(204).send()
})

// Costo Produccion Tree
apiRouter.get('/productos/:id/costo', (req, res) => {
  const producto_id = Number(req.params.id)
  const prod = productos.find((p) => p.id === producto_id)
  const boms = bomInsumos.filter((b) => b.producto_id === producto_id)
  
  let costo_directo = 0
  const desglose_insumos = boms.map((b) => {
    const ins = insumos.find((i) => i.id === b.insumo_id)
    const costo_unit = ins ? ins.costo_promedio_ponderado : 0
    const factor_desperdicio = 1 + (b.desperdicio_pct / 100)
    const subtotal = b.cantidad_requerida * costo_unit * factor_desperdicio
    costo_directo += subtotal
    return {
      insumo_id: b.insumo_id,
      nombre_insumo: ins ? ins.nombre : 'Insumo',
      unidad: ins ? ins.unidad_medida : 'un',
      cantidad: b.cantidad_requerida,
      costo_unitario: costo_unit,
      desperdicio_pct: b.desperdicio_pct,
      subtotal,
    }
  })

  res.json({
    producto_id,
    nombre_producto: prod ? prod.nombre : 'Producto',
    costo_total: Math.round(costo_directo),
    costo_directo_insumos: Math.round(costo_directo),
    costo_subproductos: 0,
    desglose_insumos,
    desglose_subproductos: [],
  })
})

// Ventas
apiRouter.get('/ventas', (req, res) => {
  let list = [...ventas]
  if (req.query.estado) {
    list = list.filter((v) => v.estado === req.query.estado)
  }
  if (req.query.q) {
    const q = String(req.query.q).toLowerCase()
    list = list.filter((v) => v.codigo.toLowerCase().includes(q) || v.canal.toLowerCase().includes(q))
  }
  res.json(paginate(list, req.query))
})

apiRouter.post('/ventas', (req, res) => {
  const rawItems = (req.body.items || []) as Array<{ producto_id: number; variante_id?: number | null; cantidad: number; precio_unitario: number }>
  let total = 0
  const processedItems: VentaItem[] = rawItems.map((it, idx: number) => {
    const qty = Number(it.cantidad) || 1
    const price = Number(it.precio_unitario) || 0
    const subtotal = qty * price
    total += subtotal
    return {
      id: idx + 1,
      venta_id: nextId.venta,
      producto_id: Number(it.producto_id),
      variante_id: it.variante_id ? Number(it.variante_id) : null,
      cantidad: qty,
      precio_unitario: price,
      subtotal,
    }
  })

  const item: Venta = {
    id: nextId.venta++,
    codigo: `VEN-2026-${String(nextId.venta).padStart(3, '0')}`,
    fecha: req.body.fecha || new Date().toISOString().split('T')[0],
    cliente_id: req.body.cliente_id ? Number(req.body.cliente_id) : null,
    total: req.body.total ? Number(req.body.total) : total,
    descuento: Number(req.body.descuento) || 0,
    estado: 'completada',
    canal: req.body.canal || 'Tienda Online',
    es_regalo: Boolean(req.body.es_regalo),
    observaciones: req.body.observaciones,
    items: processedItems,
    created_at: new Date().toISOString(),
  }
  ventas.unshift(item)

  // Add automatic financial income movement
  movimientos.unshift({
    id: nextId.movimiento++,
    fecha: item.fecha,
    tipo: 'ingreso',
    categoria: 'Ventas',
    descripcion: `Venta ${item.codigo} (${item.canal})`,
    monto: item.total,
    created_at: new Date().toISOString(),
  })

  res.status(201).json(item)
})

apiRouter.patch('/ventas/:venta_id', (req, res) => {
  const id = Number(req.params.venta_id)
  const idx = ventas.findIndex((v) => v.id === id)
  if (idx !== -1) {
    ventas[idx] = { ...ventas[idx], ...req.body }
    return res.json(ventas[idx])
  }
  res.status(404).json({ detail: 'Venta not found' })
})

apiRouter.put('/ventas/:venta_id', (req, res) => {
  const id = Number(req.params.venta_id)
  const idx = ventas.findIndex((v) => v.id === id)
  if (idx !== -1) {
    ventas[idx] = { ...ventas[idx], ...req.body }
    return res.json(ventas[idx])
  }
  res.status(404).json({ detail: 'Venta not found' })
})

apiRouter.delete('/ventas/:venta_id', (req, res) => {
  const id = Number(req.params.venta_id)
  const idx = ventas.findIndex((v) => v.id === id)
  if (idx !== -1) {
    ventas[idx].estado = 'anulada'
    return res.json(ventas[idx])
  }
  res.status(404).json({ detail: 'Venta not found' })
})

// Devoluciones
apiRouter.get('/devoluciones', (req, res) => {
  res.json(paginate(devoluciones, req.query))
})

apiRouter.post('/devoluciones', (req, res) => {
  const item: Devolucion = {
    id: nextId.devolucion++,
    venta_id: Number(req.body.venta_id),
    fecha: req.body.fecha || new Date().toISOString().split('T')[0],
    motivo: req.body.motivo,
    monto: Number(req.body.monto) || 0,
    estado: 'completada',
    created_at: new Date().toISOString(),
  }
  devoluciones.unshift(item)
  res.status(201).json(item)
})

// Finanzas
apiRouter.get('/finanzas/movimientos', (req, res) => {
  let list = [...movimientos]
  if (req.query.tipo) {
    list = list.filter((m) => m.tipo === req.query.tipo)
  }
  res.json(paginate(list, req.query))
})

apiRouter.post('/finanzas/movimientos', (req, res) => {
  const item: MovimientoFinanciero = {
    id: nextId.movimiento++,
    fecha: req.body.fecha || new Date().toISOString().split('T')[0],
    tipo: req.body.tipo,
    categoria: req.body.categoria,
    descripcion: req.body.descripcion,
    monto: Number(req.body.monto),
    socio_id: req.body.socio_id ? Number(req.body.socio_id) : null,
    created_at: new Date().toISOString(),
  }
  movimientos.unshift(item)
  res.status(201).json(item)
})

apiRouter.patch('/finanzas/movimientos/:id', (req, res) => {
  const id = Number(req.params.id)
  const idx = movimientos.findIndex((m) => m.id === id)
  if (idx !== -1) {
    movimientos[idx] = { ...movimientos[idx], ...req.body }
    return res.json(movimientos[idx])
  }
  res.status(404).json({ detail: 'Movimiento not found' })
})

apiRouter.delete('/finanzas/movimientos/:id', (req, res) => {
  const id = Number(req.params.id)
  const idx = movimientos.findIndex((m) => m.id === id)
  if (idx !== -1) {
    const deleted = movimientos.splice(idx, 1)[0]
    return res.json(deleted)
  }
  res.status(404).json({ detail: 'Movimiento not found' })
})

apiRouter.get('/finanzas/socios', (req, res) => {
  res.json(paginate(socios, req.query))
})

apiRouter.post('/finanzas/socios', (req, res) => {
  const item: Socio = {
    id: nextId.socio++,
    nombre: req.body.nombre,
    email: req.body.email,
    telefono: req.body.telefono,
    participacion_pct: Number(req.body.participacion_pct) || 0,
    activo: true,
    created_at: new Date().toISOString(),
  }
  socios.push(item)
  res.status(201).json(item)
})

apiRouter.patch('/finanzas/socios/:id', (req, res) => {
  const id = Number(req.params.id)
  const idx = socios.findIndex((s) => s.id === id)
  if (idx !== -1) {
    socios[idx] = { ...socios[idx], ...req.body }
    return res.json(socios[idx])
  }
  res.status(404).json({ detail: 'Socio not found' })
})

apiRouter.delete('/finanzas/socios/:id', (req, res) => {
  const id = Number(req.params.id)
  const idx = socios.findIndex((s) => s.id === id)
  if (idx !== -1) {
    socios[idx].activo = false
    return res.json(socios[idx])
  }
  res.status(404).json({ detail: 'Socio not found' })
})

apiRouter.post('/finanzas/liquidaciones', (req, res) => {
  const { socio_id, monto, descripcion, fecha } = req.body
  const item: MovimientoFinanciero = {
    id: nextId.movimiento++,
    fecha: fecha || new Date().toISOString().split('T')[0],
    tipo: 'retiro',
    categoria: 'Liquidación / Reparto Utilidades',
    descripcion: descripcion || 'Liquidación de socio',
    monto: Number(monto),
    socio_id: Number(socio_id),
    es_liquidacion: true,
    created_at: new Date().toISOString(),
  }
  movimientos.unshift(item)
  res.status(201).json(item)
})

// Analíticos
apiRouter.get('/analiticos/ventas-mensuales', (_req, res) => {
  res.json([
    { periodo: '2026-03', total_ventas: 4200000, cantidad_ventas: 18 },
    { periodo: '2026-04', total_ventas: 5800000, cantidad_ventas: 24 },
    { periodo: '2026-05', total_ventas: 7100000, cantidad_ventas: 31 },
    { periodo: '2026-06', total_ventas: 6900000, cantidad_ventas: 29 },
    { periodo: '2026-07', total_ventas: 8450000, cantidad_ventas: 36 },
    { periodo: '2026-08', total_ventas: 9200000, cantidad_ventas: 41 },
  ])
})

apiRouter.get('/analiticos/insumos-bajo-stock', (_req, res) => {
  const bajoStock = insumos
    .filter((i) => i.stock_actual <= i.stock_minimo)
    .map((i) => ({
      insumo_id: i.id,
      nombre: i.nombre,
      categoria: categoriasInsumos.find((c) => c.id === i.categoria_id)?.nombre || 'General',
      stock_actual: i.stock_actual,
      stock_minimo: i.stock_minimo,
      unidad_medida: i.unidad_medida,
      deficit: i.stock_minimo - i.stock_actual,
    }))
  res.json(bajoStock)
})

apiRouter.get('/analiticos/margen-por-producto', (_req, res) => {
  res.json([
    { producto_id: 1, nombre: 'Corset Nocturna', precio_venta: 189000, costo_estimado: 48500, margen_bruto: 140500, margen_pct: 74.3 },
    { producto_id: 2, nombre: 'Bralette Encaje Borgoña', precio_venta: 115000, costo_estimado: 28000, margen_bruto: 87000, margen_pct: 75.6 },
    { producto_id: 3, nombre: 'Set Lencería Arpía Gold', precio_venta: 220000, costo_estimado: 62000, margen_bruto: 158000, margen_pct: 71.8 },
  ])
})

apiRouter.get('/analiticos/top-productos', (_req, res) => {
  res.json([
    { producto_id: 1, nombre: 'Corset Nocturna', total_unidades: 28, total_ingresos: 5292000 },
    { producto_id: 2, nombre: 'Bralette Encaje Borgoña', total_unidades: 22, total_ingresos: 2530000 },
    { producto_id: 3, nombre: 'Set Lencería Arpía Gold', total_unidades: 14, total_ingresos: 3080000 },
  ])
})

apiRouter.get('/analiticos/top-insumos', (_req, res) => {
  res.json([
    { insumo_id: 1, nombre: 'Seda Satín Negro', total_usado: 22.4, costo_total_consumido: 403200 },
    { insumo_id: 2, nombre: 'Encaje Francés Rojo', total_usado: 13.2, costo_total_consumido: 310200 },
    { insumo_id: 3, nombre: 'Argollas Doradas 10mm', total_usado: 336, costo_total_consumido: 141120 },
  ])
})

apiRouter.get('/analiticos/finanzas-mensuales', (_req, res) => {
  res.json([
    { periodo: '2026-03', ingresos: 4200000, gastos: 2100000, balance: 2100000 },
    { periodo: '2026-04', ingresos: 5800000, gastos: 2800000, balance: 3000000 },
    { periodo: '2026-05', ingresos: 7100000, gastos: 3200000, balance: 3900000 },
    { periodo: '2026-06', ingresos: 6900000, gastos: 2950000, balance: 3950000 },
    { periodo: '2026-07', ingresos: 8450000, gastos: 3600000, balance: 4850000 },
    { periodo: '2026-08', ingresos: 9200000, gastos: 3900000, balance: 5300000 },
  ])
})

apiRouter.get('/analiticos/resumen', (_req, res) => {
  const totalVentas = ventas.reduce((acc, v) => acc + (v.estado === 'completada' ? v.total : 0), 0)
  const insumosBajo = insumos.filter((i) => i.stock_actual <= i.stock_minimo).length
  res.json({
    total_ventas_periodo: totalVentas + 9200000,
    total_ordenes: ventas.length + 41,
    ticket_promedio: 198000,
    insumos_criticos: insumosBajo,
    margen_promedio_pct: 73.9,
    balance_neto_periodo: 5300000,
  })
})

// Omisiones
apiRouter.get('/omisiones', (req, res) => {
  res.json(paginate(omisiones, req.query))
})

apiRouter.patch('/omisiones/:id', (req, res) => {
  const id = Number(req.params.id)
  const idx = omisiones.findIndex((o) => o.id === id)
  if (idx !== -1) {
    omisiones[idx] = { ...omisiones[idx], ...req.body }
    return res.json(omisiones[idx])
  }
  res.status(404).json({ detail: 'Omision not found' })
})

// Usuarios
apiRouter.get('/usuarios', (req, res) => {
  res.json(paginate(users, req.query))
})

apiRouter.post('/usuarios', (req, res) => {
  const item: User = {
    id: nextId.user++,
    nombre: req.body.nombre,
    email: req.body.email,
    rol: req.body.rol || 'operativo',
    activo: req.body.activo ?? true,
    created_at: new Date().toISOString(),
  }
  users.push(item)
  res.status(201).json(item)
})

apiRouter.patch('/usuarios/:id', (req, res) => {
  const id = Number(req.params.id)
  const idx = users.findIndex((u) => u.id === id)
  if (idx !== -1) {
    users[idx] = { ...users[idx], ...req.body }
    return res.json(users[idx])
  }
  res.status(404).json({ detail: 'Usuario not found' })
})

apiRouter.delete('/usuarios/:id', (req, res) => {
  const id = Number(req.params.id)
  const idx = users.findIndex((u) => u.id === id)
  if (idx !== -1) {
    users[idx].activo = false
    return res.json(users[idx])
  }
  res.status(404).json({ detail: 'Usuario not found' })
})

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

// Conditional mount: mock in-memory vs proxy to real backend
if (useMock) {
  app.use('/api/v1', apiRouter)
  app.use('/api', apiRouter)

  // Health check in mock mode (local)
  app.get('/api/health', (_req, res) => {
    res.json({ status: 'ok', mode: 'mock', time: new Date().toISOString() })
  })
} else {
  // Proxy all /api traffic to the real FastAPI backend
  app.use('/api', apiProxyMiddleware)
}

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
    if (useMock) {
      console.log(`ERP Arpía server listening on http://0.0.0.0:${PORT} — Mock API enabled (in-memory DB)`)
    } else {
      console.log(
        `ERP Arpía server listening on http://0.0.0.0:${PORT} — Mock API disabled — proxying /api to ${proxyTarget}`,
      )
    }
  })
}

start().catch((err) => {
  console.error('Failed to start server:', err)
  process.exit(1)
})
