/**
 * Universal Mock API Handler & Engine.
 *
 * Provides in-memory persistence and full REST endpoints for:
 * 1. Express server (server.ts)
 * 2. Vite dev server middleware (vite.config.ts)
 * 3. Client-side fallback adapter (client.ts)
 */

export interface User {
  id: number
  nombre: string
  email: string
  password_hash?: string
  rol: 'admin' | 'operador' | 'consulta'
  activo: boolean
  created_at: string
}

export interface CategoriaInsumo {
  id: number
  nombre: string
  descripcion?: string
  created_at: string
}

export interface Insumo {
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

export interface CompraInsumo {
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

export interface Cliente {
  id: number
  nombre: string
  documento?: string
  telefono?: string
  email?: string
  direccion?: string
  ciudad?: string
  created_at: string
}

export interface TipoProducto {
  id: number
  nombre: string
  descripcion?: string
  created_at: string
}

export interface Variante {
  id: number
  producto_id: number
  talla: string
  sku: string
  precio_override?: number | null
  stock_actual: number
  created_at: string
}

export interface BomInsumo {
  id: number
  producto_id: number
  insumo_id: number
  cantidad_requerida: number
  desperdicio_pct: number
  created_at: string
}

export interface BomProducto {
  id: number
  producto_padre_id: number
  producto_hijo_id: number
  cantidad: number
  created_at: string
}

export interface Producto {
  id: number
  nombre: string
  sku_base: string
  tipo_producto_id: number
  precio_base: number
  descripcion?: string
  activo: boolean
  created_at: string
}

export interface VentaItem {
  id: number
  venta_id: number
  producto_id: number
  variante_id?: number | null
  cantidad: number
  precio_unitario: number
  subtotal: number
}

export interface Venta {
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

export interface Devolucion {
  id: number
  venta_id: number
  fecha: string
  motivo: string
  monto: number
  estado: string
  created_at: string
}

export interface Socio {
  id: number
  nombre: string
  email?: string
  telefono?: string
  participacion_pct: number
  activo: boolean
  created_at: string
}

export interface MovimientoFinanciero {
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

export interface Omision {
  id: number
  fase: string
  nivel: string
  hoja: string
  fila?: number
  descripcion: string
  resuelta: boolean
  created_at: string
}

// Initial Database Data
export const users: User[] = [
  {
    id: 1,
    nombre: 'Administrador Arpía',
    email: 'admin@arpia.com',
    rol: 'admin',
    activo: true,
    created_at: '2026-01-01T00:00:00.000Z',
  },
  {
    id: 2,
    nombre: 'Operador Taller',
    email: 'operador@arpia.com',
    rol: 'operador',
    activo: true,
    created_at: '2026-01-10T00:00:00.000Z',
  },
  {
    id: 3,
    nombre: 'Auditor Financiero',
    email: 'consulta@arpia.com',
    rol: 'consulta',
    activo: true,
    created_at: '2026-02-01T00:00:00.000Z',
  },
]

export const categoriasInsumos: CategoriaInsumo[] = [
  { id: 1, nombre: 'Telas', descripcion: 'Telas licradas, encajes y sedas', created_at: '2026-01-01T00:00:00.000Z' },
  { id: 2, nombre: 'Herrajes', descripcion: 'Ganchos, argollas, ochos y varillas', created_at: '2026-01-01T00:00:00.000Z' },
  { id: 3, nombre: 'Empaques', descripcion: 'Bolsas, cajas, cintas y tarjetas', created_at: '2026-01-01T00:00:00.000Z' },
  { id: 4, nombre: 'Químicos & Tintes', descripcion: 'Tintas, fijadores y adhesivos', created_at: '2026-01-01T00:00:00.000Z' },
]

export const insumos: Insumo[] = [
  { id: 1, nombre: 'Seda Satín Negro', codigo: 'INS-TEL-001', categoria_id: 1, unidad_medida: 'm', stock_actual: 45.5, stock_minimo: 10, costo_unitario: 18500, costo_promedio_ponderado: 18000, ultimo_costo_compra: 18500, created_at: '2026-01-01T00:00:00.000Z' },
  { id: 2, nombre: 'Encaje Francés Rojo', codigo: 'INS-TEL-002', categoria_id: 1, unidad_medida: 'm', stock_actual: 8.2, stock_minimo: 15, costo_unitario: 24000, costo_promedio_ponderado: 23500, ultimo_costo_compra: 24000, created_at: '2026-01-01T00:00:00.000Z' },
  { id: 3, nombre: 'Argollas Doradas 10mm', codigo: 'INS-HER-001', categoria_id: 2, unidad_medida: 'un', stock_actual: 250, stock_minimo: 50, costo_unitario: 450, costo_promedio_ponderado: 420, ultimo_costo_compra: 450, created_at: '2026-01-01T00:00:00.000Z' },
  { id: 4, nombre: 'Gancho G Mediano', codigo: 'INS-HER-002', categoria_id: 2, unidad_medida: 'un', stock_actual: 120, stock_minimo: 30, costo_unitario: 650, costo_promedio_ponderado: 600, ultimo_costo_compra: 650, created_at: '2026-01-01T00:00:00.000Z' },
  { id: 5, nombre: 'Caja Regalo Premium Arpía', codigo: 'INS-EMP-001', categoria_id: 3, unidad_medida: 'un', stock_actual: 14, stock_minimo: 20, costo_unitario: 4200, costo_promedio_ponderado: 4000, ultimo_costo_compra: 4200, created_at: '2026-01-01T00:00:00.000Z' },
  { id: 6, nombre: 'Varilla Poliéster Corset 8mm', codigo: 'INS-HER-003', categoria_id: 2, unidad_medida: 'm', stock_actual: 65, stock_minimo: 15, costo_unitario: 3200, costo_promedio_ponderado: 3100, ultimo_costo_compra: 3200, created_at: '2026-01-01T00:00:00.000Z' },
]

export const comprasInsumos: CompraInsumo[] = [
  { id: 1, insumo_id: 1, cantidad: 50, costo_unitario: 18000, costo_total: 900000, fecha_compra: '2026-08-01', factura: 'FAC-0982', created_at: '2026-08-01T00:00:00.000Z' },
  { id: 2, insumo_id: 3, cantidad: 300, costo_unitario: 420, costo_total: 126000, fecha_compra: '2026-08-05', factura: 'FAC-1002', created_at: '2026-08-05T00:00:00.000Z' },
  { id: 3, insumo_id: 5, cantidad: 50, costo_unitario: 4000, costo_total: 200000, fecha_compra: '2026-08-10', factura: 'FAC-1044', created_at: '2026-08-10T00:00:00.000Z' },
]

export const clientes: Cliente[] = [
  { id: 1, nombre: 'Valentina Restrepo', documento: '1020304050', telefono: '+57 312 456 7890', email: 'valentina.restrepo@example.com', ciudad: 'Medellín', direccion: 'El Poblado Cra 35 #7-12', created_at: '2026-01-01T00:00:00.000Z' },
  { id: 2, nombre: 'Camila Morales', documento: '1098765432', telefono: '+57 300 987 6543', email: 'camila.morales@example.com', ciudad: 'Bogotá', direccion: 'Chapinero Alto Calle 65 #4-20', created_at: '2026-01-01T00:00:00.000Z' },
  { id: 3, nombre: 'Mariana Gómez', documento: '1035987123', telefono: '+57 315 234 5678', email: 'mariana.gomez@example.com', ciudad: 'Cali', direccion: 'Granada Av 9 Norte #15-30', created_at: '2026-01-01T00:00:00.000Z' },
]

export const tiposProductos: TipoProducto[] = [
  { id: 1, nombre: 'Corsetería', descripcion: 'Corsets y bustiers estructurados', created_at: '2026-01-01T00:00:00.000Z' },
  { id: 2, nombre: 'Lencería', descripcion: 'Sets de encaje y prendas íntimas de diseño', created_at: '2026-01-01T00:00:00.000Z' },
  { id: 3, nombre: 'Blusa', descripcion: 'Prendas superiores elegantes', created_at: '2026-01-01T00:00:00.000Z' },
  { id: 4, nombre: 'Accesorio', descripcion: 'Arneses, ligueros y complementos', created_at: '2026-01-01T00:00:00.000Z' },
]

export const productos: Producto[] = [
  { id: 1, nombre: 'Corset Nocturna', sku_base: 'PRD-COR-001', tipo_producto_id: 1, precio_base: 189000, descripcion: 'Corset estructurado en satín negro con varillas reforzadas', activo: true, created_at: '2026-01-01T00:00:00.000Z' },
  { id: 2, nombre: 'Bralette Encaje Borgoña', sku_base: 'PRD-LEN-001', tipo_producto_id: 2, precio_base: 115000, descripcion: 'Bralette triangular en encaje francés y detalles dorados', activo: true, created_at: '2026-01-01T00:00:00.000Z' },
  { id: 3, nombre: 'Set Lencería Arpía Gold', sku_base: 'PRD-SET-001', tipo_producto_id: 2, precio_base: 220000, descripcion: 'Set de 3 piezas: bralette, panty y liguero con herrajes dorados', activo: true, created_at: '2026-01-01T00:00:00.000Z' },
  { id: 4, nombre: 'Top Corsetero Seda', sku_base: 'PRD-BLU-001', tipo_producto_id: 3, precio_base: 145000, descripcion: 'Blusa top estilo corset con copas prehormadas', activo: true, created_at: '2026-01-01T00:00:00.000Z' },
]

export const variantes: Variante[] = [
  { id: 1, producto_id: 1, talla: 'S', sku: 'PRD-COR-001-S', stock_actual: 8, created_at: '2026-01-01T00:00:00.000Z' },
  { id: 2, producto_id: 1, talla: 'M', sku: 'PRD-COR-001-M', stock_actual: 12, created_at: '2026-01-01T00:00:00.000Z' },
  { id: 3, producto_id: 1, talla: 'L', sku: 'PRD-COR-001-L', stock_actual: 5, created_at: '2026-01-01T00:00:00.000Z' },
  { id: 4, producto_id: 2, talla: '32B', sku: 'PRD-LEN-001-32B', stock_actual: 10, created_at: '2026-01-01T00:00:00.000Z' },
  { id: 5, producto_id: 2, talla: '34B', sku: 'PRD-LEN-001-34B', stock_actual: 15, created_at: '2026-01-01T00:00:00.000Z' },
]

export const bomInsumos: BomInsumo[] = [
  { id: 1, producto_id: 1, insumo_id: 1, cantidad_requerida: 0.8, desperdicio_pct: 5, created_at: '2026-01-01T00:00:00.000Z' },
  { id: 2, producto_id: 1, insumo_id: 6, cantidad_requerida: 2.5, desperdicio_pct: 2, created_at: '2026-01-01T00:00:00.000Z' },
  { id: 3, producto_id: 1, insumo_id: 4, cantidad_requerida: 14, desperdicio_pct: 0, created_at: '2026-01-01T00:00:00.000Z' },
  { id: 4, producto_id: 2, insumo_id: 2, cantidad_requerida: 0.6, desperdicio_pct: 8, created_at: '2026-01-01T00:00:00.000Z' },
  { id: 5, producto_id: 2, insumo_id: 3, cantidad_requerida: 6, desperdicio_pct: 0, created_at: '2026-01-01T00:00:00.000Z' },
]

export const bomProductos: BomProducto[] = []

export const ventas: Venta[] = [
  {
    id: 1,
    codigo: 'VEN-2026-001',
    fecha: '2026-08-18',
    cliente_id: 1,
    total: 378000,
    descuento: 0,
    estado: 'completada',
    canal: 'Tienda Online',
    es_regalo: false,
    observaciones: 'Entregar en portería',
    items: [
      { id: 1, venta_id: 1, producto_id: 1, variante_id: 2, cantidad: 2, precio_unitario: 189000, subtotal: 378000 },
    ],
    created_at: '2026-08-18T14:30:00.000Z',
  },
  {
    id: 2,
    codigo: 'VEN-2026-002',
    fecha: '2026-08-19',
    cliente_id: 2,
    total: 230000,
    descuento: 0,
    estado: 'completada',
    canal: 'WhatsApp',
    es_regalo: true,
    observaciones: 'Empacar con tarjeta dedicatoria',
    items: [
      { id: 2, venta_id: 2, producto_id: 2, variante_id: 5, cantidad: 2, precio_unitario: 115000, subtotal: 230000 },
    ],
    created_at: '2026-08-19T10:15:00.000Z',
  },
  {
    id: 3,
    codigo: 'VEN-2026-003',
    fecha: '2026-08-20',
    cliente_id: 3,
    total: 220000,
    descuento: 0,
    estado: 'completada',
    canal: 'Showroom Medellín',
    es_regalo: false,
    items: [
      { id: 3, venta_id: 3, producto_id: 3, variante_id: null, cantidad: 1, precio_unitario: 220000, subtotal: 220000 },
    ],
    created_at: '2026-08-20T16:45:00.000Z',
  },
]

export const devoluciones: Devolucion[] = [
  { id: 1, venta_id: 1, fecha: '2026-08-19', motivo: 'Cambio de talla por preferencia de ajuste', monto: 189000, estado: 'completada', created_at: '2026-08-19T00:00:00.000Z' },
]

export const socios: Socio[] = [
  { id: 1, nombre: 'Socio Fundador A', email: 'socio1@arpia.com', telefono: '+57 300 111 2233', participacion_pct: 60, activo: true, created_at: '2026-01-01T00:00:00.000Z' },
  { id: 2, nombre: 'Socio Inversionista B', email: 'socio2@arpia.com', telefono: '+57 300 444 5566', participacion_pct: 40, activo: true, created_at: '2026-01-01T00:00:00.000Z' },
]

export const movimientos: MovimientoFinanciero[] = [
  { id: 1, fecha: '2026-08-01', tipo: 'ingreso', categoria: 'Aporte Capital', descripcion: 'Aporte inicial de trabajo', monto: 15000000, socio_id: 1, created_at: '2026-08-01T00:00:00.000Z' },
  { id: 2, fecha: '2026-08-02', tipo: 'gasto', categoria: 'Materia Prima', descripcion: 'Compra inicial de sedas y herrajes', monto: 1226000, created_at: '2026-08-02T00:00:00.000Z' },
  { id: 3, fecha: '2026-08-05', tipo: 'gasto', categoria: 'Arriendo', descripcion: 'Canon mensual taller de confección', monto: 1800000, created_at: '2026-08-05T00:00:00.000Z' },
  { id: 4, fecha: '2026-08-18', tipo: 'ingreso', categoria: 'Ventas', descripcion: 'Venta VEN-2026-001 (Tienda Online)', monto: 378000, created_at: '2026-08-18T00:00:00.000Z' },
  { id: 5, fecha: '2026-08-19', tipo: 'ingreso', categoria: 'Ventas', descripcion: 'Venta VEN-2026-002 (WhatsApp)', monto: 230000, created_at: '2026-08-19T00:00:00.000Z' },
  { id: 6, fecha: '2026-08-20', tipo: 'ingreso', categoria: 'Ventas', descripcion: 'Venta VEN-2026-003 (Showroom)', monto: 220000, created_at: '2026-08-20T00:00:00.000Z' },
]

export const omisiones: Omision[] = [
  { id: 1, fase: 'Fase 1', nivel: 'Alta', hoja: 'Compras', fila: 14, descripcion: 'Falta registrar número de factura del proveedor de tintes', resuelta: false, created_at: '2026-08-15T00:00:00.000Z' },
  { id: 2, fase: 'Fase 1', nivel: 'Media', hoja: 'Inventario', fila: 28, descripcion: 'Conteo físico pendiente para cajas de empaque premium', resuelta: true, created_at: '2026-08-16T00:00:00.000Z' },
]

export const nextId = {
  user: 10,
  insumo: 10,
  compra: 10,
  cliente: 10,
  tipoProducto: 10,
  producto: 10,
  variante: 10,
  bomInsumo: 10,
  bomProducto: 10,
  venta: 10,
  devolucion: 10,
  movimiento: 10,
  socio: 10,
}

export function paginate<T>(items: T[], query?: Record<string, unknown>) {
  const limit = Math.max(1, Number(query?.limit) || 50)
  const offset = Math.max(0, Number(query?.offset) || 0)
  const total = items.length
  const paginated = items.slice(offset, offset + limit)
  return { items: paginated, total, limit, offset }
}

/**
 * Universal Route Resolver: handles method, path, query and body.
 */
export function handleMockApiRequest(
  method: string,
  rawPath: string,
  body: Record<string, unknown> = {},
  queryParams: Record<string, unknown> = {},
  headers: Record<string, unknown> = {},
): { status: number; data: unknown } {
  const m = method.toUpperCase()
  // Strip query and normalize
  const path = rawPath.replace(/\?.*$/, '').replace(/^\/api\/v1/, '').replace(/^\/api/, '') || '/'

  // --- Auth ---
  if (path === '/auth/login' && m === 'POST') {
    const { email } = (body || {}) as { email?: string }
    const normalized = (email || '').trim().toLowerCase()
    let user = users.find((u) => u.email.toLowerCase() === normalized)
    if (!user) {
      if (normalized.includes('admin')) user = users[0]
      else if (normalized.includes('operador')) user = users[1]
      else if (normalized.includes('consulta') || normalized.includes('auditor')) user = users[2]
      else user = users[0]
    }
    return {
      status: 200,
      data: {
        access_token: `ais_token_${user.id}_${Date.now()}`,
        refresh_token: `ais_refresh_${user.id}_${Date.now()}`,
        token_type: 'bearer',
        rol: user.rol,
      },
    }
  }

  if (path === '/auth/refresh' && m === 'POST') {
    const { refresh_token } = body || {}
    let user = users[0]
    if (typeof refresh_token === 'string') {
      const match = refresh_token.match(/^ais_refresh_(\d+)_/)
      if (match) {
        const uid = Number(match[1])
        const found = users.find((u) => u.id === uid)
        if (found) user = found
      }
    }
    return {
      status: 200,
      data: {
        access_token: `ais_token_${user.id}_${Date.now()}`,
        refresh_token: `ais_refresh_${user.id}_${Date.now()}`,
        token_type: 'bearer',
        rol: user.rol,
      },
    }
  }

  if (path === '/auth/logout' && m === 'POST') {
    return { status: 204, data: null }
  }

  if (path === '/auth/me' && m === 'GET') {
    const authHeader = String(headers.authorization || headers.Authorization || '')
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
    return { status: 200, data: user }
  }

  // --- Insumos & Categorias ---
  if (path === '/categorias-insumos' && m === 'GET') {
    return { status: 200, data: paginate(categoriasInsumos, queryParams) }
  }
  if (path === '/categorias-insumos' && m === 'POST') {
    const item: CategoriaInsumo = {
      id: nextId.insumo++,
      nombre: body.nombre,
      descripcion: body.descripcion,
      created_at: new Date().toISOString(),
    }
    categoriasInsumos.push(item)
    return { status: 201, data: item }
  }

  if (path === '/insumos' && m === 'GET') {
    let list = [...insumos]
    if (queryParams.categoria_id) {
      list = list.filter((i) => i.categoria_id === Number(queryParams.categoria_id))
    }
    if (queryParams.q) {
      const q = String(queryParams.q).toLowerCase()
      list = list.filter((i) => i.nombre.toLowerCase().includes(q) || (i.codigo && i.codigo.toLowerCase().includes(q)))
    }
    return { status: 200, data: paginate(list, queryParams) }
  }

  if (/^\/insumos\/\d+$/.test(path) && m === 'GET') {
    const id = Number(path.split('/')[2])
    const item = insumos.find((i) => i.id === id)
    if (item) return { status: 200, data: item }
    return { status: 404, data: { detail: 'Insumo not found' } }
  }

  if (path === '/insumos' && m === 'POST') {
    const item: Insumo = {
      id: nextId.insumo++,
      nombre: body.nombre,
      codigo: body.codigo || `INS-${Date.now().toString().slice(-4)}`,
      categoria_id: Number(body.categoria_id),
      unidad_medida: body.unidad_medida || 'un',
      stock_actual: Number(body.stock_actual) || 0,
      stock_minimo: Number(body.stock_minimo) || 0,
      costo_unitario: Number(body.costo_unitario) || 0,
      costo_promedio_ponderado: Number(body.costo_unitario) || 0,
      ultimo_costo_compra: Number(body.costo_unitario) || 0,
      proveedor_id: body.proveedor_id,
      created_at: new Date().toISOString(),
    }
    insumos.unshift(item)
    return { status: 201, data: item }
  }

  if (/^\/insumos\/\d+$/.test(path) && (m === 'PUT' || m === 'PATCH')) {
    const id = Number(path.split('/')[2])
    const idx = insumos.findIndex((i) => i.id === id)
    if (idx !== -1) {
      insumos[idx] = { ...insumos[idx], ...body }
      return { status: 200, data: insumos[idx] }
    }
    return { status: 404, data: { detail: 'Insumo not found' } }
  }

  if (/^\/insumos\/\d+$/.test(path) && m === 'DELETE') {
    const id = Number(path.split('/')[2])
    const idx = insumos.findIndex((i) => i.id === id)
    if (idx !== -1) insumos.splice(idx, 1)
    return { status: 204, data: null }
  }

  // --- Compras ---
  if (path === '/compras-insumos' && m === 'GET') {
    let list = [...comprasInsumos]
    if (queryParams.insumo_id) {
      list = list.filter((c) => c.insumo_id === Number(queryParams.insumo_id))
    }
    return { status: 200, data: paginate(list, queryParams) }
  }

  if (path === '/compras-insumos' && m === 'POST') {
    const cantidad = Number(body.cantidad) || 1
    const costo_unitario = Number(body.costo_unitario) || (Number(body.costo_total) / cantidad)
    const costo_total = Number(body.costo_total) || (cantidad * costo_unitario)
    const item: CompraInsumo = {
      id: nextId.compra++,
      insumo_id: Number(body.insumo_id),
      cantidad,
      costo_unitario,
      costo_total,
      fecha_compra: body.fecha_compra || new Date().toISOString().split('T')[0],
      factura: body.factura,
      proveedor_id: body.proveedor_id,
      modo: body.modo || 'UNIT',
      created_at: new Date().toISOString(),
    }
    comprasInsumos.unshift(item)

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
    return { status: 201, data: item }
  }

  // --- Clientes ---
  if (path === '/clientes' && m === 'GET') {
    let list = [...clientes]
    if (queryParams.q) {
      const q = String(queryParams.q).toLowerCase()
      list = list.filter((c) => c.nombre.toLowerCase().includes(q) || (c.email && c.email.toLowerCase().includes(q)))
    }
    return { status: 200, data: paginate(list, queryParams) }
  }

  if (path === '/clientes' && m === 'POST') {
    const item: Cliente = {
      id: nextId.cliente++,
      nombre: body.nombre,
      documento: body.documento,
      telefono: body.telefono,
      email: body.email,
      ciudad: body.ciudad,
      direccion: body.direccion,
      created_at: new Date().toISOString(),
    }
    clientes.unshift(item)
    return { status: 201, data: item }
  }

  // --- Tipos Productos & Productos ---
  if (path === '/tipos-producto' && m === 'GET') {
    return { status: 200, data: paginate(tiposProductos, queryParams) }
  }

  if (path === '/tipos-producto' && m === 'POST') {
    const item: TipoProducto = {
      id: nextId.tipoProducto++,
      nombre: body.nombre,
      descripcion: body.descripcion,
      created_at: new Date().toISOString(),
    }
    tiposProductos.push(item)
    return { status: 201, data: item }
  }

  if (path === '/productos' && m === 'GET') {
    let list = [...productos]
    if (queryParams.tipo_producto_id) {
      list = list.filter((p) => p.tipo_producto_id === Number(queryParams.tipo_producto_id))
    }
    if (queryParams.q) {
      const q = String(queryParams.q).toLowerCase()
      list = list.filter((p) => p.nombre.toLowerCase().includes(q) || p.sku_base.toLowerCase().includes(q))
    }
    return { status: 200, data: paginate(list, queryParams) }
  }

  if (/^\/productos\/\d+$/.test(path) && m === 'GET') {
    const id = Number(path.split('/')[2])
    const item = productos.find((p) => p.id === id)
    if (item) return { status: 200, data: item }
    return { status: 404, data: { detail: 'Producto not found' } }
  }

  if (path === '/productos' && m === 'POST') {
    const item: Producto = {
      id: nextId.producto++,
      nombre: body.nombre,
      sku_base: body.sku_base || `PRD-${Date.now().toString().slice(-4)}`,
      tipo_producto_id: Number(body.tipo_producto_id),
      precio_base: Number(body.precio_base) || 0,
      descripcion: body.descripcion,
      activo: body.activo ?? true,
      created_at: new Date().toISOString(),
    }
    productos.unshift(item)
    return { status: 201, data: item }
  }

  // --- Variantes ---
  if (/^\/productos\/\d+\/variantes$/.test(path) && m === 'GET') {
    const id = Number(path.split('/')[2])
    return { status: 200, data: variantes.filter((v) => v.producto_id === id) }
  }

  if (/^\/productos\/\d+\/variantes$/.test(path) && m === 'POST') {
    const producto_id = Number(path.split('/')[2])
    const prod = productos.find((p) => p.id === producto_id)
    const item: Variante = {
      id: nextId.variante++,
      producto_id,
      talla: body.talla,
      sku: body.sku || `${prod ? prod.sku_base : 'SKU'}-${body.talla}`,
      precio_override: body.precio_override ? Number(body.precio_override) : null,
      stock_actual: Number(body.stock_actual) || 0,
      created_at: new Date().toISOString(),
    }
    variantes.push(item)
    return { status: 201, data: item }
  }

  // --- BOM ---
  if (/^\/productos\/\d+\/bom\/insumos$/.test(path) && m === 'GET') {
    const id = Number(path.split('/')[2])
    return { status: 200, data: bomInsumos.filter((b) => b.producto_id === id) }
  }

  if (/^\/productos\/\d+\/bom\/insumos$/.test(path) && m === 'POST') {
    const producto_id = Number(path.split('/')[2])
    const item: BomInsumo = {
      id: nextId.bomInsumo++,
      producto_id,
      insumo_id: Number(body.insumo_id),
      cantidad_requerida: Number(body.cantidad_requerida) || 1,
      desperdicio_pct: Number(body.desperdicio_pct) || 0,
      created_at: new Date().toISOString(),
    }
    bomInsumos.push(item)
    return { status: 201, data: item }
  }

  if (/^\/productos\/\d+\/costo$/.test(path) && m === 'GET') {
    const producto_id = Number(path.split('/')[2])
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
    return {
      status: 200,
      data: {
        producto_id,
        nombre_producto: prod ? prod.nombre : 'Producto',
        costo_total: Math.round(costo_directo),
        costo_directo_insumos: Math.round(costo_directo),
        costo_subproductos: 0,
        desglose_insumos,
        desglose_subproductos: [],
      },
    }
  }

  // --- Ventas ---
  if (path === '/ventas' && m === 'GET') {
    let list = [...ventas]
    if (queryParams.estado) {
      list = list.filter((v) => v.estado === queryParams.estado)
    }
    if (queryParams.q) {
      const q = String(queryParams.q).toLowerCase()
      list = list.filter((v) => v.codigo.toLowerCase().includes(q) || v.canal.toLowerCase().includes(q))
    }
    return { status: 200, data: paginate(list, queryParams) }
  }

  if (path === '/ventas' && m === 'POST') {
    const rawItems = (body.items || []) as Array<{ producto_id: number; variante_id?: number | null; cantidad: number; precio_unitario: number }>
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
      fecha: body.fecha || new Date().toISOString().split('T')[0],
      cliente_id: body.cliente_id ? Number(body.cliente_id) : null,
      total: body.total ? Number(body.total) : total,
      descuento: Number(body.descuento) || 0,
      estado: 'completada',
      canal: body.canal || 'Tienda Online',
      es_regalo: Boolean(body.es_regalo),
      observaciones: body.observaciones,
      items: processedItems,
      created_at: new Date().toISOString(),
    }
    ventas.unshift(item)

    movimientos.unshift({
      id: nextId.movimiento++,
      fecha: item.fecha,
      tipo: 'ingreso',
      categoria: 'Ventas',
      descripcion: `Venta ${item.codigo} (${item.canal})`,
      monto: item.total,
      created_at: new Date().toISOString(),
    })

    return { status: 201, data: item }
  }

