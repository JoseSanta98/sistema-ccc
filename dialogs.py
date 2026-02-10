# dialogs.py
import sys
from datetime import datetime
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QListWidget, QListWidgetItem, QPushButton, QCheckBox
)
# Separación de módulos para compatibilidad con Python 3.13 + PySide6
from PySide6.QtCore import Qt, QEvent, QRegularExpression 
from PySide6.QtGui import QRegularExpressionValidator

# ============================================================================
# 1. DIALOGO SINIIGA PREMIUM (CON MODO INTRODUCTOR-LOTE)
# ============================================================================
class SiniigaSelectorDialog(QDialog):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.selected_siniiga = None
        
        self.setFixedSize(600, 600)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        
        # Cargar datos iniciales
        self.canales = self.db.get_canales_activos() if self.db else []
        
        self.init_ui()
        self.filtrar("") 
        
    def init_ui(self):
        self.setStyleSheet("""
            QDialog { background: #202020; border: 2px solid #444; }
            QLabel { color: #fff; font-size: 22px; font-weight: bold; font-family: 'Segoe UI'; }
            QLineEdit { 
                font-size: 32px; padding: 10px; background: #1a1a1a; 
                color: #fff; border: 2px solid #555; border-radius: 4px;
            }
            QLineEdit:focus { border: 2px solid #007acc; }
            QListWidget { background: #2d2d2d; color: #eee; font-size: 16px; border: 1px solid #444; }
            QListWidget::item { padding: 8px; }
            QListWidget::item:selected { background: #007acc; color: white; }
            QPushButton { 
                background: #444; color: #888; font-size: 16px; 
                padding: 15px; border: none; border-radius: 4px; font-weight: bold;
            }
            QPushButton:enabled { background: #007acc; color: #fff; }
            QPushButton:hover:enabled { background: #005bb5; }
            QLabel#InfoLabel { font-size: 14px; color: #aaa; font-weight: normal; }
            QCheckBox { color: #ddd; font-size: 16px; font-weight: bold; padding: 5px; }
        """)

        v = QVBoxLayout(self)
        v.setContentsMargins(25, 25, 25, 25)
        v.setSpacing(15)

        v.addWidget(QLabel("Seleccionar Canal"))

        # Checkbox Modo Introductor
        self.chk_intro = QCheckBox("Modo Introductor (4 dígitos)")
        self.chk_intro.toggled.connect(self.on_mode_change)
        v.addWidget(self.chk_intro)

        # Input
        self.txt = QLineEdit()
        self.txt.setMaxLength(10)
        self.txt.setPlaceholderText("Escriba SINIIGA...")
        self.txt.textChanged.connect(self.on_tc)
        self.txt.installEventFilter(self) 
        v.addWidget(self.txt)

        self.lbl_info = QLabel("")
        self.lbl_info.setObjectName("InfoLabel")
        v.addWidget(self.lbl_info)

        self.lst = QListWidget()
        self.lst.itemClicked.connect(self.on_lc)
        v.addWidget(self.lst)

        h = QHBoxLayout()
        btn_c = QPushButton("CANCELAR"); btn_c.clicked.connect(self.reject)
        self.btn = QPushButton("ACCIÓN"); self.btn.setEnabled(False); self.btn.clicked.connect(self.confirm)
        h.addWidget(btn_c); h.addWidget(self.btn)
        v.addLayout(h)

    def on_mode_change(self, checked):
        self.txt.clear()
        if checked:
            self.txt.setMaxLength(4)
            self.txt.setPlaceholderText("4 dígitos...")
            self.txt.setValidator(QRegularExpressionValidator(QRegularExpression("[0-9]*")))
        else:
            self.txt.setMaxLength(10)
            self.txt.setPlaceholderText("Escriba SINIIGA...")
            self.txt.setValidator(None)
        self.txt.setFocus()

    def on_tc(self, t):
        self.filtrar(t); self.validate(t)

    def on_lc(self, i):
        data = i.data(Qt.UserRole)
        if data:
            if self.chk_intro.isChecked(): self.chk_intro.setChecked(False)
            # Mostrar solo el número sin el guion de identidad interna
            self.txt.setText(data['siniiga'].split("-")[0])

    def filtrar(self, t):
        self.lst.clear()
        term = t.strip()
        for c in self.canales:
            clean_siniiga = c['siniiga'].split("-")[0]
            if term in clean_siniiga:
                i = QListWidgetItem(f"📂 {clean_siniiga} | Lote: {c['lote_dia']}")
                i.setData(Qt.UserRole, c)
                self.lst.addItem(i)
        
        if self.lst.count() == 0 and t:
            i = QListWidgetItem("✨ Crear Nuevo...")
            i.setFlags(Qt.NoItemFlags)
            self.lst.addItem(i)

    def validate(self, t):
        is_intro = self.chk_intro.isChecked()
        lote_actual = datetime.now().strftime("%d%m%y")
        
        if is_intro:
            if len(t) == 4:
                target_siniiga = f"080000{t}-{lote_actual}"
            else:
                self.btn.setEnabled(False); self.lbl_info.setText("Ingrese 4 dígitos..."); return
        else:
            target_siniiga = t

        ex = next((c for c in self.canales if c['siniiga'] == target_siniiga), None)

        if not t:
            self.btn.setEnabled(False); self.lbl_info.setText("Esperando entrada...")
            return

        if ex:
            self.selected_siniiga = ex
            self.btn.setText(f"ABRIR {t}")
            self.lbl_info.setText("Canal existente encontrado.")
            self.btn.setEnabled(True)
        else:
            self.selected_siniiga = {'nuevo': True, 'texto': target_siniiga}
            self.btn.setText(f"CREAR {t}")
            self.lbl_info.setText("Se generará un nuevo canal.")
            self.btn.setEnabled(len(t) >= 4)

    def confirm(self):
        if self.btn.isEnabled(): self.accept()

    def eventFilter(self, o, e):
        if o == self.txt and e.type() == QEvent.KeyPress:
            if e.key() == Qt.Key_Down:
                self.lst.setFocus()
                if self.lst.count() > 0: self.lst.setCurrentRow(0)
                return True
            if e.key() in (Qt.Key_Return, Qt.Key_Enter):
                self.confirm(); return True
        return super().eventFilter(o, e)


