# Deuda Técnica – Sistema CCC (Estado Actual)

---

## 1. Deuda estructural

### Duplicidad en cajas

RESUELTA

* creación centralizada en BoxService
* cierre centralizado en BoxService

---

### Duplicidad en productos

RESUELTA

* ProductService es única fuente de verdad

---

### SINIIGA distribuido

RESUELTO

* generación determinística
* búsqueda alineada a usuario

---

### Cierre de caja sin garantía de impresión

RESUELTO (42dd4d4 + siguiente commit)

* print_master() se ejecuta dentro de la transacción, antes del commit
* si la impresión falla → rollback → caja queda ABIERTA
* hardware.py normalizado para retornar (bool, str) en todos los caminos
* flag _committed elimina rollback doble silencioso

---

### UI llamando DB directo en borrado de pieza

RESUELTO

* delete_selected_piece() ahora usa piece_service.borrar_pieza()
* validación de caja ABIERTA aplicada en todos los caminos de borrado

---

### Código muerto en box_service.py

RESUELTO

* función huérfana reabrir_caja(db, caja) eliminada
* stub vacío _apply_weight_policy() eliminado de main_ui.py

---

## 2. Deuda actual (leve)

### UI con lógica de flujo

Impacto: bajo

* UI aún orquesta operaciones
* aceptado por diseño actual

---

### Hardware acoplado

Impacto: bajo

* dependencias directas en UI
* comportamiento controlado

---

### API legacy en ProductService

Impacto: mínimo

* métodos list_all / get / create / update / deactivate / reactivate
* wrappers sobre API nueva
* sin fecha de retiro definida

---

## 3. Deuda tolerada

* comportamiento histórico conservado
* flujo no refactorizado completamente

---

## Estado general

Sistema sin deuda crítica.

Deuda restante es:

* conocida
* controlada
* no bloqueante
