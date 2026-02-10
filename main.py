# main.py
import sys
import configparser
import traceback
from pathlib import Path
from datetime import datetime # FIX: Importación añadida
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QFontDatabase

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

def load_config():
    config = configparser.ConfigParser()
    if not Path(CONFIG_FILE).exists():
        config['SISTEMA'] = {'MODO_DEMO': 'True'}
        config['HARDWARE'] = {
            'PRINTER_NAME': 'ZDesigner GC420t',
            'SCALE_BAUDRATE': '9600'
        }
        with open(CONFIG_FILE, 'w') as f:
            config.write(f)
    else:
        config.read(CONFIG_FILE)
    return config

def main():
    app = QApplication(sys.argv)
    
    if FONT_PATH.exists():
        QFontDatabase.addApplicationFont(str(FONT_PATH))
    
    config = load_config()
    
    try:
        window = MainUI(config)
        window.show()
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