# ============================================================================
# 2. DIALOGO CAJA INTELIGENTE (LOGICA HISTORICA)
# ============================================================================
class BoxSelectorDialog(QDialog):
    def __init__(self, db, cid, parent=None):
        super().__init__(parent)
        self.db = db
        self.cid = cid # Canal ID
        self.res = None 
        
        # 1. Obtener abiertas
        self.exist = self.db.get_cajas_abiertas(cid)
        self.open_nums = [c['numero_caja'] for c in self.exist]
        
        # 2. Obtener máximo histórico para sugerencia real
        self.max_hist = self.db.get_max_numero_caja(cid)
        self.sug = self.max_hist + 1
        
        self.setFixedSize(500, 450)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("""
            QDialog { background: #252526; border: 2px solid #555; }
            QLabel { color: #fff; font-size: 20px; font-family: 'Segoe UI'; }
            QLineEdit { 
                background: #111; color: #0f0; font-size: 60px; 
                border: 2px solid #444; font-family: 'Consolas'; font-weight: bold;
                selection-background-color: #005bb5;
            }
            QPushButton { 
                background: #444; color: #fff; font-size: 16px; 
                padding: 12px; border: none; border-radius: 4px; font-weight: bold;
            }
            QPushButton:hover { background: #555; }
            QLabel#WarnLabel { color: #ffcc00; font-size: 16px; font-weight: bold; }
        """)

        v = QVBoxLayout(self)
        v.setContentsMargins(30, 30, 30, 30); v.setSpacing(15)

        info_txt = f"Sugerida: Caja #{self.sug}"
        if self.max_hist > 0:
            info_txt += f" (Máx: #{self.max_hist})"
        v.addWidget(QLabel(info_txt))

        self.txt = QLineEdit(str(self.sug))
        self.txt.setMaxLength(3)
        self.txt.setValidator(QRegularExpressionValidator(QRegularExpression("[1-9][0-9]*")))
        self.txt.textChanged.connect(self.val)
        self.txt.returnPressed.connect(self.ok)
        v.addWidget(self.txt)

        self.lbl = QLabel(""); self.lbl.setObjectName("WarnLabel"); self.lbl.setWordWrap(True)
        v.addWidget(self.lbl); v.addStretch()

        h = QHBoxLayout()
        bc = QPushButton("CANCELAR"); bc.clicked.connect(self.reject)
        self.ba = QPushButton("ACCIÓN"); self.ba.clicked.connect(self.ok)
        h.addWidget(bc); h.addWidget(self.ba); v.addLayout(h)

        self.txt.selectAll(); self.val(self.txt.text())

    def val(self, t):
        if not t: self.ba.setEnabled(False); self.lbl.setText(""); return
        try:
            n = int(t)
        except ValueError:
            self.ba.setEnabled(False); return
        
        # CASO 1: YA ABIERTA
        if n in self.open_nums:
            self.ba.setText(f"📂 SELECCIONAR {n}"); self.ba.setStyleSheet("background: #005bb5; color: white;")
            self.lbl.setText("Esta caja ya está activa.")
        # CASO 2: SECUENCIA CORRECTA
        elif n == self.sug:
            self.ba.setText(f"✨ CREAR {n}"); self.ba.setStyleSheet("background: #28a745; color: white;")
            self.lbl.setText("Secuencia correcta.")
        # CASO 3: SALTO
        elif n > self.sug:
            salto = n - self.sug
            self.ba.setText(f"⚠️ CREAR {n} (SALTO)"); self.ba.setStyleSheet("background: #d39e00; color: #000;")
            self.lbl.setText(f"CUIDADO: Se saltarán {salto} números.")
        # CASO 4: ANTERIOR (REUTILIZACIÓN)
        else:
            self.ba.setText(f"♻️ REUTILIZAR {n}"); self.ba.setStyleSheet("background: #c65911; color: white;")
            self.lbl.setText("AVISO: Este número ya se usó anteriormente.")

        self.ba.setEnabled(True)

    def ok(self):
        if self.ba.isEnabled():
            self.res = int(self.txt.text())
            self.accept()