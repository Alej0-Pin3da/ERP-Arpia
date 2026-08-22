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

export interface ClienteCRM {
  id: number
  nombre: string
  tipo: string
  telefono: string
  email: string
  pedidos_count: number
  total_compras: number
  medidas: MedidasAnatomicas
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
      tipo: 'Cliente del taller',
      telefono: '+57 312 889 4411',
      email: 'gaby.arpia@email.com',
      pedidos_count: 3,
      total_compras: 446250.00,
      medidas: { busto: 92, cintura: 68, cadera: 98, espalda: 37, talle: 42, largo: 60 },
    },
    {
      id: 2,
      nombre: 'Maira (*Comic)',
      tipo: 'Cliente del taller',
      telefono: '+57 315 777 8899',
      email: 'maira.comic@email.com',
      pedidos_count: 1,
      total_compras: 90000.00,
      medidas: { busto: 88, cintura: 64, cadera: 92, espalda: 36, talle: 40, largo: 58 },
    },
    {
      id: 3,
      nombre: 'Camila',
      tipo: 'Cliente del taller',
      telefono: '+57 318 444 2233',
      email: 'camila.pereira@email.com',
      pedidos_count: 1,
      total_compras: 95000.00,
      medidas: { busto: 95, cintura: 72, cadera: 102, espalda: 39, talle: 43, largo: 62 },
    },
    {
      id: 4,
      nombre: 'Valentina Restrepo (Hermana Ale)',
      tipo: 'Cliente del taller',
      telefono: '+57 312 456 7890',
      email: 'valentina.r@email.com',
      pedidos_count: 2,
      total_compras: 180000.00,
      medidas: { busto: 90, cintura: 66, cadera: 96, espalda: 38, talle: 41, largo: 59 },
    },
    {
      id: 5,
      nombre: 'Celeste',
      tipo: 'Cliente del taller',
      telefono: '+57 301 222 9988',
      email: 'celeste.taller@email.com',
      pedidos_count: 1,
      total_compras: 80000.00,
      medidas: { busto: 86, cintura: 62, cadera: 90, espalda: 35, talle: 39, largo: 55 },
    },
    {
      id: 6,
      nombre: 'Evento NANA / Feria Gótica',
      tipo: 'Cliente del taller',
      telefono: '+57 310 000 1122',
      email: 'eventos@ferianana.co',
      pedidos_count: 2,
      total_compras: 520000.00,
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

  // Computed Totals & Metrics
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
      nombre: cliente.nombre || 'Nuevo Cliente',
      tipo: 'Cliente del taller',
      telefono: cliente.telefono || '',
      email: cliente.email || '',
      pedidos_count: 0,
      total_compras: 0,
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

  return {
    insumos,
    recetas,
    prendasListas,
    clientes,
    pedidos,
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
  }
})
