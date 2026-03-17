# Arquitectura del Sistema CCC (Estado Actual)

## Estado del sistema

Sistema en producción estable.

Se encuentra en fase de:

* mantenimiento controlado
* evolución incremental
* reducción de deuda técnica

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

* ya no contiene lógica crítica de dominio duplicada
* delega operaciones a servicios

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

* ya son punto único de operación
* no existe duplicidad activa con DB o UI

---

### 3. Dominio

Estado:

* definido implícitamente pero consistente
* centralizado en servicios

Dominios:

#### SINIIGA

* identidad única
* generación determinística:
  01 + YYDDD + XXXX
* búsqueda por últimos 4 dígitos

#### Caja

* creación y cierre solo vía BoxService
* uso de transacciones (BEGIN IMMEDIATE)

#### Producto

* controlado por ProductService
* estado ACTIVO/INACTIVO consistente

---

### 4. Infraestructura

Archivos:

* db_manager.py
* hardware.py

Responsabilidad:

* persistencia
* impresión

Estado:

* DB sin lógica de dominio
* hardware aislado

---

## Arquitectura final

UI → Services → DB

No existen rutas paralelas.

---

## Principios actuales

* una sola fuente de verdad por dominio
* lógica fuera de UI
* DB solo persistencia
* cambios incrementales

---

## Estado final

Sistema consistente, estable y alineado a dominio.