  // --- Devoluciones ---
  if (path === '/devoluciones' && m === 'GET') {
    return { status: 200, data: paginate(devoluciones, queryParams) }
  }

  if (path === '/devoluciones' && m === 'POST') {
    const item: Devolucion = {
      id: nextId.devolucion++,
      venta_id: Number(body.venta_id),
      fecha: body.fecha || new Date().toISOString().split('T')[0],
      motivo: body.motivo,
      monto: Number(body.monto) || 0,
      estado: 'completada',
      created_at: new Date().toISOString(),
    }
    devoluciones.unshift(item)
    return { status: 201, data: item }
  }

  // --- Finanzas ---
  if (path === '/finanzas/movimientos' && m === 'GET') {
    let list = [...movimientos]
    if (queryParams.tipo) {
      list = list.filter((m) => m.tipo === queryParams.tipo)
    }
    return { status: 200, data: paginate(list, queryParams) }
  }

  if (path === '/finanzas/movimientos' && m === 'POST') {
    const item: MovimientoFinanciero = {
      id: nextId.movimiento++,
      fecha: body.fecha || new Date().toISOString().split('T')[0],
      tipo: body.tipo,
      categoria: body.categoria,
      descripcion: body.descripcion,
      monto: Number(body.monto),
      socio_id: body.socio_id ? Number(body.socio_id) : null,
      created_at: new Date().toISOString(),
    }
    movimientos.unshift(item)
    return { status: 201, data: item }
  }

