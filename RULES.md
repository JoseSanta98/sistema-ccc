# Reglas de Trabajo – Sistema CCC (Estado Actual)

---

## 1. Regla principal

Sistema en producción.

Todo cambio debe:

* mantener comportamiento
* ser explícito
* ser verificable

---

## 2. Dominio

Cada dominio tiene UNA fuente de verdad:

* SINIIGA → UI controlada
* Caja → BoxService
* Producto → ProductService
* Peso → peso_policy.py

No permitido:

* duplicar lógica
* crear rutas paralelas
* llamar DB directo desde UI para operaciones de negocio

---

## 3. UI

La UI:

* refleja estado
* no define reglas

No debe:

* implementar lógica de negocio
* duplicar validaciones
* llamar db_manager directamente para escrituras

---

## 4. Servicios

Los servicios:

* contienen la lógica del sistema
* son punto único de operación

Regla de cierre de caja:

* si no imprime → no cierra
* la impresión ocurre dentro de la transacción, antes del commit

---

## 5. DB

La base de datos:

* solo persiste
* no define reglas de negocio

---

## 6. Cambios

Cada cambio:

* debe ser acotado
* debe tener objetivo único

---

## 7. Codex

Codex:

* NO refactoriza sin instrucción
* NO inventa lógica
* SOLO ejecuta cambios definidos

---

## 8. Regla final

El sistema debe ser:

* determinístico
* consistente
* predecible
