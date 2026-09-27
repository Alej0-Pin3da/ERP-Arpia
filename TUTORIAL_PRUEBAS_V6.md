# Tutorial de pruebas — V6 + BOM dinámico del Cotizador

Guía paso a paso para probar todo lo implementado: refactor del cotizador a BOM
dinámico, Fase 0 y Módulos 1–5 de la V6. Cada sección tiene el camino UI y el
camino API, con el resultado esperado.

---

## 0. Requisitos y arranque

1. **Docker levantado** (PostgreSQL + API):
   ```powershell
   docker compose up -d
   docker ps  # arpia-db (5433) y arpia-api (8080) en Up
   ```
2. **URLs:**
   - API → `http://localhost:8080` (prefijo `/api/v1`)
   - Frontend dev → `npm run dev` (`http://localhost:5173`)
   - DB directa → `localhost:5433` (usuario `arpia`, base `arpia`)
3. **Migraciones al día** (desde `backend/`):
   ```powershell
   alembic upgrade head
   alembic current  # debe mostrar la última revisión aplicada
   ```
4. **Login admin** para los llamados API (ajustá el puerto si tu API corre local en 8000):
   ```powershell
   $login = Invoke-RestMethod -Uri http://localhost:8080/api/v1/auth/login `
     -Method Post -ContentType "application/json" `
     -Body '{"email":"admin@arpia.com","password":"Admin123!"}'
   $token = $login.access_token
   $H = @{ Authorization = "Bearer $token" }
   ```

> Todo lo de abajo asume `$H` con un token válido y la API en el puerto 8080.

---

## 1. Suite automatizada (el camino rápido)

Corre primero los tests. Si esto está verde, el resto es verificación visual.

**Backend** (desde `backend/`, la DB de test `arpia_test` se recrea sola):

```powershell
# Por módulo V6 (rápido, ~5–20 s cada uno)
python -m pytest tests/test_cotizaciones_api.py -q   # BOM dinámico: 18
python -m pytest tests/test_kits_api.py -q           # M1: 8
python -m pytest tests/test_reparto_api.py -q        # M2: 5
python -m pytest tests/test_webhooks_woo.py -q       # M3: 5
python -m pytest tests/test_reservas_api.py -q       # M4: 5
python -m pytest tests/test_ai_copy.py -q            # M5: 5
```

```powershell
# Circuito tocado por M2/M4 (regresiones, ~7 min en total)
python -m pytest tests/test_ventas_api.py -q
python -m pytest tests/test_finanzas_api.py tests/test_finanzas_api_v4.py tests/test_finanzas_servicios.py tests/test_finanzas.py -q
python -m pytest tests/test_produccion_tiempos.py tests/test_produccion_lote.py tests/test_fase4_produccion.py tests/test_inventory.py -q
```

> La suite completa (~850 tests) tarda 20–30 min: correla por bloques como
> arriba, no de una (el buffering oculta el progreso).

**Frontend** (desde la raíz):

```powershell
npm run lint   # debe terminar sin errores ni warnings
npm test       # 52/52
npm run build  # build limpio
```

---

## 2. Cotizador con BOM dinámico

**Objetivo:** la Sección 1 acepta N líneas (nombre, cantidad, unidad, precio,
% desperdicio) y el servidor calcula igual.

**Por UI:**
1. Abrí el Cotizador sin receta → Sección 1 vacía con el hint.
2. `+ Añadir insumo` dos veces: `Tela principal, 2, m, 10000, 0%` y
   `Forro, 1, m, 5000, 0%`. Verificá subtotales por línea y total $25.000.
3. Cargá una receta con BOM → las líneas se vuelcan solas (toast
   "Base real cargada: N líneas") y la tabla Base BOM sigue visible.
4. Guardá → el historial muestra la cotización con su código `COT-XXXX`.