  if (path === '/finanzas/socios' && m === 'GET') {
    return { status: 200, data: paginate(socios, queryParams) }
  }

  if (path === '/finanzas/socios' && m === 'POST') {
    const item: Socio = {
      id: nextId.socio++,
      nombre: body.nombre,
      email: body.email,
      telefono: body.telefono,
      participacion_pct: Number(body.participacion_pct) || 0,
      activo: true,
      created_at: new Date().toISOString(),
    }
    socios.push(item)
    return { status: 201, data: item }
  }

  // --- Analiticos ---
  if (path === '/analiticos/ventas-mensuales' && m === 'GET') {
    return {
      status: 200,
      data: [
        { periodo: '2026-03', total_ventas: 4200000, cantidad_ventas: 18 },
        { periodo: '2026-04', total_ventas: 5800000, cantidad_ventas: 24 },
        { periodo: '2026-05', total_ventas: 7100000, cantidad_ventas: 31 },
        { periodo: '2026-06', total_ventas: 6900000, cantidad_ventas: 29 },
        { periodo: '2026-07', total_ventas: 8450000, cantidad_ventas: 36 },
        { periodo: '2026-08', total_ventas: 9200000, cantidad_ventas: 41 },
      ],
    }
  }

  if (path === '/analiticos/insumos-bajo-stock' && m === 'GET') {
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
    return { status: 200, data: bajoStock }
  }

