# DATOS DE CARGA — ARPIA.xlsx (regenerado 2026-08-09)

> Fuente: hojas de inversión (VALQUI/MARGARA) + BOM + OCT25 + VENTAS + CAJAS.
> SQL listos para DBeaver: ejecutar EN ORDEN; los id se resuelven por subquery de nombre.

## COMO USAR

1. Conectar a BD `arpia` (localhost:5433 / arpia / arpia_secret).
2. Ejecutar secciones en orden (1→11).
3. No ejecutar dos veces (duplica).
4. Fechas formato 'YYYY-MM-DD HH:MM:SS+00'.

## 1. TABLA Proveedores (34) — SQL

```sql
INSERT INTO "Proveedores" (nombre) VALUES ('Atenea bordados y encajes');
INSERT INTO "Proveedores" (nombre) VALUES ('Boutique de los empaques');
INSERT INTO "Proveedores" (nombre) VALUES ('C+basics');
INSERT INTO "Proveedores" (nombre) VALUES ('CasaTextil');
INSERT INTO "Proveedores" (nombre) VALUES ('ColombiaHosting');
INSERT INTO "Proveedores" (nombre) VALUES ('Dollarcity');
INSERT INTO "Proveedores" (nombre) VALUES ('Dora Estela');
INSERT INTO "Proveedores" (nombre) VALUES ('Etsy');
INSERT INTO "Proveedores" (nombre) VALUES ('Gerrajes');
INSERT INTO "Proveedores" (nombre) VALUES ('Hilos y suministros Ltda');
INSERT INTO "Proveedores" (nombre) VALUES ('HomeCenter');
INSERT INTO "Proveedores" (nombre) VALUES ('ICOLTEX');
INSERT INTO "Proveedores" (nombre) VALUES ('Kilotelas');
INSERT INTO "Proveedores" (nombre) VALUES ('La guillotina');
INSERT INTO "Proveedores" (nombre) VALUES ('Las 3BBB premium');
INSERT INTO "Proveedores" (nombre) VALUES ('MercadoLibre');
INSERT INTO "Proveedores" (nombre) VALUES ('Mil Adornos');
INSERT INTO "Proveedores" (nombre) VALUES ('Mil Telas');
INSERT INTO "Proveedores" (nombre) VALUES ('SINGER');
INSERT INTO "Proveedores" (nombre) VALUES ('Teks');
INSERT INTO "Proveedores" (nombre) VALUES ('Textiles F&M');
INSERT INTO "Proveedores" (nombre) VALUES ('The lingerie Formula');
INSERT INTO "Proveedores" (nombre) VALUES ('almacen de la 6ta');
INSERT INTO "Proveedores" (nombre) VALUES ('amazon');
INSERT INTO "Proveedores" (nombre) VALUES ('auratex');
INSERT INTO "Proveedores" (nombre) VALUES ('brother');
INSERT INTO "Proveedores" (nombre) VALUES ('corsetería');
INSERT INTO "Proveedores" (nombre) VALUES ('facol');
INSERT INTO "Proveedores" (nombre) VALUES ('grupo textil moda');
INSERT INTO "Proveedores" (nombre) VALUES ('las 3 b');
INSERT INTO "Proveedores" (nombre) VALUES ('sesgocolor');
INSERT INTO "Proveedores" (nombre) VALUES ('telas Medellín');
INSERT INTO "Proveedores" (nombre) VALUES ('temu');
INSERT INTO "Proveedores" (nombre) VALUES ('zuretex');
```

## 2. TABLA Categorias_Insumos (3) — SQL

```sql
INSERT INTO "Categorias_Insumos" (nombre) VALUES ('Telas');
INSERT INTO "Categorias_Insumos" (nombre) VALUES ('Herrajes');
INSERT INTO "Categorias_Insumos" (nombre) VALUES ('Empaques');
```

## 3. TABLA Tipos_Producto (6) — SQL

```sql
INSERT INTO "Tipos_Producto" (nombre) VALUES ('Accesorio');
INSERT INTO "Tipos_Producto" (nombre) VALUES ('Blusa');
INSERT INTO "Tipos_Producto" (nombre) VALUES ('Combo');
INSERT INTO "Tipos_Producto" (nombre) VALUES ('Corsetería');
INSERT INTO "Tipos_Producto" (nombre) VALUES ('Lencería');
INSERT INTO "Tipos_Producto" (nombre) VALUES ('Set');
```

## 4. TABLA Socios_Configuracion (3) — SQL (suma = 100)

```sql
INSERT INTO "Socios_Configuracion" (nombre, porcentaje_participacion) VALUES ('Valqui', 40);
INSERT INTO "Socios_Configuracion" (nombre, porcentaje_participacion) VALUES ('Margarita', 30);
INSERT INTO "Socios_Configuracion" (nombre, porcentaje_participacion) VALUES ('ARPIA', 30);
```

## 5. TABLA Clientes (12) — SQL

```sql
INSERT INTO "Clientes" (nombre) VALUES ('Camila');
INSERT INTO "Clientes" (nombre) VALUES ('Juan jose');
INSERT INTO "Clientes" (nombre) VALUES ('Maira *Comic');
INSERT INTO "Clientes" (nombre) VALUES ('Maria caja cumple');
INSERT INTO "Clientes" (nombre) VALUES ('Olga');
INSERT INTO "Clientes" (nombre) VALUES ('Valentina hermana ale');
INSERT INTO "Clientes" (nombre) VALUES ('Valeria Amiga gaby');
INSERT INTO "Clientes" (nombre) VALUES ('Valqui');
INSERT INTO "Clientes" (nombre) VALUES ('celes');
INSERT INTO "Clientes" (nombre) VALUES ('celeste');
INSERT INTO "Clientes" (nombre) VALUES ('evento nana');
INSERT INTO "Clientes" (nombre) VALUES ('gaby');
```

## 6. TABLA Insumos (135) — SQL

> stock_actual del INVENTARIO OCT25 cuando existe, si no 0.

```sql
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'Aguja fileteadora # 12', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'Agujas punta de bola Colla', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'Agujas punta de bola Fill', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'Agujas punta de bola Plana', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'Alfileres', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'ARCO METALICO 2001 30', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'ARCO METALICO 2001 32', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'ARCO METALICO 2001 34', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'ARCO METALICO 2001 36', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Herrajes' LIMIT 1), 'Argolla numero 10 mm', 'un', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Herrajes' LIMIT 1), 'Argolla numero 8 mm', 'un', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Herrajes' LIMIT 1), 'Barilla poliester corset negro 8mm', 'un', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Empaques' LIMIT 1), 'Bolsa de seguridad negra 25 x 35', 'un', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Empaques' LIMIT 1), 'Bolsa de seguridad rosa 25 x 35', 'un', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Empaques' LIMIT 1), 'bolsas tul 12 x 17', 'un', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Herrajes' LIMIT 1), 'Boton Aro para las faldas', 'un', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Herrajes' LIMIT 1), 'Cadena gris delgada totebag', 'un', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Herrajes' LIMIT 1), 'Cadena plateada gruesa totebag', 'un', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Empaques' LIMIT 1), 'Cajas negras de 30 x 20 x7', 'un', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'Cinta Satin negra 1 1/2', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'Cinta Térmica X 5', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Herrajes' LIMIT 1), 'Cremallera num 3', 'un', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Herrajes' LIMIT 1), 'Cremalleras falda invisibles 20 cms', 'un', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Herrajes' LIMIT 1), 'deslizadores cremallera num 3', 'un', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'Elastico contorno negro 2cm 10 mts', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'Elastico de Contorno', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'Elastico eljowoo15', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'Elastico Panty blanco 10 mts', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'Elastico pitillo rosa', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'Elastico Trenzado (7 mm)', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'Elasticos cosrseteria etc', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'Encaje 6 cm calidad blanco 8 mts', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'Encaje 6 cm calidad negro 8 mts', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'encaje bicolor', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'encaje blanco', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'Encaje Blanco y negro para bicolor', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'Encaje bordado blanco y negro', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'Encaje de ramitas', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'Encaje Elastico 19 cm blanco 10 mts', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'Encaje Elastico 19 cm negro 10 mts', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'Encaje elastico 6 cm blanco', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'Encaje elastico 6 cm negro', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'Encaje elastico negro', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'Encaje elastico negro 23 cm 10 mts', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'Encaje negro', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'Encaje vino', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'Encaje y elasticos', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'Encajes', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'Entretela elastica negra', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'Entretela rigida blanca', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'envio telas atenea', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'Folder sesgo para plana', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Herrajes' LIMIT 1), 'forro varilla negro', 'un', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Herrajes' LIMIT 1), 'forro varilla piel', 'un', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'FRAMILON', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'Framilon blanco y negro', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'Framilon elastico plano 20 mts', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'Franela color negro', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'Franela color piel', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'Franela lycra 1 mt (blanco y negro)', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'Gabardina Ultra Poliester', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Herrajes' LIMIT 1), 'gafete 3x2 blanco', 'un', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Herrajes' LIMIT 1), 'gafete 3x2 negro', 'un', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Herrajes' LIMIT 1), 'Gafetes', 'un', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Herrajes' LIMIT 1), 'gafetes +arandelas', 'un', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Herrajes' LIMIT 1), 'Herrajes / gafetes / copas prehormadas', 'un', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'herrajes en forma 8 / G', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'Hilaza negra', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'Hilaza venus 150 gms blanco', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'Hilaza venus 150 gms negro', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'Hilaza venus negro', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'Hilaza venus piel', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'HILAZAS cono amarillo', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'Hilo poliester venus negro', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'Hilo poliester venus piel', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'Hilos + Hilazas', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'licras lencería', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'Lino vertigo', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'malla piel', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'malla piel negro', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'Mallatex blnaco y negro', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'mallatex negro', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'mallatex rosa', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'mallatex vino', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'marquillas en satin', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Herrajes' LIMIT 1), 'ojales metalicos 3/8 (grandes)', 'un', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'Piel de durazno + tejido de punto', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'planchuela fileteadora', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'Powernet negro delgado', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'Ref 100 24 cm tul bordado negro', 'm', 39, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'Ref 159 24 cm tul bordado rojo pastel', 'm', 21, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'Rosas tejidas para totebag', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'Satin elastico negro', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'Satin elastico rosa', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'Sellos Arpia', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'sesgo 2 cm negro', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'sesgo 2 cm piel', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'SESGO ELASTICO', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'Sesgo Elastico 2 10 mts', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'Sesgo Elastico blanco 1,5 10 mts', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'Sesgo elastico negro 2cm brillante', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'sesgo lorex blanco', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'sesgo lorex negro', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Herrajes' LIMIT 1), 'Sesgo rigido para ojales corset', 'un', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'Sesgo satin brillante', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'Sublimacion de la tela maya', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'Sublimacion para las totebag', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'Super Brioni', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Herrajes' LIMIT 1), 'Tapavarilla negro 10 mts', 'un', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'Tejido plano sim popelina (a cuadros bn)', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'Tela control blanca', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'Tela noche de viena negra', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Herrajes' LIMIT 1), 'telas + sesgos + tira +gafetes', 'un', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'Telas algodon jersey retazos blanco', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'Telas algodon jersey retazos negro', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Herrajes' LIMIT 1), 'Tensor 8 numero 10', 'un', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'terminal metalico para cintas', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Herrajes' LIMIT 1), 'Terminales de cordon', 'un', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'Tira brasier blanco', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'tira brasier negro', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'tira brasier piel', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'Tira de Brasier blanco 10 mts', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'Tira de brasier negro', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'Tira de Brasier negro 10 mts', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'Tira de poliester para las totebag', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'Tull bordado blanco', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'Tull bordado cafe', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'Tull bordado piel', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Herrajes' LIMIT 1), 'varilla plastica cortada 18 cm', 'un', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Herrajes' LIMIT 1), 'Varillas media copa', 'un', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'varios retazos', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Empaques' LIMIT 1), 'velo estrella (papel empaque)', 'un', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Telas' LIMIT 1), 'Velo surcido negro', 'm', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Herrajes' LIMIT 1), 'Zeta numero 10', 'un', 0, 0, 0);
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual) VALUES ((SELECT id FROM "Categorias_Insumos" WHERE nombre = 'Herrajes' LIMIT 1), 'Zeta numero 2 CM', 'un', 0, 0, 0);
```

