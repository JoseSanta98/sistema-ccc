# Arquitectura del Sistema CCC (Estado Actual)

## Estado del sistema

Sistema en producción estable.

Se encuentra en fase de:

* mantenimiento controlado
* evolución incremental

El sistema NO requiere reescritura.

---

## Estructura actual

### 1. UI

Archivos:

* main_ui.py
* dialogs.py
* admin_panel.py

Responsabilidad:

* interacción con usuario
* control de flujo
* representación del estado

Estado:

* no contiene lógica crítica de dominio
* delega todas las operaciones de escritura a servicios
* no llama DB directo para operaciones de negocio

---

### 2. Servicios

Archivos:

* box_service.py
* piece_service.py
* product_service.py

Responsabilidad:

* encapsular reglas de negocio
* ser única fuente de verdad del dominio

Estado:

* punto único de operación
* no existe duplicidad activa con DB o UI
* cierre de caja con atomicidad real: impresión dentro de transacción

---

### 3. Dominio

Estado:

* definido y consistente
* centralizado en servicios

Dominios:

#### SINIIGA

* identidad única
* generación determinística: 01 + YYDDD + XXXX
* búsqueda por últimos 4 dígitos

#### Caja

* creación y cierre solo vía BoxService
* transacciones BEGIN IMMEDIATE
* cierre garantiza impresión antes de commit
* si impresión falla → rollback → caja queda ABIERTA

#### Producto

* controlado por ProductService
* estado ACTIVO/INACTIVO consistente

#### Peso

* política centralizada en peso_policy.py
* PesoConfig contiene todos los parámetros configurables
* calcular_peso_pieza() y resolver_peso_cierre() usados en flujo principal

---

### 4. Infraestructura

Archivos:

* db_manager.py
* hardware.py

Responsabilidad:

* persistencia
* impresión y báscula

Estado:

* DB sin lógica de dominio
* hardware.py retorna (bool, str) consistentemente en todos los métodos de impresión

---

## Arquitectura final

UI → Services → DB

No existen rutas paralelas.

---

## Principios actuales

* una sola fuente de verdad por dominio
* lógica fuera de UI
* DB solo persistencia
* cambios incrementales y acotados

---

## Estado final

Sistema consistente, estable y alineado a dominio.
