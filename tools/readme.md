CHECKPOINT DEL PROYECTO: SISTEMA DE ETIQUETADO CENTRAL DE CARNES (v3.3)


Fecha: 21/01/2026

Estado: Pre-Producción / Estable Modular

Tecnología: Python 3.11+ / PySide6 / SQLite / ZPL II


---

1. ARQUITECTURA TÉCNICA (MODULAR)


El sistema ha evolucionado de un script monolítico a una arquitectura desacoplada para facilitar el mantenimiento y la estabilidad.

Estructura de Archivos (El nuevo estándar)

Archivo	Responsabilidad
main.py	Lanzador. Contiene el "Error Catcher" (captura fallos críticos al inicio y genera logs). No tiene lógica UI.
main_ui.py	Controlador Principal. Maneja el flujo de captura, eventos de botones, lógica de selección de cajas y comunicación con hardware.
styles.py	SSOT Visual (Single Source of Truth). Define la paleta "Industrial Light" (Gris/Negro) y hojas de estilo QSS.
hardware.py	Driver Unificado. Consolida ZebraPrinter y ScaleWorker. Contiene el código ZPL crítico.
admin_panel.py	Gestión. Ventana independiente para reabrir cajas, reimprimir etiquetas, editar pesos y catálogo.
dialogs.py	Selectores. Ventanas modales para búsqueda de SINIIGA y creación inteligente de Cajas.
db_manager.py	Persistencia. Consultas SQL directas a produccion_local.db.
check_env.py	Diagnóstico. Script para validar librerías, archivos y drivers antes de desplegar.

---

2. REGLAS VISUALES Y UX (INDUSTRIAL LIGHT)


Se descartó el modo oscuro por problemas de contraste en planta.


- Esquema: Fondo Gris Claro (#E6E6E6) con Texto Negro Puro (#000000).

- Semántica de Botones de Caja:
	- 🟢 VERDE: Caja Abierta (Disponible).

	- 🔵 AZUL: Caja Activa (Seleccionada para pesaje actual).

	- 🔴 ROJO: Caja Cerrada (Solo visible en Admin).


- Diálogos: Se fuerza el estilo gris/negro con fuentes grandes para legibilidad del operario.


---

3. LÓGICA DE NEGOCIO Y HARDWARE

A. Báscula (Torrey EQB)


Se implementaron correcciones por software debido a desfases físicos del equipo:


1. Corrección Silenciosa: Variable CORRECCION_MANUAL = -0.01 en main_ui.py que se resta automáticamente al guardar.

2. Modo Manual: Checkbox en UI para permitir escribir el peso si la báscula falla.

3. Peso Visual: En pantalla se muestra lo que manda la báscula (sin corregir) para no confundir al operario; la corrección se aplica al grabar en BD.

B. Impresora (Zebra ZPL)


La lógica reside exclusivamente en hardware.py. Se realizaron ajustes puntuales solicitados:


- Etiqueta Individual:
	- Se eliminó el contador de pieza (#4).

	- Muestra solo el número de caja a dos dígitos (ej: 01).

	- Código de Barras concatenado.


- Etiqueta Master (Caja):
	- Se eliminó el campo "CANTIDAD" (espacio en blanco).

	- Lógica de Cierre Híbrido: Al cerrar caja, el sistema sugiere la suma calculada, pero permite al operario ingresar manualmente el peso total (basculazo final) para corregir errores acumulativos de redondeo.



---

4. FLUJOS DE TRABAJO CRÍTICOS

Flujo de Captura (Ping-Pong)

1. Selección de SINIIGA -> Selección de Caja.

2. Teclear Producto -> ENTER (Busca y bloquea si el candado está activo).

3. El foco pasa a PESO -> Lectura automática o manual -> ENTER.

4. Acción: Guarda en BD -> Imprime Etiqueta -> Actualiza Tabla -> Limpia foco.

Flujo Admin -> Producción

1. Desde Admin, doble clic en una caja o botón "Abrir en Producción".

2. Si la caja estaba CERRADA, pregunta si se desea REABRIR.

3. Al volver a Main, se ejecuta refresh_context() para redibujar la barra superior y seleccionar la caja activa automáticamente.


---

5. INSTRUCCIONES DE DESPLIEGUE

1. Limpieza: Eliminar archivos obsoletos (zebra_printer.py, serial_scale.py) para evitar confusiones.

2. Configuración: Revisar config.ini para el puerto COM correcto.

3. Verificación: Ejecutar python check_env.py en la máquina cliente.

4. Ejecución: Siempre iniciar desde main.py.

/PROYECTO_ETIQUETADO_V3
│
├── main.py            (Lanzador con Error Log)
├── main_ui.py         (Lógica principal de Ventanas)
├── admin_panel.py     (Gestión de Admin)
├── hardware.py        (Drivers Báscula e Impresora)
├── db_manager.py      (El archivo que acabamos de crear)
├── dialogs.py         (Selectores SINIIGA/Caja)
├── styles.py          (Colores y CSS)
├── check_env.py       (Script de diagnóstico)
├── schema.sql         (Estructura BD)
├── config.ini         (Se generará solo si no existe)
└── assets/
    └── DS-DIGI.TTF    (Fuente digital - OBLIGATORIA para la visualización de peso)
---

6. TAREAS PENDIENTES / FUTURO

1. Reportes: Generación de PDF/Excel de cierre de turno.

2. Red: Sincronización con servidor central (futuro).

3. Monitoreo: Validar que el ajuste de -0.01 en la báscula se mantenga constante con pesos mayores a 20kg.