## 7. TABLA Productos (22) — SQL

```sql
INSERT INTO "Productos" (tipo_producto_id, nombre, requiere_fabricacion, costos_operativos_fijos, precio_venta_sugerido) VALUES ((SELECT id FROM "Tipos_Producto" WHERE nombre = 'Blusa' LIMIT 1), 'Blusa Arpia', true, 0, 0);
INSERT INTO "Productos" (tipo_producto_id, nombre, requiere_fabricacion, costos_operativos_fijos, precio_venta_sugerido) VALUES ((SELECT id FROM "Tipos_Producto" WHERE nombre = 'Accesorio' LIMIT 1), 'BLUSA ARPIA MANGA LARGA', true, 0, 0);
INSERT INTO "Productos" (tipo_producto_id, nombre, requiere_fabricacion, costos_operativos_fijos, precio_venta_sugerido) VALUES ((SELECT id FROM "Tipos_Producto" WHERE nombre = 'Lencería' LIMIT 1), 'Blusa Manga Larga', true, 0, 0);
INSERT INTO "Productos" (tipo_producto_id, nombre, requiere_fabricacion, costos_operativos_fijos, precio_venta_sugerido) VALUES ((SELECT id FROM "Tipos_Producto" WHERE nombre = 'Lencería' LIMIT 1), 'Braleth diseño 1', true, 0, 0);
INSERT INTO "Productos" (tipo_producto_id, nombre, requiere_fabricacion, costos_operativos_fijos, precio_venta_sugerido) VALUES ((SELECT id FROM "Tipos_Producto" WHERE nombre = 'Lencería' LIMIT 1), 'Bustier', true, 0, 0);
INSERT INTO "Productos" (tipo_producto_id, nombre, requiere_fabricacion, costos_operativos_fijos, precio_venta_sugerido) VALUES ((SELECT id FROM "Tipos_Producto" WHERE nombre = 'Lencería' LIMIT 1), 'Cachetero', true, 0, 0);
INSERT INTO "Productos" (tipo_producto_id, nombre, requiere_fabricacion, costos_operativos_fijos, precio_venta_sugerido) VALUES ((SELECT id FROM "Tipos_Producto" WHERE nombre = 'Combo' LIMIT 1), 'Caja', true, 0, 0);
INSERT INTO "Productos" (tipo_producto_id, nombre, requiere_fabricacion, costos_operativos_fijos, precio_venta_sugerido) VALUES ((SELECT id FROM "Tipos_Producto" WHERE nombre = 'Accesorio' LIMIT 1), 'CAJA SACA LAS GARRAS', true, 0, 0);
INSERT INTO "Productos" (tipo_producto_id, nombre, requiere_fabricacion, costos_operativos_fijos, precio_venta_sugerido) VALUES ((SELECT id FROM "Tipos_Producto" WHERE nombre = 'Corsetería' LIMIT 1), 'Corset', true, 0, 0);
INSERT INTO "Productos" (tipo_producto_id, nombre, requiere_fabricacion, costos_operativos_fijos, precio_venta_sugerido) VALUES ((SELECT id FROM "Tipos_Producto" WHERE nombre = 'Corsetería' LIMIT 1), 'Corset Artemisia', true, 0, 0);
INSERT INTO "Productos" (tipo_producto_id, nombre, requiere_fabricacion, costos_operativos_fijos, precio_venta_sugerido) VALUES ((SELECT id FROM "Tipos_Producto" WHERE nombre = 'Corsetería' LIMIT 1), 'Corset Doble Cara', true, 0, 0);
INSERT INTO "Productos" (tipo_producto_id, nombre, requiere_fabricacion, costos_operativos_fijos, precio_venta_sugerido) VALUES ((SELECT id FROM "Tipos_Producto" WHERE nombre = 'Accesorio' LIMIT 1), 'CORSET GARRAS', true, 0, 0);
INSERT INTO "Productos" (tipo_producto_id, nombre, requiere_fabricacion, costos_operativos_fijos, precio_venta_sugerido) VALUES ((SELECT id FROM "Tipos_Producto" WHERE nombre = 'Corsetería' LIMIT 1), 'Corset Hypatia', true, 0, 0);
INSERT INTO "Productos" (tipo_producto_id, nombre, requiere_fabricacion, costos_operativos_fijos, precio_venta_sugerido) VALUES ((SELECT id FROM "Tipos_Producto" WHERE nombre = 'Lencería' LIMIT 1), 'Envio', true, 0, 0);
INSERT INTO "Productos" (tipo_producto_id, nombre, requiere_fabricacion, costos_operativos_fijos, precio_venta_sugerido) VALUES ((SELECT id FROM "Tipos_Producto" WHERE nombre = 'Lencería' LIMIT 1), 'Falda Emily', true, 0, 0);
INSERT INTO "Productos" (tipo_producto_id, nombre, requiere_fabricacion, costos_operativos_fijos, precio_venta_sugerido) VALUES ((SELECT id FROM "Tipos_Producto" WHERE nombre = 'Lencería' LIMIT 1), 'Noche y Dia', true, 0, 0);
INSERT INTO "Productos" (tipo_producto_id, nombre, requiere_fabricacion, costos_operativos_fijos, precio_venta_sugerido) VALUES ((SELECT id FROM "Tipos_Producto" WHERE nombre = 'Lencería' LIMIT 1), 'Papel', true, 0, 0);
INSERT INTO "Productos" (tipo_producto_id, nombre, requiere_fabricacion, costos_operativos_fijos, precio_venta_sugerido) VALUES ((SELECT id FROM "Tipos_Producto" WHERE nombre = 'Accesorio' LIMIT 1), 'SET AELO', true, 0, 0);
INSERT INTO "Productos" (tipo_producto_id, nombre, requiere_fabricacion, costos_operativos_fijos, precio_venta_sugerido) VALUES ((SELECT id FROM "Tipos_Producto" WHERE nombre = 'Accesorio' LIMIT 1), 'SET OCIPETE', true, 0, 0);
INSERT INTO "Productos" (tipo_producto_id, nombre, requiere_fabricacion, costos_operativos_fijos, precio_venta_sugerido) VALUES ((SELECT id FROM "Tipos_Producto" WHERE nombre = 'Accesorio' LIMIT 1), 'Tote Bag Arpia', true, 0, 0);
INSERT INTO "Productos" (tipo_producto_id, nombre, requiere_fabricacion, costos_operativos_fijos, precio_venta_sugerido) VALUES ((SELECT id FROM "Tipos_Producto" WHERE nombre = 'Accesorio' LIMIT 1), 'TOTEBAG', true, 0, 0);
INSERT INTO "Productos" (tipo_producto_id, nombre, requiere_fabricacion, costos_operativos_fijos, precio_venta_sugerido) VALUES ((SELECT id FROM "Tipos_Producto" WHERE nombre = 'Lencería' LIMIT 1), 'Vela', true, 0, 0);
```

## 8. TABLA Compras_Insumos (144) — SQL