**Por API:**
```powershell
$body = @{
  nombre_prenda = "Prueba BOM"
  insumos = @(
    @{ nombre="Tela principal"; cantidad=2; precio_unitario=10000; unidad_medida="m"; desperdicio_pct=10 },
    @{ nombre="Forro"; cantidad=1; precio_unitario=5000; unidad_medida="m"; desperdicio_pct=0 }
  )
  costo_avios = 3000; costo_empaque = 2000
  tiempo_confeccion_min = 60; tarifa_hora = 12000; costo_cif = 1000; margen_pct = 60
} | ConvertTo-Json -Depth 5
$r = Invoke-RestMethod -Uri http://localhost:8080/api/v1/cotizaciones `
  -Method Post -ContentType "application/json" -Headers $H -Body $body
# Esperado: costo_total 45000 (2×1.1×10000 + 5000 + 5000 + 12000 + 1000),
# insumos_detalle con las 2 líneas intactas (snapshot inmutable).
$r.costo_total; $r.insumos_detalle.Count
```

**Casos borde:** línea con cantidad 0 o sin nombre → 422; se ignoran las
incompletas al guardar desde la UI con aviso.

---

## 3. Módulo 1 — Kits y Cajas

**Objetivo:** armar una caja con productos, ver costo en vivo y alerta si el
margen baja del 5%.

**Por UI (Maestros → tab 📦 Kits & Cajas):**
1. `Nueva caja`: nombre `Caja Promo Madre`, precio `100000`, sumá 2 productos
   con cantidades → crear.
2. La tarjeta muestra costo total, margen y badge verde. Bajá el precio hasta
   que el margen caiga bajo 5% → badge rojo `⚠ margen X%` (avisa, no bloquea).
3. Sumá/quita líneas desde la tarjeta: costo y margen se recalculan.
4. Eliminar pide confirmación (diálogo global).

**Por API:**
```powershell
# Crear (usá IDs reales de /api/v1/productos)
$kit = Invoke-RestMethod -Uri http://localhost:8080/api/v1/kits `
  -Method Post -ContentType "application/json" -Headers $H `
  -Body '{"nombre":"Caja Test","precio_promocional":"100000","lineas":[{"producto_id":1,"cantidad":"2"}]}'
$kit.costo_total; $kit.margen_pct; $kit.alerta_margen  # alerta $false si margen >= 5
# Duplicar producto en la caja → 409. Producto fantasma → 422.
```

---

## 4. Módulo 2 — Reparto automático

**Objetivo:** cada venta confirmada reparte su ganancia según las reglas, con
saldos en vivo y reversión exacta al anular.

**Por UI (Finanzas → tab Saldos en Vivo):**
1. Verificá las reglas seeded del estatuto (Fondo 40 / Margarita 30 / Valqui 30).
2. Registrá una venta con ganancia (ej. costo 10, precio 100) → los saldos
   suben al instante (45/45 en un 50/50).
3. Anulá la venta → los saldos vuelven a cero.
4. Pausá una regla (toggle) → las próximas ventas la saltean.

**Por API:**
```powershell
# Reglas y saldos
Invoke-RestMethod -Uri http://localhost:8080/api/v1/reparto/reglas -Headers $H
Invoke-RestMethod -Uri http://localhost:8080/api/v1/reparto/saldos -Headers $H
# Ledger de una venta
Invoke-RestMethod -Uri http://localhost:8080/api/v1/reparto/ventas/123 -Headers $H
```

**Reglas del negocio a verificar:** regalos y ventas sin ganancia no reparten;
sin reglas no hay reparto (la venta igual se registra); la suma por venta
siempre cuadra al centavo; el cierre mensual oficial no cambia (los saldos
son informativos, nada se paga doble).

---

## 5. Módulo 3 — Webhook WooCommerce

**Objetivo:** una orden de Woo se convierte en venta web real, sin duplicar.

**Previo (una vez):** configurar el secreto (si está vacío el endpoint
responde 503 a propósito):
```powershell
# en backend/.env (o variable de entorno)
WOO_WEBHOOK_SECRET=mi-secreto-woo
# reiniciar la API para que lo tome
```

