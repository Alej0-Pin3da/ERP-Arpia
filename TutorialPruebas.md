# Tutorial de pruebas integrales ERP-Arpia

Verificacion funcional de todo lo publicado hasta `67d8cf6`, en el orden de uso del taller.

## Ruta rapida

1. Levantar el stack en modo dev.
2. Probar Productos (filtro y ficha).
3. Probar Cotizador (auditor, ficha, BOM y herrajes).
4. Probar Kits y venta explotada.
5. Probar Termometro y saldos.
6. Ejecutar verificacion tecnica.

## 0. Arranque del stack

```powershell
npm run dev:all
```

| Verificacion | Resultado esperado |
|---|---|
| Docker DB y API en 8080 | `Invoke-WebRequest http://localhost:8080/docs` responde con estado menor a 500 |
| Frontend vite en 5173 | La aplicacion abre sin errores en consola |
| Consola del navegador | Sin `Vue warn` ni `Cannot access before initialization` |

> Si Docker no inicia, iniciarlo manualmente y reintentar. No usar backend local salvo que el archivo `.env` apunte a `localhost:5433`.

## 1. Productos: filtro dinamico y ficha

Ir a **Productos** (`/productos`).

### 1.1 Filtro de categorias

1. Ir a Maestros, seccion Categorias, y crear una categoria de tipo `CATEGORIA`, por ejemplo `Lenceria` (con tilde a proposito).
2. Volver a Productos y abrir el filtro de categoria.
3. Verificar que la categoria nueva aparece sola, sin cambios de codigo.
4. Buscar en minusculas y sin tilde, por ejemplo `lenceria` o `corseteria`.

Resultado esperado: la busqueda es insensible a mayusculas y tildes (`Corseteria`, `Lenceria`). Si la categoria deja de existir, el filtro vuelve a "Todos los Modelos".

### 1.2 Ficha tecnica

1. Abrir cualquier receta y consultar la ficha.
2. Verificar que presenta mano de obra, costo de insumos, tiempos y margen.

Resultado esperado: la vista carga sin error de setup y sin pantalla en blanco.

## 2. Cotizador: evaluador interno y auditor

Ir a **Cotizador** (`/cotizador`).

### 2.1 Evaluador interno

1. Verificar que no existen: campo Cliente, campo Observaciones, boton de WhatsApp ni control deslizante de margen.
2. Verificar que el margen aplicado es siempre la meta global (valor por defecto 35 %).

Resultado esperado: el panel muestra `GANANCIA: $X (Y%)` con la pastilla `RENTABLE` o `ALERTA` segun la meta.

### 2.2 Auditor y boton Actualizar Ficha

1. Cargar una receta con BOM real.
2. Ajustar el precio de tienda y verificar el veredicto del auditor.
3. Pulsar **Actualizar Ficha Tecnica**.
4. Verificar el mensaje de confirmacion con el nombre del producto.
5. Recargar la receta y comprobar que el campo "Costo real BOM (DB)" refleja el cambio (el campo `tiempo_confeccion_min` alimenta la mano de obra).

### 2.3 Sincronizacion de cantidades al BOM (Fase 2)

1. Editar manualmente la cantidad de una linea del BOM en el cotizador.
2. Pulsar Actualizar Ficha.
3. Se presenta el dialogo de confirmacion con el detalle linea por linea.
4. Confirmar la operacion.

Resultado esperado: se ejecuta `PUT bom/insumos` por linea, sin recarga completa, y los valores originales quedan actualizados.

### 2.4 Herrajes al BOM

1. En la Seccion 2, verificar los textos: "Sumar a Herrajes" y "Llevar herrajes al BOM".
2. Pulsar **Llevar herrajes al BOM** con una receta cargada.
3. En el dialogo de mapeo, asignar cada fila a un insumo real del maestro.
4. Confirmar y verificar que se crean lineas mediante `POST bom/insumos` con el detalle de auditoria del cotizador.

Resultado esperado: el costo real incluye esas lineas valorizadas al precio del maestro. Por diseno no se requiere igualdad al centavo con el monto auditado.

## 3. Kits y venta explotada

### 3.1 Menu

1. Verificar las entradas del menu lateral: **Kits y Cajas** (`/kits`) y **Saldos en Vivo** (`/saldos`).
2. Abrir cada vista y verificar que reutilizan los componentes existentes sin logica duplicada.

### 3.2 Venta de caja promocional (prueba real pendiente)

1. Ir a Ventas y crear una Nueva Venta.
2. En el campo **Prenda / Modelo** verificar que solo se listan productos de `/productos` (los kits no aparecen aqui; es el comportamiento esperado).
3. Utilizar el selector de **caja promocional**, elegir un kit y la cantidad de cajas.
4. Verificar que se expande en un renglon por producto (cantidad del kit por cajas, promocion prorrateada por precio sugerido, redondeo absorbido en el ultimo renglon).
5. Completar cliente, canal (por ejemplo Showroom Pereira) y metodo de pago, luego guardar.
6. Abrir la venta guardada y verificar detalles, descuento de stock, ganancia y reparto 40/30/30.

## 4. Termometro y costos fijos

### 4.1 Configuracion (pendiente del operador)

1. Ir a Maestros, seccion Costeo.
2. Registrar el valor de `costos_fijos_mensuales`. Sin este valor el componente permanece en estado `sin_configurar`.

### 4.2 Componente en el panel principal

1. Ir al Dashboard y localizar el **Termometro Operativo del Mes**.
2. Verificar el estado segun el mes: `sin_datos`, `en_camino` (presenta faltante), `superada` (presenta utilidad extra) o `alerta` (margen menor o igual a cero, sin barra).

Resultado esperado: montos en COP (`es-CO`), periodo en `America/Bogota`, solo ventas en estado `confirmed` y devoluciones confirmadas neteadas.

## 5. Saldos y finanzas

1. Ir a **Saldos en Vivo** (`/saldos`) y verificar los saldos por socia.
2. Verificar anticipos (`PENDIENTE_DESCUENTO` hacia `DESCONTADO` o `ANULADO`) y distribuciones (`PENDIENTE`, `PAGADO` o `RETENIDO`).

## Lista de verificacion final

- [ ] Productos filtra sin tildes y sin errores de inicializacion
- [ ] Cotizador sin campos externos y auditor con veredicto correcto
- [ ] Actualizar Ficha persiste mano de obra e insumos, y actualiza el costo real
- [ ] Sincronizacion del BOM solicita confirmacion linea por linea
- [ ] Herrajes se asigna a insumos reales y crea lineas en el BOM
- [ ] Venta de caja promocional genera renglones y descuenta stock
- [ ] Termometro presenta meta, faltante o utilidad con costos fijos registrados
- [ ] Kits y Saldos abren desde el menu lateral

## Verificacion tecnica

```powershell
npm run lint
npm run test
npm run build
```

Resultado esperado: lint sin errores, pruebas vitest en verde (67/67 en frontend) y build sin fallos. Para cambios de backend, ejecutar `pytest` del modulo correspondiente.

## Paso siguiente

Cuando la lista de verificacion este completa, registrar los resultados (fallos con captura y ruta exacta, o confirmacion total) y continuar con el plan de subida al servidor, incluidas las migraciones (entre ellas `e7f1a2b3c4d5`) y la compilacion de produccion.
