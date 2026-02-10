# Reglas de trabajo del Sistema CCC

Este archivo define las reglas operativas para modificar el sistema CCC.
Su objetivo es **reducir riesgo**, **evitar regresiones** y **mantener
consistencia**, no frenar el desarrollo.

Estas reglas derivan directamente de `ARCHITECTURE.md`.

---

## 1. Regla fundamental
El sistema CCC **funciona en producción**.

Por lo tanto:
- Ningún cambio debe alterar comportamiento sin validación explícita.
- La estabilidad tiene prioridad sobre la elegancia del código.

---

## 2. Regla de alcance de cambios
Un cambio debe cumplir **una sola intención clara**.

- ❌ No mezclar refactor con cambios funcionales
- ❌ No mezclar UI + DB + hardware en un mismo cambio
- ✅ Un objetivo = un commit

---

## 3. Zonas críticas (alto riesgo)
Estas zonas **no deben modificarse** sin confirmación explícita:

- `hardware.py` (ZPL, impresión, báscula)
- Esquema de base de datos (`schema.sql`)
- Estados y semántica de tablas (ABIERTA, CERRADA, ACTIVA, etc.)
- Flujo operativo visible en planta
- Semántica visual industrial (colores/estados)

---

## 4. Reglas de UI y estilos (SSOT)

### Fuente de verdad
`styles.py` es la **única fuente autorizada** de valores visuales.

Incluye:
- Colores
- Tipografías
- Tamaños
- QSS global
- Estados visuales

### Permitido
- Uso de `setStyleSheet()` local **solo** si consume estilos definidos en `styles.py`
- Cambios de estado visual (error, activo, selección) usando estilos existentes

### No permitido
- Hardcodear colores, fuentes o tamaños nuevos en UI
- Introducir valores visuales nuevos fuera de `styles.py`

### Nota importante
La deuda visual existente fuera de `styles.py` se acepta como **deuda conocida**
y no debe corregirse salvo refactor planificado.

---

## 5. Reglas de arquitectura
- La UI no contiene SQL, ZPL ni lógica de hardware
- La UI no decide reglas de negocio complejas
- La orquestación de flujos debe ser explícita y legible
- Las reglas de negocio deben tender a ser funciones puras

---

## 6. Reglas de refactor
- Refactors deben ser:
  - incrementales
  - reversibles
  - con comportamiento idéntico
- No refactorizar múltiples flujos en un solo cambio
- Cada refactor debe poder explicarse en una frase clara

---

## 7. Archivos legacy / históricos
Algunos archivos existen solo como referencia histórica.

Ejemplo:
- `numeros de productos en caja, hardware.py`

Reglas:
- No usar estos archivos como base para nuevos cambios
- No sincronizar comportamiento con ellos
- No refactorizarlos

---

## 8. Uso de Codex / herramientas automáticas
Al usar Codex u otras herramientas automáticas:

- Mostrar siempre el diff antes de aplicar cambios
- No aceptar cambios que violen estas reglas
- No permitir refactors agresivos o implícitos
- Priorizar cambios pequeños y controlados

---

## 9. Regla de salida segura
Si existe duda sobre el impacto de un cambio:

- Detener el cambio
- Documentar la duda
- Resolver antes de continuar

---

## 10. Regla final
Si un cambio genera miedo o no se entiende con claridad,
**todavía no es el momento de implementarlo**.