**Probar el flujo completo (PowerShell):**
```powershell
$secret = "mi-secreto-woo"
$order = '{"id":9001,"line_items":[{"sku":"SKU-REAL-DE-TU-PRODUCTO","quantity":1,"price":"100"}]}'
$hmac = New-Object System.Security.Cryptography.HMACSHA256
$hmac.Key = [Text.Encoding]::UTF8.GetBytes($secret)
$sig = [Convert]::ToBase64String($hmac.ComputeHash([Text.Encoding]::UTF8.GetBytes($order)))
# 1) Primera entrega → 200 {venta_id, duplicado:false}; la venta es canal "web"
$r1 = Invoke-RestMethod -Uri http://localhost:8080/api/v1/webhooks/woo/order-created `
  -Method Post -Body $order -ContentType "application/json" `
  -Headers @{"X-WC-Webhook-Signature"=$sig}
# 2) Reenviar el MISMO body → 200 {mismo venta_id, duplicado:true}, UNA sola venta
$r2 = Invoke-RestMethod -Uri http://localhost:8080/api/v1/webhooks/woo/order-created `
  -Method Post -Body $order -ContentType "application/json" `
  -Headers @{"X-WC-Webhook-Signature"=$sig}
# 3) Firma mala → 401. SKU fantasma → 422 (Woo reintenta cuando repongas).
```

**Casos borde:** producto bajo pedido (sin prendas, con tela) consume insumos
por explosión estándar; sin stock en ningún lado → 409/422 y Woo reintenta.

---

## 6. Módulo 4 — Reservas predictivas

**Objetivo:** un pedido abierto aparta su tela; nadie más puede asumirla libre.

**Por UI (Inventario):**
1. Creá un pedido de producción por N unidades → la fila de la tela muestra
   `Disponible` menor y la pista `actual X · reservado Y` en ámbar.
2. Si `Disponible ≤ mínimo`: fila roja + `⚠️ REPONER` + contador de críticos.
3. Completá el lote → reservado vuelve a 0 y el actual baja lo consumido.
4. Borrá un pedido abierto → libera su reserva.

**Por API / casos a verificar:**
- Cerrar un lote juzga `actual − reservas ajenas`: con overbooking real (más
  reservado que stock) el cierre da **409 honesto** con detalle por insumo.
- Un 409 **no suelta** la reserva (el reintento sigue posible); el pedido
  bloqueado debe ceder (borrarse) para que el otro cierre.
- Doble cierre es no-op (no descuenta ni libera dos veces).
- `GET /api/v1/insumos` expone `stock_reservado` y `disponible` por fila.

---

## 7. Módulo 5 — Copy con IA local

**Objetivo:** descripción comercial generada desde el BOM real.

**Previo:** Ollama corriendo con el modelo configurado:
```powershell
ollama pull llama3.1
ollama serve  # http://localhost:11434
```

**Por UI:** abrí la Ficha Técnica de un producto en edición → botón
`✨ Generar Descripción con IA` junto a la descripción → rellena el textarea
(revisá y guardá por el flujo normal).

**Por API:**
```powershell
$r = Invoke-RestMethod -Uri http://localhost:8080/api/v1/ai/generar-copy `
  -Method Post -ContentType "application/json" -Headers $H `
  -Body '{"producto_id":1}'
$r.texto; $r.modelo
```

**Casos borde:** sin Ollama → 503 con mensaje claro (esperado, no es bug);
producto fantasma → 404; nada se persiste hasta que guardes la ficha.

---

## 8. Checklist final y troubleshooting

- [ ] `alembic current` = última revisión (`dcc928a70607` o superior)
- [ ] Backend 6 suites V6 en verde (sección 1)
- [ ] `npm run lint` (0), `npm test` (52/52), `npm run build` (limpio)
- [ ] Flujos UI 2–7 recorridos sin errores en consola del navegador
- [ ] `CambiosV3.md` al día con lo que hayas tocado (regla del proyecto)

**Problemas comunes:**
- *401 en todo*: token vencido (15 min) → logueate de nuevo (sección 0.4).
- *429 en tests/login masivo*: solo pasa con rate-limit activo fuera de `test`.
- *Puertos*: API docker 8080 vs local 8000; DB siempre 5433; frontend 5173.
- *Suite lenta*: es normal (~20–30 min completa); corre por bloques.
- *`insumos_detalle` null en cotizaciones viejas*: la migración lo deja en `[]`.