```sql
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Cinta Térmica X 5' LIMIT 1), (SELECT id FROM "Proveedores" WHERE nombre = 'MercadoLibre' LIMIT 1), '2023-07-31 00:00:00+00', 1, 43830.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Folder sesgo para plana' LIMIT 1), (SELECT id FROM "Proveedores" WHERE nombre = 'brother' LIMIT 1), '2024-02-08 00:00:00+00', 1, 45000.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'forro varilla negro' LIMIT 1), (SELECT id FROM "Proveedores" WHERE nombre = 'Dora Estela' LIMIT 1), '2024-02-08 00:00:00+00', 4, 1000.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'forro varilla piel' LIMIT 1), (SELECT id FROM "Proveedores" WHERE nombre = 'Dora Estela' LIMIT 1), '2024-02-08 00:00:00+00', 4, 1000.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Gafetes' LIMIT 1), (SELECT id FROM "Proveedores" WHERE nombre = 'Dora Estela' LIMIT 1), '2024-02-08 00:00:00+00', 6, 800.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'herrajes en forma 8 / G' LIMIT 1), (SELECT id FROM "Proveedores" WHERE nombre = 'Dora Estela' LIMIT 1), '2024-02-08 00:00:00+00', 24, 200.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'malla piel' LIMIT 1), (SELECT id FROM "Proveedores" WHERE nombre = 'Mil Telas' LIMIT 1), '2024-02-08 00:00:00+00', 50, 230.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'mallatex negro' LIMIT 1), (SELECT id FROM "Proveedores" WHERE nombre = 'Textiles F&M' LIMIT 1), '2024-02-08 00:00:00+00', 50, 80.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'mallatex rosa' LIMIT 1), (SELECT id FROM "Proveedores" WHERE nombre = 'Textiles F&M' LIMIT 1), '2024-02-08 00:00:00+00', 50, 80.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'sesgo 2 cm negro' LIMIT 1), (SELECT id FROM "Proveedores" WHERE nombre = 'Dora Estela' LIMIT 1), '2024-02-08 00:00:00+00', 4, 600.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'sesgo 2 cm piel' LIMIT 1), (SELECT id FROM "Proveedores" WHERE nombre = 'Dora Estela' LIMIT 1), '2024-02-08 00:00:00+00', 4, 600.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'tira brasier negro' LIMIT 1), (SELECT id FROM "Proveedores" WHERE nombre = 'Dora Estela' LIMIT 1), '2024-02-08 00:00:00+00', 4, 800.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'tira brasier piel' LIMIT 1), (SELECT id FROM "Proveedores" WHERE nombre = 'Dora Estela' LIMIT 1), '2024-02-08 00:00:00+00', 4, 800.0000);
-- [cantidad no numérica: None] cantidad=1, precio=costo_total — revisar
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Agujas punta de bola Colla' LIMIT 1), (SELECT id FROM "Proveedores" WHERE nombre = 'Mil Adornos' LIMIT 1), '2024-02-17 00:00:00+00', 1, 12700.0000);
-- [cantidad no numérica: None] cantidad=1, precio=costo_total — revisar
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Agujas punta de bola Fill' LIMIT 1), (SELECT id FROM "Proveedores" WHERE nombre = 'Mil Adornos' LIMIT 1), '2024-02-17 00:00:00+00', 1, 12700.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Agujas punta de bola Plana' LIMIT 1), (SELECT id FROM "Proveedores" WHERE nombre = 'Mil Adornos' LIMIT 1), '2024-02-17 00:00:00+00', 2, 1100.0000);
-- [cantidad no numérica: None] cantidad=1, precio=costo_total — revisar
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Alfileres' LIMIT 1), NULL, '2024-02-17 00:00:00+00', 1, 2000.0000);
-- [cantidad no numérica: None] cantidad=1, precio=costo_total — revisar
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Alfileres' LIMIT 1), NULL, '2024-02-17 00:00:00+00', 1, 3500.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Argolla numero 10 mm' LIMIT 1), (SELECT id FROM "Proveedores" WHERE nombre = 'Gerrajes' LIMIT 1), '2024-02-17 00:00:00+00', 12, 166.6667);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Elastico de Contorno' LIMIT 1), (SELECT id FROM "Proveedores" WHERE nombre = 'Kilotelas' LIMIT 1), '2024-02-17 00:00:00+00', 4, 2000.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Elastico eljowoo15' LIMIT 1), (SELECT id FROM "Proveedores" WHERE nombre = 'Las 3BBB premium' LIMIT 1), '2024-02-17 00:00:00+00', 4, 1950.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Elastico pitillo rosa' LIMIT 1), NULL, '2024-02-17 00:00:00+00', 1, 600.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Elastico Trenzado (7 mm)' LIMIT 1), (SELECT id FROM "Proveedores" WHERE nombre = 'Las 3BBB premium' LIMIT 1), '2024-02-17 00:00:00+00', 4, 850.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Encaje elastico negro' LIMIT 1), (SELECT id FROM "Proveedores" WHERE nombre = 'Las 3BBB premium' LIMIT 1), '2024-02-17 00:00:00+00', 1, 7600.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Encaje negro' LIMIT 1), NULL, '2024-02-17 00:00:00+00', 1, 4000.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Encaje vino' LIMIT 1), NULL, '2024-02-17 00:00:00+00', 1, 4000.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Franela color negro' LIMIT 1), (SELECT id FROM "Proveedores" WHERE nombre = 'Kilotelas' LIMIT 1), '2024-02-17 00:00:00+00', 50, 125.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Franela color piel' LIMIT 1), (SELECT id FROM "Proveedores" WHERE nombre = 'Kilotelas' LIMIT 1), '2024-02-17 00:00:00+00', 50, 125.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Hilaza venus negro' LIMIT 1), (SELECT id FROM "Proveedores" WHERE nombre = 'Hilos y suministros Ltda' LIMIT 1), '2024-02-17 00:00:00+00', 100, 30.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Hilaza venus piel' LIMIT 1), (SELECT id FROM "Proveedores" WHERE nombre = 'Hilos y suministros Ltda' LIMIT 1), '2024-02-17 00:00:00+00', 100, 30.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Hilo poliester venus negro' LIMIT 1), (SELECT id FROM "Proveedores" WHERE nombre = 'Hilos y suministros Ltda' LIMIT 1), '2024-02-17 00:00:00+00', 120, 18.3333);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Hilo poliester venus negro' LIMIT 1), (SELECT id FROM "Proveedores" WHERE nombre = 'Hilos y suministros Ltda' LIMIT 1), '2024-02-17 00:00:00+00', 120, 18.3333);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Hilo poliester venus piel' LIMIT 1), (SELECT id FROM "Proveedores" WHERE nombre = 'Hilos y suministros Ltda' LIMIT 1), '2024-02-17 00:00:00+00', 120, 18.3333);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Hilo poliester venus piel' LIMIT 1), (SELECT id FROM "Proveedores" WHERE nombre = 'Hilos y suministros Ltda' LIMIT 1), '2024-02-17 00:00:00+00', 120, 18.3333);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Tensor 8 numero 10' LIMIT 1), (SELECT id FROM "Proveedores" WHERE nombre = 'Gerrajes' LIMIT 1), '2024-02-17 00:00:00+00', 12, 150.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Tull bordado blanco' LIMIT 1), NULL, '2024-02-17 00:00:00+00', 1, 4500.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Tull bordado cafe' LIMIT 1), NULL, '2024-02-17 00:00:00+00', 1, 4500.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Tull bordado piel' LIMIT 1), NULL, '2024-02-17 00:00:00+00', 1, 4500.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Varillas media copa' LIMIT 1), NULL, '2024-02-17 00:00:00+00', 5, 1000.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Velo surcido negro' LIMIT 1), (SELECT id FROM "Proveedores" WHERE nombre = 'Las 3BBB premium' LIMIT 1), '2024-02-17 00:00:00+00', 4, 1500.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Zeta numero 10' LIMIT 1), (SELECT id FROM "Proveedores" WHERE nombre = 'Gerrajes' LIMIT 1), '2024-02-17 00:00:00+00', 12, 166.6667);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Zeta numero 2 CM' LIMIT 1), (SELECT id FROM "Proveedores" WHERE nombre = 'Gerrajes' LIMIT 1), '2024-02-17 00:00:00+00', 4, 600.0000);
-- [cantidad no numérica: None] cantidad=1, precio=costo_total — revisar
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'licras lencería' LIMIT 1), (SELECT id FROM "Proveedores" WHERE nombre = 'telas Medellín' LIMIT 1), '2024-06-04 00:00:00+00', 1, 30100.0000);
-- [cantidad no numérica: None] cantidad=1, precio=costo_total — revisar
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'mallatex vino' LIMIT 1), NULL, '2024-06-04 00:00:00+00', 1, 12000.0000);
-- [cantidad no numérica: None] cantidad=1, precio=costo_total — revisar
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'planchuela fileteadora' LIMIT 1), NULL, '2024-06-04 00:00:00+00', 1, 25000.0000);
-- [cantidad no numérica: None] cantidad=1, precio=costo_total — revisar
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Elasticos cosrseteria etc' LIMIT 1), (SELECT id FROM "Proveedores" WHERE nombre = 'Kilotelas' LIMIT 1), '2024-06-29 00:00:00+00', 1, 76000.0000);
-- [cantidad no numérica: None] cantidad=1, precio=costo_total — revisar
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Encajes' LIMIT 1), (SELECT id FROM "Proveedores" WHERE nombre = 'Kilotelas' LIMIT 1), '2024-06-29 00:00:00+00', 1, 41000.0000);
-- [cantidad no numérica: None] cantidad=1, precio=costo_total — revisar
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'varios retazos' LIMIT 1), NULL, '2024-06-29 00:00:00+00', 1, 52000.0000);
-- [cantidad no numérica: None] cantidad=1, precio=costo_total — revisar
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Encaje y elasticos' LIMIT 1), NULL, '2024-07-16 00:00:00+00', 1, 18900.0000);
-- [cantidad no numérica: None] cantidad=1, precio=costo_total — revisar
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Piel de durazno + tejido de punto' LIMIT 1), (SELECT id FROM "Proveedores" WHERE nombre = 'grupo textil moda' LIMIT 1), '2024-07-16 00:00:00+00', 1, 22400.0000);
-- [cantidad no numérica: None] cantidad=1, precio=costo_total — revisar
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'telas + sesgos + tira +gafetes' LIMIT 1), NULL, '2024-07-23 00:00:00+00', 1, 39000.0000);
-- [cantidad no numérica: None] cantidad=1, precio=costo_total — revisar
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'encaje bicolor' LIMIT 1), NULL, '2024-08-28 00:00:00+00', 1, 27000.0000);
-- [cantidad no numérica: None] cantidad=1, precio=costo_total — revisar
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Herrajes / gafetes / copas prehormadas' LIMIT 1), NULL, '2024-09-06 00:00:00+00', 1, 83000.0000);
-- [cantidad no numérica: None] cantidad=1, precio=costo_total — revisar
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Elastico contorno negro 2cm 10 mts' LIMIT 1), NULL, '2024-09-07 00:00:00+00', 1, 18000.0000);
-- [cantidad no numérica: None] cantidad=1, precio=costo_total — revisar
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Encaje Elastico 19 cm blanco 10 mts' LIMIT 1), NULL, '2024-09-07 00:00:00+00', 1, 27000.0000);
-- [cantidad no numérica: None] cantidad=1, precio=costo_total — revisar
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Encaje Elastico 19 cm negro 10 mts' LIMIT 1), NULL, '2024-09-07 00:00:00+00', 1, 27000.0000);
-- [cantidad no numérica: None] cantidad=1, precio=costo_total — revisar
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Encaje elastico 6 cm blanco' LIMIT 1), NULL, '2024-09-07 00:00:00+00', 1, 12200.0000);
-- [cantidad no numérica: None] cantidad=1, precio=costo_total — revisar
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Encaje elastico 6 cm negro' LIMIT 1), NULL, '2024-09-07 00:00:00+00', 1, 12200.0000);
-- [cantidad no numérica: None] cantidad=1, precio=costo_total — revisar
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Encaje elastico negro 23 cm 10 mts' LIMIT 1), NULL, '2024-09-07 00:00:00+00', 1, 36000.0000);
-- [cantidad no numérica: None] cantidad=1, precio=costo_total — revisar
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Franela lycra 1 mt (blanco y negro)' LIMIT 1), NULL, '2024-09-07 00:00:00+00', 1, 30000.0000);
-- [cantidad no numérica: None] cantidad=1, precio=costo_total — revisar
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Hilaza negra' LIMIT 1), NULL, '2024-09-07 00:00:00+00', 1, 9300.0000);
-- [cantidad no numérica: None] cantidad=1, precio=costo_total — revisar
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Sesgo Elastico 2 10 mts' LIMIT 1), NULL, '2024-09-07 00:00:00+00', 1, 6300.0000);
-- [cantidad no numérica: None] cantidad=1, precio=costo_total — revisar
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Tapavarilla negro 10 mts' LIMIT 1), NULL, '2024-09-07 00:00:00+00', 1, 9000.0000);
-- [cantidad no numérica: None] cantidad=1, precio=costo_total — revisar
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Elastico Panty blanco 10 mts' LIMIT 1), NULL, '2024-09-13 00:00:00+00', 1, 5400.0000);
-- [cantidad no numérica: None] cantidad=1, precio=costo_total — revisar
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Framilon elastico plano 20 mts' LIMIT 1), NULL, '2024-09-13 00:00:00+00', 1, 9000.0000);
-- [cantidad no numérica: None] cantidad=1, precio=costo_total — revisar
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Hilaza venus 150 gms blanco' LIMIT 1), NULL, '2024-09-13 00:00:00+00', 1, 3500.0000);
-- [cantidad no numérica: None] cantidad=1, precio=costo_total — revisar
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Hilaza venus 150 gms negro' LIMIT 1), NULL, '2024-09-13 00:00:00+00', 1, 4000.0000);
-- [cantidad no numérica: None] cantidad=1, precio=costo_total — revisar
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Hilaza venus 150 gms negro' LIMIT 1), NULL, '2024-09-13 00:00:00+00', 1, 4000.0000);
-- [cantidad no numérica: None] cantidad=1, precio=costo_total — revisar
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Sesgo Elastico blanco 1,5 10 mts' LIMIT 1), NULL, '2024-09-13 00:00:00+00', 1, 5000.0000);
-- [cantidad no numérica: None] cantidad=1, precio=costo_total — revisar
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Telas algodon jersey retazos blanco' LIMIT 1), NULL, '2024-09-13 00:00:00+00', 1, 6500.0000);
-- [cantidad no numérica: None] cantidad=1, precio=costo_total — revisar
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Telas algodon jersey retazos negro' LIMIT 1), NULL, '2024-09-13 00:00:00+00', 1, 4500.0000);
-- [cantidad no numérica: None] cantidad=1, precio=costo_total — revisar
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Tira de Brasier blanco 10 mts' LIMIT 1), NULL, '2024-09-13 00:00:00+00', 1, 6000.0000);
-- [cantidad no numérica: None] cantidad=1, precio=costo_total — revisar
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Tira de Brasier negro 10 mts' LIMIT 1), NULL, '2024-09-13 00:00:00+00', 1, 6000.0000);
-- [cantidad no numérica: None] cantidad=1, precio=costo_total — revisar
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Encaje 6 cm calidad blanco 8 mts' LIMIT 1), NULL, '2024-09-16 00:00:00+00', 1, 22400.0000);
-- [cantidad no numérica: None] cantidad=1, precio=costo_total — revisar
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Encaje 6 cm calidad negro 8 mts' LIMIT 1), NULL, '2024-09-16 00:00:00+00', 1, 22400.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'marquillas en satin' LIMIT 1), NULL, '2024-10-03 00:00:00+00', 100, 660.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'encaje blanco' LIMIT 1), NULL, '2024-10-08 00:00:00+00', 10, 2700.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Encaje negro' LIMIT 1), NULL, '2024-10-08 00:00:00+00', 10, 2700.0000);
-- [cantidad no numérica: None] cantidad=1, precio=costo_total — revisar
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Hilos + Hilazas' LIMIT 1), NULL, '2024-10-08 00:00:00+00', 1, 62500.0000);
-- [cantidad no numérica: None] cantidad=1, precio=costo_total — revisar
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Sellos Arpia' LIMIT 1), NULL, '2024-10-08 00:00:00+00', 1, 154000.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Tira brasier blanco' LIMIT 1), NULL, '2024-10-08 00:00:00+00', 10, 600.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'tira brasier negro' LIMIT 1), NULL, '2024-10-08 00:00:00+00', 10, 600.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'gafete 3x2 blanco' LIMIT 1), (SELECT id FROM "Proveedores" WHERE nombre = 'sesgocolor' LIMIT 1), '2024-10-17 00:00:00+00', 127, 358.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'gafete 3x2 negro' LIMIT 1), (SELECT id FROM "Proveedores" WHERE nombre = 'sesgocolor' LIMIT 1), '2024-10-17 00:00:00+00', 100, 358.0000);
-- [cantidad no numérica: None] cantidad=1, precio=costo_total — revisar
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Alfileres' LIMIT 1), NULL, '2024-10-23 00:00:00+00', 1, 6000.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'ARCO METALICO 2001 30' LIMIT 1), (SELECT id FROM "Proveedores" WHERE nombre = 'auratex' LIMIT 1), '2024-10-23 00:00:00+00', 50, 247.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'ARCO METALICO 2001 32' LIMIT 1), (SELECT id FROM "Proveedores" WHERE nombre = 'auratex' LIMIT 1), '2024-10-23 00:00:00+00', 50, 247.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'ARCO METALICO 2001 34' LIMIT 1), (SELECT id FROM "Proveedores" WHERE nombre = 'auratex' LIMIT 1), '2024-10-23 00:00:00+00', 50, 247.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'ARCO METALICO 2001 36' LIMIT 1), (SELECT id FROM "Proveedores" WHERE nombre = 'auratex' LIMIT 1), '2024-10-23 00:00:00+00', 50, 247.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'bolsas tul 12 x 17' LIMIT 1), (SELECT id FROM "Proveedores" WHERE nombre = 'las 3 b' LIMIT 1), '2024-10-23 00:00:00+00', 12, 850.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Encaje Blanco y negro para bicolor' LIMIT 1), NULL, '2024-10-23 00:00:00+00', 20, 4000.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Encaje bordado blanco y negro' LIMIT 1), NULL, '2024-10-23 00:00:00+00', 2, 15000.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'FRAMILON' LIMIT 1), NULL, '2024-10-23 00:00:00+00', 1, 5500.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Framilon blanco y negro' LIMIT 1), NULL, '2024-10-23 00:00:00+00', 10, 7500.0000);
-- [cantidad no numérica: None] cantidad=1, precio=costo_total — revisar
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'gafetes +arandelas' LIMIT 1), (SELECT id FROM "Proveedores" WHERE nombre = 'Gerrajes' LIMIT 1), '2024-10-23 00:00:00+00', 1, 21350.0000);
-- [cantidad no numérica: None] cantidad=1, precio=costo_total — revisar
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'HILAZAS cono amarillo' LIMIT 1), NULL, '2024-10-23 00:00:00+00', 1, 15000.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'malla piel negro' LIMIT 1), NULL, '2024-10-23 00:00:00+00', 3, 12500.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Mallatex blnaco y negro' LIMIT 1), NULL, '2024-10-23 00:00:00+00', 6, 12500.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'SESGO ELASTICO' LIMIT 1), NULL, '2024-10-23 00:00:00+00', 10, 450.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'sesgo lorex blanco' LIMIT 1), NULL, '2024-10-23 00:00:00+00', 10, 950.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'sesgo lorex negro' LIMIT 1), NULL, '2024-10-23 00:00:00+00', 10, 950.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Tela control blanca' LIMIT 1), (SELECT id FROM "Proveedores" WHERE nombre = 'Teks' LIMIT 1), '2024-10-23 00:00:00+00', 5, 51160.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Tira de brasier negro' LIMIT 1), NULL, '2024-10-23 00:00:00+00', 10, 320.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'varilla plastica cortada 18 cm' LIMIT 1), (SELECT id FROM "Proveedores" WHERE nombre = 'auratex' LIMIT 1), '2024-10-23 00:00:00+00', 200, 144.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Cajas negras de 30 x 20 x7' LIMIT 1), NULL, '2025-10-25 00:00:00+00', 20, 9135.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Cajas negras de 30 x 20 x7' LIMIT 1), NULL, '2025-10-25 00:00:00+00', 20, 9135.0000);
-- [cantidad no numérica: None] cantidad=1, precio=costo_total — revisar
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'envio telas atenea' LIMIT 1), (SELECT id FROM "Proveedores" WHERE nombre = 'Atenea bordados y encajes' LIMIT 1), '2025-10-25 00:00:00+00', 1, 18000.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Ref 100 24 cm tul bordado negro' LIMIT 1), (SELECT id FROM "Proveedores" WHERE nombre = 'Atenea bordados y encajes' LIMIT 1), '2025-10-25 00:00:00+00', 39, 10512.8205);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Ref 159 24 cm tul bordado rojo pastel' LIMIT 1), (SELECT id FROM "Proveedores" WHERE nombre = 'Atenea bordados y encajes' LIMIT 1), '2025-10-25 00:00:00+00', 21, 9761.9048);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Sublimacion de la tela maya' LIMIT 1), NULL, '2025-10-25 00:00:00+00', 15, 21600.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Aguja fileteadora # 12' LIMIT 1), (SELECT id FROM "Proveedores" WHERE nombre = 'brother' LIMIT 1), '2025-10-27 00:00:00+00', 10, 1090.0000);
-- [cantidad no numérica: None] cantidad=1, precio=costo_total — revisar
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Alfileres' LIMIT 1), (SELECT id FROM "Proveedores" WHERE nombre = 'brother' LIMIT 1), '2025-10-27 00:00:00+00', 1, 5000.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Argolla numero 8 mm' LIMIT 1), NULL, '2025-10-27 00:00:00+00', 100, 87.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Bolsa de seguridad negra 25 x 35' LIMIT 1), (SELECT id FROM "Proveedores" WHERE nombre = 'Boutique de los empaques' LIMIT 1), '2025-10-27 00:00:00+00', 50, 450.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Bolsa de seguridad rosa 25 x 35' LIMIT 1), (SELECT id FROM "Proveedores" WHERE nombre = 'Boutique de los empaques' LIMIT 1), '2025-10-27 00:00:00+00', 50, 500.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Satin elastico negro' LIMIT 1), NULL, '2025-10-27 00:00:00+00', 1, 7900.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Satin elastico rosa' LIMIT 1), (SELECT id FROM "Proveedores" WHERE nombre = 'Textiles F&M' LIMIT 1), '2025-10-27 00:00:00+00', 1, 8000.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Sesgo elastico negro 2cm brillante' LIMIT 1), (SELECT id FROM "Proveedores" WHERE nombre = 'Kilotelas' LIMIT 1), '2025-10-27 00:00:00+00', 10, 990.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Sesgo rigido para ojales corset' LIMIT 1), (SELECT id FROM "Proveedores" WHERE nombre = 'Kilotelas' LIMIT 1), '2025-10-27 00:00:00+00', 10, 900.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'velo estrella (papel empaque)' LIMIT 1), (SELECT id FROM "Proveedores" WHERE nombre = 'Boutique de los empaques' LIMIT 1), '2025-10-27 00:00:00+00', 6, 3166.6667);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Cremallera num 3' LIMIT 1), (SELECT id FROM "Proveedores" WHERE nombre = 'MercadoLibre' LIMIT 1), '2026-03-03 00:00:00+00', 10, 1100.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Gabardina Ultra Poliester' LIMIT 1), (SELECT id FROM "Proveedores" WHERE nombre = 'CasaTextil' LIMIT 1), '2026-03-03 00:00:00+00', 8, 18653.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Barilla poliester corset negro 8mm' LIMIT 1), NULL, '2026-03-27 00:00:00+00', 45, 743.9111);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Cadena gris delgada totebag' LIMIT 1), NULL, '2026-03-27 00:00:00+00', 1, 2000.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Cadena plateada gruesa totebag' LIMIT 1), NULL, '2026-03-27 00:00:00+00', 1, 4000.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Cinta Satin negra 1 1/2' LIMIT 1), NULL, '2026-03-27 00:00:00+00', 50, 210.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'deslizadores cremallera num 3' LIMIT 1), NULL, '2026-03-27 00:00:00+00', 12, 208.3333);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Entretela elastica negra' LIMIT 1), (SELECT id FROM "Proveedores" WHERE nombre = 'almacen de la 6ta' LIMIT 1), '2026-03-27 00:00:00+00', 3, 5500.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Lino vertigo' LIMIT 1), NULL, '2026-03-27 00:00:00+00', 90, 170.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Rosas tejidas para totebag' LIMIT 1), NULL, '2026-03-27 00:00:00+00', 6, 3500.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Sublimacion para las totebag' LIMIT 1), NULL, '2026-03-27 00:00:00+00', 2, 20000.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Super Brioni' LIMIT 1), (SELECT id FROM "Proveedores" WHERE nombre = 'ICOLTEX' LIMIT 1), '2026-03-27 00:00:00+00', 2.9, 4934.4828);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Terminales de cordon' LIMIT 1), NULL, '2026-03-27 00:00:00+00', 12, 208.3333);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Tira de poliester para las totebag' LIMIT 1), NULL, '2026-03-27 00:00:00+00', 10, 2300.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Boton Aro para las faldas' LIMIT 1), (SELECT id FROM "Proveedores" WHERE nombre = 'Las 3BBB premium' LIMIT 1), '2026-07-18 00:00:00+00', 144, 221.9861);
-- [cantidad no numérica: None] cantidad=1, precio=costo_total — revisar
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Cremalleras falda invisibles 20 cms' LIMIT 1), NULL, '2026-07-18 00:00:00+00', 1, 0);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Encaje de ramitas' LIMIT 1), NULL, '2026-07-18 00:00:00+00', 10, 3500.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Entretela rigida blanca' LIMIT 1), NULL, '2026-07-18 00:00:00+00', 1, 19000.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'ojales metalicos 3/8 (grandes)' LIMIT 1), (SELECT id FROM "Proveedores" WHERE nombre = 'Gerrajes' LIMIT 1), '2026-07-18 00:00:00+00', 200, 200.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Powernet negro delgado' LIMIT 1), NULL, '2026-07-18 00:00:00+00', 4, 18000.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Sesgo satin brillante' LIMIT 1), (SELECT id FROM "Proveedores" WHERE nombre = 'temu' LIMIT 1), '2026-07-18 00:00:00+00', 12, 1635.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Tejido plano sim popelina (a cuadros bn)' LIMIT 1), (SELECT id FROM "Proveedores" WHERE nombre = 'facol' LIMIT 1), '2026-07-18 00:00:00+00', 1, 11900.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'Tela noche de viena negra' LIMIT 1), NULL, '2026-07-18 00:00:00+00', 1, 16000.0000);
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra) VALUES ((SELECT id FROM "Insumos" WHERE nombre = 'terminal metalico para cintas' LIMIT 1), (SELECT id FROM "Proveedores" WHERE nombre = 'Gerrajes' LIMIT 1), '2026-07-18 00:00:00+00', 12, 200.0000);
```

