# Registro de Cambios y Evolución - Versión 3 (V3)
## Atelier Arpía — ERP & Sistema Integral de Confección de Autor

Este documento registra cronológica y detalladamente todas las modificaciones, nuevas funcionalidades, módulos maestros, correcciones y expansiones integradas a partir de la versión 3 (V3).

---

### [2026-08-23] — V3.0.0: Módulo Integral de Catálogos & Parámetros Maestros (Full CRUD)

#### 1. Arquitectura de Estado Global (`src/stores/atelier.ts`)
- **Nuevas Estructuras de Datos y Tipado TypeScript:**
  - `ProveedorMaestro`: Directorio integral de proveedores con categoría, ciudad, tiempos de entrega en días hábiles, condiciones de pago, contacto directo y calificación.
  - `CanalVentaMaestro`: Puntos de venta físicos (Showroom Pereira), canales digitales (Instagram / WhatsApp) y stands en eventos/convenciones con costos fijos y tasas de comisión.
  - `MetodoPagoMaestro`: Medios de pago bancarios, billeteras digitales y pasarelas de datáfono/link con tasa de comisión financiera y plazos de acreditación.
  - `CategoriaColeccionMaestro`: Familias de confección (Corsets de Estructura Fuerte, Corsets Livianos, Tote Bags & Merch) con márgenes meta de rentabilidad (%) y asignación de tipo de talla.
  - `UbicacionTallerMaestro`: Bodegas y ubicaciones físicas de almacenamiento (rollos de tela, gavetas de herrajes, percheros y bodega de lonas) con códigos y capacidades.
  - `TallaEstandarMaestro`: Matriz oficial de tallaje de alta costura y corsetería (**XXS, XS, S, M, L, XL**) con contornos de busto, cintura, cadera y factor de reducción en cm.
  - `ProductoSinTallaMaestro`: Especificaciones técnicas para productos no basados en silueta corporal (*Tote Bags ilustradas de lona, Scrunchies, Pañoletas y Joyería de autor*) con dimensiones, materiales y precios sugeridos.
  - `ParametrosCosteoMaestro`: Tarifas base de mano de obra (costo/minuto de costura, costo/hora de patronaje y corte), merma textil (%) y estatuto de reparto de utilidades de socias (40% Fondo Taller, 30% Margara, 30% Valqui).
- **Acciones CRUD Implementadas en el Store Pinia:**
  - `crearProveedor`, `actualizarProveedor`, `eliminarProveedor`
  - `crearCanalVenta`, `actualizarCanalVenta`, `eliminarCanalVenta`
  - `crearMetodoPago`, `actualizarMetodoPago`, `eliminarMetodoPago`
  - `crearCategoriaColeccion`, `actualizarCategoriaColeccion`, `eliminarCategoriaColeccion`
  - `crearUbicacionTaller`, `actualizarUbicacionTaller`, `eliminarUbicacionTaller`
  - `crearTallaEstandar`, `actualizarTallaEstandar`, `eliminarTallaEstandar`
  - `crearProductoSinTalla`, `actualizarProductoSinTalla`, `eliminarProductoSinTalla`
  - `actualizarParametrosCosteo`: Con soporte para persistencia reactiva y cálculo en tiempo real.

---

#### 2. Vista de Catálogos & Parámetros Maestros (`src/views/MaestrosView.vue`)
- **Navegación Modular por Pestañas:**
  - **Pestaña 1 (Proveedores Textil & Herrajes):** Tarjetas interactivas con datos de contacto, enlaces directos a WhatsApp, filtro por categoría de insumos, modal de alta/edición y botón de eliminación.
  - **Pestaña 2 (Canales de Venta & Comercialización):** Panel de gestión de canales de comercialización con cálculo de costos de intermediación y comisiones por venta.
  - **Pestaña 3 (Medios de Pago & Pasarelas):** Administración de tasas de adquirencia, cuentas y tiempos de acreditación bancaria.
  - **Pestaña 4 (Matriz de Tallas & Formatos Sin Talla):** 
    - Tabla editable de medidas anatómicas estándar para corsetería.
    - Fichas técnicas editables para Tote Bags, moñas/scrunchies y merchandising.
  - **Pestaña 5 (Familias de Colección):** Configuración de colecciones activas y márgenes de rentabilidad meta.
  - **Pestaña 6 (Ubicaciones Físicas del Taller):** Directorio de estantes, bodegas y gavetas de insumos.
  - **Pestaña 7 (Tarifas Globales de Costeo & Estatuto Socias):** Formulario para ajustar los valores del minuto de costura y hora de corte, validando en tiempo real que la regla 40/30/30 sume exactamente el 100%.
- **Modales Formularios Responsivos y Accesibles:**
  - Modales dedicados para la creación y edición de cada entidad con validaciones de campos y botones semánticos de acción.

---

### Instrucción de Mantenimiento Continuo
A partir de esta versión (V3), cada cambio, ajuste de lógica, nuevo componente o funcionalidad agregada en el proyecto será documentada en este archivo `CambiosV3.md` con su respectiva fecha, archivo modificado y resumen operativo.
