Resultado del diagnóstico (sin cambios)
A continuación, la deuda/violaciones actuales observables contra ARCHITECTURE.md y RULES.md, organizada por las categorías que pediste.

1) SSOT visual
Referencia de regla

styles.py es la fuente única de verdad visual y no deben aparecer valores visuales nuevos hardcodeados fuera de ahí. Además, setStyleSheet() local solo debería consumir estilos ya definidos en styles.py.

Hallazgos

main_ui.py contiene múltiples setStyleSheet() con colores/tamaños hardcodeados (no referenciados a constantes de styles.py), por ejemplo en btn_adm, lbl_total, validación de producto, encabezado SINIIGA, etc. 

dialogs.py define hojas de estilo completas embebidas con valores visuales explícitos (fondos, bordes, font-size, colores) en ambos diálogos. 

admin_panel.py define un bloque ADMIN_STYLE completo con valores hardcodeados y además estilos locales adicionales en navegación, labels y frames. 

Nota documental: tanto ARCHITECTURE.md como RULES.md registran explícitamente que esta deuda visual existente se considera “deuda conocida”.

2) Acoplamiento UI → DB
Referencia de regla

La UI no debe contener SQL/ZPL/lógica hardware; y por arquitectura conceptual, UI debería centrarse en presentación. 

Hallazgos

main_ui.py instancia y usa directamente DatabaseManager, llamando operaciones de persistencia en handlers de UI (consulta de producto, registro pieza, cierre/reapertura, borrado, estadísticas, etc.). 

dialogs.py depende de db_manager en el constructor y usa consultas/estados DB para filtrar y decidir acciones de canal/caja. 

admin_panel.py recibe db_manager y ejecuta directamente operaciones de lectura/escritura/estado desde eventos UI (cerrar/reabrir, borrar, catálogo). 

3) Acoplamiento UI → hardware
Referencia de regla

La UI no debe contener lógica de hardware. 

Hallazgos

main_ui.py importa hardware, crea HardwareManager, lista puertos COM, controla thread/timer de báscula y dispara impresión desde la UI. 

admin_panel.py también importa hardware, instancia HardwareManager y ejecuta reimpresiones/masters desde acciones de interfaz. 

4) Reglas de negocio dispersas
Referencia de regla

La UI no debe decidir reglas complejas; reglas de negocio deberían tender a funciones puras y el propio ARCHITECTURE.md ya indica dispersión entre UI/dialogs/db_manager. 

Hallazgos

Corrección de peso de negocio (CORRECCION_MANUAL, umbral >0.02, validación final) en main_ui.py dentro de flujo UI. 

Regla de secuencia/reutilización/salto de caja (4 casos) implementada en BoxSelectorDialog (UI), no aislada en capa de dominio. 

Regla de normalización/armado de SINIIGA y lote implementada en diálogo (080000{t}-{lote_actual}), mientras también hay normalización en persistencia (buscar_o_crear_canal agrega prefijo/cero-padding). Esto evidencia regla distribuida en más de un módulo. 

Regla de cálculo de peso final master duplicada/distribuida: UI calcula y pide override, hardware vuelve a decidir peso_final con peso_manual_override. 

5) Archivos legacy / ambiguos
Referencia de regla

Se reconoce explícitamente archivo histórico numeros de productos en caja, hardware.py como referencia no operativa. 

Hallazgos

El archivo legacy efectivamente existe en el repo y contiene implementación completa de hardware/ZPL, lo que crea ambigüedad documental-operativa al coexistir con hardware.py. {line_range_start=1 line_range_end=9 path=numeros de productos en caja, hardware.py git_url="https://github.com/JoseSanta98/sistema-ccc/blob/main/numeros de productos en caja, hardware.py#L1-L9"}

Ambigüedad de esquema DB: db_manager.py busca schema.sql en raíz (SCHEMA_FILE = "schema.sql"), pero el archivo versionado visible está en tools/schema.sql; esto deja una discrepancia de ubicación/nombre operativo. 