# check_env.py
import sys
import os
import importlib
from pathlib import Path

def check_requirements():
    print("="*60)
    print(" VERIFICADOR DE ENTORNO - SISTEMA CCC v3.2 ")
    print("="*60)

    # 1. Verificar Versión de Python
    version_ok = sys.version_info >= (3, 11)
    status_v = "OK" if version_ok else "ADVERTENCIA"
    print(f"[*] Python {sys.version.split()[0]} -> {status_v}")
    if not version_ok:
        print("    Se recomienda Python 3.11 o superior para evitar errores de PySide6.")

    # 2. Verificar Librerías Python
    # (Nombre interno, Nombre del paquete para pip)
    dependencies = [
        ('PySide6', 'PySide6'),
        ('serial', 'pyserial'),
        ('win32print', 'pywin32'),
        ('reportlab', 'reportlab'),
        ('matplotlib', 'matplotlib')
    ]

    missing_libs = []
    print("\n[*] Verificando librerías:")
    for imp_name, pkg_name in dependencies:
        try:
            importlib.import_module(imp_name)
            print(f"    [OK] {pkg_name}")
        except ImportError:
            print(f"    [X]  FALTA: {pkg_name}")
            missing_libs.append(pkg_name)

    # 3. Verificar Estructura de Archivos (Modularización)
    critical_files = [
        'main.py',
        'main_ui.py',
        'styles.py',
        'hardware.py',
        'dialogs.py',
        'admin_panel.py',
        'db_manager.py',
        'schema.sql',
        'assets/DS-DIGI.TTF'
    ]

    print("\n[*] Verificando integridad de archivos:")
    files_missing = False
    for file_path in critical_files:
        if Path(file_path).exists():
            print(f"    [OK] {file_path}")
        else:
            print(f"    [X]  FALTA: {file_path}")
            files_missing = True

    # 4. Verificar Impresora Zebra
    print("\n[*] Verificando impresora:")
    try:
        import win32print
        printers = [p[2] for p in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)]
        zebra_found = any("ZEBRA" in p.upper() or "ZTC" in p.upper() or "ZDESIGNER" in p.upper() for p in printers)
        if zebra_found:
            print(f"    [OK] Impresora Zebra detectada.")
        else:
            print(f"    [!]  ALERTA: No se encontró impresora Zebra en el Panel de Control.")
    except:
        print("    [!]  Error al consultar drivers de impresión.")

    print("\n" + "="*60)
    
    # RESULTADO FINAL
    if missing_libs:
        print("--- RESULTADO: ENTORNO INCOMPLETO ---")
        print("\nPara solucionar las librerías faltantes, ejecuta este comando:")
        # Comando específico para la versión que solicita PySide6 6.10
        pyside_fix = ""
        if "PySide6" in missing_libs:
            missing_libs.remove("PySide6")
            pyside_fix = '"PySide6>=6.10,<6.11" '
        
        cmd = f"python -m pip install {pyside_fix}{' '.join(missing_libs)}"
        print(f"\n{cmd}\n")
    elif files_missing:
        print("--- RESULTADO: FALTAN ARCHIVOS DEL PROYECTO ---")
        print("Asegúrate de copiar todos los archivos .py y la carpeta assets.")
    else:
        print("--- RESULTADO: ENTORNO LISTO PARA PRODUCCIÓN ---")
    
    print("="*60)
    
    # Pausa para que el usuario pueda leer el reporte en la consola
    input("\nPresiona ENTER para cerrar este verificador...")

if __name__ == "__main__":
    check_requirements()