  if (path === '/analiticos/margen-por-producto' && m === 'GET') {
    return {
      status: 200,
      data: [
        { producto_id: 1, nombre: 'Corset Nocturna', precio_venta: 189000, costo_estimado: 48500, margen_bruto: 140500, margen_pct: 74.3 },
        { producto_id: 2, nombre: 'Bralette Encaje Borgoña', precio_venta: 115000, costo_estimado: 28000, margen_bruto: 87000, margen_pct: 75.6 },
        { producto_id: 3, nombre: 'Set Lencería Arpía Gold', precio_venta: 220000, costo_estimado: 62000, margen_bruto: 158000, margen_pct: 71.8 },
      ],
    }
  }

  if (path === '/analiticos/top-productos' && m === 'GET') {
    return {
      status: 200,
      data: [
        { producto_id: 1, nombre: 'Corset Nocturna', total_unidades: 28, total_ingresos: 5292000 },
        { producto_id: 2, nombre: 'Bralette Encaje Borgoña', total_unidades: 22, total_ingresos: 2530000 },
        { producto_id: 3, nombre: 'Set Lencería Arpía Gold', total_unidades: 14, total_ingresos: 3080000 },
      ],
    }
  }

  if (path === '/analiticos/top-insumos' && m === 'GET') {
    return {
      status: 200,
      data: [
        { insumo_id: 1, nombre: 'Seda Satín Negro', total_usado: 22.4, costo_total_consumido: 403200 },
        { insumo_id: 2, nombre: 'Encaje Francés Rojo', total_usado: 13.2, costo_total_consumido: 310200 },
        { insumo_id: 3, nombre: 'Argollas Doradas 10mm', total_usado: 336, costo_total_consumido: 141120 },
      ],
    }
  }

