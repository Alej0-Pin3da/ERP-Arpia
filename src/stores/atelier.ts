/**
 * @deprecated Mock Pinia store — retained for VITE_USE_MOCK=true only.
 * Real data now lives in Postgres via FastAPI /api/v1. Use
 * src/services/api/* + src/composables/useClientes|useVentas|useSocios|useFinanzas when
 * VITE_USE_MOCK=false. This store will be removed in Fase 5.
 * @see src/composables/useMode.ts — isMock / GET /api/__mode badge
 * @see src/services/api/clientes.ts, ventas.ts, socios.ts, liquidaciones.ts, anticipos.ts
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface InsumoAtelier {
  id: number
  codigo: string
  nombre: string
  descripcion: string
  tipo: 'Directo' | 'Indirecto'
  categoria: string
  ubicacion: string
  proveedor: string
  stock_actual: number
  stock_minimo: number
  unidad_medida: string
  costo_unitario: number
  valor_total: number
}

export interface BomItem {
  id: number
  insumo_id: number
  nombre: string
  tipo: 'Directo' | 'Indirecto'
  consumo_unitario: number
  unidad: string
  merma_pct: number
  costo_unitario: number
  subtotal: number
  ancho?: number
  alto?: number
  cantidad_cms?: number
}

export interface FaseProduccion {
  nombre: string
  descripcion: string
  minutos: number
}

export interface RecetaBOM {
  id: number
  codigo: string
  nombre: string
  categoria: string
  linea: string
  descripcion: string
  tiempo_confeccion_min: number
  insumos_count: number
  costo_insumos: number
  mano_obra: number
  cif_energia: number
  costo_total_unitario: number
  precio_venta: number
  markup_pct: number
  recomendaciones_taller: string
  items: BomItem[]
  fases: FaseProduccion[]
}

export interface PrendaVariante {
  id: number
  talla: string
  color: string
  sku: string
  stock_fisico: number
  reservado: number
  disponible: number
}

export interface PrendaConfeccionada {
  id: number
  codigo: string
  nombre: string
  categoria: string
  costo_base: number
  precio_venta: number
  fisico_total: number
  disponible_total: number
  variantes: PrendaVariante[]
}

export interface MedidasAnatomicas {
  busto?: number | string
  cintura?: number | string
  cadera?: number | string
  espalda?: number | string
  talle?: number | string
  largo?: number | string
}

export type TallaEstandarPrenda = 'XXS' | 'XS' | 'S' | 'M' | 'L' | 'XL' | 'SIN_TALLA' | 'TALLA_UNICA'

export interface ClienteCRM {
  id: number
  nombre: string
  tipo: string
  telefono: string
  email: string
  ciudad?: string
  direccion?: string
  pedidos_count: number
  total_compras: number
  talla_habitual: string // 'XXS' | 'XS' | 'S' | 'M' | 'L' | 'XL' | 'Sin Talla' | 'Talla Única'
  talla_superior?: string
  talla_inferior?: string
  categoria_preferida: string // 'Corsetería & Tops', 'Faldas & Conjuntos', 'Tote Bags & Merch', 'Accesorios'
  tipo_producto_frecuente?: 'PRENDAS_TALLAS' | 'PRODUCTOS_SIN_TALLA' | 'AMBOS'
  notas?: string
  medidas?: MedidasAnatomicas
}

export interface PedidoProduccion {
  id: number
  codigo: string
  cliente_id: number
  cliente_nombre: string
  prenda_nombre: string
  estado: 'COTIZADO' | 'RESERVADO' | 'CORTE' | 'COSTURA' | 'ACABADOS' | 'CALIDAD' | 'LISTO' | 'ENTREGADO'
  precio_venta: number
  costo_produccion: number
  utilidad_neta: number
  margen_pct: number
  fecha: string
  observaciones?: string
}

export interface ItemVentaAtelier {
  id: number
  producto_id?: number | null
  nombre_prenda: string
  talla: string
  color: string
  cantidad: number
  precio_unitario: number
  costo_unitario: number
  subtotal: number
  costo_subtotal: number
}

export interface VentaAtelier {
  id: number
  codigo: string
  cliente_id?: number | null
  cliente_nombre: string
  fecha: string
  canal: string
  metodo_pago: string
  estado: 'COMPLETADA' | 'PENDIENTE' | 'ANULADA'
  items: ItemVentaAtelier[]
  subtotal: number
  descuento_porcentaje: number
  descuento_valor: number
  total_venta: number
  costo_total: number
  ganancia_neta: number
  margen_pct: number
  reinversion_40: number
  margarita_30: number
  valqui_30: number
  observaciones?: string
  descontar_inventario?: boolean
}

export interface SociaAtelier {
  id: number
  nombre: string
  rol: string
  porcentaje: number
  es_fondo_taller?: boolean
  telefono?: string
  email?: string
  banco?: string
  tipo_cuenta?: string
  numero_cuenta?: string
  titular_cuenta?: string
  activo: boolean
  notas?: string
}

export interface LiquidacionSociaItem {
  socia_id: number
  nombre_socia: string
  rol_socia: string
  porcentaje: number
  monto_bruto: number
  deduccion_anticipos: number
  monto_neto_pagar: number
  estado_pago: 'PAGADO' | 'PENDIENTE' | 'RETENIDO'
  fecha_pago?: string
  comprobante_transferencia?: string
  banco_destino?: string
}

export interface LiquidacionSocias {
  id: number
  codigo: string
  periodo: string
  fecha_cierre: string
  total_ventas_brutas: number
  costo_taller_insumos: number
  gastos_operativos: number
  utilidad_neta_total: number
  fondo_reinversion_monto: number
  utilidad_repartible: number
  estado: 'BORRADOR' | 'APROBADA' | 'PAGADA'
  distribucion: LiquidacionSociaItem[]
  observaciones?: string
  created_at: string
}

export interface AnticipoSocia {
  id: number
  socia_id: number
  nombre_socia: string
  fecha: string
  monto: number
  concepto: string
  metodo_desembolso: string
  estado: 'DESCONTADO' | 'PENDIENTE_DESCUENTO' | 'ANULADO'
  liquidacion_id?: number | null
  comprobante?: string
  observaciones?: string
}

// Interfaces Maestras Atelier
export interface ProveedorMaestro {
  id: number
  nombre: string
  categoria: string // 'Telas Principales', 'Herrajes & Corsetería', 'Lonas & Estampación', 'Hilos & Accesorios'
  ciudad: string
  contacto: string
  telefono: string
  email: string
  tiempo_entrega_dias: number
  condicion_pago: string
  calificacion: number
  activo: boolean
  notas?: string
}

export interface CanalVentaMaestro {
  id: number
  nombre: string
  tipo: 'FISICO' | 'DIGITAL' | 'EVENTO'
  comision_pct: number
  costo_fijo_mensual: number
  activo: boolean
  descripcion: string
}

export interface MetodoPagoMaestro {
  id: number
  nombre: string
  tipo: 'TRANSFERENCIA' | 'BILLETERA_DIGITAL' | 'EFECTIVO' | 'PASARELA_DATAFONO'
  comision_pct: number
  tiempo_acreditacion: string
  activo: boolean
  datos_cuenta?: string
}

export interface CategoriaColeccionMaestro {
  id: number
  nombre: string
  tipo_talla: 'CON_TALLAS_ESTANDAR' | 'SIN_TALLA_MERCH' | 'TALLA_UNICA'
  descripcion: string
  margen_meta_pct: number
  total_modelos: number
  activo: boolean
}

export interface UbicacionTallerMaestro {
  id: number
  codigo: string
  nombre: string
  tipo: 'ROLLOS_TELAS' | 'GAVETAS_HERRAJES' | 'PERCHERO_SHOWROOM' | 'ACCESORIOS_BODEGA'
  capacidad: string
  observaciones: string
}

export interface TallaEstandarMaestro {
  id: number
  talla: string // 'XXS', 'XS', 'S', 'M', 'L', 'XL', etc.
  busto: string // '78 – 82 cm'
  cintura: string // '58 – 62 cm'
  cadera: string // '84 – 88 cm'
  reduccion_corset: string // '-4 cm a -6 cm'
  descripcion: string
  orden: number
  activo: boolean
}

export interface ProductoSinTallaMaestro {
  id: number
  nombre: string
  categoria: string // 'Tote Bags', 'Scrunchies & Accesorios', 'Pines & Joyería', 'Merchandising'
  dimensiones: string
  materiales: string
  descripcion: string
  precio_sugerido: number
  activo: boolean
}

export interface ParametrosCosteoMaestro {
  costo_minuto_costura: number
  costo_hora_patronaje: number
  margen_meta_global_pct: number
  desperdicio_textil_default_pct: number
  iva_regimen_pct: number
  distribucion_reinversion_pct: number
  distribucion_margara_pct: number
  distribucion_valqui_pct: number
}


export const useAtelierStore = defineStore('atelier', () => {
  // 1. Insumos
  const insumos = ref<InsumoAtelier[]>([
    {
      id: 1,
      codigo: 'TEL-TUL-100',
      nombre: 'Ref 100 24 cm Tul Bordado Negro',
      descripcion: 'Ancho 24 cm. Encaje bordado de lujo para corsetería y bustiers.',
      tipo: 'Directo',
      categoria: 'Telas Principales',
      ubicacion: 'Estante Telas Atenea A1',
      proveedor: 'Atenea Bordados y Encajes',
      stock_actual: 39,
      stock_minimo: 10,
      unidad_medida: 'm',
      costo_unitario: 10512.82,
      valor_total: 409999.98,
    },
    {
      id: 2,
      codigo: 'TEL-TUL-159',
      nombre: 'Ref 159 24 cm Tul Bordado Rojo Pastel',
      descripcion: 'Ancho 24 cm. Utilizado para Set Aelo y conjuntos rojo pastel.',
      tipo: 'Directo',
      categoria: 'Telas Principales',
      ubicacion: 'Estante Telas Atenea A2',
      proveedor: 'Atenea Bordados y Encajes',
      stock_actual: 21,
      stock_minimo: 6,
      unidad_medida: 'm',
      costo_unitario: 9761.90,
      valor_total: 204999.90,
    },
    {
      id: 3,
      codigo: 'TEL-ENC-BIC',
      nombre: 'Encaje Chantilly Blanco & Negro para Bicolor',
      descripcion: 'Encaje con pelitos para confección del Conjunto Bicolor Celeno.',
      tipo: 'Directo',
      categoria: 'Telas Principales',
      ubicacion: 'Cajón Encajes Bicolor',
      proveedor: 'Kilotelas',
      stock_actual: 19,
      stock_minimo: 8,
      unidad_medida: 'm',
      costo_unitario: 4000.00,
      valor_total: 76000.00,
    },
    {
      id: 4,
      codigo: 'TEL-ENC-RAM',
      nombre: 'Encaje de Ramitas Botánico',
      descripcion: 'Base ornamental para copas y piezas de bustiers.',
      tipo: 'Directo',
      categoria: 'Telas Principales',
      ubicacion: 'Estante Encajes Finos',
      proveedor: 'La Corsetería',
      stock_actual: 10,
      stock_minimo: 4,
      unidad_medida: 'm',
      costo_unitario: 3500.00,
      valor_total: 35000.00,
    },
    {
      id: 5,
      codigo: 'TEL-MAY-ILU',
      nombre: 'Tela Malla Ilustrada Sublimada Garra',
      descripcion: 'Malla estampada para Blusa Arpía Manga Larga y Manga Corta.',
      tipo: 'Directo',
      categoria: 'Telas Principales',
      ubicacion: 'Perchero Mallas Ilustradas',
      proveedor: 'Sublimación Pereira Textil',
      stock_actual: 15,
      stock_minimo: 5,
      unidad_medida: 'm',
      costo_unitario: 21600.00,
      valor_total: 324000.00,
    },
    {
      id: 6,
      codigo: 'TEL-POW-NEG',
      nombre: 'Powernet Negro Delgado Estructurante',
      descripcion: 'Tela de alta compresión para corsets y corpiños moldeadores.',
      tipo: 'Directo',
      categoria: 'Forros y Entretelas',
      ubicacion: 'Estante Mallas Compresión',
      proveedor: 'Tienda Cuadra Herrajes',
      stock_actual: 4,
      stock_minimo: 2,
      unidad_medida: 'm',
      costo_unitario: 18000.00,
      valor_total: 72000.00,
    },
    {
      id: 7,
      codigo: 'TEL-GAB-POL',
      nombre: 'Gabardina Ultra Poliéster',
      descripcion: 'Para faldas estructuradas (Falda Emily) y totebags.',
      tipo: 'Directo',
      categoria: 'Telas Principales',
      ubicacion: 'Rollo Gabardinas G1',
      proveedor: 'CasaTextil',
      stock_actual: 8,
      stock_minimo: 3,
      unidad_medida: 'm',
      costo_unitario: 18653.00,
      valor_total: 149224.00,
    },
    {
      id: 8,
      codigo: 'TEL-LIN-VER',
      nombre: 'Lino Vértigo',
      descripcion: 'Lino de caída premium para prendas casuales y corsets frescos.',
      tipo: 'Directo',
      categoria: 'Telas Principales',
      ubicacion: 'Estante Linos Naturales',
      proveedor: 'Kilotelas',
      stock_actual: 4.5,
      stock_minimo: 6,
      unidad_medida: 'm',
      costo_unitario: 17000.00,
      valor_total: 76500.00,
    },
    {
      id: 9,
      codigo: 'TEL-MAL-NEG',
      nombre: 'Mallatex Negra / Forro Copa',
      descripcion: 'Forro interior suave y transpirable para busto y copas.',
      tipo: 'Directo',
      categoria: 'Forros y Entretelas',
      ubicacion: 'Gaveta Mallas Forro',
      proveedor: 'Textiles F&M',
      stock_actual: 3,
      stock_minimo: 2,
      unidad_medida: 'm',
      costo_unitario: 8000.00,
      valor_total: 24000.00,
    },
    {
      id: 10,
      codigo: 'TEL-ENT-NEG',
      nombre: 'Tela Entrepierna Negra / Algodón',
      descripcion: '100% Algodón para refuerzo higiénico en pantys y tangas.',
      tipo: 'Directo',
      categoria: 'Forros y Entretelas',
      ubicacion: 'Cajón Algodones Puros',
      proveedor: 'Facol',
      stock_actual: 3,
      stock_minimo: 1.5,
      unidad_medida: 'm',
      costo_unitario: 6500.00,
      valor_total: 19500.00,
    },
    {
      id: 11,
      codigo: 'TEL-SAT-ELA',
      nombre: 'Satín Elástico Negro',
      descripcion: 'Brillo sedoso con elasticidad para detalles y sesgos.',
      tipo: 'Directo',
      categoria: 'Telas Principales',
      ubicacion: 'Estante Satines',
      proveedor: 'Kilotelas',
      stock_actual: 5,
      stock_minimo: 2,
      unidad_medida: 'm',
      costo_unitario: 7900.00,
      valor_total: 39500.00,
    },
    {
      id: 12,
      codigo: 'EMP-CAJ-GARRAS',
      nombre: 'Caja Regalo Colección "Saca las Garras"',
      descripcion: 'Empaque de lujo rígido con estampado dorado y papel seda negro.',
      tipo: 'Indirecto',
      categoria: 'Empaques y Avíos',
      ubicacion: 'Estante Cajas Showroom',
      proveedor: 'Litografía Central Pereira',
      stock_actual: 8,
      stock_minimo: 10,
      unidad_medida: 'un',
      costo_unitario: 14500.00,
      valor_total: 116000.00,
    },
  ])

  // 2. Recetas BOM
  const recetas = ref<RecetaBOM[]>([
    {
      id: 1,
      codigo: 'REC-ARP-05',
      nombre: 'Blusa Malla Garra Manga Larga (ML)',
      categoria: 'Blusas y Tops',
      linea: 'Prêt-à-Porter',
      descripcion: 'Blusa en tela malla ilustrada con estampado exclusivo Garra de Arpía. Manga larga con terminaciones fileteadas limpias.',
      tiempo_confeccion_min: 90,
      insumos_count: 1,
      costo_insumos: 20460,
      mano_obra: 0,
      cif_energia: 1101,
      costo_total_unitario: 21561,
      precio_venta: 90000,
      markup_pct: 76.04,
      recomendaciones_taller: 'Alinear la ilustración de las garras en el pecho y mangas.',
      items: [
        {
          id: 1,
          insumo_id: 5,
          nombre: 'Tela Malla Ilustrada Sublimada',
          tipo: 'Directo',
          consumo_unitario: 0.9,
          unidad: 'm',
          merma_pct: 4,
          costo_unitario: 21600,
          subtotal: 19440,
          ancho: 1,
          alto: 1,
          cantidad_cms: 1,
        },
      ],
      fases: [
        { nombre: '1. Trazado, Moldería y Corte', descripcion: 'Corte de piezas al hilo de tela, encajes y entretelas', minutos: 23 },
        { nombre: '2. Ensamble, Costura y Varillaje', descripcion: 'Armado de copas, unión de costadillos, fijación de sesgos y tapavarillas', minutos: 45 },
        { nombre: '3. Acabados, Ojalillos y Planchado', descripcion: 'Colocación de aros, elásticos, tensores, limpieza de hilos y vaporizado', minutos: 23 },
      ],
    },
    {
      id: 2,
      codigo: 'REC-ARP-01',
      nombre: 'Caja Colección "Saca las Garras" (Edición Especial)',
      categoria: 'Conjuntos y Sets',
      linea: 'Corsetería',
      descripcion: 'Conjunto completo insigne de Atelier Arpía. Incluye Bustier Ocípete, Corset Aelo, Conjunto Bicolor Celeno, Blusa Malla y Caja Regalo.',
      tiempo_confeccion_min: 480,
      insumos_count: 6,
      costo_insumos: 114984,
      mano_obra: 10000,
      cif_energia: 4404,
      costo_total_unitario: 129388,
      precio_venta: 360000,
      markup_pct: 64.06,
      recomendaciones_taller: 'Incluir tarjeta con sello de cera negra y dedicatoria personalizada.',
      items: [
        { id: 1, insumo_id: 1, nombre: 'Tul Bordado Negro 24cm', tipo: 'Directo', consumo_unitario: 2.2, unidad: 'm', merma_pct: 5, costo_unitario: 10512.82, subtotal: 23128 },
        { id: 2, insumo_id: 2, nombre: 'Tul Bordado Rojo Pastel', tipo: 'Directo', consumo_unitario: 1.8, unidad: 'm', merma_pct: 5, costo_unitario: 9761.90, subtotal: 17571 },
        { id: 3, insumo_id: 6, nombre: 'Powernet Negro Estructurante', tipo: 'Directo', consumo_unitario: 1.2, unidad: 'm', merma_pct: 4, costo_unitario: 18000, subtotal: 21600 },
        { id: 4, insumo_id: 5, nombre: 'Tela Malla Ilustrada', tipo: 'Directo', consumo_unitario: 0.9, unidad: 'm', merma_pct: 4, costo_unitario: 21600, subtotal: 19440 },
        { id: 5, insumo_id: 12, nombre: 'Caja Regalo Colección', tipo: 'Indirecto', consumo_unitario: 1, unidad: 'un', merma_pct: 0, costo_unitario: 14500, subtotal: 14500 },
        { id: 6, insumo_id: 11, nombre: 'Satín Elástico Negro', tipo: 'Directo', consumo_unitario: 2.3, unidad: 'm', merma_pct: 3, costo_unitario: 7900, subtotal: 18170 },
      ],
      fases: [
        { nombre: '1. Trazado, Moldería y Corte Multi-piezas', descripcion: 'Corte agrupado para 4 prendas de la colección', minutos: 120 },
        { nombre: '2. Costura de Alta Precisión & Varillado', descripcion: 'Ensamble simultáneo de corpiño y corsetería fina', minutos: 240 },
        { nombre: '3. Acabados, Control de Calidad y Embalaje', descripcion: 'Planchado, colocado de herrajes dorados y caja de presentación', minutos: 120 },
      ],
    },
    {
      id: 3,
      codigo: 'REC-ARP-06',
      nombre: 'Corset Estructurado "Garras"',
      categoria: 'Corsetería',
      linea: 'Corsetería',
      descripcion: 'Corset insignia con cortes anatómicos de alta compresión en powernet y lino, con ojales metálicos posteriores para entallado.',
      tiempo_confeccion_min: 180,
      insumos_count: 3,
      costo_insumos: 27991,
      mano_obra: 0,
      cif_energia: 1835,
      costo_total_unitario: 29826,
      precio_venta: 95000,
      markup_pct: 68.6,
      recomendaciones_taller: 'Reforzar las costuras centrales con pespunte doble y puntada de seguridad.',
      items: [
        { id: 1, insumo_id: 6, nombre: 'Powernet Negro', tipo: 'Directo', consumo_unitario: 0.8, unidad: 'm', merma_pct: 5, costo_unitario: 18000, subtotal: 14400 },
        { id: 2, insumo_id: 8, nombre: 'Lino Vértigo', tipo: 'Directo', consumo_unitario: 0.6, unidad: 'm', merma_pct: 5, costo_unitario: 17000, subtotal: 10200 },
        { id: 3, insumo_id: 9, nombre: 'Mallatex Forro', tipo: 'Directo', consumo_unitario: 0.4, unidad: 'm', merma_pct: 3, costo_unitario: 8000, subtotal: 3200 },
      ],
      fases: [
        { nombre: '1. Patronaje Anatómico y Corte', descripcion: 'Corte preciso de costadillos y delanteros', minutos: 45 },
        { nombre: '2. Ensamble, Unión y Canales de Varillas', descripcion: 'Inserción de varillas alemanas y forro', minutos: 90 },
        { nombre: '3. Ojalillado y Ajuste Posterior', descripcion: 'Remachado de ojales inoxidables y cinta de satén', minutos: 45 },
      ],
    },
    {
      id: 4,
      codigo: 'REC-ARP-08',
      nombre: 'Falda Estructurada "Emily"',
      categoria: 'Pantalones',
      linea: 'Prêt-à-Porter',
      descripcion: 'Falda en gabardina ultra poliéster con cortes sesgados y bolsillo invisible lateral.',
      tiempo_confeccion_min: 110,
      insumos_count: 2,
      costo_insumos: 22800,
      mano_obra: 0,
      cif_energia: 1200,
      costo_total_unitario: 24000,
      precio_venta: 85000,
      markup_pct: 71.76,
      recomendaciones_taller: 'Planchar con paño húmedo para fijar la estructura de la gabardina.',
      items: [
        { id: 1, insumo_id: 7, nombre: 'Gabardina Ultra Poliéster', tipo: 'Directo', consumo_unitario: 1.1, unidad: 'm', merma_pct: 4, costo_unitario: 18653, subtotal: 20518 },
        { id: 2, insumo_id: 9, nombre: 'Mallatex Forro', tipo: 'Directo', consumo_unitario: 0.25, unidad: 'm', merma_pct: 2, costo_unitario: 8000, subtotal: 2000 },
      ],
      fases: [
        { nombre: '1. Corte y Marcado de Pliegues', descripcion: 'Corte de tablero y pretina', minutos: 30 },
        { nombre: '2. Costura, Ensamble y Cierre Invisible', descripcion: 'Unión de costados y dobladillo ciego', minutos: 60 },
        { nombre: '3. Planchado Final', descripcion: 'Asentamiento de costuras', minutos: 20 },
      ],
    },
    {
      id: 5,
      codigo: 'REC-ARP-02',
      nombre: 'Set Aelo: Corset Encaje Rojo Pastel & Tanga',
      categoria: 'Corsetería',
      linea: 'Corsetería',
      descripcion: 'Conjunto sensual en tul rojo pastel con encaje botánico y panty graduable.',
      tiempo_confeccion_min: 150,
      insumos_count: 4,
      costo_insumos: 36500,
      mano_obra: 0,
      cif_energia: 1500,
      costo_total_unitario: 38000,
      precio_venta: 110000,
      markup_pct: 65.45,
      recomendaciones_taller: 'Usar aguja punta de bola #70 para evitar rotura de mallas en el tul rojo.',
      items: [
        { id: 1, insumo_id: 2, nombre: 'Tul Bordado Rojo Pastel', tipo: 'Directo', consumo_unitario: 1.6, unidad: 'm', merma_pct: 5, costo_unitario: 9761.90, subtotal: 15619 },
        { id: 2, insumo_id: 4, nombre: 'Encaje Ramitas', tipo: 'Directo', consumo_unitario: 1.2, unidad: 'm', merma_pct: 4, costo_unitario: 3500, subtotal: 4200 },
        { id: 3, insumo_id: 10, nombre: 'Tela Entrepierna Algodón', tipo: 'Directo', consumo_unitario: 0.15, unidad: 'm', merma_pct: 0, costo_unitario: 6500, subtotal: 975 },
        { id: 4, insumo_id: 11, nombre: 'Satín Elástico Negro', tipo: 'Directo', consumo_unitario: 1.8, unidad: 'm', merma_pct: 3, costo_unitario: 7900, subtotal: 14220 },
      ],
      fases: [
        { nombre: '1. Corte de Encajes Emparejados', descripcion: 'Simetría de flores en copas', minutos: 40 },
        { nombre: '2. Ensamble de Copas y Varillas', descripcion: 'Colocación de sesgos elásticos', minutos: 80 },
        { nombre: '3. Graduación de Elásticos y Tanga', descripcion: 'Colocación de tensores dorados', minutos: 30 },
      ],
    },
    {
      id: 6,
      codigo: 'REC-ARP-04',
      nombre: 'Set Celeno: Conjunto Bicolor Blanco & Negro',
      categoria: 'Conjuntos y Sets',
      linea: 'Lencería Fina',
      descripcion: 'Bralette y panty en contraste blanco y negro con encaje chantilly.',
      tiempo_confeccion_min: 130,
      insumos_count: 3,
      costo_insumos: 24500,
      mano_obra: 0,
      cif_energia: 1300,
      costo_total_unitario: 25800,
      precio_venta: 88000,
      markup_pct: 70.68,
      recomendaciones_taller: 'Rematar con costura elástica de tres pasos.',
      items: [
        { id: 1, insumo_id: 3, nombre: 'Encaje Chantilly Bicolor', tipo: 'Directo', consumo_unitario: 2.1, unidad: 'm', merma_pct: 4, costo_unitario: 4000, subtotal: 8400 },
        { id: 2, insumo_id: 11, nombre: 'Satín Elástico Negro', tipo: 'Directo', consumo_unitario: 1.5, unidad: 'm', merma_pct: 3, costo_unitario: 7900, subtotal: 11850 },
        { id: 3, insumo_id: 10, nombre: 'Tela Entrepierna Algodón', tipo: 'Directo', consumo_unitario: 0.15, unidad: 'm', merma_pct: 0, costo_unitario: 6500, subtotal: 975 },
      ],
      fases: [
        { nombre: '1. Corte Bicolor', descripcion: 'Corte de piezas contrastadas', minutos: 30 },
        { nombre: '2. Costura de Elásticos y Copas', descripcion: 'Ensamble de bralette', minutos: 70 },
        { nombre: '3. Acabados y Etiquetado', descripcion: 'Revisión de puntadas', minutos: 30 },
      ],
    },
    {
      id: 7,
      codigo: 'REC-ARP-03',
      nombre: 'Bustier Ocípete: Encaje Negro & Satín',
      categoria: 'Corsetería',
      linea: 'Corsetería',
      descripcion: 'Bustier con copas acolchadas en satín negro y sobrepuesto en tul bordado oscuro.',
      tiempo_confeccion_min: 160,
      insumos_count: 4,
      costo_insumos: 29800,
      mano_obra: 0,
      cif_energia: 1600,
      costo_total_unitario: 31400,
      precio_venta: 92000,
      markup_pct: 65.86,
      recomendaciones_taller: 'Preformar las copas con calor suave antes de forrar.',
      items: [
        { id: 1, insumo_id: 1, nombre: 'Tul Bordado Negro', tipo: 'Directo', consumo_unitario: 1.4, unidad: 'm', merma_pct: 4, costo_unitario: 10512.82, subtotal: 14718 },
        { id: 2, insumo_id: 11, nombre: 'Satín Elástico', tipo: 'Directo', consumo_unitario: 1.1, unidad: 'm', merma_pct: 3, costo_unitario: 7900, subtotal: 8690 },
        { id: 3, insumo_id: 9, nombre: 'Mallatex Forro', tipo: 'Directo', consumo_unitario: 0.5, unidad: 'm', merma_pct: 2, costo_unitario: 8000, subtotal: 4000 },
      ],
      fases: [
        { nombre: '1. Corte y Acolchado de Copas', descripcion: 'Preparación de esponjas y forro', minutos: 40 },
        { nombre: '2. Ensamble de Bustier y Espalda', descripcion: 'Inserción de broches y elásticos', minutos: 90 },
        { nombre: '3. Planchado y Acabados', descripcion: 'Vaporizado de satín', minutos: 30 },
      ],
    },
    {
      id: 8,
      codigo: 'REC-ARP-07',
      nombre: 'Vestido Lino Solero Alta Costura',
      categoria: 'Vestidos',
      linea: 'Alta Costura',
      descripcion: 'Vestido fluido con silueta halter en lino vértice, detalles calados y espalda descubierta.',
      tiempo_confeccion_min: 220,
      insumos_count: 3,
      costo_insumos: 38900,
      mano_obra: 5000,
      cif_energia: 2200,
      costo_total_unitario: 46100,
      precio_venta: 145000,
      markup_pct: 68.2,
      recomendaciones_taller: 'Dejar descolgar el vestido 24 horas antes de marcar la basta o dobladillo.',
      items: [
        { id: 1, insumo_id: 8, nombre: 'Lino Vértigo', tipo: 'Directo', consumo_unitario: 1.9, unidad: 'm', merma_pct: 5, costo_unitario: 17000, subtotal: 32300 },
        { id: 2, insumo_id: 9, nombre: 'Mallatex Forro', tipo: 'Directo', consumo_unitario: 0.7, unidad: 'm', merma_pct: 3, costo_unitario: 8000, subtotal: 5600 },
      ],
      fases: [
        { nombre: '1. Corte al Sesgo de Piezas', descripcion: 'Moldería de falda campana y canesú', minutos: 60 },
        { nombre: '2. Costuras Francesas y Forrado', descripcion: 'Acabados limpios sin orillos a la vista', minutos: 120 },
        { nombre: '3. Prueba de Caída y Basta', descripcion: 'Dobladillo pañuelo fino', minutos: 40 },
      ],
    },
  ])

  // 3. Prendas Listas (Showroom / Perchero)
  const prendasListas = ref<PrendaConfeccionada[]>([
    {
      id: 1,
      codigo: 'PRD-CAJA-001',
      nombre: 'Caja Colección "Saca las Garras"',
      categoria: 'Corsetería',
      costo_base: 129388.00,
      precio_venta: 360000.00,
      fisico_total: 3,
      disponible_total: 3,
      variantes: [
        { id: 1, talla: 'S', color: 'Negro & Rojo Pastel', sku: 'GARRAS-BOX-S', stock_fisico: 2, reservado: 0, disponible: 2 },
        { id: 2, talla: 'M', color: 'Negro & Rojo Pastel', sku: 'GARRAS-BOX-M', stock_fisico: 1, reservado: 0, disponible: 1 },
      ],
    },
    {
      id: 2,
      codigo: 'PRD-AELO-002',
      nombre: 'Set Aelo: Corset Rojo Pastel',
      categoria: 'Corsetería',
      costo_base: 38805.00,
      precio_venta: 110000.00,
      fisico_total: 4,
      disponible_total: 3,
      variantes: [
        { id: 3, talla: '32 (XS)', color: 'Rojo Pastel', sku: 'AELO-COR-32', stock_fisico: 1, reservado: 0, disponible: 1 },
        { id: 4, talla: '34 (S)', color: 'Rojo Pastel', sku: 'AELO-COR-34', stock_fisico: 2, reservado: 1, disponible: 1 },
        { id: 5, talla: '36 (M)', color: 'Rojo Pastel', sku: 'AELO-COR-36', stock_fisico: 1, reservado: 0, disponible: 1 },
      ],
    },
    {
      id: 3,
      codigo: 'PRD-BLU-005',
      nombre: 'Blusa Malla Garra Manga Larga',
      categoria: 'Prêt-à-Porter',
      costo_base: 21561.00,
      precio_venta: 90000.00,
      fisico_total: 12,
      disponible_total: 12,
      variantes: [
        { id: 6, talla: 'S', color: 'Ilustración Garra Negra', sku: 'BLU-GAR-S', stock_fisico: 4, reservado: 0, disponible: 4 },
        { id: 7, talla: 'M', color: 'Ilustración Garra Negra', sku: 'BLU-GAR-M', stock_fisico: 5, reservado: 0, disponible: 5 },
        { id: 8, talla: 'L', color: 'Ilustración Garra Negra', sku: 'BLU-GAR-L', stock_fisico: 3, reservado: 0, disponible: 3 },
      ],
    },
    {
      id: 4,
      codigo: 'PRD-COR-006',
      nombre: 'Corset Estructurado "Garras"',
      categoria: 'Corsetería',
      costo_base: 29826.00,
      precio_venta: 95000.00,
      fisico_total: 7,
      disponible_total: 7,
      variantes: [
        { id: 9, talla: 'S', color: 'Negro Profundo', sku: 'COR-GAR-S', stock_fisico: 3, reservado: 0, disponible: 3 },
        { id: 10, talla: 'M', color: 'Negro Profundo', sku: 'COR-GAR-M', stock_fisico: 3, reservado: 0, disponible: 3 },
        { id: 11, talla: 'L', color: 'Negro Profundo', sku: 'COR-GAR-L', stock_fisico: 1, reservado: 0, disponible: 1 },
      ],
    },
    {
      id: 5,
      codigo: 'PRD-FAL-008',
      nombre: 'Falda Estructurada "Emily"',
      categoria: 'Prêt-à-Porter',
      costo_base: 24000.00,
      precio_venta: 85000.00,
      fisico_total: 8,
      disponible_total: 8,
      variantes: [
        { id: 12, talla: 'S', color: 'Negro Gabardina', sku: 'FAL-EMI-S', stock_fisico: 4, reservado: 0, disponible: 4 },
        { id: 13, talla: 'M', color: 'Negro Gabardina', sku: 'FAL-EMI-M', stock_fisico: 4, reservado: 0, disponible: 4 },
      ],
    },
  ])

  // 4. Clientes CRM
  const clientes = ref<ClienteCRM[]>([
    {
      id: 1,
      nombre: 'Gabriela (Gaby)',
      tipo: 'Clienta Habitual',
      telefono: '+57 312 889 4411',
      email: 'gaby.arpia@email.com',
      ciudad: 'Pereira',
      direccion: 'Cra 15 # 12-45, Alamos',
      pedidos_count: 3,
      total_compras: 446250.00,
      talla_habitual: 'S',
      talla_superior: 'S',
      talla_inferior: 'S',
      categoria_preferida: 'Corsetería & Tops',
      tipo_producto_frecuente: 'PRENDAS_TALLAS',
      notas: 'Prefiere corsets en talla S. Calce ceñido con copa estándar.',
      medidas: { busto: 90, cintura: 68, cadera: 96, espalda: 37, talle: 42, largo: 60 },
    },
    {
      id: 2,
      nombre: 'Maira (*Comic)',
      tipo: 'Clienta VIP',
      telefono: '+57 315 777 8899',
      email: 'maira.comic@email.com',
      ciudad: 'Manizales',
      direccion: 'Av. Santander # 54-10',
      pedidos_count: 1,
      total_compras: 90000.00,
      talla_habitual: 'XS',
      talla_superior: 'XS',
      talla_inferior: 'XS',
      categoria_preferida: 'Sets & Corsets',
      tipo_producto_frecuente: 'PRENDAS_TALLAS',
      notas: 'Talla estándar XS para corsetería y bustiers.',
      medidas: { busto: 84, cintura: 64, cadera: 90, espalda: 36, talle: 40, largo: 58 },
    },
    {
      id: 3,
      nombre: 'Camila Pereira',
      tipo: 'Clienta Habitual',
      telefono: '+57 318 444 2233',
      email: 'camila.pereira@email.com',
      ciudad: 'Pereira',
      direccion: 'Calle 21 # 8-30, Centro',
      pedidos_count: 1,
      total_compras: 95000.00,
      talla_habitual: 'M',
      talla_superior: 'M',
      talla_inferior: 'M',
      categoria_preferida: 'Faldas & Corsets',
      tipo_producto_frecuente: 'PRENDAS_TALLAS',
      notas: 'Usa M estándar en falda gabardina Emily y tops.',
      medidas: { busto: 94, cintura: 72, cadera: 98, espalda: 39, talle: 43, largo: 62 },
    },
    {
      id: 4,
      nombre: 'Valentina Restrepo (Hermana Ale)',
      tipo: 'Clienta Showroom',
      telefono: '+57 312 456 7890',
      email: 'valentina.r@email.com',
      ciudad: 'Medellín',
      direccion: 'El Poblado, Cra 34 # 10-20',
      pedidos_count: 2,
      total_compras: 180000.00,
      talla_habitual: 'Sin Talla (Tote Bags & Merch)',
      talla_superior: 'S',
      talla_inferior: 'S',
      categoria_preferida: 'Tote Bags & Accesorios (Sin Talla)',
      tipo_producto_frecuente: 'PRODUCTOS_SIN_TALLA',
      notas: 'Colecciona Tote Bags ilustrados Arpía y accesorios textiles sin talla.',
      medidas: { busto: '-', cintura: '-', cadera: '-', espalda: '-', talle: '-', largo: '-' },
    },
    {
      id: 5,
      nombre: 'Celeste',
      tipo: 'Clienta Habitual',
      telefono: '+57 301 222 9988',
      email: 'celeste.taller@email.com',
      ciudad: 'Pereira',
      direccion: 'Av. Circunvalar # 14-22',
      pedidos_count: 1,
      total_compras: 80000.00,
      talla_habitual: 'XXS',
      talla_superior: 'XXS',
      talla_inferior: 'XXS',
      categoria_preferida: 'Corsetería de Autor',
      tipo_producto_frecuente: 'PRENDAS_TALLAS',
      notas: 'Talla mínima de confección estándar XXS.',
      medidas: { busto: 80, cintura: 60, cadera: 86, espalda: 35, talle: 39, largo: 55 },
    },
    {
      id: 6,
      nombre: 'Evento NANA / Feria Gótica',
      tipo: 'Feria / Stand Mayorista',
      telefono: '+57 310 000 1122',
      email: 'eventos@ferianana.co',
      ciudad: 'Bogotá',
      direccion: 'Pabellón Corferias Stand 42',
      pedidos_count: 2,
      total_compras: 520000.00,
      talla_habitual: 'Surtido (XXS a XL & Tote Bags)',
      talla_superior: 'Surtido',
      talla_inferior: 'Surtido',
      categoria_preferida: 'Tote Bags, Accesorios & Colección Completa',
      tipo_producto_frecuente: 'AMBOS',
      notas: 'Puntos de venta en feria: stock de Tote Bags de lona y corsets en tallas estándar S, M, L.',
      medidas: { busto: '-', cintura: '-', cadera: '-', espalda: '-', talle: '-', largo: '-' },
    },
    {
      id: 7,
      nombre: 'Manuela Henao',
      tipo: 'Clienta Online',
      telefono: '+57 316 333 1122',
      email: 'manu.henao@email.com',
      ciudad: 'Armenia',
      direccion: 'Cra 14 # 9 Norte',
      pedidos_count: 1,
      total_compras: 135000.00,
      talla_habitual: 'L',
      talla_superior: 'L',
      talla_inferior: 'L',
      categoria_preferida: 'Corsetería & Faldas',
      tipo_producto_frecuente: 'PRENDAS_TALLAS',
      notas: 'Talla estándar L.',
      medidas: { busto: 98, cintura: 78, cadera: 104, espalda: 40, talle: 44, largo: 64 },
    },
    {
      id: 8,
      nombre: 'Sofía Londoño',
      tipo: 'Clienta Showroom',
      telefono: '+57 311 990 0887',
      email: 'sofi.londono@email.com',
      ciudad: 'Pereira',
      direccion: 'Pinares, Manzana 4 Casa 12',
      pedidos_count: 2,
      total_compras: 90000.00,
      talla_habitual: 'Sin Talla (Tote Bags)',
      talla_superior: 'M',
      talla_inferior: 'M',
      categoria_preferida: 'Tote Bags de Lona',
      tipo_producto_frecuente: 'PRODUCTOS_SIN_TALLA',
      notas: 'Compra Tote Bags ilustradas para regalos.',
      medidas: { busto: '-', cintura: '-', cadera: '-', espalda: '-', talle: '-', largo: '-' },
    },
  ])

  // 5. Pedidos & Producción
  const pedidos = ref<PedidoProduccion[]>([
    {
      id: 1,
      codigo: '#ORD-ARP-001',
      cliente_id: 1,
      cliente_nombre: 'Gabriela (Gaby)',
      prenda_nombre: 'Caja Colección "Saca las Garras"',
      estado: 'ENTREGADO',
      precio_venta: 295000,
      costo_produccion: 129388,
      utilidad_neta: 165612,
      margen_pct: 56.1,
      fecha: '2026-08-10',
    },
    {
      id: 2,
      codigo: '#ORD-ARP-002',
      cliente_id: 5,
      cliente_nombre: 'Celeste',
      prenda_nombre: 'Set Aelo: Corset Rojo Pastel',
      estado: 'ENTREGADO',
      precio_venta: 80000,
      costo_produccion: 38805,
      utilidad_neta: 41195,
      margen_pct: 51.5,
      fecha: '2026-08-12',
    },
    {
      id: 3,
      codigo: '#ORD-ARP-003',
      cliente_id: 2,
      cliente_nombre: 'Maira (*Comic)',
      prenda_nombre: 'Blusa Malla Garra Manga Larga',
      estado: 'ENTREGADO',
      precio_venta: 90000,
      costo_produccion: 21561,
      utilidad_neta: 68439,
      margen_pct: 76.0,
      fecha: '2026-08-14',
    },
    {
      id: 4,
      codigo: '#ORD-ARP-004',
      cliente_id: 1,
      cliente_nombre: 'Gabriela (Gaby)',
      prenda_nombre: 'Set Ocípete: Bustier Encaje Negro/Satín',
      estado: 'ENTREGADO',
      precio_venta: 71250,
      costo_produccion: 26109,
      utilidad_neta: 45141,
      margen_pct: 63.4,
      fecha: '2026-08-15',
    },
    {
      id: 5,
      codigo: '#ORD-ARP-005',
      cliente_id: 3,
      cliente_nombre: 'Camila',
      prenda_nombre: 'Corset Estructurado "Garras"',
      estado: 'ENTREGADO',
      precio_venta: 95000,
      costo_produccion: 29826,
      utilidad_neta: 65174,
      margen_pct: 68.6,
      fecha: '2026-08-16',
    },
    {
      id: 6,
      codigo: '#ORD-ARP-006',
      cliente_id: 4,
      cliente_nombre: 'Valentina Restrepo',
      prenda_nombre: 'Blusa Malla Garra Manga Larga',
      estado: 'COSTURA',
      precio_venta: 90000,
      costo_produccion: 21561,
      utilidad_neta: 68439,
      margen_pct: 76.0,
      fecha: '2026-08-20',
      observaciones: 'Entalle ajustado según medidas personalizadas.',
    },
    {
      id: 7,
      codigo: '#ORD-ARP-007',
      cliente_id: 6,
      cliente_nombre: 'Evento NANA / Feria Gótica',
      prenda_nombre: 'Pack 4 Faldas Estructuradas Emily',
      estado: 'ENTREGADO',
      precio_venta: 340000,
      costo_produccion: 96000,
      utilidad_neta: 244000,
      margen_pct: 71.8,
      fecha: '2026-08-17',
    },
    {
      id: 8,
      codigo: '#ORD-ARP-008',
      cliente_id: 1,
      cliente_nombre: 'Gabriela (Gaby)',
      prenda_nombre: 'Set Celeno Bicolor',
      estado: 'ENTREGADO',
      precio_venta: 80000,
      costo_produccion: 25800,
      utilidad_neta: 54200,
      margen_pct: 67.8,
      fecha: '2026-08-18',
    },
  ])

  // 6. Ventas Realizadas (Histórico Real de Atelier Arpía)
  const ventas = ref<VentaAtelier[]>([
    {
      id: 1,
      codigo: 'VEN-ARP-001',
      cliente_id: 1,
      cliente_nombre: 'Gabriela (Gaby)',
      fecha: '2025-12-13',
      canal: 'Feria Showroom',
      metodo_pago: 'Transferencia Bancolombia',
      estado: 'COMPLETADA',
      items: [
        {
          id: 1,
          producto_id: 1,
          nombre_prenda: 'Caja Colección "Saca las Garras" (Bustier S + Set Aelo S + Celeno S + Blusa XS)',
          talla: 'S / XS',
          color: 'Negro & Rojo',
          cantidad: 1,
          precio_unitario: 295000,
          costo_unitario: 129388,
          subtotal: 295000,
          costo_subtotal: 129388,
        },
      ],
      subtotal: 295000,
      descuento_porcentaje: 0,
      descuento_valor: 0,
      total_venta: 295000,
      costo_total: 129388,
      ganancia_neta: 165612,
      margen_pct: 56.1,
      reinversion_40: 66245,
      margarita_30: 49684,
      valqui_30: 49684,
      observaciones: 'Incluye Caja de lujo con 4 prendas de lanzamiento',
      descontar_inventario: true,
    },
    {
      id: 2,
      codigo: 'VEN-ARP-002',
      cliente_id: 4,
      cliente_nombre: 'Celeste',
      fecha: '2025-12-13',
      canal: 'Feria Showroom',
      metodo_pago: 'Efectivo Showroom',
      estado: 'COMPLETADA',
      items: [
        {
          id: 2,
          producto_id: 2,
          nombre_prenda: 'Set Aelo: Corset Rojo Pastel',
          talla: 'S',
          color: 'Rojo Pastel',
          cantidad: 1,
          precio_unitario: 80000,
          costo_unitario: 38805,
          subtotal: 80000,
          costo_subtotal: 38805,
        },
      ],
      subtotal: 80000,
      descuento_porcentaje: 0,
      descuento_valor: 0,
      total_venta: 80000,
      costo_total: 38805,
      ganancia_neta: 41195,
      margen_pct: 51.5,
      reinversion_40: 16478,
      margarita_30: 12359,
      valqui_30: 12359,
      observaciones: 'Pago completo en efectivo feria',
      descontar_inventario: true,
    },
    {
      id: 3,
      codigo: 'VEN-ARP-003',
      cliente_id: 5,
      cliente_nombre: 'Maira (*Comic)',
      fecha: '2026-01-05',
      canal: 'WhatsApp / DM',
      metodo_pago: 'Transferencia Bancolombia',
      estado: 'COMPLETADA',
      items: [
        {
          id: 3,
          producto_id: 4,
          nombre_prenda: 'Blusa Malla Garra Manga Larga',
          talla: 'M',
          color: 'Negro Translúcido',
          cantidad: 1,
          precio_unitario: 90000,
          costo_unitario: 21561,
          subtotal: 90000,
          costo_subtotal: 21561,
        },
      ],
      subtotal: 90000,
      descuento_porcentaje: 0,
      descuento_valor: 0,
      total_venta: 90000,
      costo_total: 21561,
      ganancia_neta: 68439,
      margen_pct: 76.0,
      reinversion_40: 27376,
      margarita_30: 20532,
      valqui_30: 20532,
      observaciones: 'Envío local Pereira',
      descontar_inventario: true,
    },
    {
      id: 4,
      codigo: 'VEN-ARP-004',
      cliente_id: 1,
      cliente_nombre: 'Gabriela (Gaby)',
      fecha: '2026-03-20',
      canal: 'WhatsApp / DM',
      metodo_pago: 'Transferencia Bancolombia',
      estado: 'COMPLETADA',
      items: [
        {
          id: 4,
          producto_id: 3,
          nombre_prenda: 'Set Ocípete: Bustier Encaje / Satín',
          talla: 'S',
          color: 'Vino Tinto',
          cantidad: 1,
          precio_unitario: 95000,
          costo_unitario: 26109,
          subtotal: 95000,
          costo_subtotal: 26109,
        },
      ],
      subtotal: 95000,
      descuento_porcentaje: 25,
      descuento_valor: 23750,
      total_venta: 71250,
      costo_total: 26109,
      ganancia_neta: 45141,
      margen_pct: 63.4,
      reinversion_40: 18056,
      margarita_30: 13542,
      valqui_30: 13542,
      observaciones: 'Color Vino Tinto, Descuento 25% amiga del atelier',
      descontar_inventario: true,
    },
    {
      id: 5,
      codigo: 'VEN-ARP-005',
      cliente_id: 6,
      cliente_nombre: 'Valeria (Amiga Gaby)',
      fecha: '2026-03-28',
      canal: 'WhatsApp / DM',
      metodo_pago: 'Transferencia Nequi',
      estado: 'COMPLETADA',
      items: [
        {
          id: 5,
          producto_id: 3,
          nombre_prenda: 'Set Ocípete: Bustier Encaje / Satín',
          talla: 'M',
          color: 'Vino Tinto',
          cantidad: 1,
          precio_unitario: 95000,
          costo_unitario: 26109,
          subtotal: 95000,
          costo_subtotal: 26109,
        },
      ],
      subtotal: 95000,
      descuento_porcentaje: 25,
      descuento_valor: 23750,
      total_venta: 71250,
      costo_total: 26109,
      ganancia_neta: 45141,
      margen_pct: 63.4,
      reinversion_40: 18056,
      margarita_30: 13542,
      valqui_30: 13542,
      observaciones: 'Color Vino Tinto, Descuento 25% referida Gaby',
      descontar_inventario: true,
    },
    {
      id: 6,
      codigo: 'VEN-ARP-006',
      cliente_id: 7,
      cliente_nombre: 'Juan José',
      fecha: '2026-03-29',
      canal: 'Showroom Pereira',
      metodo_pago: 'Transferencia Bancolombia',
      estado: 'COMPLETADA',
      items: [
        {
          id: 6,
          producto_id: 2,
          nombre_prenda: 'Set Aelo: Corset Rojo Pastel',
          talla: 'XS',
          color: 'Rojo Pastel',
          cantidad: 1,
          precio_unitario: 110000,
          costo_unitario: 38805,
          subtotal: 110000,
          costo_subtotal: 38805,
        },
      ],
      subtotal: 110000,
      descuento_porcentaje: 25,
      descuento_valor: 27500,
      total_venta: 82500,
      costo_total: 38805,
      ganancia_neta: 43695,
      margen_pct: 53.0,
      reinversion_40: 17478,
      margarita_30: 13109,
      valqui_30: 13109,
      observaciones: 'Descuento 25% para regalo especial',
      descontar_inventario: true,
    },
    {
      id: 7,
      codigo: 'VEN-ARP-007',
      cliente_id: 2,
      cliente_nombre: 'Valentina Restrepo (Hermana Ale)',
      fecha: '2026-03-31',
      canal: 'Showroom Pereira',
      metodo_pago: 'Transferencia Nequi',
      estado: 'COMPLETADA',
      items: [
        {
          id: 7,
          producto_id: 2,
          nombre_prenda: 'Set Aelo: Corset Rojo Pastel',
          talla: 'S',
          color: 'Rojo Pastel',
          cantidad: 1,
          precio_unitario: 110000,
          costo_unitario: 38805,
          subtotal: 110000,
          costo_subtotal: 38805,
        },
      ],
      subtotal: 110000,
      descuento_porcentaje: 25,
      descuento_valor: 27500,
      total_venta: 82500,
      costo_total: 38805,
      ganancia_neta: 43695,
      margen_pct: 53.0,
      reinversion_40: 17478,
      margarita_30: 13109,
      valqui_30: 13109,
      observaciones: 'Descuento 25% familiar',
      descontar_inventario: true,
    },
    {
      id: 8,
      codigo: 'VEN-ARP-008',
      cliente_id: 2,
      cliente_nombre: 'Valentina Restrepo (Hermana Ale)',
      fecha: '2026-03-31',
      canal: 'Showroom Pereira',
      metodo_pago: 'Transferencia Nequi',
      estado: 'COMPLETADA',
      items: [
        {
          id: 8,
          producto_id: 5,
          nombre_prenda: 'Totebag Ilustrado Arpía',
          talla: 'Única',
          color: 'Crudo / Negro',
          cantidad: 1,
          precio_unitario: 45000,
          costo_unitario: 25765,
          subtotal: 45000,
          costo_subtotal: 25765,
        },
      ],
      subtotal: 45000,
      descuento_porcentaje: 0,
      descuento_valor: 0,
      total_venta: 45000,
      costo_total: 25765,
      ganancia_neta: 19235,
      margen_pct: 42.7,
      reinversion_40: 7694,
      margarita_30: 5770,
      valqui_30: 5770,
      observaciones: 'Totebag lona 100% algodón',
      descontar_inventario: true,
    },
    {
      id: 9,
      codigo: 'VEN-ARP-009',
      cliente_id: 8,
      cliente_nombre: 'Camila',
      fecha: '2026-03-31',
      canal: 'Showroom Pereira',
      metodo_pago: 'Transferencia Bancolombia',
      estado: 'COMPLETADA',
      items: [
        {
          id: 9,
          producto_id: 5,
          nombre_prenda: 'Totebag Ilustrado Arpía',
          talla: 'Única',
          color: 'Crudo / Negro',
          cantidad: 1,
          precio_unitario: 45000,
          costo_unitario: 25765,
          subtotal: 45000,
          costo_subtotal: 25765,
        },
      ],
      subtotal: 45000,
      descuento_porcentaje: 0,
      descuento_valor: 0,
      total_venta: 45000,
      costo_total: 25765,
      ganancia_neta: 19235,
      margen_pct: 42.7,
      reinversion_40: 7694,
      margarita_30: 5770,
      valqui_30: 5770,
      observaciones: 'Totebag ilustración oficial',
      descontar_inventario: true,
    },
    {
      id: 10,
      codigo: 'VEN-ARP-010',
      cliente_id: 4,
      cliente_nombre: 'Celeste',
      fecha: '2026-04-24',
      canal: 'Showroom Pereira',
      metodo_pago: 'Efectivo Showroom',
      estado: 'COMPLETADA',
      items: [
        {
          id: 10,
          producto_id: 5,
          nombre_prenda: 'Totebag Ilustrado Arpía',
          talla: 'Única',
          color: 'Crudo / Negro',
          cantidad: 1,
          precio_unitario: 45000,
          costo_unitario: 25765,
          subtotal: 45000,
          costo_subtotal: 25765,
        },
      ],
      subtotal: 45000,
      descuento_porcentaje: 0,
      descuento_valor: 0,
      total_venta: 45000,
      costo_total: 25765,
      ganancia_neta: 19235,
      margen_pct: 42.7,
      reinversion_40: 7694,
      margarita_30: 5770,
      valqui_30: 5770,
      observaciones: 'Compra en efectivo en taller',
      descontar_inventario: true,
    },
    {
      id: 11,
      codigo: 'VEN-ARP-011',
      cliente_id: 9,
      cliente_nombre: 'Valqui',
      fecha: '2026-04-29',
      canal: 'Showroom Pereira',
      metodo_pago: 'Efectivo Showroom',
      estado: 'COMPLETADA',
      items: [
        {
          id: 11,
          producto_id: 5,
          nombre_prenda: 'Totebag Ilustrado Arpía',
          talla: 'Única',
          color: 'Crudo / Negro',
          cantidad: 1,
          precio_unitario: 45000,
          costo_unitario: 25765,
          subtotal: 45000,
          costo_subtotal: 25765,
        },
      ],
      subtotal: 45000,
      descuento_porcentaje: 0,
      descuento_valor: 0,
      total_venta: 45000,
      costo_total: 25765,
      ganancia_neta: 19235,
      margen_pct: 42.7,
      reinversion_40: 7694,
      margarita_30: 5770,
      valqui_30: 5770,
      observaciones: 'Totebag personal socia',
      descontar_inventario: true,
    },
    {
      id: 12,
      codigo: 'VEN-ARP-012',
      cliente_id: 8,
      cliente_nombre: 'Camila',
      fecha: '2026-05-09',
      canal: 'Showroom Pereira',
      metodo_pago: 'Transferencia Bancolombia',
      estado: 'COMPLETADA',
      items: [
        {
          id: 12,
          producto_id: 1,
          nombre_prenda: 'Corset Estructurado "Garras"',
          talla: 'M',
          color: 'Negro Satín',
          cantidad: 1,
          precio_unitario: 95000,
          costo_unitario: 29826,
          subtotal: 95000,
          costo_subtotal: 29826,
        },
      ],
      subtotal: 95000,
      descuento_porcentaje: 0,
      descuento_valor: 0,
      total_venta: 95000,
      costo_total: 29826,
      ganancia_neta: 65174,
      margen_pct: 68.6,
      reinversion_40: 26070,
      margarita_30: 19552,
      valqui_30: 19552,
      observaciones: 'Corset varillado alta confección',
      descontar_inventario: true,
    },
    {
      id: 13,
      codigo: 'VEN-ARP-013',
      cliente_id: 10,
      cliente_nombre: 'Olga',
      fecha: '2026-05-09',
      canal: 'Showroom Pereira',
      metodo_pago: 'Transferencia Nequi',
      estado: 'COMPLETADA',
      items: [
        {
          id: 13,
          producto_id: 1,
          nombre_prenda: 'Corset Estructurado "Garras"',
          talla: 'L',
          color: 'Negro Satín',
          cantidad: 1,
          precio_unitario: 95000,
          costo_unitario: 29826,
          subtotal: 95000,
          costo_subtotal: 29826,
        },
      ],
      subtotal: 95000,
      descuento_porcentaje: 0,
      descuento_valor: 0,
      total_venta: 95000,
      costo_total: 29826,
      ganancia_neta: 65174,
      margen_pct: 68.6,
      reinversion_40: 26070,
      margarita_30: 19552,
      valqui_30: 19552,
      observaciones: 'Corset Garras con ajuste en espalda',
      descontar_inventario: true,
    },
    {
      id: 14,
      codigo: 'VEN-ARP-014',
      cliente_id: 1,
      cliente_nombre: 'Gabriela (Gaby)',
      fecha: '2026-05-10',
      canal: 'WhatsApp / DM',
      metodo_pago: 'Transferencia Bancolombia',
      estado: 'COMPLETADA',
      items: [
        {
          id: 14,
          producto_id: 1,
          nombre_prenda: 'Corset Estructurado "Garras"',
          talla: 'S',
          color: 'Negro Satín',
          cantidad: 1,
          precio_unitario: 95000,
          costo_unitario: 29826,
          subtotal: 95000,
          costo_subtotal: 29826,
        },
      ],
      subtotal: 95000,
      descuento_porcentaje: 36.3,
      descuento_valor: 34500,
      total_venta: 60500,
      costo_total: 29826,
      ganancia_neta: 30674,
      margen_pct: 50.7,
      reinversion_40: 12270,
      margarita_30: 9202,
      valqui_30: 9202,
      observaciones: 'Precio especial socia y modelo de campaña',
      descontar_inventario: true,
    },
    {
      id: 15,
      codigo: 'VEN-ARP-015',
      cliente_id: 5,
      cliente_nombre: 'Maira (*Comic)',
      fecha: '2026-05-19',
      canal: 'WhatsApp / DM',
      metodo_pago: 'Transferencia Bancolombia',
      estado: 'COMPLETADA',
      items: [
        {
          id: 15,
          producto_id: 5,
          nombre_prenda: 'Totebag Ilustrado Arpía',
          talla: 'Única',
          color: 'Crudo / Negro',
          cantidad: 2,
          precio_unitario: 45000,
          costo_unitario: 25765,
          subtotal: 90000,
          costo_subtotal: 51530,
        },
      ],
      subtotal: 90000,
      descuento_porcentaje: 0,
      descuento_valor: 0,
      total_venta: 90000,
      costo_total: 51530,
      ganancia_neta: 38470,
      margen_pct: 42.7,
      reinversion_40: 15388,
      margarita_30: 11541,
      valqui_30: 11541,
      observaciones: '2 unidades totebag para obsequio',
      descontar_inventario: true,
    },
    {
      id: 16,
      codigo: 'VEN-ARP-016',
      cliente_id: 11,
      cliente_nombre: 'Evento NANA / Feria Gótica',
      fecha: '2026-07-25',
      canal: 'Feria / Evento NANA',
      metodo_pago: 'Efectivo Showroom',
      estado: 'COMPLETADA',
      items: [
        {
          id: 16,
          producto_id: 5,
          nombre_prenda: 'Totebag Ilustrado Arpía',
          talla: 'Única',
          color: 'Crudo / Negro',
          cantidad: 1,
          precio_unitario: 45000,
          costo_unitario: 25765,
          subtotal: 45000,
          costo_subtotal: 25765,
        },
      ],
      subtotal: 45000,
      descuento_porcentaje: 0,
      descuento_valor: 0,
      total_venta: 45000,
      costo_total: 25765,
      ganancia_neta: 19235,
      margen_pct: 42.7,
      reinversion_40: 7694,
      margarita_30: 5770,
      valqui_30: 5770,
      observaciones: 'Venta presencial en stand NANA',
      descontar_inventario: true,
    },
    {
      id: 17,
      codigo: 'VEN-ARP-017',
      cliente_id: 11,
      cliente_nombre: 'Evento NANA / Feria Gótica',
      fecha: '2026-07-25',
      canal: 'Feria / Evento NANA',
      metodo_pago: 'Efectivo Showroom',
      estado: 'COMPLETADA',
      items: [
        {
          id: 17,
          producto_id: 1,
          nombre_prenda: 'Corset Estructurado "Garras"',
          talla: 'M',
          color: 'Negro Satín',
          cantidad: 1,
          precio_unitario: 95000,
          costo_unitario: 33581,
          subtotal: 95000,
          costo_subtotal: 33581,
        },
      ],
      subtotal: 95000,
      descuento_porcentaje: 15,
      descuento_valor: 14250,
      total_venta: 80750,
      costo_total: 33581,
      ganancia_neta: 47169,
      margen_pct: 58.4,
      reinversion_40: 18868,
      margarita_30: 14151,
      valqui_30: 14151,
      observaciones: 'Corset garras en feria NANA con descuento feria',
      descontar_inventario: true,
    },
    {
      id: 18,
      codigo: 'VEN-ARP-018',
      cliente_id: 11,
      cliente_nombre: 'Evento NANA / Feria Gótica',
      fecha: '2026-07-25',
      canal: 'Feria / Evento NANA',
      metodo_pago: 'Efectivo Showroom',
      estado: 'COMPLETADA',
      items: [
        {
          id: 18,
          producto_id: 5,
          nombre_prenda: 'Totebag Ilustrado Arpía (Sorteo)',
          talla: 'Única',
          color: 'Crudo / Negro',
          cantidad: 1,
          precio_unitario: 45000,
          costo_unitario: 25765,
          subtotal: 45000,
          costo_subtotal: 25765,
        },
      ],
      subtotal: 45000,
      descuento_porcentaje: 0,
      descuento_valor: 0,
      total_venta: 45000,
      costo_total: 25765,
      ganancia_neta: 19235,
      margen_pct: 42.7,
      reinversion_40: 7694,
      margarita_30: 5770,
      valqui_30: 5770,
      observaciones: 'Premio sorteo evento NANA registrado',
      descontar_inventario: true,
    },
    {
      id: 19,
      codigo: 'VEN-ARP-019',
      cliente_id: 1,
      cliente_nombre: 'Gabriela (Gaby)',
      fecha: '2026-08-01',
      canal: 'Showroom Pereira',
      metodo_pago: 'Transferencia Bancolombia',
      estado: 'COMPLETADA',
      items: [
        {
          id: 19,
          producto_id: 6,
          nombre_prenda: 'Falda Estructurada "Emily"',
          talla: 'S',
          color: 'Negro Gabardina',
          cantidad: 1,
          precio_unitario: 80000,
          costo_unitario: 23465,
          subtotal: 80000,
          costo_subtotal: 23465,
        },
      ],
      subtotal: 80000,
      descuento_porcentaje: 0,
      descuento_valor: 0,
      total_venta: 80000,
      costo_total: 23465,
      ganancia_neta: 56535,
      margen_pct: 70.7,
      reinversion_40: 22614,
      margarita_30: 16960,
      valqui_30: 16960,
      observaciones: 'Falda Emily negra con herrajes dorados',
      descontar_inventario: true,
    },
    {
      id: 20,
      codigo: 'VEN-ARP-020',
      cliente_id: 12,
      cliente_nombre: 'María (Caja Cumpleaños)',
      fecha: '2026-08-05',
      canal: 'WhatsApp / DM',
      metodo_pago: 'Transferencia Bancolombia',
      estado: 'COMPLETADA',
      items: [
        {
          id: 20,
          producto_id: 4,
          nombre_prenda: 'Blusa Malla Garra Manga Larga',
          talla: 'S',
          color: 'Negro Translúcido',
          cantidad: 1,
          precio_unitario: 90000,
          costo_unitario: 21561,
          subtotal: 90000,
          costo_subtotal: 21561,
        },
      ],
      subtotal: 90000,
      descuento_porcentaje: 0,
      descuento_valor: 0,
      total_venta: 90000,
      costo_total: 21561,
      ganancia_neta: 68439,
      margen_pct: 76.0,
      reinversion_40: 27376,
      margarita_30: 20532,
      valqui_30: 20532,
      observaciones: 'Caja regalo cumpleañera con tarjeta dedicatoria',
      descontar_inventario: true,
    },
  ])

  // Computed Totals & Metrics
  const totalVentasRealizadas = computed(() => {
    return ventas.value
      .filter((v) => v.estado === 'COMPLETADA')
      .reduce((acc, v) => acc + v.total_venta, 0)
  })

  const totalGananciaVentas = computed(() => {
    return ventas.value
      .filter((v) => v.estado === 'COMPLETADA')
      .reduce((acc, v) => acc + v.ganancia_neta, 0)
  })

  const margenPromedioVentas = computed(() => {
    if (totalVentasRealizadas.value === 0) return 0
    return ((totalGananciaVentas.value / totalVentasRealizadas.value) * 100).toFixed(1)
  })

  const distribucionSociasVentas = computed(() => {
    const total = totalGananciaVentas.value
    return {
      total,
      reversion40: Math.round(total * 0.4),
      margara30: Math.round(total * 0.3),
      valqui30: Math.round(total * 0.3),
    }
  })

  const totalVentas = computed(() => {
    return pedidos.value.reduce((acc, p) => acc + p.precio_venta, 0)
  })

  const totalUtilidad = computed(() => {
    return pedidos.value.reduce((acc, p) => acc + p.utilidad_neta, 0)
  })

  const rentabilidadPromedio = computed(() => {
    if (totalVentas.value === 0) return 0
    return ((totalUtilidad.value / totalVentas.value) * 100).toFixed(1)
  })

  const pedidosActivos = computed(() => {
    return pedidos.value.filter((p) => p.estado !== 'ENTREGADO').length
  })

  const insumosCriticos = computed(() => {
    return insumos.value.filter((i) => i.stock_actual <= i.stock_minimo)
  })

  const valorTotalInventario = computed(() => {
    return insumos.value.reduce((acc, i) => acc + (i.stock_actual * i.costo_unitario), 0)
  })

  const prendasStockFisico = computed(() => {
    return prendasListas.value.reduce((acc, p) => acc + p.fisico_total, 0)
  })

  const prendasStockDisponible = computed(() => {
    return prendasListas.value.reduce((acc, p) => acc + p.disponible_total, 0)
  })

  const valorizacionPVP = computed(() => {
    return prendasListas.value.reduce((acc, p) => acc + (p.fisico_total * p.precio_venta), 0)
  })

  // Profit Distribution (Fórmula de Socias Activa)
  // 40% Fondo Reinversión Taller, 30% Margara, 30% Valqui
  const distribucionSocias = computed(() => {
    const total = totalUtilidad.value
    return {
      total,
      reversion40: total * 0.4,
      margara30: total * 0.3,
      valqui30: total * 0.3,
    }
  })

  // Pipeline Counts for Kanban
  const pipelineCounts = computed(() => {
    const counts: Record<string, number> = {
      COTIZADO: 0,
      RESERVADO: 0,
      CORTE: 0,
      COSTURA: 0,
      ACABADOS: 0,
      CALIDAD: 0,
      LISTO: 0,
      ENTREGADO: 0,
    }
    pedidos.value.forEach((p) => {
      if (counts[p.estado] !== undefined) {
        counts[p.estado]++
      }
    })
    return counts
  })

  // Methods
  function ajustarStockInsumo(id: number, delta: number) {
    const item = insumos.value.find((i) => i.id === id)
    if (item) {
      item.stock_actual = Math.max(0, parseFloat((item.stock_actual + delta).toFixed(2)))
      item.valor_total = parseFloat((item.stock_actual * item.costo_unitario).toFixed(2))
    }
  }

  function agregarCompraInsumo(id: number, cantidad: number, costoUnitario?: number) {
    const item = insumos.value.find((i) => i.id === id)
    if (item) {
      const costo = costoUnitario ?? item.costo_unitario
      item.stock_actual = parseFloat((item.stock_actual + cantidad).toFixed(2))
      item.costo_unitario = costo
      item.valor_total = parseFloat((item.stock_actual * item.costo_unitario).toFixed(2))
    }
  }

  function ajustarStockPrenda(productoId: number, varianteId: number, delta: number) {
    const prod = prendasListas.value.find((p) => p.id === productoId)
    if (prod) {
      const variante = prod.variantes.find((v) => v.id === varianteId)
      if (variante) {
        variante.stock_fisico = Math.max(0, variante.stock_fisico + delta)
        variante.disponible = Math.max(0, variante.stock_fisico - variante.reservado)
      }
      prod.fisico_total = prod.variantes.reduce((sum, v) => sum + v.stock_fisico, 0)
      prod.disponible_total = prod.variantes.reduce((sum, v) => sum + v.disponible, 0)
    }
  }

  function crearPedido(nuevo: Partial<PedidoProduccion>) {
    const nextId = (pedidos.value.length ? Math.max(...pedidos.value.map((p) => p.id)) : 0) + 1
    const p: PedidoProduccion = {
      id: nextId,
      codigo: `#ORD-ARP-00${nextId}`,
      cliente_id: nuevo.cliente_id || 1,
      cliente_nombre: nuevo.cliente_nombre || 'Cliente Taller',
      prenda_nombre: nuevo.prenda_nombre || 'Prenda a Medida',
      estado: nuevo.estado || 'COTIZADO',
      precio_venta: nuevo.precio_venta || 0,
      costo_produccion: nuevo.costo_produccion || 0,
      utilidad_neta: (nuevo.precio_venta || 0) - (nuevo.costo_produccion || 0),
      margen_pct: nuevo.precio_venta ? parseFloat(((((nuevo.precio_venta - (nuevo.costo_produccion || 0)) / nuevo.precio_venta) * 100)).toFixed(1)) : 50,
      fecha: new Date().toISOString().split('T')[0],
      observaciones: nuevo.observaciones,
    }
    pedidos.value.unshift(p)
    return p
  }

  function cambiarEstadoPedido(id: number, nuevoEstado: PedidoProduccion['estado']) {
    const p = pedidos.value.find((x) => x.id === id)
    if (p) {
      p.estado = nuevoEstado
    }
  }

  function crearCliente(cliente: Partial<ClienteCRM>) {
    const nextId = (clientes.value.length ? Math.max(...clientes.value.map((c) => c.id)) : 0) + 1
    const c: ClienteCRM = {
      id: nextId,
      nombre: cliente.nombre || 'Nueva Clienta',
      tipo: cliente.tipo || 'Clienta Habitual',
      telefono: cliente.telefono || '',
      email: cliente.email || '',
      ciudad: cliente.ciudad || 'Pereira',
      direccion: cliente.direccion || '',
      pedidos_count: cliente.pedidos_count || 0,
      total_compras: cliente.total_compras || 0,
      talla_habitual: cliente.talla_habitual || 'S',
      talla_superior: cliente.talla_superior || cliente.talla_habitual || 'S',
      talla_inferior: cliente.talla_inferior || cliente.talla_habitual || 'S',
      categoria_preferida: cliente.categoria_preferida || 'Corsetería & Tops',
      tipo_producto_frecuente: cliente.tipo_producto_frecuente || (cliente.talla_habitual?.includes('Sin Talla') ? 'PRODUCTOS_SIN_TALLA' : 'PRENDAS_TALLAS'),
      notas: cliente.notas || '',
      medidas: cliente.medidas || { busto: '-', cintura: '-', cadera: '-', espalda: '-', talle: '-', largo: '-' },
    }
    clientes.value.unshift(c)
    return c
  }

  function actualizarCliente(id: number, data: Partial<ClienteCRM>) {
    const idx = clientes.value.findIndex((c) => c.id === id)
    if (idx !== -1) {
      clientes.value[idx] = { ...clientes.value[idx], ...data }
    }
  }

  function crearReceta(receta: Partial<RecetaBOM>) {
    const nextId = (recetas.value.length ? Math.max(...recetas.value.map((r) => r.id)) : 0) + 1
    const r: RecetaBOM = {
      id: nextId,
      codigo: receta.codigo || `REC-ARP-0${nextId}`,
      nombre: receta.nombre || 'Nueva Receta / Modelo',
      categoria: receta.categoria || 'Corsetería',
      linea: receta.linea || 'Atelier',
      descripcion: receta.descripcion || 'Ficha técnica de confección en taller.',
      tiempo_confeccion_min: receta.tiempo_confeccion_min || 90,
      insumos_count: receta.items?.length || 1,
      costo_insumos: receta.costo_insumos || 20000,
      mano_obra: receta.mano_obra || 0,
      cif_energia: receta.cif_energia || 1000,
      costo_total_unitario: (receta.costo_insumos || 20000) + (receta.mano_obra || 0) + (receta.cif_energia || 1000),
      precio_venta: receta.precio_venta || 85000,
      markup_pct: receta.markup_pct || 65,
      recomendaciones_taller: receta.recomendaciones_taller || 'Seguir moldería oficial de corte.',
      items: receta.items || [],
      fases: receta.fases || [
        { nombre: '1. Corte', descripcion: 'Corte de piezas al hilo', minutos: 30 },
        { nombre: '2. Ensamble', descripcion: 'Costura principal', minutos: 40 },
        { nombre: '3. Acabados', descripcion: 'Planchado y remates', minutos: 20 },
      ],
    }
    recetas.value.unshift(r)
    return r
  }

  function crearInsumo(insumo: Partial<InsumoAtelier>) {
    const nextId = (insumos.value.length ? Math.max(...insumos.value.map((i) => i.id)) : 0) + 1
    const item: InsumoAtelier = {
      id: nextId,
      codigo: insumo.codigo || `TEL-NUEVO-0${nextId}`,
      nombre: insumo.nombre || 'Nuevo Insumo',
      descripcion: insumo.descripcion || '',
      tipo: insumo.tipo || 'Directo',
      categoria: insumo.categoria || 'Telas Principales',
      ubicacion: insumo.ubicacion || 'Estante Central',
      proveedor: insumo.proveedor || 'Proveedor Local',
      stock_actual: Number(insumo.stock_actual) || 0,
      stock_minimo: Number(insumo.stock_minimo) || 5,
      unidad_medida: insumo.unidad_medida || 'm',
      costo_unitario: Number(insumo.costo_unitario) || 10000,
      valor_total: (Number(insumo.stock_actual) || 0) * (Number(insumo.costo_unitario) || 10000),
    }
    insumos.value.unshift(item)
    return item
  }

  function crearVenta(venta: Partial<VentaAtelier>): VentaAtelier {
    const nextId = (ventas.value.length ? Math.max(...ventas.value.map((v) => v.id)) : 0) + 1
    const items: ItemVentaAtelier[] = (venta.items || []).map((it, idx) => {
      const cant = Number(it.cantidad) || 1
      const pUnit = Number(it.precio_unitario) || 0
      const cUnit = Number(it.costo_unitario) || 0
      return {
        id: it.id || idx + 1,
        producto_id: it.producto_id || null,
        nombre_prenda: it.nombre_prenda || 'Prenda Atelier Arpía',
        talla: it.talla || 'Única',
        color: it.color || 'Negro',
        cantidad: cant,
        precio_unitario: pUnit,
        costo_unitario: cUnit,
        subtotal: cant * pUnit,
        costo_subtotal: cant * cUnit,
      }
    })

    const rawSubtotal = items.reduce((acc, it) => acc + it.subtotal, 0)
    const subtotal = venta.subtotal !== undefined ? Number(venta.subtotal) : rawSubtotal
    const descPct = Number(venta.descuento_porcentaje) || 0
    const descVal = venta.descuento_valor !== undefined ? Number(venta.descuento_valor) : (subtotal * (descPct / 100))
    const totalVenta = Math.max(0, venta.total_venta !== undefined ? Number(venta.total_venta) : (subtotal - descVal))
    const costoTotal = venta.costo_total !== undefined ? Number(venta.costo_total) : items.reduce((acc, it) => acc + it.costo_subtotal, 0)
    const gananciaNeta = Math.round(totalVenta - costoTotal)
    const margenPct = totalVenta > 0 ? Number(((gananciaNeta / totalVenta) * 100).toFixed(1)) : 0
    const reinversion40 = Math.round(gananciaNeta * 0.4)
    const margara30 = Math.round(gananciaNeta * 0.3)
    const valqui30 = Math.round(gananciaNeta * 0.3)

    const nuevaVenta: VentaAtelier = {
      id: nextId,
      codigo: venta.codigo || `VEN-ARP-${String(nextId).padStart(3, '0')}`,
      cliente_id: venta.cliente_id || null,
      cliente_nombre: venta.cliente_nombre || 'Cliente General',
      fecha: venta.fecha || new Date().toISOString().split('T')[0],
      canal: venta.canal || 'Showroom Pereira',
      metodo_pago: venta.metodo_pago || 'Transferencia Bancolombia',
      estado: venta.estado || 'COMPLETADA',
      items,
      subtotal,
      descuento_porcentaje: descPct,
      descuento_valor: descVal,
      total_venta: totalVenta,
      costo_total: costoTotal,
      ganancia_neta: gananciaNeta,
      margen_pct: margenPct,
      reinversion_40: reinversion40,
      margarita_30: margara30,
      valqui_30: valqui30,
      observaciones: venta.observaciones || '',
      descontar_inventario: venta.descontar_inventario ?? true,
    }

    ventas.value.unshift(nuevaVenta)

    // Si se vinculó cliente, actualizar compras acumuladas
    if (nuevaVenta.cliente_id) {
      const cli = clientes.value.find((c) => c.id === nuevaVenta.cliente_id)
      if (cli) {
        cli.pedidos_count += 1
        cli.total_compras += nuevaVenta.total_venta
      }
    }

    return nuevaVenta
  }

  function actualizarVenta(id: number, ventaData: Partial<VentaAtelier>): VentaAtelier | null {
    const idx = ventas.value.findIndex((v) => v.id === id)
    if (idx === -1) return null

    const existing = ventas.value[idx]
    const items: ItemVentaAtelier[] = (ventaData.items || existing.items || []).map((it, itemIdx) => {
      const cant = Number(it.cantidad) || 1
      const pUnit = Number(it.precio_unitario) || 0
      const cUnit = Number(it.costo_unitario) || 0
      return {
        id: it.id || itemIdx + 1,
        producto_id: it.producto_id || null,
        nombre_prenda: it.nombre_prenda || 'Prenda Atelier Arpía',
        talla: it.talla || 'Única',
        color: it.color || 'Negro',
        cantidad: cant,
        precio_unitario: pUnit,
        costo_unitario: cUnit,
        subtotal: cant * pUnit,
        costo_subtotal: cant * cUnit,
      }
    })

    const rawSubtotal = items.reduce((acc, it) => acc + it.subtotal, 0)
    const subtotal = ventaData.subtotal !== undefined ? Number(ventaData.subtotal) : rawSubtotal
    const descPct = ventaData.descuento_porcentaje !== undefined ? Number(ventaData.descuento_porcentaje) : existing.descuento_porcentaje
    const descVal = ventaData.descuento_valor !== undefined ? Number(ventaData.descuento_valor) : (subtotal * (descPct / 100))
    const totalVenta = Math.max(0, ventaData.total_venta !== undefined ? Number(ventaData.total_venta) : (subtotal - descVal))
    const costoTotal = ventaData.costo_total !== undefined ? Number(ventaData.costo_total) : items.reduce((acc, it) => acc + it.costo_subtotal, 0)
    const gananciaNeta = Math.round(totalVenta - costoTotal)
    const margenPct = totalVenta > 0 ? Number(((gananciaNeta / totalVenta) * 100).toFixed(1)) : 0
    const reinversion40 = Math.round(gananciaNeta * 0.4)
    const margara30 = Math.round(gananciaNeta * 0.3)
    const valqui30 = Math.round(gananciaNeta * 0.3)

    const updated: VentaAtelier = {
      ...existing,
      ...ventaData,
      items,
      subtotal,
      descuento_porcentaje: descPct,
      descuento_valor: descVal,
      total_venta: totalVenta,
      costo_total: costoTotal,
      ganancia_neta: gananciaNeta,
      margen_pct: margenPct,
      reinversion_40: reinversion40,
      margarita_30: margara30,
      valqui_30: valqui30,
    }

    ventas.value[idx] = updated
    return updated
  }

  function eliminarVenta(id: number): boolean {
    const idx = ventas.value.findIndex((v) => v.id === id)
    if (idx !== -1) {
      ventas.value.splice(idx, 1)
      return true
    }
    return false
  }

  function cambiarEstadoVenta(id: number, nuevoEstado: VentaAtelier['estado']) {
    const v = ventas.value.find((x) => x.id === id)
    if (v) {
      v.estado = nuevoEstado
    }
  }

  // 7. Socias & Reparto de Utilidades
  const socias = ref<SociaAtelier[]>([
    {
      id: 1,
      nombre: '🏛️ Fondo Reinversión Atelier Arpía',
      rol: 'Fondo de Reserva & Compras Mayoristas',
      porcentaje: 40,
      es_fondo_taller: true,
      banco: 'Cuenta Ahorros Atelier',
      tipo_cuenta: 'Ahorros Empresarial',
      numero_cuenta: 'ARP-REINV-2026',
      titular_cuenta: 'Atelier Arpía SAS',
      activo: true,
      notas: '40% destinado a compra de rollos de tela, herrajes de corsetería, mantenimiento de máquinas y fondo de emergencia.',
    },
    {
      id: 2,
      nombre: '🪡 Margarita Restrepo (Margara)',
      rol: 'Co-fundadora & Jefa de Confección',
      porcentaje: 30,
      es_fondo_taller: false,
      telefono: '+57 312 445 8921',
      email: 'margara@atelierarpia.com',
      banco: 'Bancolombia',
      tipo_cuenta: 'Ahorros',
      numero_cuenta: '312-445892-11',
      titular_cuenta: 'Margarita Restrepo',
      activo: true,
      notas: 'Supervisión de patronaje, escalado de moldería, corte especializado y confección de piezas alta costura.',
    },
    {
      id: 3,
      nombre: '🎨 Valeria Quintero (Valqui)',
      rol: 'Co-fundadora & Directora Creativa',
      porcentaje: 30,
      es_fondo_taller: false,
      telefono: '+57 300 889 1245',
      email: 'valqui@atelierarpia.com',
      banco: 'Nequi / Bancolombia',
      tipo_cuenta: 'Digital / Ahorros',
      numero_cuenta: '300-889124-55',
      titular_cuenta: 'Valeria Quintero',
      activo: true,
      notas: 'Dirección de colecciones, estilismo, imagen de marca, comunicación visual y relacionamiento comercial.',
    },
  ])

  // Anticipos / Adelantos de Socias
  const anticipos = ref<AnticipoSocia[]>([
    {
      id: 1,
      socia_id: 2,
      nombre_socia: '🪡 Margarita Restrepo (Margara)',
      fecha: '2026-08-05',
      monto: 350000,
      concepto: 'Adelanto compra urgente de hiladillas y sesgos en Medellín',
      metodo_desembolso: 'Transferencia Nequi',
      estado: 'PENDIENTE_DESCUENTO',
      comprobante: 'NEQ-TR-998124',
      observaciones: 'Pendiente descontar en liquidación Agosto 2026.',
    },
    {
      id: 2,
      socia_id: 3,
      nombre_socia: '🎨 Valeria Quintero (Valqui)',
      fecha: '2026-08-10',
      monto: 400000,
      concepto: 'Anticipo honorarios modelos y estilismo campaña Septiembre',
      metodo_desembolso: 'Transferencia Bancolombia',
      estado: 'PENDIENTE_DESCUENTO',
      comprobante: 'BN-882194',
      observaciones: 'Descontar en próximo cierre mensual.',
    },
  ])

  // Historial de Liquidaciones de Socias
  const liquidaciones = ref<LiquidacionSocias[]>([
    {
      id: 1,
      codigo: 'LIQ-2025-12',
      periodo: 'Diciembre 2025 (Campaña "Saca las Garras")',
      fecha_cierre: '2025-12-31',
      total_ventas_brutas: 16500000,
      costo_taller_insumos: 4800000,
      gastos_operativos: 1500000,
      utilidad_neta_total: 10200000,
      fondo_reinversion_monto: 4080000,
      utilidad_repartible: 6120000,
      estado: 'PAGADA',
      distribucion: [
        {
          socia_id: 1,
          nombre_socia: '🏛️ Fondo Reinversión Atelier Arpía',
          rol_socia: 'Fondo Taller (40%)',
          porcentaje: 40,
          monto_bruto: 4080000,
          deduccion_anticipos: 0,
          monto_neto_pagar: 4080000,
          estado_pago: 'PAGADO',
          fecha_pago: '2026-01-05',
          comprobante_transferencia: 'INT-TR-0012',
          banco_destino: 'Cuenta Ahorros Atelier',
        },
        {
          socia_id: 2,
          nombre_socia: '🪡 Margarita Restrepo (Margara)',
          rol_socia: 'Co-fundadora Confección (30%)',
          porcentaje: 30,
          monto_bruto: 3060000,
          deduccion_anticipos: 0,
          monto_neto_pagar: 3060000,
          estado_pago: 'PAGADO',
          fecha_pago: '2026-01-05',
          comprobante_transferencia: 'BC-TR-881294',
          banco_destino: 'Bancolombia #312-445892-11',
        },
        {
          socia_id: 3,
          nombre_socia: '🎨 Valeria Quintero (Valqui)',
          rol_socia: 'Co-fundadora Diseño (30%)',
          porcentaje: 30,
          monto_bruto: 3060000,
          deduccion_anticipos: 0,
          monto_neto_pagar: 3060000,
          estado_pago: 'PAGADO',
          fecha_pago: '2026-01-05',
          comprobante_transferencia: 'BC-TR-881295',
          banco_destino: 'Nequi / Bancolombia #300-889124-55',
        },
      ],
      observaciones: 'Excelente balance de cierre de año con récord de ventas de corsets.',
      created_at: '2025-12-31T20:00:00Z',
    },
    {
      id: 2,
      codigo: 'LIQ-2026-03',
      periodo: 'Marzo 2026 (Showroom Trimestre I)',
      fecha_cierre: '2026-03-31',
      total_ventas_brutas: 14200000,
      costo_taller_insumos: 3900000,
      gastos_operativos: 1800000,
      utilidad_neta_total: 8500000,
      fondo_reinversion_monto: 3400000,
      utilidad_repartible: 5100000,
      estado: 'PAGADA',
      distribucion: [
        {
          socia_id: 1,
          nombre_socia: '🏛️ Fondo Reinversión Atelier Arpía',
          rol_socia: 'Fondo Taller (40%)',
          porcentaje: 40,
          monto_bruto: 3400000,
          deduccion_anticipos: 0,
          monto_neto_pagar: 3400000,
          estado_pago: 'PAGADO',
          fecha_pago: '2026-04-03',
          comprobante_transferencia: 'INT-TR-0045',
          banco_destino: 'Cuenta Ahorros Atelier',
        },
        {
          socia_id: 2,
          nombre_socia: '🪡 Margarita Restrepo (Margara)',
          rol_socia: 'Co-fundadora Confección (30%)',
          porcentaje: 30,
          monto_bruto: 2550000,
          deduccion_anticipos: 0,
          monto_neto_pagar: 2550000,
          estado_pago: 'PAGADO',
          fecha_pago: '2026-04-03',
          comprobante_transferencia: 'BC-TR-904122',
          banco_destino: 'Bancolombia #312-445892-11',
        },
        {
          socia_id: 3,
          nombre_socia: '🎨 Valeria Quintero (Valqui)',
          rol_socia: 'Co-fundadora Diseño (30%)',
          porcentaje: 30,
          monto_bruto: 2550000,
          deduccion_anticipos: 0,
          monto_neto_pagar: 2550000,
          estado_pago: 'PAGADO',
          fecha_pago: '2026-04-03',
          comprobante_transferencia: 'BC-TR-904123',
          banco_destino: 'Nequi / Bancolombia #300-889124-55',
        },
      ],
      observaciones: 'Liquidación trimestral completa y transferida a las cuentas bancarias.',
      created_at: '2026-03-31T18:00:00Z',
    },
    {
      id: 3,
      codigo: 'LIQ-2026-05',
      periodo: 'Mayo 2026 (Set Aelo & Preventas Especiales)',
      fecha_cierre: '2026-05-31',
      total_ventas_brutas: 18900000,
      costo_taller_insumos: 5200000,
      gastos_operativos: 2100000,
      utilidad_neta_total: 11600000,
      fondo_reinversion_monto: 4640000,
      utilidad_repartible: 6960000,
      estado: 'PAGADA',
      distribucion: [
        {
          socia_id: 1,
          nombre_socia: '🏛️ Fondo Reinversión Atelier Arpía',
          rol_socia: 'Fondo Taller (40%)',
          porcentaje: 40,
          monto_bruto: 4640000,
          deduccion_anticipos: 0,
          monto_neto_pagar: 4640000,
          estado_pago: 'PAGADO',
          fecha_pago: '2026-06-03',
          comprobante_transferencia: 'INT-TR-0089',
          banco_destino: 'Cuenta Ahorros Atelier',
        },
        {
          socia_id: 2,
          nombre_socia: '🪡 Margarita Restrepo (Margara)',
          rol_socia: 'Co-fundadora Confección (30%)',
          porcentaje: 30,
          monto_bruto: 3480000,
          deduccion_anticipos: 0,
          monto_neto_pagar: 3480000,
          estado_pago: 'PAGADO',
          fecha_pago: '2026-06-03',
          comprobante_transferencia: 'BC-TR-945671',
          banco_destino: 'Bancolombia #312-445892-11',
        },
        {
          socia_id: 3,
          nombre_socia: '🎨 Valeria Quintero (Valqui)',
          rol_socia: 'Co-fundadora Diseño (30%)',
          porcentaje: 30,
          monto_bruto: 3480000,
          deduccion_anticipos: 0,
          monto_neto_pagar: 3480000,
          estado_pago: 'PAGADO',
          fecha_pago: '2026-06-03',
          comprobante_transferencia: 'BC-TR-945672',
          banco_destino: 'Nequi / Bancolombia #300-889124-55',
        },
      ],
      observaciones: 'Campaña con alta aceptación en redes sociales y boutique.',
      created_at: '2026-05-31T20:00:00Z',
    },
    {
      id: 4,
      codigo: 'LIQ-2026-07',
      periodo: 'Julio 2026 (Evento NANA & Feria Gótica Pereira)',
      fecha_cierre: '2026-07-31',
      total_ventas_brutas: 21400000,
      costo_taller_insumos: 6100000,
      gastos_operativos: 2400000,
      utilidad_neta_total: 12900000,
      fondo_reinversion_monto: 5160000,
      utilidad_repartible: 7740000,
      estado: 'PAGADA',
      distribucion: [
        {
          socia_id: 1,
          nombre_socia: '🏛️ Fondo Reinversión Atelier Arpía',
          rol_socia: 'Fondo Taller (40%)',
          porcentaje: 40,
          monto_bruto: 5160000,
          deduccion_anticipos: 0,
          monto_neto_pagar: 5160000,
          estado_pago: 'PAGADO',
          fecha_pago: '2026-08-02',
          comprobante_transferencia: 'INT-TR-0112',
          banco_destino: 'Cuenta Ahorros Atelier',
        },
        {
          socia_id: 2,
          nombre_socia: '🪡 Margarita Restrepo (Margara)',
          rol_socia: 'Co-fundadora Confección (30%)',
          porcentaje: 30,
          monto_bruto: 3870000,
          deduccion_anticipos: 0,
          monto_neto_pagar: 3870000,
          estado_pago: 'PAGADO',
          fecha_pago: '2026-08-02',
          comprobante_transferencia: 'BC-TR-978102',
          banco_destino: 'Bancolombia #312-445892-11',
        },
        {
          socia_id: 3,
          nombre_socia: '🎨 Valeria Quintero (Valqui)',
          rol_socia: 'Co-fundadora Diseño (30%)',
          porcentaje: 30,
          monto_bruto: 3870000,
          deduccion_anticipos: 0,
          monto_neto_pagar: 3870000,
          estado_pago: 'PAGADO',
          fecha_pago: '2026-08-02',
          comprobante_transferencia: 'BC-TR-978103',
          banco_destino: 'Nequi / Bancolombia #300-889124-55',
        },
      ],
      observaciones: 'Excelente rotación en ferias presenciales.',
      created_at: '2026-07-31T22:00:00Z',
    },
  ])

  // Computed Financial Totals for Partner Distributions
  const totalHistoricoFacturadoLiquidaciones = computed(() => {
    return liquidaciones.value.reduce((acc, l) => acc + l.total_ventas_brutas, 0)
  })

  const totalHistoricoUtilidadSocias = computed(() => {
    return liquidaciones.value.reduce((acc, l) => acc + l.utilidad_neta_total, 0)
  })

  const totalHistoricoFondoReinversion = computed(() => {
    return liquidaciones.value.reduce((acc, l) => acc + l.fondo_reinversion_monto, 0)
  })

  const totalHistoricoRepartidoMargara = computed(() => {
    return liquidaciones.value.reduce((acc, l) => {
      const item = l.distribucion.find((d) => d.socia_id === 2)
      return acc + (item ? item.monto_neto_pagar : 0)
    }, 0)
  })

  const totalHistoricoRepartidoValqui = computed(() => {
    return liquidaciones.value.reduce((acc, l) => {
      const item = l.distribucion.find((d) => d.socia_id === 3)
      return acc + (item ? item.monto_neto_pagar : 0)
    }, 0)
  })

  const totalAnticiposPendientes = computed(() => {
    return anticipos.value
      .filter((a) => a.estado === 'PENDIENTE_DESCUENTO')
      .reduce((acc, a) => acc + a.monto, 0)
  })

  // 8. Catálogos Maestros Atelier
  const proveedoresMaestros = ref<ProveedorMaestro[]>([
    {
      id: 1,
      nombre: 'Atenea Bordados y Encajes',
      categoria: 'Telas Principales',
      ciudad: 'Pereira, Risaralda',
      contacto: 'Carlos Mario Duque',
      telefono: '+57 314 678 9900',
      email: 'ventas@ateneatelas.com',
      tiempo_entrega_dias: 2,
      condicion_pago: 'Contado / Transferencia',
      calificacion: 5,
      activo: true,
      notas: 'Proveedor exclusivo de tul bordado negro Ref 100 y rojo pastel Ref 159. Excelente calidad.',
    },
    {
      id: 2,
      nombre: 'CasaTextil Colombia',
      categoria: 'Telas Principales',
      ciudad: 'Medellín, Antioquia',
      contacto: 'Lina María Morales',
      telefono: '+57 320 889 1122',
      email: 'pedidos@casatextil.co',
      tiempo_entrega_dias: 4,
      condicion_pago: '30 días crédito',
      calificacion: 4.8,
      activo: true,
      notas: 'Gabardina ultra poliéster para Falda Emily y lonas 100% algodón para Tote Bags.',
    },
    {
      id: 3,
      nombre: 'Herrajes & Insumos del Otún',
      categoria: 'Herrajes & Corsetería',
      ciudad: 'Pereira, Risaralda',
      contacto: 'Hernán Darío Gómez',
      telefono: '+57 312 450 7820',
      email: 'herrajesotun@gmail.com',
      tiempo_entrega_dias: 1,
      condicion_pago: 'Contado',
      calificacion: 4.9,
      activo: true,
      notas: 'Varillas de acero espiralado de 6mm, ojaletes niquelados/dorados antioxidantes y busks frontales.',
    },
    {
      id: 4,
      nombre: 'Distribuidora Sedas & Licras Andina',
      categoria: 'Telas Principales',
      ciudad: 'Cali, Valle',
      contacto: 'Margarita Soto',
      telefono: '+57 318 901 2345',
      email: 'contacto@sedasandina.com',
      tiempo_entrega_dias: 3,
      condicion_pago: 'Transferencia anticipada',
      calificacion: 4.7,
      activo: true,
      notas: 'Satín licrado opaco y suave para copas y forros interiores hipoalergénicos.',
    },
    {
      id: 5,
      nombre: 'Estampados & Serigrafía Pereira',
      categoria: 'Lonas & Estampación',
      ciudad: 'Pereira, Risaralda',
      contacto: 'Sebastián Restrepo',
      telefono: '+57 315 670 4433',
      email: 'taller@estampadospereira.com',
      tiempo_entrega_dias: 5,
      condicion_pago: '50% anticipo, 50% entrega',
      calificacion: 4.6,
      activo: true,
      notas: 'Serigrafía textil de alta definición en tintas ecológicas para Tote Bags ilustradas.',
    },
    {
      id: 6,
      nombre: 'Hilos & Hilazas La Perla',
      categoria: 'Hilos & Accesorios',
      ciudad: 'Dosquebradas, Risaralda',
      contacto: 'Gloria Inés Patiño',
      telefono: '+57 311 320 8899',
      email: 'ventas@hiloslaperla.com',
      tiempo_entrega_dias: 1,
      condicion_pago: 'Contado',
      calificacion: 5,
      activo: true,
      notas: 'Hilos de poliéster de alta tenacidad (Calibre 40 y 75) para costuras reforzadas.',
    },
  ])

  const canalesVentaMaestros = ref<CanalVentaMaestro[]>([
    {
      id: 1,
      nombre: 'Showroom Pereira (Taller Principal)',
      tipo: 'FISICO',
      comision_pct: 0,
      costo_fijo_mensual: 450000,
      activo: true,
      descripcion: 'Espacio de atención personalizada, pruebas de prendas en stock y entrega física directa.',
    },
    {
      id: 2,
      nombre: 'WhatsApp & Instagram DM Directo',
      tipo: 'DIGITAL',
      comision_pct: 0,
      costo_fijo_mensual: 50000,
      activo: true,
      descripcion: 'Canal principal de ventas personalizadas y asesoría directa por Margarita y Valeria.',
    },
    {
      id: 3,
      nombre: 'Feria NANA / Feria Gótica (Stands)',
      tipo: 'EVENTO',
      comision_pct: 5.0,
      costo_fijo_mensual: 250000,
      activo: true,
      descripcion: 'Eventos masivos de cultura alternativa: alta rotación de Tote Bags y prendas en tallas estándar.',
    },
    {
      id: 4,
      nombre: 'Comic Con & Convenciones Pop',
      tipo: 'EVENTO',
      comision_pct: 6.0,
      costo_fijo_mensual: 350000,
      activo: true,
      descripcion: 'Stands en eventos geek y cosplay en Pereira, Manizales y Medellín.',
    },
    {
      id: 5,
      nombre: 'Boutiques Aliadas & Consignación',
      tipo: 'FISICO',
      comision_pct: 15.0,
      costo_fijo_mensual: 0,
      activo: true,
      descripcion: 'Percheros en tiendas multimarca de diseño independiente.',
    },
  ])

  const metodosPagoMaestros = ref<MetodoPagoMaestro[]>([
    {
      id: 1,
      nombre: 'Transferencia Bancolombia',
      tipo: 'TRANSFERENCIA',
      comision_pct: 0,
      tiempo_acreditacion: 'Inmediata',
      activo: true,
      datos_cuenta: 'Cuenta de Ahorros # 312-445892-11 a nombre de Atelier Arpía',
    },
    {
      id: 2,
      nombre: 'Nequi / Daviplata',
      tipo: 'BILLETERA_DIGITAL',
      comision_pct: 0,
      tiempo_acreditacion: 'Inmediata',
      activo: true,
      datos_cuenta: 'Número móvil: 300 889 1245',
    },
    {
      id: 3,
      nombre: 'Efectivo en Showroom / Ferias',
      tipo: 'EFECTIVO',
      comision_pct: 0,
      tiempo_acreditacion: 'Inmediata (Caja física)',
      activo: true,
      datos_cuenta: 'Caja menor de taller y ferias',
    },
    {
      id: 4,
      nombre: 'Datáfono Bold / SumUp (Tarjetas)',
      tipo: 'PASARELA_DATAFONO',
      comision_pct: 2.99,
      tiempo_acreditacion: '24 horas hábiles',
      activo: true,
      datos_cuenta: 'Terminal Bold conectada a cuenta principal',
    },
    {
      id: 5,
      nombre: 'Wompi / Link de Pago Online',
      tipo: 'PASARELA_DATAFONO',
      comision_pct: 3.25,
      tiempo_acreditacion: '48 horas hábiles',
      activo: true,
      datos_cuenta: 'Pagos con tarjeta de crédito nacional e internacional',
    },
  ])

  const categoriasColeccionMaestros = ref<CategoriaColeccionMaestro[]>([
    {
      id: 1,
      nombre: 'Corsetería & Bustiers Estructurados',
      tipo_talla: 'CON_TALLAS_ESTANDAR',
      descripcion: 'Prendas con varillas de acero, ojaletes reforzados y patrones de modelado (XXS a XL).',
      margen_meta_pct: 68,
      total_modelos: 4,
      activo: true,
    },
    {
      id: 2,
      nombre: 'Faldas & Prendas Inferiores',
      tipo_talla: 'CON_TALLAS_ESTANDAR',
      descripcion: 'Faldas plisadas, faldas estructuradas en gabardina y conjuntos inferiores (XXS a XL).',
      margen_meta_pct: 70,
      total_modelos: 2,
      activo: true,
    },
    {
      id: 3,
      nombre: 'Blusas & Tops de Malla / Satín',
      tipo_talla: 'CON_TALLAS_ESTANDAR',
      descripcion: 'Tops translúcidos, mangas con garras y blusas combinables con corsets (XXS a XL).',
      margen_meta_pct: 65,
      total_modelos: 3,
      activo: true,
    },
    {
      id: 4,
      nombre: 'Tote Bags Ilustradas de Lona (Sin Talla)',
      tipo_talla: 'SIN_TALLA_MERCH',
      descripcion: 'Bolsos de lona 100% algodón con ilustraciones exclusivas Arpía. Producto estrella en ferias.',
      margen_meta_pct: 55,
      total_modelos: 3,
      activo: true,
    },
    {
      id: 5,
      nombre: 'Accesorios Textiles & Joyería Gótica (Sin Talla)',
      tipo_talla: 'SIN_TALLA_MERCH',
      descripcion: 'Scrunchies de satín, pañoletas de seda, arneses graduables y pines metálicos.',
      margen_meta_pct: 75,
      total_modelos: 5,
      activo: true,
    },
  ])

  const ubicacionesTallerMaestros = ref<UbicacionTallerMaestro[]>([
    {
      id: 1,
      codigo: 'UB-EST-A1',
      nombre: 'Estante Telas Atenea A1',
      tipo: 'ROLLOS_TELAS',
      capacidad: '25 Rollos',
      observaciones: 'Tules bordados negro y rojo pastel, encajes finos.',
    },
    {
      id: 2,
      codigo: 'UB-GAB-G1',
      nombre: 'Rollo Gabardinas & Lonas G1',
      tipo: 'ROLLOS_TELAS',
      capacidad: '15 Rollos',
      observaciones: 'Gabardina ultra poliéster y rollos de lona cruda.',
    },
    {
      id: 3,
      codigo: 'UB-GAV-H1',
      nombre: 'Gavetero Herrajes & Varillas H1',
      tipo: 'GAVETAS_HERRAJES',
      capacidad: '10 Gavetas',
      observaciones: 'Varillas de acero, punteras metálicas, ojaletes y cinta hiladilla.',
    },
    {
      id: 4,
      codigo: 'UB-PER-S1',
      nombre: 'Perchero Showroom Pereira P1',
      tipo: 'PERCHERO_SHOWROOM',
      capacidad: '40 Prendas',
      observaciones: 'Prendas listas para exhibición directa y entrega inmediata.',
    },
    {
      id: 5,
      codigo: 'UB-BOD-T1',
      nombre: 'Bodega de Lonas & Merch B1',
      tipo: 'ACCESORIOS_BODEGA',
      capacidad: '100 Unidades',
      observaciones: 'Stock de Tote Bags estampadas y accesorios sin talla.',
    },
  ])

  const tallasEstandarMaestros = ref<TallaEstandarMaestro[]>([
    {
      id: 1,
      talla: 'XXS',
      busto: '78 – 82 cm',
      cintura: '58 – 62 cm',
      cadera: '84 – 88 cm',
      reduccion_corset: '-4 cm a -6 cm',
      descripcion: 'Silueta petite / extra reducida',
      orden: 1,
      activo: true,
    },
    {
      id: 2,
      talla: 'XS',
      busto: '82 – 86 cm',
      cintura: '62 – 66 cm',
      cadera: '88 – 92 cm',
      reduccion_corset: '-5 cm a -7 cm',
      descripcion: 'Talla pequeña estándar',
      orden: 2,
      activo: true,
    },
    {
      id: 3,
      talla: 'S',
      busto: '86 – 90 cm',
      cintura: '66 – 70 cm',
      cadera: '92 – 96 cm',
      reduccion_corset: '-6 cm a -8 cm',
      descripcion: 'Talla base de muestrario y stock regular',
      orden: 3,
      activo: true,
    },
    {
      id: 4,
      talla: 'M',
      busto: '90 – 94 cm',
      cintura: '70 – 74 cm',
      cadera: '96 – 100 cm',
      reduccion_corset: '-6 cm a -8 cm',
      descripcion: 'Talla intermedia de alta rotación',
      orden: 4,
      activo: true,
    },
    {
      id: 5,
      talla: 'L',
      busto: '94 – 100 cm',
      cintura: '74 – 80 cm',
      cadera: '100 – 106 cm',
      reduccion_corset: '-7 cm a -9 cm',
      descripcion: 'Silueta completa y busto generoso',
      orden: 5,
      activo: true,
    },
    {
      id: 6,
      talla: 'XL',
      busto: '100 – 108 cm',
      cintura: '80 – 88 cm',
      cadera: '106 – 114 cm',
      reduccion_corset: '-8 cm a -10 cm',
      descripcion: 'Silueta plus y corsetería de soporte reforzado',
      orden: 6,
      activo: true,
    },
  ])

  const productosSinTallaMaestros = ref<ProductoSinTallaMaestro[]>([
    {
      id: 1,
      nombre: 'Tote Bag Ilustrada de Lona',
      categoria: 'Tote Bags & Bolsos',
      dimensiones: '40 cm alto × 35 cm ancho × 8 cm fuelle. Manijas de 60 cm.',
      materiales: 'Lona cruda 100% algodón 320g, serigrafía ecológica reforzada.',
      descripcion: 'Bolsos de autor ilustrados por Atelier Arpía. Producto insignia en ferias y stands.',
      precio_sugerido: 45000,
      activo: true,
    },
    {
      id: 2,
      nombre: 'Scrunchie de Satín & Sedas de Lujo',
      categoria: 'Accesorios Textiles',
      dimensiones: 'Diámetro exterior 12 cm, elástico interno reforzado 18 cm.',
      materiales: 'Retazos seleccionados de satín licrado y seda estampada.',
      descripcion: 'Moñas y lazos que aprovechan sobrantes finos de corte para cero desperdicio.',
      precio_sugerido: 15000,
      activo: true,
    },
    {
      id: 3,
      nombre: 'Pañoleta / Bandana Ilustrada',
      categoria: 'Accesorios Textiles',
      dimensiones: '55 cm × 55 cm.',
      materiales: 'Seda poliéster satinada con dobladillo fino al pañuelo.',
      descripcion: 'Accesorio versátil para cuello, cabeza o atar a la Tote Bag.',
      precio_sugerido: 35000,
      activo: true,
    },
    {
      id: 4,
      nombre: 'Pins Metálicos Esmaltados Colección Arpía',
      categoria: 'Pines & Joyería',
      dimensiones: '3.5 cm × 3.5 cm con broche de mariposa doble.',
      materiales: 'Aleación de zinc esmaltada con baño niquelado y negro mate.',
      descripcion: 'Pines coleccionables para personalizar chamarras, corsets y totes.',
      precio_sugerido: 18000,
      activo: true,
    },
  ])

  const parametrosCosteo = ref<ParametrosCosteoMaestro>({
    costo_minuto_costura: 280, // COP / minuto de mano de obra
    costo_hora_patronaje: 22000, // COP / hora de diseño y corte
    margen_meta_global_pct: 65, // 65% de margen deseado
    desperdicio_textil_default_pct: 12, // 12% merma estimada en corte
    iva_regimen_pct: 0, // Régimen simple / No responsable IVA
    distribucion_reinversion_pct: 40,
    distribucion_margara_pct: 30,
    distribucion_valqui_pct: 30,
  })

  // Acciones CRUD Maestros
  function crearProveedor(prov: Partial<ProveedorMaestro>) {
    const nextId = (proveedoresMaestros.value.length ? Math.max(...proveedoresMaestros.value.map((p) => p.id)) : 0) + 1
    const p: ProveedorMaestro = {
      id: nextId,
      nombre: prov.nombre || 'Nuevo Proveedor',
      categoria: prov.categoria || 'Telas Principales',
      ciudad: prov.ciudad || 'Pereira',
      contacto: prov.contacto || '',
      telefono: prov.telefono || '',
      email: prov.email || '',
      tiempo_entrega_dias: prov.tiempo_entrega_dias || 2,
      condicion_pago: prov.condicion_pago || 'Contado',
      calificacion: prov.calificacion || 5,
      activo: prov.activo ?? true,
      notas: prov.notas || '',
    }
    proveedoresMaestros.value.push(p)
    return p
  }

  function actualizarProveedor(id: number, data: Partial<ProveedorMaestro>) {
    const idx = proveedoresMaestros.value.findIndex((p) => p.id === id)
    if (idx !== -1) {
      proveedoresMaestros.value[idx] = { ...proveedoresMaestros.value[idx], ...data }
    }
  }

  function eliminarProveedor(id: number) {
    const idx = proveedoresMaestros.value.findIndex((p) => p.id === id)
    if (idx !== -1) proveedoresMaestros.value.splice(idx, 1)
  }

  function crearCanalVenta(canal: Partial<CanalVentaMaestro>) {
    const nextId = (canalesVentaMaestros.value.length ? Math.max(...canalesVentaMaestros.value.map((c) => c.id)) : 0) + 1
    const c: CanalVentaMaestro = {
      id: nextId,
      nombre: canal.nombre || 'Nuevo Canal',
      tipo: canal.tipo || 'DIGITAL',
      comision_pct: canal.comision_pct || 0,
      costo_fijo_mensual: canal.costo_fijo_mensual || 0,
      activo: canal.activo ?? true,
      descripcion: canal.descripcion || '',
    }
    canalesVentaMaestros.value.push(c)
    return c
  }

  function actualizarCanalVenta(id: number, data: Partial<CanalVentaMaestro>) {
    const idx = canalesVentaMaestros.value.findIndex((c) => c.id === id)
    if (idx !== -1) canalesVentaMaestros.value[idx] = { ...canalesVentaMaestros.value[idx], ...data }
  }

  function eliminarCanalVenta(id: number) {
    const idx = canalesVentaMaestros.value.findIndex((c) => c.id === id)
    if (idx !== -1) canalesVentaMaestros.value.splice(idx, 1)
  }

  function crearMetodoPago(mp: Partial<MetodoPagoMaestro>) {
    const nextId = (metodosPagoMaestros.value.length ? Math.max(...metodosPagoMaestros.value.map((m) => m.id)) : 0) + 1
    const m: MetodoPagoMaestro = {
      id: nextId,
      nombre: mp.nombre || 'Nuevo Método',
      tipo: mp.tipo || 'TRANSFERENCIA',
      comision_pct: mp.comision_pct || 0,
      tiempo_acreditacion: mp.tiempo_acreditacion || 'Inmediata',
      activo: mp.activo ?? true,
      datos_cuenta: mp.datos_cuenta || '',
    }
    metodosPagoMaestros.value.push(m)
    return m
  }

  function actualizarMetodoPago(id: number, data: Partial<MetodoPagoMaestro>) {
    const idx = metodosPagoMaestros.value.findIndex((m) => m.id === id)
    if (idx !== -1) metodosPagoMaestros.value[idx] = { ...metodosPagoMaestros.value[idx], ...data }
  }

  function eliminarMetodoPago(id: number) {
    const idx = metodosPagoMaestros.value.findIndex((m) => m.id === id)
    if (idx !== -1) metodosPagoMaestros.value.splice(idx, 1)
  }

  function crearCategoriaColeccion(cat: Partial<CategoriaColeccionMaestro>) {
    const nextId = (categoriasColeccionMaestros.value.length ? Math.max(...categoriasColeccionMaestros.value.map((c) => c.id)) : 0) + 1
    const c: CategoriaColeccionMaestro = {
      id: nextId,
      nombre: cat.nombre || 'Nueva Categoría',
      tipo_talla: cat.tipo_talla || 'CON_TALLAS_ESTANDAR',
      descripcion: cat.descripcion || '',
      margen_meta_pct: cat.margen_meta_pct || 65,
      total_modelos: cat.total_modelos || 0,
      activo: cat.activo ?? true,
    }
    categoriasColeccionMaestros.value.push(c)
    return c
  }

  function actualizarCategoriaColeccion(id: number, data: Partial<CategoriaColeccionMaestro>) {
    const idx = categoriasColeccionMaestros.value.findIndex((c) => c.id === id)
    if (idx !== -1) {
      categoriasColeccionMaestros.value[idx] = { ...categoriasColeccionMaestros.value[idx], ...data }
    }
  }

  function eliminarCategoriaColeccion(id: number) {
    const idx = categoriasColeccionMaestros.value.findIndex((c) => c.id === id)
    if (idx !== -1) categoriasColeccionMaestros.value.splice(idx, 1)
  }

  function crearUbicacionTaller(ub: Partial<UbicacionTallerMaestro>) {
    const nextId = (ubicacionesTallerMaestros.value.length ? Math.max(...ubicacionesTallerMaestros.value.map((u) => u.id)) : 0) + 1
    const u: UbicacionTallerMaestro = {
      id: nextId,
      codigo: ub.codigo || `UB-${nextId}`,
      nombre: ub.nombre || 'Nueva Ubicación',
      tipo: ub.tipo || 'ROLLOS_TELAS',
      capacidad: ub.capacidad || '20 Unidades',
      observaciones: ub.observaciones || '',
    }
    ubicacionesTallerMaestros.value.push(u)
    return u
  }

  function actualizarUbicacionTaller(id: number, data: Partial<UbicacionTallerMaestro>) {
    const idx = ubicacionesTallerMaestros.value.findIndex((u) => u.id === id)
    if (idx !== -1) {
      ubicacionesTallerMaestros.value[idx] = { ...ubicacionesTallerMaestros.value[idx], ...data }
    }
  }

  function eliminarUbicacionTaller(id: number) {
    const idx = ubicacionesTallerMaestros.value.findIndex((u) => u.id === id)
    if (idx !== -1) ubicacionesTallerMaestros.value.splice(idx, 1)
  }

  function crearTallaEstandar(talla: Partial<TallaEstandarMaestro>) {
    const nextId = (tallasEstandarMaestros.value.length ? Math.max(...tallasEstandarMaestros.value.map((t) => t.id)) : 0) + 1
    const t: TallaEstandarMaestro = {
      id: nextId,
      talla: talla.talla || 'NUEVA',
      busto: talla.busto || '80 – 85 cm',
      cintura: talla.cintura || '60 – 65 cm',
      cadera: talla.cadera || '85 – 90 cm',
      reduccion_corset: talla.reduccion_corset || '-5 cm a -7 cm',
      descripcion: talla.descripcion || '',
      orden: talla.orden || nextId,
      activo: talla.activo ?? true,
    }
    tallasEstandarMaestros.value.push(t)
    return t
  }

  function actualizarTallaEstandar(id: number, data: Partial<TallaEstandarMaestro>) {
    const idx = tallasEstandarMaestros.value.findIndex((t) => t.id === id)
    if (idx !== -1) {
      tallasEstandarMaestros.value[idx] = { ...tallasEstandarMaestros.value[idx], ...data }
    }
  }

  function eliminarTallaEstandar(id: number) {
    const idx = tallasEstandarMaestros.value.findIndex((t) => t.id === id)
    if (idx !== -1) tallasEstandarMaestros.value.splice(idx, 1)
  }

  function crearProductoSinTalla(prod: Partial<ProductoSinTallaMaestro>) {
    const nextId = (productosSinTallaMaestros.value.length ? Math.max(...productosSinTallaMaestros.value.map((p) => p.id)) : 0) + 1
    const p: ProductoSinTallaMaestro = {
      id: nextId,
      nombre: prod.nombre || 'Nuevo Producto Sin Talla',
      categoria: prod.categoria || 'Tote Bags & Bolsos',
      dimensiones: prod.dimensiones || '',
      materiales: prod.materiales || '',
      descripcion: prod.descripcion || '',
      precio_sugerido: prod.precio_sugerido || 0,
      activo: prod.activo ?? true,
    }
    productosSinTallaMaestros.value.push(p)
    return p
  }

  function actualizarProductoSinTalla(id: number, data: Partial<ProductoSinTallaMaestro>) {
    const idx = productosSinTallaMaestros.value.findIndex((p) => p.id === id)
    if (idx !== -1) {
      productosSinTallaMaestros.value[idx] = { ...productosSinTallaMaestros.value[idx], ...data }
    }
  }

  function eliminarProductoSinTalla(id: number) {
    const idx = productosSinTallaMaestros.value.findIndex((p) => p.id === id)
    if (idx !== -1) productosSinTallaMaestros.value.splice(idx, 1)
  }

  function actualizarParametrosCosteo(data: Partial<ParametrosCosteoMaestro>) {
    parametrosCosteo.value = { ...parametrosCosteo.value, ...data }
  }


  // CRUD Actions: Socias
  function crearSocia(sociaData: Partial<SociaAtelier>): SociaAtelier {
    const nextId = (socias.value.length ? Math.max(...socias.value.map((s) => s.id)) : 0) + 1
    const nueva: SociaAtelier = {
      id: nextId,
      nombre: sociaData.nombre || 'Nueva Socia Atelier',
      rol: sociaData.rol || 'Socia Colaboradora',
      porcentaje: Number(sociaData.porcentaje) || 0,
      es_fondo_taller: Boolean(sociaData.es_fondo_taller),
      telefono: sociaData.telefono || '',
      email: sociaData.email || '',
      banco: sociaData.banco || 'Bancolombia',
      tipo_cuenta: sociaData.tipo_cuenta || 'Ahorros',
      numero_cuenta: sociaData.numero_cuenta || '',
      titular_cuenta: sociaData.titular_cuenta || sociaData.nombre || '',
      activo: sociaData.activo ?? true,
      notas: sociaData.notas || '',
    }
    socias.value.push(nueva)
    return nueva
  }

  function actualizarSocia(id: number, data: Partial<SociaAtelier>): SociaAtelier | null {
    const idx = socias.value.findIndex((s) => s.id === id)
    if (idx === -1) return null
    socias.value[idx] = { ...socias.value[idx], ...data }
    return socias.value[idx]
  }

  function eliminarSocia(id: number): boolean {
    const idx = socias.value.findIndex((s) => s.id === id)
    if (idx !== -1) {
      socias.value.splice(idx, 1)
      return true
    }
    return false
  }

  function toggleActivoSocia(id: number) {
    const s = socias.value.find((x) => x.id === id)
    if (s) {
      s.activo = !s.activo
    }
  }

  // CRUD Actions: Liquidaciones
  function crearLiquidacion(liqData: Partial<LiquidacionSocias>): LiquidacionSocias {
    const nextId = (liquidaciones.value.length ? Math.max(...liquidaciones.value.map((l) => l.id)) : 0) + 1
    const totalVentas = Number(liqData.total_ventas_brutas) || 0
    const costos = Number(liqData.costo_taller_insumos) || 0
    const gastos = Number(liqData.gastos_operativos) || 0
    const utilNeta = Math.max(0, totalVentas - costos - gastos)
    const fondoMonto = Math.round(utilNeta * 0.4)
    const utilRepartible = utilNeta - fondoMonto

    let distribucion: LiquidacionSociaItem[] = []
    if (liqData.distribucion && liqData.distribucion.length > 0) {
      distribucion = liqData.distribucion
    } else {
      // Auto-generate from active socias
      const activas = socias.value.filter((s) => s.activo)
      distribucion = activas.map((s) => {
        const montoBruto = Math.round(utilNeta * (s.porcentaje / 100))
        // Check pending anticipos
        const antSocia = anticipos.value
          .filter((a) => a.socia_id === s.id && a.estado === 'PENDIENTE_DESCUENTO')
          .reduce((sum, a) => sum + a.monto, 0)
        const ded = Math.min(montoBruto, antSocia)
        return {
          socia_id: s.id,
          nombre_socia: s.nombre,
          rol_socia: s.rol,
          porcentaje: s.porcentaje,
          monto_bruto: montoBruto,
          deduccion_anticipos: ded,
          monto_neto_pagar: Math.max(0, montoBruto - ded),
          estado_pago: 'PENDIENTE',
          banco_destino: s.banco ? `${s.banco} (${s.numero_cuenta || 'N/A'})` : 'Efectivo Taller',
        }
      })
    }

    const nueva: LiquidacionSocias = {
      id: nextId,
      codigo: liqData.codigo || `LIQ-${new Date().getFullYear()}-${String(nextId).padStart(2, '0')}`,
      periodo: liqData.periodo || `Periodo ${new Date().toLocaleString('es-CO', { month: 'long', year: 'numeric' })}`,
      fecha_cierre: liqData.fecha_cierre || new Date().toISOString().split('T')[0],
      total_ventas_brutas: totalVentas,
      costo_taller_insumos: costos,
      gastos_operativos: gastos,
      utilidad_neta_total: utilNeta,
      fondo_reinversion_monto: fondoMonto,
      utilidad_repartible: utilRepartible,
      estado: liqData.estado || 'BORRADOR',
      distribucion,
      observaciones: liqData.observaciones || '',
      created_at: new Date().toISOString(),
    }

    liquidaciones.value.unshift(nueva)
    return nueva
  }

  function actualizarLiquidacion(id: number, data: Partial<LiquidacionSocias>): LiquidacionSocias | null {
    const idx = liquidaciones.value.findIndex((l) => l.id === id)
    if (idx === -1) return null

    const existing = liquidaciones.value[idx]
    const totalVentas = data.total_ventas_brutas !== undefined ? Number(data.total_ventas_brutas) : existing.total_ventas_brutas
    const costos = data.costo_taller_insumos !== undefined ? Number(data.costo_taller_insumos) : existing.costo_taller_insumos
    const gastos = data.gastos_operativos !== undefined ? Number(data.gastos_operativos) : existing.gastos_operativos
    const utilNeta = Math.max(0, totalVentas - costos - gastos)
    const fondoMonto = Math.round(utilNeta * 0.4)
    const utilRepartible = utilNeta - fondoMonto

    const updated: LiquidacionSocias = {
      ...existing,
      ...data,
      total_ventas_brutas: totalVentas,
      costo_taller_insumos: costos,
      gastos_operativos: gastos,
      utilidad_neta_total: utilNeta,
      fondo_reinversion_monto: fondoMonto,
      utilidad_repartible: utilRepartible,
    }

    liquidaciones.value[idx] = updated
    return updated
  }

  function eliminarLiquidacion(id: number): boolean {
    const idx = liquidaciones.value.findIndex((l) => l.id === id)
    if (idx !== -1) {
      liquidaciones.value.splice(idx, 1)
      return true
    }
    return false
  }

  function cambiarEstadoLiquidacion(id: number, nuevoEstado: LiquidacionSocias['estado']) {
    const l = liquidaciones.value.find((x) => x.id === id)
    if (l) {
      l.estado = nuevoEstado
      if (nuevoEstado === 'PAGADA') {
        // Mark all items as PAGADO
        l.distribucion.forEach((d) => {
          d.estado_pago = 'PAGADO'
          if (!d.fecha_pago) d.fecha_pago = new Date().toISOString().split('T')[0]
        })
      }
    }
  }

  function marcarPagoSociaItem(liquidacionId: number, sociaId: number, comprobante?: string) {
    const l = liquidaciones.value.find((x) => x.id === liquidacionId)
    if (l) {
      const item = l.distribucion.find((d) => d.socia_id === sociaId)
      if (item) {
        item.estado_pago = 'PAGADO'
        item.fecha_pago = new Date().toISOString().split('T')[0]
        if (comprobante) item.comprobante_transferencia = comprobante
      }
      // If all paid, mark whole liquidation as PAGADA
      const todasPagadas = l.distribucion.every((d) => d.estado_pago === 'PAGADO')
      if (todasPagadas) {
        l.estado = 'PAGADA'
      }
    }
  }

  // CRUD Actions: Anticipos
  function crearAnticipo(antData: Partial<AnticipoSocia>): AnticipoSocia {
    const nextId = (anticipos.value.length ? Math.max(...anticipos.value.map((a) => a.id)) : 0) + 1
    const soc = socias.value.find((s) => s.id === antData.socia_id)
    const nuevo: AnticipoSocia = {
      id: nextId,
      socia_id: antData.socia_id || 2,
      nombre_socia: soc?.nombre || antData.nombre_socia || 'Socia Atelier',
      fecha: antData.fecha || new Date().toISOString().split('T')[0],
      monto: Number(antData.monto) || 0,
      concepto: antData.concepto || 'Adelanto a cuenta de utilidades',
      metodo_desembolso: antData.metodo_desembolso || 'Transferencia Bancaria',
      estado: antData.estado || 'PENDIENTE_DESCUENTO',
      comprobante: antData.comprobante || '',
      observaciones: antData.observaciones || '',
    }
    anticipos.value.unshift(nuevo)
    return nuevo
  }

  function actualizarAnticipo(id: number, data: Partial<AnticipoSocia>): AnticipoSocia | null {
    const idx = anticipos.value.findIndex((a) => a.id === id)
    if (idx === -1) return null
    anticipos.value[idx] = { ...anticipos.value[idx], ...data }
    return anticipos.value[idx]
  }

  function eliminarAnticipo(id: number): boolean {
    const idx = anticipos.value.findIndex((a) => a.id === id)
    if (idx !== -1) {
      anticipos.value.splice(idx, 1)
      return true
    }
    return false
  }

  function cambiarEstadoAnticipo(id: number, estado: AnticipoSocia['estado']) {
    const a = anticipos.value.find((x) => x.id === id)
    if (a) {
      a.estado = estado
    }
  }

  return {
    insumos,
    recetas,
    prendasListas,
    clientes,
    pedidos,
    ventas,
    totalVentasRealizadas,
    totalGananciaVentas,
    margenPromedioVentas,
    distribucionSociasVentas,
    totalVentas,
    totalUtilidad,
    rentabilidadPromedio,
    pedidosActivos,
    insumosCriticos,
    valorTotalInventario,
    prendasStockFisico,
    prendasStockDisponible,
    valorizacionPVP,
    distribucionSocias,
    pipelineCounts,
    ajustarStockInsumo,
    agregarCompraInsumo,
    ajustarStockPrenda,
    crearPedido,
    cambiarEstadoPedido,
    crearCliente,
    actualizarCliente,
    crearReceta,
    crearInsumo,
    crearVenta,
    actualizarVenta,
    eliminarVenta,
    cambiarEstadoVenta,
    socias,
    liquidaciones,
    anticipos,
    totalHistoricoFacturadoLiquidaciones,
    totalHistoricoUtilidadSocias,
    totalHistoricoFondoReinversion,
    totalHistoricoRepartidoMargara,
    totalHistoricoRepartidoValqui,
    totalAnticiposPendientes,
    crearSocia,
    actualizarSocia,
    eliminarSocia,
    toggleActivoSocia,
    crearLiquidacion,
    actualizarLiquidacion,
    eliminarLiquidacion,
    cambiarEstadoLiquidacion,
    marcarPagoSociaItem,
    crearAnticipo,
    actualizarAnticipo,
    eliminarAnticipo,
    cambiarEstadoAnticipo,
    proveedoresMaestros,
    canalesVentaMaestros,
    metodosPagoMaestros,
    categoriasColeccionMaestros,
    ubicacionesTallerMaestros,
    tallasEstandarMaestros,
    productosSinTallaMaestros,
    parametrosCosteo,
    crearProveedor,
    actualizarProveedor,
    eliminarProveedor,
    crearCanalVenta,
    actualizarCanalVenta,
    eliminarCanalVenta,
    crearMetodoPago,
    actualizarMetodoPago,
    eliminarMetodoPago,
    crearCategoriaColeccion,
    actualizarCategoriaColeccion,
    eliminarCategoriaColeccion,
    crearUbicacionTaller,
    actualizarUbicacionTaller,
    eliminarUbicacionTaller,
    crearTallaEstandar,
    actualizarTallaEstandar,
    eliminarTallaEstandar,
    crearProductoSinTalla,
    actualizarProductoSinTalla,
    eliminarProductoSinTalla,
    actualizarParametrosCosteo,
  }
})
