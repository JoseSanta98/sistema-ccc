# ARCHITECTURE.md — Sistema CCC

## Visión general

Sistema de captura de peso y etiquetado para rastro. Aplicación de escritorio PyQt5 con una sola base de datos SQLite local. Un único punto de producción, sin servidor, sin red.

## Capas del sistema

```
┌─────────────────────────────────────────────────────┐
│                   main_ui.py                        │
│         (UI PyQt5 — un solo hilo principal)         │
│         admin_panel.py (subventana QDialog)         │
└────────────┬────────────┬───────────────────────────┘
             │            │
    ┌────────▼──────┐  ┌──▼────────────┐
    │ PieceService  │  │  BoxService   │
    │piece_service  │  │ box_service   │
    └────────┬──────┘  └──┬────────────┘
             │             │
    ┌────────▼─────────────▼────────────┐
    │         ProductService            │
    │        product_service.py         │
    └────────────────┬──────────────────┘
                     │
    ┌────────────────▼──────────────────┐
    │          DatabaseManager          │
    │           db_manager.py           │
    │         (SQLite — WAL mode)       │
    └───────────────────────────────────┘
    
    ┌───────────────────────────────────┐
    │          box_domain.py            │
    │    (predicados de estado puro)    │
    └───────────────────────────────────┘
    
    ┌───────────────────────────────────┐
    │          peso_policy.py           │
    │   (política de peso centralizada) │
    └───────────────────────────────────┘
    
    ┌───────────────────────────────────┐
    │         hardware.py               │
    │   (HardwareManager — impresora)   │
    └───────────────────────────────────┘
```

## Responsabilidades por archivo

### `box_domain.py`
Predicados de estado puro. Sin dependencias externas. Sin efectos secundarios.

```python
puede_agregar_pieza(estado_caja)   # ABIERTA → True
puede_cerrar_caja(estado_caja)     # ABIERTA → True
puede_reabrir_caja(estado_caja)    # CERRADA → True
```

Única fuente de verdad sobre qué operaciones permite cada estado de caja. Todos los servicios importan desde aquí — nadie hardcodea strings de estado.

### `peso_policy.py`
Política de peso centralizada. Sin dependencias externas.

- `PesoConfig` — constantes: `MIN_PIEZA`, `TARA_DEFAULT`, `DECIMALES`
- `PesoInvalidoError` — excepción tipada para peso inválido
- `calcular_peso_pieza(raw, aplicar_correccion, tara)` — aplica tara dinámica configurable
- `calcular_peso_caja(piezas)` — suma pesos de lista de dicts
- `resolver_peso_cierre(peso_calculado, peso_override)` — lógica de override en cierre

### `db_manager.py`
Acceso a datos puro. Sin lógica de negocio, sin transacciones propias en operaciones de piezas y cajas.

**Patrón de métodos:** Para cada operación que modifica datos existe una variante `_conn(conn, ...)` que recibe una conexión activa y ejecuta solo el SQL. La transacción es responsabilidad del servicio llamador.

Métodos `_conn` existentes:
- `registrar_pieza_conn(conn, caja_id, codigo, nombre, peso)`
- `editar_pieza_conn(conn, pieza_id, nuevo_peso)` — actualiza peso y recalcula `peso_acumulado`/`num_piezas` en `cajas`
- `borrar_pieza_conn(conn, pieza_id)` — elimina pieza y recalcula totales en `cajas`
- `cerrar_caja_conn(conn, caja_id)` — solo UPDATE de estado y fecha_cierre

### `piece_service.py`
Dueño de todas las transacciones de piezas.

Patrón invariante para los tres métodos públicos:
1. `conn = self.db._get_conn()`
2. `conn.execute("BEGIN IMMEDIATE")`
3. Validaciones contra dominio (`box_domain`, `peso_policy`)
4. Delegación a método `_conn` de `db_manager`
5. `conn.commit()` / `except: conn.rollback()` / `finally: conn.close()`

**Métodos públicos:**
- `registrar_pieza(caja_id, codigo_producto, peso)`
- `editar_pieza(pieza_id, nuevo_peso)`
- `borrar_pieza(pieza_id)`

### `box_service.py`
Dueño de las transacciones de cajas. Mismo patrón transaccional que `PieceService`.

**Métodos públicos:**
- `cerrar_caja(caja_id, canal, contenido, peso_final)` — **blindado**: imprime etiqueta MASTER antes de hacer commit. Si `print_master` retorna `(False, msg)`, hace rollback y lanza `RuntimeError`. La caja nunca se cierra sin etiqueta.
- `crear_o_recuperar_caja(canal_id, numero_caja)`

### `product_service.py`
Gestión del catálogo de productos.

**API pública:**
- `get_producto(codigo)` — busca cualquier estado
- `get_producto_activo(codigo)` — solo productos ACTIVO
- `get_all_productos(incluir_inactivos=False)`
- `upsert_producto(codigo, nombre, especie)` — INSERT OR UPDATE
- `desactivar_producto(codigo)` / `activar_producto(codigo)`
- `change_codigo(codigo_original, nuevo_codigo)` — valida que no tenga piezas registradas
- `delete_if_unused(codigo)` — valida que no tenga piezas registradas

### `hardware.py`
Interfaz con impresora ZPL vía `win32print`.

**Contrato de retorno:** Todos los métodos públicos retornan `(bool, str)`.
- `send_raw_zpl(zpl_code)` → `(True, "OK")` o `(False, "Fallo al abrir impresora: ...")`
- `print_ticket(pieza_data, caja_data, canal_data, producto_data)` → delega a `send_raw_zpl`
- `print_master(caja_data, canal_data, contenido_piezas, peso_manual_override)` → `(True, "")` o `(False, msg)` en 4 paths explícitos

### `main_ui.py`
UI principal PyQt5. No contiene lógica de negocio.

**Puntos de contacto con hardware (3 — todos manejan el retorno):**
- `logic_close_box` → `box_service.cerrar_caja()` (blindaje delegado al servicio)
- `logic_save_print` línea 439 → captura `ok, msg` de `print_ticket`
- `reprint_selected_piece` → captura `ok, msg`, muestra `QMessageBox.warning` si falla

### `admin_panel.py`
Panel de administración (QDialog). Usa exclusivamente la API nueva de `ProductService` y `DatabaseManager`. Sin callers legacy.

## Esquema de base de datos

```
canales        id, siniiga, estado, fecha_creacion
cajas          id, canal_id, numero_caja, estado, fecha_apertura, fecha_cierre,
               peso_acumulado, num_piezas
piezas         id, caja_id, codigo_producto, nombre_producto, peso,
               consecutivo, fecha_registro
               UNIQUE(caja_id, consecutivo)
               INDEX(codigo_producto)
productos      codigo PK, nombre, especie, estado (ACTIVO|INACTIVO)
```

## Reglas de integridad

- `peso_acumulado` y `num_piezas` en `cajas` se recalculan en la misma transacción que modifica `piezas` — nunca quedan desincronizados.
- `consecutivo` es único por caja — conflicto de integridad se convierte en `ValueError` tipado.
- Una caja solo puede cerrarse si tiene contenido (`contenido` no vacío).
- Una caja solo se cierra en DB si la etiqueta MASTER se imprimió exitosamente.

## Flujo principal de operación

```
1. Operador selecciona canal (siniiga)
2. Sistema crea o recupera caja abierta para ese canal
3. Por cada pieza: escanea código → ingresa peso → PieceService.registrar_pieza()
4. Al completar caja: BoxService.cerrar_caja() → print_master → commit
5. Sistema queda listo para nueva caja
```