## 9. TABLA Movimientos_Financieros (59) — SQL

```sql
INSERT INTO "Movimientos_Financieros" (fecha, tipo, descripcion, monto, socio_id) VALUES ('2023-03-17 00:00:00+00', 'Inversion', 'Termofijadora', 960000.00, (SELECT id FROM "Socios_Configuracion" WHERE nombre = 'Valqui' LIMIT 1));
INSERT INTO "Movimientos_Financieros" (fecha, tipo, descripcion, monto, socio_id) VALUES ('2023-04-14 00:00:00+00', 'Inversion', 'camisetas:2 croptop 2 camiseta hombre (algodon peinado 155 gr/ tela fria 165 gr 40-1)', 61000.00, (SELECT id FROM "Socios_Configuracion" WHERE nombre = 'Valqui' LIMIT 1));
INSERT INTO "Movimientos_Financieros" (fecha, tipo, descripcion, monto, socio_id) VALUES ('2023-04-17 00:00:00+00', 'Inversion', 'camisetas: 2 croptop 2 camisetas hombre (algodon pima peruano 190 gr)', 194000.00, (SELECT id FROM "Socios_Configuracion" WHERE nombre = 'Valqui' LIMIT 1));
INSERT INTO "Movimientos_Financieros" (fecha, tipo, descripcion, monto, socio_id) VALUES ('2023-07-22 00:00:00+00', 'Inversion', 'Madera + tornillos', 354500.00, (SELECT id FROM "Socios_Configuracion" WHERE nombre = 'Valqui' LIMIT 1));
INSERT INTO "Movimientos_Financieros" (fecha, tipo, descripcion, monto, socio_id) VALUES ('2023-07-23 00:00:00+00', 'Inversion', 'Reglas Modisteria', 37600.00, (SELECT id FROM "Socios_Configuracion" WHERE nombre = 'Valqui' LIMIT 1));
INSERT INTO "Movimientos_Financieros" (fecha, tipo, descripcion, monto, socio_id) VALUES ('2023-07-31 00:00:00+00', 'Inversion', 'Teflon 40 X 60', 72000.00, (SELECT id FROM "Socios_Configuracion" WHERE nombre = 'Valqui' LIMIT 1));
INSERT INTO "Movimientos_Financieros" (fecha, tipo, descripcion, monto, socio_id) VALUES ('2024-02-05 00:00:00+00', 'Inversion', 'Hosting y dominio', 283360.00, (SELECT id FROM "Socios_Configuracion" WHERE nombre = 'Valqui' LIMIT 1));
INSERT INTO "Movimientos_Financieros" (fecha, tipo, descripcion, monto, socio_id) VALUES ('2023-03-17 00:00:00+00', 'Inversion', 'Maquina plana Industrial', 2367000.00, (SELECT id FROM "Socios_Configuracion" WHERE nombre = 'Valqui' LIMIT 1));
INSERT INTO "Movimientos_Financieros" (fecha, tipo, descripcion, monto, socio_id) VALUES ('2023-03-17 00:00:00+00', 'Inversion', 'Maquina Collarin industrial', 2367000.00, (SELECT id FROM "Socios_Configuracion" WHERE nombre = 'Valqui' LIMIT 1));
INSERT INTO "Movimientos_Financieros" (fecha, tipo, descripcion, monto, socio_id) VALUES ('2023-03-17 00:00:00+00', 'Inversion', 'Maquina Filetiadora Industrial', 2367000.00, (SELECT id FROM "Socios_Configuracion" WHERE nombre = 'Valqui' LIMIT 1));
INSERT INTO "Movimientos_Financieros" (fecha, tipo, descripcion, monto, socio_id) VALUES ('2024-02-18 00:00:00+00', 'Inversion', 'Patron brasier media copa', 52706.00, (SELECT id FROM "Socios_Configuracion" WHERE nombre = 'Valqui' LIMIT 1));
INSERT INTO "Movimientos_Financieros" (fecha, tipo, descripcion, monto, socio_id) VALUES ('2024-02-18 00:00:00+00', 'Inversion', 'Patron Bralets Quili', 15900.00, (SELECT id FROM "Socios_Configuracion" WHERE nombre = 'Valqui' LIMIT 1));
INSERT INTO "Movimientos_Financieros" (fecha, tipo, descripcion, monto, socio_id) VALUES ('2024-02-19 00:00:00+00', 'Inversion', 'Curso confeccion domestica', 16000.00, (SELECT id FROM "Socios_Configuracion" WHERE nombre = 'Valqui' LIMIT 1));
INSERT INTO "Movimientos_Financieros" (fecha, tipo, descripcion, monto, socio_id) VALUES ('2024-02-19 00:00:00+00', 'Inversion', 'Patron pantys', 69831.00, (SELECT id FROM "Socios_Configuracion" WHERE nombre = 'Valqui' LIMIT 1));
INSERT INTO "Movimientos_Financieros" (fecha, tipo, descripcion, monto, socio_id) VALUES ('2024-05-20 00:00:00+00', 'Inversion', 'Brazo estampar', 341100.00, (SELECT id FROM "Socios_Configuracion" WHERE nombre = 'Valqui' LIMIT 1));
INSERT INTO "Movimientos_Financieros" (fecha, tipo, descripcion, monto, socio_id) VALUES ('2024-06-25 00:00:00+00', 'Inversion', 'Lamparas', 91418.00, (SELECT id FROM "Socios_Configuracion" WHERE nombre = 'Valqui' LIMIT 1));
INSERT INTO "Movimientos_Financieros" (fecha, tipo, descripcion, monto, socio_id) VALUES ('2024-06-25 00:00:00+00', 'Inversion', 'tijeras + corta hilo + deshenebradores', 41000.00, (SELECT id FROM "Socios_Configuracion" WHERE nombre = 'Valqui' LIMIT 1));
INSERT INTO "Movimientos_Financieros" (fecha, tipo, descripcion, monto, socio_id) VALUES ('2024-06-30 00:00:00+00', 'Inversion', 'extensiones + papelera + regleta', 123000.00, (SELECT id FROM "Socios_Configuracion" WHERE nombre = 'Valqui' LIMIT 1));
INSERT INTO "Movimientos_Financieros" (fecha, tipo, descripcion, monto, socio_id) VALUES ('2024-07-23 00:00:00+00', 'Inversion', 'accesorio collarin 2 cm', 90000.00, (SELECT id FROM "Socios_Configuracion" WHERE nombre = 'Valqui' LIMIT 1));
INSERT INTO "Movimientos_Financieros" (fecha, tipo, descripcion, monto, socio_id) VALUES ('2024-07-23 00:00:00+00', 'Inversion', 'maniqui', 40000.00, (SELECT id FROM "Socios_Configuracion" WHERE nombre = 'Valqui' LIMIT 1));
INSERT INTO "Movimientos_Financieros" (fecha, tipo, descripcion, monto, socio_id) VALUES ('2025-10-27 00:00:00+00', 'Inversion', 'Sprey pegante tela', 21000.00, (SELECT id FROM "Socios_Configuracion" WHERE nombre = 'Valqui' LIMIT 1));
INSERT INTO "Movimientos_Financieros" (fecha, tipo, descripcion, monto, socio_id) VALUES ('2026-03-27 00:00:00+00', 'Inversion', 'Stand en feria gotica 2 dias', 60000.00, (SELECT id FROM "Socios_Configuracion" WHERE nombre = 'Valqui' LIMIT 1));
INSERT INTO "Movimientos_Financieros" (fecha, tipo, descripcion, monto, socio_id) VALUES ('2026-07-25 00:00:00+00', 'Inversion', 'Stand en feria NANA 1 dia', 60000.00, (SELECT id FROM "Socios_Configuracion" WHERE nombre = 'Valqui' LIMIT 1));
INSERT INTO "Movimientos_Financieros" (fecha, tipo, descripcion, monto, socio_id) VALUES ('2026-07-18 00:00:00+00', 'Inversion', 'Fotografia y Video para redes sociales', 700000.00, (SELECT id FROM "Socios_Configuracion" WHERE nombre = 'Valqui' LIMIT 1));
INSERT INTO "Movimientos_Financieros" (fecha, tipo, descripcion, monto, socio_id) VALUES ('2024-02-08 00:00:00+00', 'Inversion', 'restante maquinas industriales', 1099000.00, (SELECT id FROM "Socios_Configuracion" WHERE nombre = 'Valqui' LIMIT 1));
INSERT INTO "Movimientos_Financieros" (fecha, tipo, descripcion, monto, socio_id) VALUES ('2024-07-03 00:00:00+00', 'Inversion', 'configuracion tecnico maquinas', 200000.00, (SELECT id FROM "Socios_Configuracion" WHERE nombre = 'Valqui' LIMIT 1));
INSERT INTO "Movimientos_Financieros" (fecha, tipo, descripcion, monto, socio_id) VALUES ('2024-07-13 00:00:00+00', 'Inversion', 'papeleria + oraganizacion', 100000.00, (SELECT id FROM "Socios_Configuracion" WHERE nombre = 'Valqui' LIMIT 1));
INSERT INTO "Movimientos_Financieros" (fecha, tipo, descripcion, monto, socio_id) VALUES ('2024-07-22 00:00:00+00', 'Inversion', 'maniqui', 150000.00, (SELECT id FROM "Socios_Configuracion" WHERE nombre = 'Valqui' LIMIT 1));
INSERT INTO "Movimientos_Financieros" (fecha, tipo, descripcion, monto, socio_id) VALUES ('2025-01-16 00:00:00+00', 'Inversion', 'Maquina Zigsiadora Industrial', 2200000.00, (SELECT id FROM "Socios_Configuracion" WHERE nombre = 'Valqui' LIMIT 1));
INSERT INTO "Movimientos_Financieros" (fecha, tipo, descripcion, monto, socio_id) VALUES ('2024-06-04 00:00:00+00', 'Inversion', 'kit cortadores rotativos', 131150.00, (SELECT id FROM "Socios_Configuracion" WHERE nombre = 'Valqui' LIMIT 1));
INSERT INTO "Movimientos_Financieros" (fecha, tipo, descripcion, monto, socio_id) VALUES ('2024-06-04 00:00:00+00', 'Inversion', 'silla cajero', 300000.00, (SELECT id FROM "Socios_Configuracion" WHERE nombre = 'Valqui' LIMIT 1));
INSERT INTO "Movimientos_Financieros" (fecha, tipo, descripcion, monto, socio_id) VALUES ('2024-06-04 00:00:00+00', 'Inversion', 'patron brasier', 36000.00, (SELECT id FROM "Socios_Configuracion" WHERE nombre = 'Valqui' LIMIT 1));
INSERT INTO "Movimientos_Financieros" (fecha, tipo, descripcion, monto, socio_id) VALUES ('2024-06-04 00:00:00+00', 'Inversion', 'curso lenceria', 326730.00, (SELECT id FROM "Socios_Configuracion" WHERE nombre = 'Valqui' LIMIT 1));
INSERT INTO "Movimientos_Financieros" (fecha, tipo, descripcion, monto, socio_id) VALUES ('2024-06-04 00:00:00+00', 'Inversion', 'impresion patrones', 150000.00, (SELECT id FROM "Socios_Configuracion" WHERE nombre = 'Valqui' LIMIT 1));
INSERT INTO "Movimientos_Financieros" (fecha, tipo, descripcion, monto, socio_id) VALUES ('2024-06-04 00:00:00+00', 'Inversion', 'insumos curso lencería', 170000.00, (SELECT id FROM "Socios_Configuracion" WHERE nombre = 'Valqui' LIMIT 1));
INSERT INTO "Movimientos_Financieros" (fecha, tipo, descripcion, monto, socio_id) VALUES ('2024-06-04 00:00:00+00', 'Inversion', 'insumos curso lencería', 63300.00, (SELECT id FROM "Socios_Configuracion" WHERE nombre = 'Valqui' LIMIT 1));
INSERT INTO "Movimientos_Financieros" (fecha, tipo, descripcion, monto, socio_id) VALUES ('2024-06-04 00:00:00+00', 'Inversion', 'accesorios maquinas', 153000.00, (SELECT id FROM "Socios_Configuracion" WHERE nombre = 'Valqui' LIMIT 1));
INSERT INTO "Movimientos_Financieros" (fecha, tipo, descripcion, monto, socio_id) VALUES ('2024-10-23 00:00:00+00', 'Gasto', 'envio', 16500.00, (SELECT id FROM "Socios_Configuracion" WHERE nombre = 'ARPIA' LIMIT 1));
INSERT INTO "Movimientos_Financieros" (fecha, tipo, descripcion, monto, socio_id) VALUES ('2024-10-23 00:00:00+00', 'Gasto', 'envio', 16500.00, (SELECT id FROM "Socios_Configuracion" WHERE nombre = 'ARPIA' LIMIT 1));
INSERT INTO "Movimientos_Financieros" (fecha, tipo, descripcion, monto, socio_id) VALUES ('2024-10-23 00:00:00+00', 'Gasto', 'iva', 14858.00, (SELECT id FROM "Socios_Configuracion" WHERE nombre = 'ARPIA' LIMIT 1));
INSERT INTO "Movimientos_Financieros" (fecha, tipo, descripcion, monto, socio_id) VALUES ('2024-10-23 00:00:00+00', 'Gasto', 'fragancia', 12000.00, (SELECT id FROM "Socios_Configuracion" WHERE nombre = 'ARPIA' LIMIT 1));
INSERT INTO "Movimientos_Financieros" (fecha, tipo, descripcion, monto, socio_id) VALUES ('2025-02-02 00:00:00+00', 'Gasto', 'HOSTING ARPIA', 382360.00, (SELECT id FROM "Socios_Configuracion" WHERE nombre = 'ARPIA' LIMIT 1));
INSERT INTO "Movimientos_Financieros" (fecha, tipo, descripcion, monto, socio_id) VALUES ('2025-01-05 00:00:00+00', 'Gasto', 'Decoracion fotos Arpia', 108000.00, (SELECT id FROM "Socios_Configuracion" WHERE nombre = 'ARPIA' LIMIT 1));
INSERT INTO "Movimientos_Financieros" (fecha, tipo, descripcion, monto, socio_id) VALUES ('2024-10-23 00:00:00+00', 'Gasto', 'Bono celeste trabajo', 200000.00, (SELECT id FROM "Socios_Configuracion" WHERE nombre = 'ARPIA' LIMIT 1));
INSERT INTO "Movimientos_Financieros" (fecha, tipo, descripcion, monto, socio_id) VALUES ('2024-10-23 00:00:00+00', 'Gasto', 'Bono margara trabajo', 400000.00, (SELECT id FROM "Socios_Configuracion" WHERE nombre = 'ARPIA' LIMIT 1));
INSERT INTO "Movimientos_Financieros" (fecha, tipo, descripcion, monto, socio_id) VALUES ('2024-10-23 00:00:00+00', 'Gasto', 'herrajes', 20000.00, (SELECT id FROM "Socios_Configuracion" WHERE nombre = 'ARPIA' LIMIT 1));
INSERT INTO "Movimientos_Financieros" (fecha, tipo, descripcion, monto, socio_id) VALUES ('2024-10-23 00:00:00+00', 'Gasto', 'Refri', 15000.00, (SELECT id FROM "Socios_Configuracion" WHERE nombre = 'ARPIA' LIMIT 1));
INSERT INTO "Movimientos_Financieros" (fecha, tipo, descripcion, monto, socio_id) VALUES ('2024-10-23 00:00:00+00', 'Gasto', 'Revision maquina', 50000.00, (SELECT id FROM "Socios_Configuracion" WHERE nombre = 'ARPIA' LIMIT 1));
INSERT INTO "Movimientos_Financieros" (fecha, tipo, descripcion, monto, socio_id) VALUES ('2024-10-23 00:00:00+00', 'Gasto', 'prestamo margara', 150000.00, (SELECT id FROM "Socios_Configuracion" WHERE nombre = 'ARPIA' LIMIT 1));
INSERT INTO "Movimientos_Financieros" (fecha, tipo, descripcion, monto, socio_id) VALUES ('2025-12-31 00:00:00+00', 'Gasto', 'MATERIALES SURTIDOS', 21000.00, (SELECT id FROM "Socios_Configuracion" WHERE nombre = 'ARPIA' LIMIT 1));
INSERT INTO "Movimientos_Financieros" (fecha, tipo, descripcion, monto, socio_id) VALUES ('2025-12-31 00:00:00+00', 'Gasto', 'DOMICILIO CAJA SACA LAS GARRAS', 10000.00, (SELECT id FROM "Socios_Configuracion" WHERE nombre = 'ARPIA' LIMIT 1));
INSERT INTO "Movimientos_Financieros" (fecha, tipo, descripcion, monto, socio_id) VALUES ('2025-12-31 00:00:00+00', 'Gasto', 'ENVIO TELA ENCAJE ROJO', 20300.00, (SELECT id FROM "Socios_Configuracion" WHERE nombre = 'ARPIA' LIMIT 1));
INSERT INTO "Movimientos_Financieros" (fecha, tipo, descripcion, monto, socio_id) VALUES ('2025-12-31 00:00:00+00', 'Gasto', 'AYUDANTE CORTE PIEZAS', 10000.00, (SELECT id FROM "Socios_Configuracion" WHERE nombre = 'ARPIA' LIMIT 1));
INSERT INTO "Movimientos_Financieros" (fecha, tipo, descripcion, monto, socio_id) VALUES ('2025-12-31 00:00:00+00', 'Gasto', 'PUBLICIDAD EN META ADS', 13288.00, (SELECT id FROM "Socios_Configuracion" WHERE nombre = 'ARPIA' LIMIT 1));
INSERT INTO "Movimientos_Financieros" (fecha, tipo, descripcion, monto, socio_id) VALUES ('2026-01-31 00:00:00+00', 'Gasto', 'SESGO ELASTICO NEGRO BRILLANTE 30 MTS', 28500.00, (SELECT id FROM "Socios_Configuracion" WHERE nombre = 'ARPIA' LIMIT 1));
INSERT INTO "Movimientos_Financieros" (fecha, tipo, descripcion, monto, socio_id) VALUES ('2026-02-28 00:00:00+00', 'Gasto', 'Telas lona / cremallera', 70000.00, (SELECT id FROM "Socios_Configuracion" WHERE nombre = 'ARPIA' LIMIT 1));
INSERT INTO "Movimientos_Financieros" (fecha, tipo, descripcion, monto, socio_id) VALUES ('2026-02-28 00:00:00+00', 'Gasto', 'Temu ojaletes / troqueles / cintas', 62807.00, (SELECT id FROM "Socios_Configuracion" WHERE nombre = 'ARPIA' LIMIT 1));
INSERT INTO "Movimientos_Financieros" (fecha, tipo, descripcion, monto, socio_id) VALUES ('2026-02-28 00:00:00+00', 'Gasto', 'Varillas 22 cm Aretex 200 uni', 47200.00, (SELECT id FROM "Socios_Configuracion" WHERE nombre = 'ARPIA' LIMIT 1));
INSERT INTO "Movimientos_Financieros" (fecha, tipo, descripcion, monto, socio_id) VALUES ('2026-02-28 00:00:00+00', 'Gasto', 'varilla propileno 8 mm 50 yardas', 33475.00, (SELECT id FROM "Socios_Configuracion" WHERE nombre = 'ARPIA' LIMIT 1));
```

