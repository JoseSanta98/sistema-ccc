# Arquitectura del Sistema CCC

## Estado actual
El sistema CCC es funcional y estable en operación, pero ha evolucionado
mediante parches incrementales, lo que incrementó el acoplamiento interno
y el miedo a modificar partes que ya funcionan.

Este documento define la arquitectura conceptual del sistema y un plan
de evolución **sin cambiar comportamiento**.

---

## Objetivos
- Reducir el riesgo percibido al modificar el sistema
- Mejorar la comprensión estructural del código
- Permitir refactors incrementales y reversibles
- Mantener compatibilidad total con operación actual

---

## Principios no negociables
- No cambiar comportamiento visible al operario
- No modificar lógica de impresión (ZPL / hardware.py) sin validación explícita
- No modificar esquema de base de datos ni estados existentes
- No mezclar cambios estructurales con cambios funcionales
- Un cambio = un objetivo = un commit

---

## Semántica operativa del sistema (importante)
El sistema CCC se utiliza en entorno industrial.  
Por lo tanto, **los elementos visuales no son decoración**, sino
**señales operativas para el operario**.

Ejemplos de semántica visual:
- Verde: correcto / listo / continuar
- Rojo: peligro / stop / acción inválida
- Amarillo: advertencia / atención / revisión
- Azul: selección activa / contexto actual

Cualquier cambio visual debe respetar esta semántica para evitar errores
humanos en operación.

---

## Arquitectura conceptual por capas (futura)

### 1. Presentación (UI)
Responsabilidad:
- Renderizado de pantallas
- Captura de eventos
- Feedback visual al operario

Archivos actuales:
- main_ui.py
- dialogs.py
- admin_panel.py
- styles.py

Regla:
La UI no contiene SQL, ZPL ni lógica de hardware.

---

### 2. Aplicación / Casos de uso
Responsabilidad:
- Orquestar flujos de negocio
- Definir el orden de operaciones

Ejemplos de flujos:
- Abrir SINIIGA
- Seleccionar caja
- Registrar pieza
- Cerrar caja
- Reimpresión

Estado actual:
Esta lógica vive embebida dentro de archivos de UI.

---

### 3. Dominio (reglas de negocio)
Responsabilidad:
- Reglas puras del negocio
- Validaciones
- Políticas de cálculo

Ejemplos:
- Corrección de peso
- Validación de estados
- Normalización SINIIGA

Estado actual:
Disperso entre UI, dialogs y db_manager.

---

### 4. Infraestructura
Responsabilidad:
- Implementaciones concretas de tecnología

Componentes:
- db_manager.py (SQLite)
- hardware.py (báscula + impresora)
- config.ini
- schema.sql

---

### 5. Bootstrap
Responsabilidad:
- Arranque del sistema
- Wiring de dependencias
- Manejo de fallos fatales

Archivo actual:
- main.py

---

## Qué NO se toca (zona de riesgo alto)
- Lógica ZPL y envío a impresora
- Esquema y estados de base de datos
- Flujo operativo visible en planta
- Semántica visual industrial vigente
- Formato actual de configuración

---

## Single Source of Truth (SSOT)

### Estilos y apariencia visual
`styles.py` es la **única fuente autorizada** de definición visual del sistema.

Incluye:
- Colores
- Tipografías
- Tamaños visuales
- QSS global
- Estados visuales (activo, abierto, cerrado, error)

Reglas:
- No se deben introducir valores visuales nuevos fuera de `styles.py`.
- `setStyleSheet()` local está permitido **solo** si consume estilos definidos en `styles.py`.
- No se permite hardcodear colores, fuentes o tamaños nuevos en archivos de UI.
- Si un estilo no existe, se define primero en `styles.py`.

Objetivo:
- Evitar divergencia visual
- Permitir cambios de diseño sin miedo
- Mantener consistencia operativa

---

## Excepciones permitidas (importante)
- Se permite el uso de `setStyleSheet()` local para:
  - activar/desactivar estados
  - mostrar errores temporales
  - feedback inmediato de operación
- Siempre que:
  - no introduzca valores visuales nuevos
  - consuma constantes o estilos de `styles.py`

La deuda visual existente fuera de `styles.py` se considera **deuda conocida**
y no se tratará como violación hasta refactor planificado.

---

## Archivos históricos / legacy
Existen archivos que no forman parte del flujo activo del sistema, pero se
conservan como referencia histórica.

Ejemplo:
- `numeros de productos en caja, hardware.py`

Reglas:
- Estos archivos no deben ser usados como base para nuevos cambios.
- No representan el comportamiento actual del sistema.
- Su presencia es documental, no operativa.

---

## Plan de evolución (incremental y reversible)

### Fase 1 — Diagnóstico
✔ Completado  
Mapa de responsabilidades y acoplamientos.

### Fase 2 — Arquitectura conceptual
✔ Completado  
Este documento.

### Fase 3 — Refactor invisible (futuro)
- Extracción de funciones puras
- Separación de casos de uso
- Sin cambio de comportamiento

### Fase 4 — Mejora controlada (opcional)
- Simplificación
- Reducción de duplicidad
- Mejora de testabilidad

---

## Regla de oro
Si un cambio no puede explicarse en una frase clara,
entonces todavía no es seguro implementarlo.
