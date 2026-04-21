# main.py
import sys
import configparser
import traceback
from pathlib import Path
from datetime import datetime # FIX: Importación añadida
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QTimer
from PySide6.QtGui import QFontDatabase, QGuiApplication

try:
    from main_ui import MainUI
except Exception as e:
    with open("error_log.txt", "w") as f:
        f.write(f"FALLO CRITICO AL CARGAR MODULOS:\n{traceback.format_exc()}")
    print("Error crítico al cargar módulos. Revisa error_log.txt")
    sys.exit(1)

CONFIG_FILE = "config.ini"
BASE_DIR = Path(__file__).resolve().parent
FONT_PATH = BASE_DIR / "assets" / "DS-DIGI.TTF"

def apply_smart_geometry(window):
    screen = window.screen() or QGuiApplication.primaryScreen()
    if screen is None:
        return

    available_geometry = screen.availableGeometry()
    target_width = max(window.minimumWidth(), int(available_geometry.width() * 0.92))
    target_height = max(window.minimumHeight(), int(available_geometry.height() * 0.92))

    target_width = min(target_width, available_geometry.width())
    target_height = min(target_height, available_geometry.height())

    x = available_geometry.x() + (available_geometry.width() - target_width) // 2
    y = available_geometry.y() + (available_geometry.height() - target_height) // 2

    window.setGeometry(x, y, target_width, target_height)

def load_config():
    config = configparser.ConfigParser()
    if not Path(CONFIG_FILE).exists():
        config['SISTEMA'] = {'MODO_DEMO': 'True'}
        config['HARDWARE'] = {
            'PRINTER_NAME': 'ZDesigner GC420t',
            'SCALE_BAUDRATE': '9600',
            'TARA': '0.00'
        }
        with open(CONFIG_FILE, 'w') as f:
            config.write(f)
    else:
        config.read(CONFIG_FILE)
        if not config.has_section('HARDWARE'):
            config['HARDWARE'] = {}
        config['HARDWARE']['TARA'] = str(config.getfloat('HARDWARE', 'TARA', fallback=0.00))
    return config

def main():
    app = QApplication(sys.argv)
    
    if FONT_PATH.exists():
        QFontDatabase.addApplicationFont(str(FONT_PATH))
    
    config = load_config()
    
    try:
        window = MainUI(config)
        window.show()
        QTimer.singleShot(0, lambda: apply_smart_geometry(window))
        sys.exit(app.exec())
    except Exception:
        error_msg = traceback.format_exc()
        with open("error_log.txt", "a") as f:
            f.write(f"\n--- ERROR DE EJECUCION ({datetime.now()}) ---\n")
            f.write(error_msg)
        
        error_dialog = QMessageBox()
        error_dialog.setIcon(QMessageBox.Critical)
        error_dialog.setWindowTitle("Error Crítico")
        error_dialog.setText("El programa se cerró inesperadamente.")
        error_dialog.setDetailedText(error_msg)
        error_dialog.exec()
        sys.exit(1)

if __name__ == "__main__":
    main()