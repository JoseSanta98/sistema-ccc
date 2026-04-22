# RULES.md — Sistema CCC

Reglas de desarrollo derivadas de decisiones de diseño tomadas en el proyecto. No son preferencias — son invariantes que protegen la integridad del sistema.

---

## Reglas de arquitectura

### R1 — La transacción vive en el servicio, no en `db_manager`

`db_manager` expone métodos `_conn(conn, ...)` que reciben una conexión activa y ejecutan solo el SQL. El `BEGIN IMMEDIATE`, `commit`, `rollback` y `close` son responsabilidad exclusiva del servicio que llama.

**Violación:** Agregar `conn.execute("BEGIN IMMEDIATE")` dentro de un método de `db_manager`.

---

### R2 — El estado de caja se consulta solo a través de `box_domain`

Ningún servicio ni UI hardcodea strings como `"ABIERTA"`, `"CERRADA"`. Toda lógica de estado pasa por los predicados de `box_domain.py`.

```python
# Correcto
if puede_agregar_pieza(caja["estado"]):

# Incorrecto
if caja["estado"] == "ABIERTA":
```

---

### R3 — La impresora se llama antes del commit, nunca después

En cualquier flujo que involucre impresión seguida de persistencia, la impresión ocurre dentro de la transacción abierta. Si la impresión falla → rollback → la operación no se registra en DB.

**Aplica a:** `BoxService.cerrar_caja` y cualquier operación futura que combine impresión con escritura.

---

### R4 — Todo método de hardware retorna `(bool, str)`

`send_raw_zpl`, `print_ticket`, `print_master` — todos los paths (éxito, error, excepción) retornan `(bool, str)`. El caller siempre desempaca `ok, msg = ...` y maneja `not ok`.

**Violación:** Llamar `hw_mgr.print_ticket(...)` sin capturar el retorno.

---

### R5 — El nombre del producto se deriva del catálogo, nunca se acepta como parámetro libre

Al registrar una pieza, `PieceService` consulta `get_producto_activo(codigo)` y toma el nombre de ahí. El nombre nunca viene de la UI directamente.

---

### R6 — `peso_acumulado` y `num_piezas` se recalculan en la misma transacción

Cualquier operación que modifique `piezas` (insert, update, delete) debe actualizar los totales de la caja padre en la misma transacción. Nunca quedan pendientes para recalcular después.

---

### R7 — `ProductService` es la única vía para modificar el catálogo

Ningún componente de UI ni otro servicio llama directamente a `db_manager.upsert_producto`, `db_manager.delete_producto` o similares. Todo pasa por `ProductService`.

---

## Reglas de validación

### R8 — El peso mínimo de pieza es `PesoConfig.MIN_PIEZA`

No existe otro lugar donde se defina o verifique el peso mínimo. Cualquier cambio al umbral se hace únicamente en `peso_policy.PesoConfig`.

---

### R9 — Un producto inexistente o INACTIVO no puede registrarse en una pieza

`PieceService.registrar_pieza` verifica `get_producto_activo(codigo)`. Si retorna `None` → `ValueError`. No existe forma de registrar una pieza con un código que no esté activo en el catálogo.

---

### R10 — Una caja sin contenido no puede cerrarse

`BoxService.cerrar_caja` verifica `if not contenido: raise ValueError(...)` antes de intentar imprimir. Una caja vacía nunca llega a `print_master`.

---

## Reglas de interfaz de usuario

### R11 — La UI no contiene lógica de negocio

`main_ui.py` y `admin_panel.py` no calculan pesos, no validan estados de caja, no toman decisiones de dominio. Toda decisión de negocio ocurre en los servicios.

---

### R12 — Errores de hardware se muestran al operador

Cualquier llamada a `hw_mgr` en la UI captura el retorno y muestra `QMessageBox.warning` si `ok` es `False`. El operador siempre sabe si la impresión falló.

---

## Reglas de base de datos

### R13 — `consecutivo` es único por caja

`UNIQUE(caja_id, consecutivo)` en la tabla `piezas`. Un conflicto de integridad se convierte en `ValueError("Conflicto de consecutivo en la caja")` — nunca se deja burbujear como `IntegrityError` crudo.

---

### R14 — Migraciones son incrementales y no destructivas

Las migraciones en `db_manager._run_pending_migrations()` verifican la existencia de columnas/índices antes de crearlos. Nunca eliminan datos existentes. Siempre son seguras de ejecutar sobre una DB con datos.

