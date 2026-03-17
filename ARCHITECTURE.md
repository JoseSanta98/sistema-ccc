# Arquitectura del Sistema CCC

## Estado del sistema

El sistema CCC se encuentra en operación estable en planta.

No está en fase de diseño ni de blindaje.
Está en una etapa de:

- mantenimiento controlado
- evolución incremental
- reducción de deuda técnica

El sistema funciona y no debe reescribirse.

---

## Estructura actual

### 1. UI (Interfaz)

Archivos:
- main_ui.py
- dialogs.py
- admin_panel.py
- styles.py

Responsabilidad:
- interacción con el usuario
- renderizado
- control de flujo inmediato

Estado real:
- contiene lógica de negocio parcial
- accede directamente a DB y hardware

---

### 2. Servicios

Archivos:
- box_service.py
- piece_service.py
- product_service.py

Responsabilidad:
- encapsular reglas de negocio
- validar operaciones

Estado real:
- conviven con lógica duplicada en UI y DB
- no son única fuente de verdad

---

### 3. Dominio (implícito)

Archivos:
- box_domain.py
- lógica distribuida en servicios y UI

Responsabilidad:
- definir reglas del sistema

Estado real:
- distribuido
- no centralizado
- parcialmente duplicado

---

### 4. Infraestructura

Archivos:
- db_manager.py
- hardware.py
- tools/schema.sql

Responsabilidad:
- persistencia
- impresión / hardware

Estado real:
- DB contiene validaciones de negocio
- hardware contiene lógica operativa

---

## Modelo de datos (resumen)

- Canal (SINIIGA)
- Caja (contenedor)
- Pieza (registro de peso)
- Producto (catálogo)

Relaciones:

- Canal → Cajas
- Caja → Piezas

---

## Dominio SINIIGA (estado real)

SINIIGA es la identidad principal del sistema.

Estado actual en código:

- Se almacena como `TEXT UNIQUE`
- Puede contener sufijo de lote (`-DDMMYY`)
- Se manipula en múltiples capas

Uso actual:

- UI:
  - generación parcial (4 dígitos → prefijo + lote)
  - display con split("-")

- DB:
  - normalización parcial (zfill, prefijo 08)

- Hardware:
  - uso de últimos 4 dígitos
  - impresión parcial

Conclusión:

SINIIGA:
- es clave única en DB
- su construcción no está centralizada
- su representación varía por capa

---

## Estados del sistema

### Canal
- ACTIVO
- CERRADO

### Caja
- ABIERTA
- CERRADA

Validación:

- definida en DB (CHECK parcial)
- replicada en servicios
- usada en UI

---

## Flujo operativo

1. Selección / creación de canal
2. Creación / selección de caja
3. Registro de piezas
4. Cierre de caja
5. Impresión

El flujo está distribuido entre:

- UI
- servicios
- DB
- hardware

---

## Realidad actual (importante)

El sistema presenta:

- lógica duplicada
- reglas distribuidas
- acoplamiento UI ↔ DB ↔ hardware

Esto es conocido y controlado.

No se corrige de forma masiva.

---

## Principios actuales

- No romper comportamiento existente
- Cambios incrementales
- Cambios con impacto controlado
- No introducir lógica implícita
- No cambiar dominio sin definirlo primero

---

## Evolución permitida

Se permite:

- refactor incremental
- eliminación de duplicidad
- centralización de reglas

No se permite:

- reescritura total
- cambios invisibles
- cambios sin validación funcional

---

## Regla clave

Si un cambio:

- modifica comportamiento sin evidencia
- altera identidad (SINIIGA)
- afecta flujo de planta

→ No se implementa