## 10. TABLA Ventas + Detalle_Ventas (21) — SQL

```sql
-- Venta 1: CAJA SACA LAS GARRAS S 2025-12-13 $295000.0 cliente gaby
INSERT INTO "Ventas" (fecha, cliente_id, descuento_porcentaje, estado, total_venta, canal_venta) VALUES ('2025-12-13 00:00:00+00', (SELECT id FROM "Clientes" WHERE nombre = 'gaby' LIMIT 1), 0, 'completada', 295000.00, 'feria');
INSERT INTO "Detalle_Ventas" (venta_id, producto_id, variante_id, cantidad, precio_unitario_aplicado, costo_unitario_aplicado) VALUES ((SELECT max(id) FROM "Ventas"), (SELECT id FROM "Productos" WHERE nombre = 'CAJA SACA LAS GARRAS' LIMIT 1), NULL, 1, 295000.00, 129388.00);
-- Venta 2: SET AELO S 2025-12-13 $80000.0 cliente celes
INSERT INTO "Ventas" (fecha, cliente_id, descuento_porcentaje, estado, total_venta, canal_venta) VALUES ('2025-12-13 00:00:00+00', (SELECT id FROM "Clientes" WHERE nombre = 'celes' LIMIT 1), 0, 'completada', 80000.00, 'feria');
INSERT INTO "Detalle_Ventas" (venta_id, producto_id, variante_id, cantidad, precio_unitario_aplicado, costo_unitario_aplicado) VALUES ((SELECT max(id) FROM "Ventas"), (SELECT id FROM "Productos" WHERE nombre = 'SET AELO' LIMIT 1), NULL, 1, 80000.00, 38805.00);
-- Venta 3: BLUSA ARPIA MANGA LARGA M 2026-01-05 $90000.0 cliente Maira *Comic
INSERT INTO "Ventas" (fecha, cliente_id, descuento_porcentaje, estado, total_venta, canal_venta) VALUES ('2026-01-05 00:00:00+00', (SELECT id FROM "Clientes" WHERE nombre = 'Maira *Comic' LIMIT 1), 0, 'completada', 90000.00, 'feria');
INSERT INTO "Detalle_Ventas" (venta_id, producto_id, variante_id, cantidad, precio_unitario_aplicado, costo_unitario_aplicado) VALUES ((SELECT max(id) FROM "Ventas"), (SELECT id FROM "Productos" WHERE nombre = 'BLUSA ARPIA MANGA LARGA' LIMIT 1), NULL, 1, 90000.00, 21561.00);
-- Venta 4: SET OCIPETE S 2026-03-20 $71250.0 DESC 25% cliente gaby
INSERT INTO "Ventas" (fecha, cliente_id, descuento_porcentaje, estado, total_venta, canal_venta) VALUES ('2026-03-20 00:00:00+00', (SELECT id FROM "Clientes" WHERE nombre = 'gaby' LIMIT 1), 25, 'completada', 71250.00, 'feria');
INSERT INTO "Detalle_Ventas" (venta_id, producto_id, variante_id, cantidad, precio_unitario_aplicado, costo_unitario_aplicado) VALUES ((SELECT max(id) FROM "Ventas"), (SELECT id FROM "Productos" WHERE nombre = 'SET OCIPETE' LIMIT 1), NULL, 1, 71250.00, 26109.00);
-- Venta 5: SET OCIPETE vino 2026-03-28 $71250.0 DESC 25% cliente Valeria Amiga gaby
INSERT INTO "Ventas" (fecha, cliente_id, descuento_porcentaje, estado, total_venta, canal_venta) VALUES ('2026-03-28 00:00:00+00', (SELECT id FROM "Clientes" WHERE nombre = 'Valeria Amiga gaby' LIMIT 1), 25, 'completada', 71250.00, 'feria');
INSERT INTO "Detalle_Ventas" (venta_id, producto_id, variante_id, cantidad, precio_unitario_aplicado, costo_unitario_aplicado) VALUES ((SELECT max(id) FROM "Ventas"), (SELECT id FROM "Productos" WHERE nombre = 'SET OCIPETE' LIMIT 1), NULL, 1, 71250.00, 26109.00);
-- Venta 6: SET AELO XS 2026-03-29 $82500.0 DESC 25% cliente Juan jose
INSERT INTO "Ventas" (fecha, cliente_id, descuento_porcentaje, estado, total_venta, canal_venta) VALUES ('2026-03-29 00:00:00+00', (SELECT id FROM "Clientes" WHERE nombre = 'Juan jose' LIMIT 1), 25, 'completada', 82500.00, 'feria');
INSERT INTO "Detalle_Ventas" (venta_id, producto_id, variante_id, cantidad, precio_unitario_aplicado, costo_unitario_aplicado) VALUES ((SELECT max(id) FROM "Ventas"), (SELECT id FROM "Productos" WHERE nombre = 'SET AELO' LIMIT 1), NULL, 1, 82500.00, 38805.00);
-- Venta 7: SET AELO S 2026-03-31 $82500.0 DESC 25% cliente Valentina hermana ale
INSERT INTO "Ventas" (fecha, cliente_id, descuento_porcentaje, estado, total_venta, canal_venta) VALUES ('2026-03-31 00:00:00+00', (SELECT id FROM "Clientes" WHERE nombre = 'Valentina hermana ale' LIMIT 1), 25, 'completada', 82500.00, 'feria');
INSERT INTO "Detalle_Ventas" (venta_id, producto_id, variante_id, cantidad, precio_unitario_aplicado, costo_unitario_aplicado) VALUES ((SELECT max(id) FROM "Ventas"), (SELECT id FROM "Productos" WHERE nombre = 'SET AELO' LIMIT 1), NULL, 1, 82500.00, 38805.00);
-- Venta 8: TOTEBAG  2026-03-31 $45000.0 cliente Valentina hermana ale
INSERT INTO "Ventas" (fecha, cliente_id, descuento_porcentaje, estado, total_venta, canal_venta) VALUES ('2026-03-31 00:00:00+00', (SELECT id FROM "Clientes" WHERE nombre = 'Valentina hermana ale' LIMIT 1), 0, 'completada', 45000.00, 'feria');
INSERT INTO "Detalle_Ventas" (venta_id, producto_id, variante_id, cantidad, precio_unitario_aplicado, costo_unitario_aplicado) VALUES ((SELECT max(id) FROM "Ventas"), (SELECT id FROM "Productos" WHERE nombre = 'TOTEBAG' LIMIT 1), NULL, 1, 45000.00, 25765.00);
-- Venta 9: TOTEBAG  2026-03-31 $45000.0 cliente Camila
INSERT INTO "Ventas" (fecha, cliente_id, descuento_porcentaje, estado, total_venta, canal_venta) VALUES ('2026-03-31 00:00:00+00', (SELECT id FROM "Clientes" WHERE nombre = 'Camila' LIMIT 1), 0, 'completada', 45000.00, 'feria');
INSERT INTO "Detalle_Ventas" (venta_id, producto_id, variante_id, cantidad, precio_unitario_aplicado, costo_unitario_aplicado) VALUES ((SELECT max(id) FROM "Ventas"), (SELECT id FROM "Productos" WHERE nombre = 'TOTEBAG' LIMIT 1), NULL, 1, 45000.00, 25765.00);
-- Venta 10: TOTEBAG  2026-04-24 $45000.0 cliente celeste
INSERT INTO "Ventas" (fecha, cliente_id, descuento_porcentaje, estado, total_venta, canal_venta) VALUES ('2026-04-24 00:00:00+00', (SELECT id FROM "Clientes" WHERE nombre = 'celeste' LIMIT 1), 0, 'completada', 45000.00, 'feria');
INSERT INTO "Detalle_Ventas" (venta_id, producto_id, variante_id, cantidad, precio_unitario_aplicado, costo_unitario_aplicado) VALUES ((SELECT max(id) FROM "Ventas"), (SELECT id FROM "Productos" WHERE nombre = 'TOTEBAG' LIMIT 1), NULL, 1, 45000.00, 25765.00);
-- Venta 11: CORSET GARRAS  2026-05-09 $95000.0 cliente Camila
INSERT INTO "Ventas" (fecha, cliente_id, descuento_porcentaje, estado, total_venta, canal_venta) VALUES ('2026-05-09 00:00:00+00', (SELECT id FROM "Clientes" WHERE nombre = 'Camila' LIMIT 1), 0, 'completada', 95000.00, 'feria');
INSERT INTO "Detalle_Ventas" (venta_id, producto_id, variante_id, cantidad, precio_unitario_aplicado, costo_unitario_aplicado) VALUES ((SELECT max(id) FROM "Ventas"), (SELECT id FROM "Productos" WHERE nombre = 'CORSET GARRAS' LIMIT 1), NULL, 1, 95000.00, 29826.00);
-- Venta 12: CORSET GARRAS  2026-05-09 $95000.0 cliente Olga
INSERT INTO "Ventas" (fecha, cliente_id, descuento_porcentaje, estado, total_venta, canal_venta) VALUES ('2026-05-09 00:00:00+00', (SELECT id FROM "Clientes" WHERE nombre = 'Olga' LIMIT 1), 0, 'completada', 95000.00, 'feria');
INSERT INTO "Detalle_Ventas" (venta_id, producto_id, variante_id, cantidad, precio_unitario_aplicado, costo_unitario_aplicado) VALUES ((SELECT max(id) FROM "Ventas"), (SELECT id FROM "Productos" WHERE nombre = 'CORSET GARRAS' LIMIT 1), NULL, 1, 95000.00, 29826.00);
-- Venta 13: CORSET GARRAS  2026-05-10 $60500.0 cliente Gaby
INSERT INTO "Ventas" (fecha, cliente_id, descuento_porcentaje, estado, total_venta, canal_venta) VALUES ('2026-05-10 00:00:00+00', (SELECT id FROM "Clientes" WHERE nombre = 'gaby' LIMIT 1), 0, 'completada', 60500.00, 'feria');
INSERT INTO "Detalle_Ventas" (venta_id, producto_id, variante_id, cantidad, precio_unitario_aplicado, costo_unitario_aplicado) VALUES ((SELECT max(id) FROM "Ventas"), (SELECT id FROM "Productos" WHERE nombre = 'CORSET GARRAS' LIMIT 1), NULL, 1, 60500.00, 29826.00);
-- Venta 14: TOTEBAG  2026-04-29 $45000.0 cliente Valqui
INSERT INTO "Ventas" (fecha, cliente_id, descuento_porcentaje, estado, total_venta, canal_venta) VALUES ('2026-04-29 00:00:00+00', (SELECT id FROM "Clientes" WHERE nombre = 'Valqui' LIMIT 1), 0, 'completada', 45000.00, 'feria');
INSERT INTO "Detalle_Ventas" (venta_id, producto_id, variante_id, cantidad, precio_unitario_aplicado, costo_unitario_aplicado) VALUES ((SELECT max(id) FROM "Ventas"), (SELECT id FROM "Productos" WHERE nombre = 'TOTEBAG' LIMIT 1), NULL, 1, 45000.00, 25765.00);
-- Venta 15: TOTEBAG  2026-05-19 $45000.0 cliente Maira *Comic
INSERT INTO "Ventas" (fecha, cliente_id, descuento_porcentaje, estado, total_venta, canal_venta) VALUES ('2026-05-19 00:00:00+00', (SELECT id FROM "Clientes" WHERE nombre = 'Maira *Comic' LIMIT 1), 0, 'completada', 45000.00, 'feria');
INSERT INTO "Detalle_Ventas" (venta_id, producto_id, variante_id, cantidad, precio_unitario_aplicado, costo_unitario_aplicado) VALUES ((SELECT max(id) FROM "Ventas"), (SELECT id FROM "Productos" WHERE nombre = 'TOTEBAG' LIMIT 1), NULL, 1, 45000.00, 25765.00);
-- Venta 16: TOTEBAG  2026-05-19 $45000.0 cliente Maira *Comic
INSERT INTO "Ventas" (fecha, cliente_id, descuento_porcentaje, estado, total_venta, canal_venta) VALUES ('2026-05-19 00:00:00+00', (SELECT id FROM "Clientes" WHERE nombre = 'Maira *Comic' LIMIT 1), 0, 'completada', 45000.00, 'feria');
INSERT INTO "Detalle_Ventas" (venta_id, producto_id, variante_id, cantidad, precio_unitario_aplicado, costo_unitario_aplicado) VALUES ((SELECT max(id) FROM "Ventas"), (SELECT id FROM "Productos" WHERE nombre = 'TOTEBAG' LIMIT 1), NULL, 1, 45000.00, 25765.00);
-- Venta 17: TOTEBAG  2026-07-25 $45000.0 cliente evento nana
INSERT INTO "Ventas" (fecha, cliente_id, descuento_porcentaje, estado, total_venta, canal_venta) VALUES ('2026-07-25 00:00:00+00', (SELECT id FROM "Clientes" WHERE nombre = 'evento nana' LIMIT 1), 0, 'completada', 45000.00, 'feria');
INSERT INTO "Detalle_Ventas" (venta_id, producto_id, variante_id, cantidad, precio_unitario_aplicado, costo_unitario_aplicado) VALUES ((SELECT max(id) FROM "Ventas"), (SELECT id FROM "Productos" WHERE nombre = 'TOTEBAG' LIMIT 1), NULL, 1, 45000.00, 25765.00);
-- Venta 18: CORSET GARRAS corset garras 2026-07-25 $80750.0 cliente evento nana
INSERT INTO "Ventas" (fecha, cliente_id, descuento_porcentaje, estado, total_venta, canal_venta) VALUES ('2026-07-25 00:00:00+00', (SELECT id FROM "Clientes" WHERE nombre = 'evento nana' LIMIT 1), 0, 'completada', 80750.00, 'feria');
INSERT INTO "Detalle_Ventas" (venta_id, producto_id, variante_id, cantidad, precio_unitario_aplicado, costo_unitario_aplicado) VALUES ((SELECT max(id) FROM "Ventas"), (SELECT id FROM "Productos" WHERE nombre = 'CORSET GARRAS' LIMIT 1), NULL, 1, 80750.00, 33581.00);
-- Venta 19: TOTEBAG sorteo 2026-07-25 $45000.0 cliente evento nana
INSERT INTO "Ventas" (fecha, cliente_id, descuento_porcentaje, estado, total_venta, canal_venta) VALUES ('2026-07-25 00:00:00+00', (SELECT id FROM "Clientes" WHERE nombre = 'evento nana' LIMIT 1), 0, 'completada', 45000.00, 'feria');
INSERT INTO "Detalle_Ventas" (venta_id, producto_id, variante_id, cantidad, precio_unitario_aplicado, costo_unitario_aplicado) VALUES ((SELECT max(id) FROM "Ventas"), (SELECT id FROM "Productos" WHERE nombre = 'TOTEBAG' LIMIT 1), NULL, 1, 45000.00, 25765.00);
-- Venta 20: BLUSA ARPIA MANGA LARGA  2026-08-05 $90000.0 cliente Maria caja cumple
INSERT INTO "Ventas" (fecha, cliente_id, descuento_porcentaje, estado, total_venta, canal_venta) VALUES ('2026-08-05 00:00:00+00', (SELECT id FROM "Clientes" WHERE nombre = 'Maria caja cumple' LIMIT 1), 0, 'completada', 90000.00, 'feria');
INSERT INTO "Detalle_Ventas" (venta_id, producto_id, variante_id, cantidad, precio_unitario_aplicado, costo_unitario_aplicado) VALUES ((SELECT max(id) FROM "Ventas"), (SELECT id FROM "Productos" WHERE nombre = 'BLUSA ARPIA MANGA LARGA' LIMIT 1), NULL, 1, 90000.00, 21561.00);
-- Venta 21: FALDA EMILY falda emily negra 2026-08-01 $80000.0 cliente gaby
INSERT INTO "Ventas" (fecha, cliente_id, descuento_porcentaje, estado, total_venta, canal_venta) VALUES ('2026-08-01 00:00:00+00', (SELECT id FROM "Clientes" WHERE nombre = 'gaby' LIMIT 1), 0, 'completada', 80000.00, 'feria');
INSERT INTO "Detalle_Ventas" (venta_id, producto_id, variante_id, cantidad, precio_unitario_aplicado, costo_unitario_aplicado) VALUES ((SELECT max(id) FROM "Ventas"), (SELECT id FROM "Productos" WHERE nombre = 'Falda Emily' LIMIT 1), NULL, 1, 80000.00, 23465.00);
```