  if (path === '/analiticos/finanzas-mensuales' && m === 'GET') {
    return {
      status: 200,
      data: [
        { periodo: '2026-03', ingresos: 4200000, gastos: 2100000, balance: 2100000 },
        { periodo: '2026-04', ingresos: 5800000, gastos: 2800000, balance: 3000000 },
        { periodo: '2026-05', ingresos: 7100000, gastos: 3200000, balance: 3900000 },
        { periodo: '2026-06', ingresos: 6900000, gastos: 2950000, balance: 3950000 },
        { periodo: '2026-07', ingresos: 8450000, gastos: 3600000, balance: 4850000 },
        { periodo: '2026-08', ingresos: 9200000, gastos: 3900000, balance: 5300000 },
      ],
    }
  }

  if (path === '/analiticos/resumen' && m === 'GET') {
    const totalVentas = ventas.reduce((acc, v) => acc + (v.estado === 'completada' ? v.total : 0), 0)
    const insumosBajo = insumos.filter((i) => i.stock_actual <= i.stock_minimo).length
    return {
      status: 200,
      data: {
        total_ventas_periodo: totalVentas + 9200000,
        total_ordenes: ventas.length + 41,
        ticket_promedio: 198000,
        insumos_criticos: insumosBajo,
        margen_promedio_pct: 73.9,
        balance_neto_periodo: 5300000,
      },
    }
  }

  // --- Omisiones ---
  if (path === '/omisiones' && m === 'GET') {
    return { status: 200, data: paginate(omisiones, queryParams) }
  }

  // --- Usuarios ---
  if (path === '/usuarios' && m === 'GET') {
    return { status: 200, data: paginate(users, queryParams) }
  }

  if (path === '/usuarios' && m === 'POST') {
    const item: User = {
      id: nextId.user++,
      nombre: body.nombre,
      email: body.email,
      rol: body.rol || 'operador',
      activo: body.activo ?? true,
      created_at: new Date().toISOString(),
    }
    users.push(item)
    return { status: 201, data: item }
  }

  return { status: 200, data: { status: 'ok' } }
}
