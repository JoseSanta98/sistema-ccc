# Deuda Técnica – Sistema CCC

Basado en el estado real del código.

---

## 1. Deuda estructural

### Duplicidad en cajas
- crear_o_recuperar_caja en DB y Service

Impacto: alto

---

### Duplicidad en cierre de caja
- función libre y método en BoxService

Impacto: alto

---

### Inconsistencia de schema
- db_manager busca schema.sql en raíz
- archivo real en tools/

Impacto: alto

---

### Productos sin estado en schema
- código usa estado ACTIVO
- schema no lo define

Impacto: alto

---

## 2. Deuda de dominio

### SINIIGA distribuido
- UI genera
- DB normaliza
- hardware interpreta

Impacto: alto

---

### Validación duplicada de caja
- service + DB

Impacto: medio

---

### Producto depende de estado no garantizado
Impacto: alto

---

## 3. Deuda de acoplamiento

### UI → DB
Impacto: alto

### UI → hardware
Impacto: alto

### lógica en UI
Impacto: medio

---

## 4. Deuda tolerada

### Código legacy
Impacto: medio

### diferencias en impresión
Impacto: medio

### comportamiento congelado
Impacto: bajo

---

## Estado general

Sistema funcional con deuda localizada.

No requiere reescritura.