## 11. Ajuste de stock tras ventas históricas

> Las ventas insertadas directo NO descuentan stock. Ajustar Insumos.stock_actual manualmente.

## ANEXO A — Referencia

### Proveedores (34)
- Atenea bordados y encajes
- Boutique de los empaques
- C+basics
- CasaTextil
- ColombiaHosting
- Dollarcity
- Dora Estela
- Etsy
- Gerrajes
- Hilos y suministros Ltda
- HomeCenter
- ICOLTEX
- Kilotelas
- La guillotina
- Las 3BBB premium
- MercadoLibre
- Mil Adornos
- Mil Telas
- SINGER
- Teks
- Textiles F&M
- The lingerie Formula
- almacen de la 6ta
- amazon
- auratex
- brother
- corsetería
- facol
- grupo textil moda
- las 3 b
- sesgocolor
- telas Medellín
- temu
- zuretex

### Insumos (135)

| nombre | categoria | unidad |
|---|---|---|
| Aguja fileteadora # 12 | Telas | m |
| Agujas punta de bola Colla | Telas | m |
| Agujas punta de bola Fill | Telas | m |
| Agujas punta de bola Plana | Telas | m |
| Alfileres | Telas | m |
| ARCO METALICO 2001 30 | Telas | m |
| ARCO METALICO 2001 32 | Telas | m |
| ARCO METALICO 2001 34 | Telas | m |
| ARCO METALICO 2001 36 | Telas | m |
| Argolla numero 10 mm | Herrajes | un |
| Argolla numero 8 mm | Herrajes | un |
| Barilla poliester corset negro 8mm | Herrajes | un |
| Bolsa de seguridad negra 25 x 35 | Empaques | un |
| Bolsa de seguridad rosa 25 x 35 | Empaques | un |
| bolsas tul 12 x 17 | Empaques | un |
| Boton Aro para las faldas | Herrajes | un |
| Cadena gris delgada totebag | Herrajes | un |
| Cadena plateada gruesa totebag | Herrajes | un |
| Cajas negras de 30 x 20 x7 | Empaques | un |
| Cinta Satin negra 1 1/2 | Telas | m |
| Cinta Térmica X 5 | Telas | m |
| Cremallera num 3 | Herrajes | un |
| Cremalleras falda invisibles 20 cms | Herrajes | un |
| deslizadores cremallera num 3 | Herrajes | un |
| Elastico contorno negro 2cm 10 mts | Telas | m |
| Elastico de Contorno | Telas | m |
| Elastico eljowoo15 | Telas | m |
| Elastico Panty blanco 10 mts | Telas | m |
| Elastico pitillo rosa | Telas | m |
| Elastico Trenzado (7 mm) | Telas | m |
| Elasticos cosrseteria etc | Telas | m |
| Encaje 6 cm calidad blanco 8 mts | Telas | m |
| Encaje 6 cm calidad negro 8 mts | Telas | m |
| encaje bicolor | Telas | m |
| encaje blanco | Telas | m |
| Encaje Blanco y negro para bicolor | Telas | m |
| Encaje bordado blanco y negro | Telas | m |
| Encaje de ramitas | Telas | m |
| Encaje Elastico 19 cm blanco 10 mts | Telas | m |
| Encaje Elastico 19 cm negro 10 mts | Telas | m |
| Encaje elastico 6 cm blanco | Telas | m |
| Encaje elastico 6 cm negro | Telas | m |
| Encaje elastico negro | Telas | m |
| Encaje elastico negro 23 cm 10 mts | Telas | m |
| Encaje negro | Telas | m |
| Encaje vino | Telas | m |
| Encaje y elasticos | Telas | m |
| Encajes | Telas | m |
| Entretela elastica negra | Telas | m |
| Entretela rigida blanca | Telas | m |
| envio telas atenea | Telas | m |
| Folder sesgo para plana | Telas | m |
| forro varilla negro | Herrajes | un |
| forro varilla piel | Herrajes | un |
| FRAMILON | Telas | m |
| Framilon blanco y negro | Telas | m |
| Framilon elastico plano 20 mts | Telas | m |
| Franela color negro | Telas | m |
| Franela color piel | Telas | m |
| Franela lycra 1 mt (blanco y negro) | Telas | m |
| Gabardina Ultra Poliester | Telas | m |
| gafete 3x2 blanco | Herrajes | un |
| gafete 3x2 negro | Herrajes | un |
| Gafetes | Herrajes | un |
| gafetes +arandelas | Herrajes | un |
| Herrajes / gafetes / copas prehormadas | Herrajes | un |
| herrajes en forma 8 / G | Telas | m |
| Hilaza negra | Telas | m |
| Hilaza venus 150 gms blanco | Telas | m |
| Hilaza venus 150 gms negro | Telas | m |
| Hilaza venus negro | Telas | m |
| Hilaza venus piel | Telas | m |
| HILAZAS cono amarillo | Telas | m |
| Hilo poliester venus negro | Telas | m |
| Hilo poliester venus piel | Telas | m |
| Hilos + Hilazas | Telas | m |
| licras lencería | Telas | m |
| Lino vertigo | Telas | m |
| malla piel | Telas | m |
| malla piel negro | Telas | m |
| Mallatex blnaco y negro | Telas | m |
| mallatex negro | Telas | m |
| mallatex rosa | Telas | m |
| mallatex vino | Telas | m |
| marquillas en satin | Telas | m |
| ojales metalicos 3/8 (grandes) | Herrajes | un |
| Piel de durazno + tejido de punto | Telas | m |
| planchuela fileteadora | Telas | m |
| Powernet negro delgado | Telas | m |
| Ref 100 24 cm tul bordado negro | Telas | m |
| Ref 159 24 cm tul bordado rojo pastel | Telas | m |
| Rosas tejidas para totebag | Telas | m |
| Satin elastico negro | Telas | m |
| Satin elastico rosa | Telas | m |
| Sellos Arpia | Telas | m |
| sesgo 2 cm negro | Telas | m |
| sesgo 2 cm piel | Telas | m |
| SESGO ELASTICO | Telas | m |
| Sesgo Elastico 2 10 mts | Telas | m |
| Sesgo Elastico blanco 1,5 10 mts | Telas | m |
| Sesgo elastico negro 2cm brillante | Telas | m |
| sesgo lorex blanco | Telas | m |
| sesgo lorex negro | Telas | m |
| Sesgo rigido para ojales corset | Herrajes | un |
| Sesgo satin brillante | Telas | m |
| Sublimacion de la tela maya | Telas | m |
| Sublimacion para las totebag | Telas | m |
| Super Brioni | Telas | m |
| Tapavarilla negro 10 mts | Herrajes | un |
| Tejido plano sim popelina (a cuadros bn) | Telas | m |
| Tela control blanca | Telas | m |
| Tela noche de viena negra | Telas | m |
| telas + sesgos + tira +gafetes | Herrajes | un |
| Telas algodon jersey retazos blanco | Telas | m |
| Telas algodon jersey retazos negro | Telas | m |
| Tensor 8 numero 10 | Herrajes | un |
| terminal metalico para cintas | Telas | m |
| Terminales de cordon | Herrajes | un |
| Tira brasier blanco | Telas | m |
| tira brasier negro | Telas | m |
| tira brasier piel | Telas | m |
| Tira de Brasier blanco 10 mts | Telas | m |
| Tira de brasier negro | Telas | m |
| Tira de Brasier negro 10 mts | Telas | m |
| Tira de poliester para las totebag | Telas | m |
| Tull bordado blanco | Telas | m |
| Tull bordado cafe | Telas | m |
| Tull bordado piel | Telas | m |
| varilla plastica cortada 18 cm | Herrajes | un |
| Varillas media copa | Herrajes | un |
| varios retazos | Telas | m |
| velo estrella (papel empaque) | Empaques | un |
| Velo surcido negro | Telas | m |
| Zeta numero 10 | Herrajes | un |
| Zeta numero 2 CM | Herrajes | un |
