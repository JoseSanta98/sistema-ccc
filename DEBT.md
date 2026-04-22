# DEBT.md — Sistema CCC

## Deuda activa

### `except:` desnudo en tooling

**Archivo:** `tools/check_env.py`, línea 71  
**Riesgo:** Bajo — fuera del path de producción  
**Acción:** Tipificar como `except Exception:` en cualquier momento sin urgencia

---

### `create` y `update` en `ProductService` — lógica duplicada con `upsert_producto`

**Archivo:** `product_service.py`  
**Descripción:** Los métodos `create` y `update` tienen lógica propia con validaciones y transacciones separadas. `upsert_producto` cubre el mismo caso de uso con un solo `INSERT OR UPDATE`. Los únicos callers eran `admin_panel.py` — ya migrados a `upsert_producto`. `create` y `update` fueron eliminados en PR #86.  
**Estado:** ✅ Resuelto

---

### Wrappers legacy en `ProductService`

**Archivo:** `product_service.py`  
**Descripción:** Existían `list_all`, `get`, `deactivate`, `reactivate` como aliases de los métodos reales.  
**Estado:** ✅ Resuelto en PR #84 y #86

---

### Transacciones en `db_manager.py`

**Descripción:** Los métodos `registrar_pieza`, `editar_pieza`, `borrar_pieza` gestionaban sus propias transacciones en `db_manager`, mezclando acceso a datos con lógica de negocio.  
**Estado:** ✅ Resuelto en PR #80, #83. Todos los métodos tienen ahora variante `_conn`.

---

### Nombre de producto hardcodeado al registrar pieza

**Descripción:** `registrar_pieza` en `db_manager` recibía el nombre como parámetro libre, sin derivarlo del catálogo. Era posible registrar piezas con nombres arbitrarios.  
**Estado:** ✅ Resuelto en PR #80 — nombre siempre derivado de `ProductService.get_producto_activo`.

---

### Cierre de caja sin verificación de impresión

**Descripción:** `cerrar_caja` en `BoxService` hacía commit antes de intentar imprimir. Si `print_master` fallaba, se intentaba `reabrir_caja` como compensación — patrón frágil que podía dejar la caja cerrada sin etiqueta.  
**Estado:** ✅ Resuelto — impresión ocurre antes del commit. Si falla → rollback automático.

---

### `ESTADO_ABIERTA` importado sin usar

**Archivo:** `piece_service.py`  
**Estado:** ✅ Resuelto en PR #85

---

### `reprint_selected_piece` sin manejo de error

**Archivo:** `main_ui.py`  
**Descripción:** La llamada a `hw_mgr.print_ticket` no capturaba el retorno `(bool, str)`. Fallo silencioso.  
**Estado:** ✅ Resuelto en PR #87

---

## Deuda conocida no bloqueante

### 80+ ramas remotas de Codex en `origin`

**Descripción:** Cada PR de Codex dejó su rama en `origin`. Son ramas mergeadas e inactivas, no afectan funcionamiento.  
**Acción:** `git remote prune origin` cuando sea conveniente.

---

### `num_piezas` vs `total_piezas` en `current_box`

**Archivo:** `main_ui.py`, líneas 782-783  
```python
self.state.current_box.get('num_piezas')
or self.state.current_box.get('total_piezas')
```
**Descripción:** Fallback defensivo que sugiere inconsistencia histórica en el nombre del campo. La columna real en DB es `num_piezas`.  
**Riesgo:** Bajo — el fallback funciona correctamente  
**Acción:** Verificar y eliminar `total_piezas` del fallback cuando se confirme que nunca aparece.

