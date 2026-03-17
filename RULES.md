# Reglas de Trabajo – Sistema CCC

Estas reglas controlan cómo se modifica el sistema.

Aplican especialmente al uso de Codex.

---

## 1. Regla principal

El sistema está en producción.

Todo cambio debe:

- mantener comportamiento existente
- ser predecible
- ser verificable

---

## 2. Cambios

Cada cambio debe:

- tener un objetivo único
- ser entendible
- ser reversible

No permitido:

- cambios mezclados
- cambios implícitos
- cambios sin evidencia

---

## 3. Dominio

El sistema tiene reglas ya implementadas.

Se debe:

- respetar comportamiento actual
- no modificar reglas sin instrucción explícita

Importante:

- existen transformaciones de SINIIGA en el sistema
- estas no deben cambiarse sin definición previa

---

## 4. Transformaciones

Permitido:

- usar transformaciones existentes

No permitido:

- crear nuevas transformaciones sin validación
- modificar lógica de identidad

---

## 5. UI

La UI actualmente:

- contiene lógica de negocio
- accede a DB
- accede a hardware

Esto se acepta como estado actual.

No se debe:

- aumentar acoplamiento
- duplicar más lógica

---

## 6. Servicios

Los servicios:

- validan reglas
- no son única fuente de verdad

No se debe:

- asumir que toda lógica está ahí
- mover lógica sin validar impacto

---

## 7. DB

La base de datos:

- contiene validaciones reales
- protege integridad

No se debe:

- eliminar validaciones
- cambiar constraints sin análisis

---

## 8. Hardware

HardwareManager:

- es crítico para operación
- impacta directamente planta

No se modifica:

- formato de impresión
- lógica de etiquetas

sin instrucción explícita

---

## 9. Codex

Codex debe:

- seguir comportamiento actual
- no “mejorar” lógica por su cuenta
- no refactorizar sin instrucción

Siempre:

- mostrar diff
- no aplicar cambios automáticos

---

## 10. Seguridad

Si un cambio:

- no está claro
- toca múltiples capas
- cambia flujo operativo

→ detener

---

## 11. Regla final

El sistema debe ser:

- predecible
- explícito
- estable

No “inteligente”