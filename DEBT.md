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

### Redundancia menor en nombres

Impacto: mínimo

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
