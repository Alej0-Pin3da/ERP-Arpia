# Manual Operativo & Guía Financiera - Arpía Atelier ERP

Este documento contiene la guía operativa detallada para la gestión integral del taller de alta costura y corsetería **Arpía Atelier**, incluyendo la administración de inventario, recetas BOM, pedidos a medida, ventas realizadas y el modelo estatutario de reparto de utilidades entre socias.

---

## Índice
1. [Ingreso y Gestión de Prendas Confeccionadas](#1-ingreso-y-gestión-de-prendas-confeccionadas)
2. [Gestión de Categorías en Maestros](#2-gestión-de-categorías-en-maestros)
3. [Administración de Usuarios y Permisos](#3-administración-de-usuarios-y-permisos)
4. [Gestión de Insumos, Telas y Proveedores](#4-gestión-de-insumos-telas-y-proveedores)
5. [Edición de Recetas de Confección y Fichas Técnicas (BOM)](#5-edición-de-recetas-de-confección-y-fichas-técnicas-bom)
6. [Historial y Ejemplos de Ventas Realizadas](#6-historial-y-ejemplos-de-ventas-realizadas)
7. [Modelo y Ejemplos de Reparto de Socias](#7-modelo-y-ejemplos-de-reparto-de-socias)

---

## 1. Ingreso y Gestión de Prendas Confeccionadas

Existen dos vías para registrar y controlar las prendas terminadas disponibles en el perchero/showroom:

### Vía A: Desde el Módulo de Perchero (`Prendas Listas`)
1. Ingresa a la sección **"Prendas Listas"** en el menú lateral.
2. Cada tarjeta representa un modelo de la colección (por ejemplo, *Set Aelo*, *Corset Garras*, *Falda Emily*).
3. En la tabla de variantes (desglosada por talla XS, S, M, L y color):
   * Haz clic en el botón **`+1`** para ingresar unidades terminadas directamente al inventario físico.
   * Haz clic en **`-1`** para registrar retiros o ventas directas en showroom.
   * El sistema actualiza en tiempo real los valores de **Stock Físico**, **Reservado** y **Disponible**.
4. Haz clic en el botón **`Etiqueta QR`** para generar el certificado de autenticidad y etiqueta física de alta costura con código de barras y cuidados de lavado.

### Vía B: Desde el Módulo de Taller (`Producción / Kanban`)
1. Cuando se confecciona un pedido sobre medidas o un lote para stock, el pedido avanza por las 8 fases del taller:
   * *COTIZADO → CORTE → COSTURA → ACABADOS → CONTROL DE CALIDAD → LISTO → ENTREGADO*.
2. Al mover la orden al estado **LISTO** o **ENTREGADO**:
   * El sistema descuenta automáticamente los insumos textiles requeridos según la ficha BOM.
   * La prenda se suma al inventario disponible para entrega o venta.

---

## 2. Gestión de Categorías en Maestros

El catálogo maestro organiza los recursos del atelier en dos grandes familias:

### A. Categorías de Insumos Textiles & Fornituras
* **Telas & Sedas**: Satín duquesa, encaje chantilly, tules bordados, popelinas de algodón, terciopelos.
* **Estructura & Corsetería**: Varillas de acero espiralado inoxidable, varillas plásticas de alta densidad, busks de acero para cierre frontal.
* **Herrajes & Metales**: Ojaletes metálicos niquelados, pasadores, argollas, corchetes y cierres reforzados.
* **Forros & Entretelas**: Entretelas termoadhesivas tejidas, batista de algodón, forro tafetán y retor para pruebas.

### B. Categorías de Prendas Terminadas
* **Corsets Overbust & Underbust**
* **Lencería de Autor & Bustiers**
* **Prêt-à-Porter & Faldas Estructuradas**
* **Vestidos & Piezas a Medida**

> **Procedimiento de Edición**: Al crear o modificar un insumo (en *Inventario*) o una receta (en *Fichas Técnicas*), puedes seleccionar del listado desplegable o registrar una categoría personalizada que se indexará automáticamente en los filtros globales del sistema.

---

## 3. Administración de Usuarios y Permisos

El sistema implementa un modelo de control de acceso basado en roles (RBAC) adaptado a la dinámica del taller:

| Rol | Usuario de Ejemplo | Funcionalidades Habilitadas |
| :--- | :--- | :--- |
| **`Admin`** | **Valeria Arpía** *(Directora Creativa)* | Acceso total: Configuración de costos, liquidación financiera de socias, edición de márgenes BOM y auditoría completa. |
| **`Operador`** | **Camila Modista** *(Jefa de Taller)* | Control del tablero Kanban de producción, registro de tiempos reales de modistería, actualización de inventario físico y toma de medidas anatómicas. |
| **`Consulta`** | **Elena Inversionista** *(Socia Auditora)* | Modo lectura para visualización de dashboards ejecutivos, catálogo de showroom y balances generales. |

*Para alternar o probar permisos*: Ve al menú **"Usuarios"** y selecciona el rol activo desde el panel superior.

---

## 4. Gestión de Insumos, Telas y Proveedores

1. **Creación de Nuevo Insumo**:
   * Ve a **"Inventario"** y presiona **`+ Nuevo Insumo`**.
   * Define el código único (ej: `TEL-SAT-01`), nombre descriptivo, clasificación (*Directo / Indirecto*), unidad de medida (*Metros, Unidades, Rollos*), proveedor y costo de reposición.
2. **Ingreso de Compras & Abastecimiento**:
   * Haz clic en **`+ Compra Insumo`** en la fila correspondiente para ingresar facturas de compra y actualizar el costo promedio ponderado.
3. **Generador de Órdenes a Proveedores**:
   * Haz clic en **`Orden a Proveedores`** para identificar de forma automática los insumos que se encuentran por debajo del stock de seguridad y generar la orden consolidada para textileras como *Atenea Bordados* o distribuidores de herrajes.

---

## 5. Edición de Recetas de Confección y Fichas Técnicas (BOM)

Las fichas BOM (*Bill of Materials*) determinan el costo exacto de fabricación de cada pieza:

1. Ve a **"Fichas Técnicas & BOM"**.
2. Haz clic en **`Ver Ficha Técnica`** de cualquier modelo o en **`+ Nueva Receta BOM`**.
3. **Composición de la Ficha Técnica**:
   * **Matriz de Insumos**: Define el metraje de telas principales, forros, metros de varilla de acero, número de ojaletes y el porcentaje de merma por corte anatómico al sesgo (*5% a 15%*).
   * **Mano de Obra & Fases de Confección**: Asigna los minutos requeridos para cada fase (*Patronaje, Corte & Fusing, Envarillado, Ojales y Acabados a Mano*).
   * **Costos Indirectos de Fabricación (CIF)**: Proporción de energía, depreciación de maquinaria Singer y desgaste de agujas.
   * **Markup & Precio de Venta (PVP)**: El sistema calcula automáticamente el costo primo, costo total y sugiere el precio al público según el margen deseado.

---

## 6. Historial y Ejemplos de Ventas Realizadas

A continuación se detalla el registro de ventas con su desglose de costo de fabricación, precio facturado y rentabilidad neta generada:

| Orden N° | Clienta | Prenda / Producto Confeccionado | Estado | PVP Facturado | Costo Total (Insumos + MOD) | Utilidad Neta | Margen % |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **#ORD-ARP-001** | Gabriela (Gaby) | Caja Colección *"Saca las Garras"* | `ENTREGADO` | $295.000 COP | $129.388 COP | **$165.612 COP** | **56.1%** |
| **#ORD-ARP-002** | Celeste | Set Aelo: Corset Rojo Pastel | `ENTREGADO` | $80.000 COP | $38.805 COP | **$41.195 COP** | **51.5%** |
| **#ORD-ARP-003** | Maira (*Comic) | Blusa Malla Garra Manga Larga | `ENTREGADO` | $90.000 COP | $21.561 COP | **$68.439 COP** | **76.0%** |
| **#ORD-ARP-004** | Gabriela (Gaby) | Set Ocípete: Bustier Encaje / Satín | `ENTREGADO` | $71.250 COP | $26.109 COP | **$45.141 COP** | **63.4%** |
| **#ORD-ARP-005** | Camila | Corset Estructurado *"Garras"* | `ENTREGADO` | $95.000 COP | $29.826 COP | **$65.174 COP** | **68.6%** |
| **#ORD-ARP-007** | Evento NANA / Feria | Pack 4 Faldas Estructuradas Emily | `ENTREGADO` | $340.000 COP | $96.000 COP | **$244.000 COP** | **71.8%** |

### Resumen Financiero del Periodo:
* **Ingresos Totales por Ventas:** `$1.141.250 COP`
* **Costo Total de Producción:** `$433.250 COP`
* **Utilidad Neta Acumulada para Reparto:** **`$708.000 COP`**
* **Margen Promedio Ponderado del Atelier:** **`62.0%`**

---

## 7. Modelo y Ejemplos de Reparto de Socias

El estatuto financiero de **Arpía Atelier** establece la distribución de la **Utilidad Neta** bajo la siguiente regla proporcional:

```
                                    ┌─── [40%] Fondo de Reinversión Taller : $283.200 COP
                                    │
Utilidad Neta Total ($708.000 COP) ─┼─── [30%] Ganancia Socia Margara      : $212.400 COP
                                    │
                                    └─── [30%] Ganancia Socia Valqui       : $212.400 COP
```

### Detalle de Asignación:

1. **Fondo de Reinversión de Taller (40%) = `$283.200 COP`**
   * **Objetivo**: Asegurar liquidez operativa para compra por volumen de insumos críticos (*rollos de satín duquesa, encaje chantilly, cajas de varillas de acero*), mantenimiento preventivo de máquinas industriales y desarrollo de nuevas colecciones.

2. **Liquidación Socia Margara (30%) = `$212.400 COP`**
   * **Concepto**: Retribución por corte anatómico de precisión, confección de alta dificultad técnica, colocación de ballenas y control de calidad en taller.

3. **Liquidación Socia Valqui (30%) = `$212.400 COP`**
   * **Concepto**: Retribución por diseño creativo de colecciones, patronaje y graduación de moldes, pruebas de calce con clientas y gestión de ventas.

---
*Manual generado y actualizado para la versión 1.2 del ERP de Arpía Atelier.*
