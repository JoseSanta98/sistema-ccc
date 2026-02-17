# main_ui.py
import datetime
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView, QSplitter, 
    QMessageBox, QFrame, QScrollArea, QComboBox, QCheckBox, QInputDialog,
    QAbstractItemView
)
from PySide6.QtCore import Qt, QTimer

from db_manager import DatabaseManager
from dialogs import SiniigaSelectorDialog, BoxSelectorDialog
from admin_panel import AdminPanel
from box_domain import (
    ESTADO_ABIERTA,
    ESTADO_CERRADA,
    puede_agregar_pieza,
    puede_cerrar_caja,
    puede_reabrir_caja
)
from box_service import cerrar_caja
import styles 
import hardware
from peso_policy import calcular_peso_pieza, calcular_peso_caja, PesoInvalidoError, resolver_peso_cierre


class MainUI(QMainWindow):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.setWindowTitle("SISTEMA DE ETIQUETADO TIF - V4.1")
        self.resize(1280, 850)
        self.setStyleSheet(styles.MAIN_STYLESHEET)
        
        self.db = DatabaseManager()
        self.hw_mgr = hardware.HardwareManager(config.get('HARDWARE', 'PRINTER_NAME', fallback='ZDesigner'))
        
        self.current_canal = None
        self.current_box = None
        self.current_product = None
        self.last_activity = datetime.datetime.now()
        
        # Estado de hardware
        self.scale_active = False 
        self.th_scale = None
        self.tm_demo = None
        
        self.init_ui()
        # Sincronizar estado inicial (esto llamará a update_scale_ui)
        self.toggle_scale(False) 
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_kpis)
        self.timer.start(1000)

    def init_ui(self):
        cw = QWidget()
        self.setCentralWidget(cw)
        main_lay = QVBoxLayout(cw)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.setSpacing(0)
        
        # 1. TOP BAR (SINIIGA + CAJAS ABIERTAS)
        top = QFrame()
        top.setObjectName("TopBar")
        top.setFixedHeight(120)
        th = QHBoxLayout(top)
        th.setContentsMargins(10, 10, 10, 10)
        th.setSpacing(15)
        
        self.btn_sin = QPushButton("SINIIGA: ---\nClic para iniciar")
        self.btn_sin.setObjectName("btnSiniiga")
        self.btn_sin.setFixedSize(260, 95)
        self.btn_sin.clicked.connect(self.flow_open_siniiga)
        th.addWidget(self.btn_sin)
        
        sa = QScrollArea()
        sa.setWidgetResizable(True)
        sa.setStyleSheet("background: transparent; border: none;")
        self.sw = QWidget()
        self.sw.setStyleSheet("background: transparent;")
        self.box_layout = QHBoxLayout(self.sw)
        self.box_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.box_layout.setSpacing(10)
        sa.setWidget(self.sw)
        th.addWidget(sa, 1)
        
        btn_adm = QPushButton("⚙️ ADMIN")
        btn_adm.setFixedSize(90, 95)
        btn_adm.setStyleSheet("background-color: #333; color: white; border: 2px solid black; font-weight: bold;")
        btn_adm.clicked.connect(self.flow_open_admin)
        th.addWidget(btn_adm)
        
        main_lay.addWidget(top)
        
        # 2. CUERPO (SPLITTER)
        spl = QSplitter(Qt.Horizontal)
        
        # --- PANEL IZQUIERDO (CAPTURA) ---
        left_w = QWidget()
        lv = QVBoxLayout(left_w)
        lv.setContentsMargins(15, 15, 15, 15)
        lv.setSpacing(12)
        
        kf = QFrame()
        kf.setObjectName("KpiPanel")
        kh = QHBoxLayout(kf)
        self.k_h = self.mk_kpi("PZAS HOY", "0")
        self.k_p = self.mk_kpi("PESO HOY", "0.0")
        self.k_t = self.mk_kpi("INACTIVO", "00:00")
        kh.addLayout(self.k_h)
        kh.addLayout(self.k_p)
        kh.addLayout(self.k_t)
        lv.addWidget(kf)
        
        hl = QHBoxLayout()
        self.cb_ports = QComboBox()
        self.cb_ports.addItems(hardware.get_com_ports())
        self.chk_scale = QCheckBox("Báscula Activa")
        self.chk_scale.setObjectName("ChkIndustrial")
        self.chk_scale.toggled.connect(self.toggle_scale)
        hl.addWidget(QLabel("Puerto:"))
        hl.addWidget(self.cb_ports)
        hl.addWidget(self.chk_scale)
        lv.addLayout(hl)
        
        lv.addWidget(QLabel("1. CÓDIGO PRODUCTO:"))
        self.txt_prod = QLineEdit()
        self.txt_prod.returnPressed.connect(self.logic_validate_product)
        lv.addWidget(self.txt_prod)
        
        self.lbl_prod_name = QLabel("⚠️ SELECCIONE CAJA")
        self.lbl_prod_name.setObjectName("LblFeedback")
        lv.addWidget(self.lbl_prod_name)
        
        gl_opts = QHBoxLayout()
        self.chk_lock_prod = QCheckBox("🔒 Fijo")
        self.chk_lock_prod.setObjectName("ChkIndustrial")
        
        self.chk_apply_corr = QCheckBox("⚖️ Corr. -0.02")
        self.chk_apply_corr.setObjectName("ChkIndustrial")
        self.chk_apply_corr.setChecked(True)
        
        gl_opts.addWidget(self.chk_lock_prod)
        gl_opts.addWidget(self.chk_apply_corr)
        lv.addLayout(gl_opts)
        
        lv.addWidget(QLabel("2. PESO NETO (Kg):"))
        self.txt_weight = QLineEdit("") 
        self.txt_weight.setObjectName("WeightField") # Fuente Digital Permanente
        self.txt_weight.setAlignment(Qt.AlignRight)
        self.txt_weight.setFixedHeight(125)
        self.txt_weight.returnPressed.connect(self.logic_save_print)
        lv.addWidget(self.txt_weight)
        
        self.btn_print = QPushButton("IMPRIMIR ETIQUETA")
        self.btn_print.setObjectName("BtnPrint")
        self.btn_print.setFixedHeight(85)
        self.btn_print.setEnabled(False)
        self.btn_print.clicked.connect(self.logic_save_print)
        lv.addWidget(self.btn_print)
        lv.addStretch()
        
        # --- PANEL DERECHO (GRID) ---
        right_w = QWidget()
        rv = QVBoxLayout(right_w)
        rv.setContentsMargins(10, 15, 10, 15)
        
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["#", "COD", "PROD", "PESO", "HORA"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        head = self.table.horizontalHeader()
        head.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        head.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        head.setSectionResizeMode(2, QHeaderView.Stretch)
        head.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        head.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        rv.addWidget(self.table)
        
        self.lbl_total = QLabel("TOTAL CAJA: 0.00 Kg")
        self.lbl_total.setStyleSheet("font-size: 26px; border: 3px solid black; padding: 10px; background: white; color: black;")
        self.lbl_total.setAlignment(Qt.AlignRight)
        rv.addWidget(self.lbl_total)
        
        al = QHBoxLayout()
        btn_del = QPushButton("🗑️ BORRAR")
        btn_del.setStyleSheet(f"background:{styles.COLOR_BTN_DANGER}; color:white;")
        btn_del.clicked.connect(self.logic_delete_row)
        
        btn_rep = QPushButton("🏷️ REIMPRIMIR")
        btn_rep.setStyleSheet(f"background:{styles.COLOR_BTN_WARN}; color:black;")
        btn_rep.clicked.connect(self.logic_reprint)
        al.addWidget(btn_del)
        al.addWidget(btn_rep)
        rv.addLayout(al)
        
        self.btn_cls = QPushButton("📦 CERRAR CAJA / ETIQUETA MASTER")
        self.btn_cls.setObjectName("BtnClose")
        self.btn_cls.setFixedHeight(70)
        self.btn_cls.clicked.connect(self.logic_close_box)
        rv.addWidget(self.btn_cls)
        
        spl.addWidget(left_w)
        spl.addWidget(right_w)
        spl.setSizes([450, 830])
        main_lay.addWidget(spl)

    def mk_kpi(self, t, v):
        l = QVBoxLayout()
        lbl = QLabel(t); lbl.setProperty("class", "kpiTitle")
        l.addWidget(lbl)
        val = QLabel(v); val.setProperty("class", "kpiValue")
        l.addWidget(val)
        return l

    # =========================================================================
    # HARDWARE (BÁSCULA)
    # =========================================================================
    def toggle_scale(self, active):
        if self.th_scale:
            self.th_scale.stop()
            self.th_scale = None
        if self.tm_demo:
            self.tm_demo.stop()
            self.tm_demo = None

        self.scale_active = False

        if active:
            if self.config.getboolean('SISTEMA', 'MODO_DEMO', fallback=True):
                self.tm_demo = QTimer()
                self.tm_demo.timeout.connect(lambda: self.update_weight_display(12.54))
                self.tm_demo.start(500)
                self.scale_active = True
            else:
                try:
                    self.th_scale = hardware.ScaleWorker(self.cb_ports.currentText())
                    self.th_scale.weight_received.connect(self.update_weight_display)
                    self.th_scale.start()
                    self.scale_active = True
                except Exception:
                    QMessageBox.warning(self, "Báscula", "No se pudo conectar.")
                    self.chk_scale.setChecked(False)
                    return
        
        self.update_scale_ui()

    def update_scale_ui(self):
        """
        FIX: El estilo visual lo controla SIEMPRE styles.py vía QSS.
        Solo gestionamos el comportamiento de edición aquí.
        """
        if self.scale_active:
            self.txt_weight.setReadOnly(True)
        else:
            self.txt_weight.setReadOnly(False)

    def update_weight_display(self, w):
        if self.scale_active:
            self.txt_weight.setText(f"{w:.2f}")

    # =========================================================================
    # FLUJO OPERATIVO
    # =========================================================================
    def _buscar_producto(self, code):
        return self.db.get_producto(code)

    def logic_validate_product(self):
        code = self.txt_prod.text().strip()
        if not code:
            return
        p = self._buscar_producto(code)
        if p:
            self.current_product = p
            self.lbl_prod_name.setText(p['nombre'])
            self.lbl_prod_name.setStyleSheet("color:#008000;")
            self.btn_print.setEnabled(True)
            self.txt_weight.setFocus()
            if not self.scale_active:
                self.txt_weight.clear()
        else:
            self.current_product = None
            self.lbl_prod_name.setText("NO ENCONTRADO")
            self.btn_print.setEnabled(False)
            self.txt_prod.selectAll()

    def _calcular_peso_final(self):
        txt_w = self.txt_weight.text().strip()
        if not txt_w:
            return None

        try:
            raw_weight = float(txt_w)
        except ValueError:
            QMessageBox.warning(self, "Peso", "Valor inválido.")
            return None

        aplicar_correccion_checkbox = self.chk_apply_corr.isChecked()

        try:
            peso_final = calcular_peso_pieza(raw_weight, aplicar_correccion_checkbox)
        except PesoInvalidoError as e:
            QMessageBox.warning(self, "Error de peso", str(e))
            return None

        return peso_final

    def _registrar_e_imprimir(self, final_w):
        consec, pid = self.db.registrar_pieza(self.current_box['id'], self.current_product['codigo'], self.current_product['nombre'], final_w)
        full = self.db.get_pieza_by_id(pid)
        ok, msg = self.hw_mgr.print_ticket(full, self.current_box, self.current_canal, self.current_product)
        if not ok: QMessageBox.critical(self, "Impresora", msg)

    def logic_save_print(self):
        if not self.current_box or not self.current_product:
            return

        final_w = self._calcular_peso_final()
        if final_w is None:
            return

        if not puede_agregar_pieza(self.current_box['estado']):
            return

        self._registrar_e_imprimir(final_w)

        self.current_box = self.db.get_caja_by_id(self.current_box['id'])

        self.last_activity = datetime.datetime.now()
        self.refresh_table()
        self.update_stats()
        self.highlight_buttons(self.current_box['numero_caja'])

        if self.scale_active:
            self.txt_weight.setFocus()
        else:
            self.txt_weight.clear()
            if self.chk_lock_prod.isChecked():
                self.txt_weight.setFocus()
            else:
                self.txt_prod.clear()
                self.current_product = None
                self.lbl_prod_name.setText("LISTO - ESCANEE PRODUCTO")
                self.lbl_prod_name.setStyleSheet("color: #000;")
                self.btn_print.setEnabled(False)
                self.txt_prod.setFocus()

    def _ejecutar_cierre_caja(self, peso_final, contenido):
        cerrar_caja(self.db, self.hw_mgr, self.current_box, self.current_canal, contenido, peso_final)

    def logic_close_box(self):
        if not self.current_box: return
        if not puede_cerrar_caja(self.current_box['estado']):
            return
        cont = self.db.get_contenido_caja(self.current_box['id'])
        if not cont: return
        peso_calc = calcular_peso_caja(cont)
        peso_f, ok = QInputDialog.getDouble(self, "Peso Final", f"Suma: {peso_calc:.2f} Kg", value=peso_calc, minValue=0.1, maxValue=20.0, decimals=2)
        if ok:
            try:
                resultado = resolver_peso_cierre(peso_calc, peso_f)
            except PesoInvalidoError as e:
                QMessageBox.warning(self, "Error de peso", str(e))
                return

            peso_final = resultado["peso_final"]

            if resultado["hay_diferencia"]:
                QMessageBox.warning(
                    self,
                    "Advertencia",
                    f"El peso final difiere de la suma calculada por {resultado['delta']:.2f} kg"
                )

            self._ejecutar_cierre_caja(peso_final, cont)
            self.current_box = None
            self.refresh_context()

    def flow_open_siniiga(self):
        d = SiniigaSelectorDialog(self.db, self)
        if d.exec() and d.selected_siniiga:
            data = d.selected_siniiga
            self.current_canal = self.db.buscar_o_crear_canal(data['texto']) if 'nuevo' in data else data
            self.current_box = None
            self.refresh_context()

    def flow_new_box(self):
        if not self.current_canal: return
        d = BoxSelectorDialog(self.db, self.current_canal['id'], self)
        if d.exec():
            bid = self.db.crear_o_recuperar_caja(self.current_canal['id'], d.res)
            self.current_box = self.db.get_caja_by_id(bid)
            self.refresh_context()
            self.flow_select_box(self.current_box)

    def flow_select_box(self, box_data):
        if not box_data: return
        self.current_box = box_data
        self.highlight_buttons(box_data['numero_caja'])
        self.refresh_table()
        self.txt_prod.setEnabled(True)
        self.btn_print.setEnabled(False)
        self.lbl_prod_name.setText("LISTO - ESCANEE PRODUCTO")
        self.txt_prod.setFocus()
        self.txt_weight.clear()

    def highlight_buttons(self, num):
        tgt = f"CAJA {num}"
        for i in range(self.box_layout.count()):
            w = self.box_layout.itemAt(i).widget()
            if isinstance(w, QPushButton) and "CAJA" in w.text():
                if tgt in w.text().split('\n')[0]:
                    w.setStyleSheet(styles.STYLE_BOX_ACTIVE)
                else:
                    w.setStyleSheet(styles.STYLE_BOX_OPEN)

    def refresh_context(self):
        if not self.current_canal: return
        stats = self.db.get_resumen_canal(self.current_canal['id'])
        cajas_ab = self.db.get_cajas_abiertas(self.current_canal['id'])
        siniiga_display = self.current_canal['siniiga'].split("-")[0]
        
        num_ab = len(cajas_ab)
        num_ce = stats['total_cajas'] - num_ab
        header = f"SINIIGA: {siniiga_display}\nLOTE: {self.current_canal['lote_dia']}\nCAJAS: {stats['total_cajas']} ({num_ab} ABIERTAS / {num_ce} CERRADAS)"
        
        self.btn_sin.setText(header)
        self.btn_sin.setStyleSheet("background-color:#28a745; color:black; border:3px solid #1e7e34; text-align:left; padding-left:10px; font-size:14px; font-weight:bold;")
        
        while self.box_layout.count():
            it = self.box_layout.takeAt(0)
            w = it.widget()
            if w: w.deleteLater()
            
        for c in cajas_ab:
            b = QPushButton(f"CAJA {c['numero_caja']}\n{c['peso_acumulado']:.1f}kg")
            b.setProperty("class", "boxBtn"); b.setStyleSheet(styles.STYLE_BOX_OPEN)
            cid = c['id']
            b.clicked.connect(lambda ch, cid=cid: self.flow_select_box(self.db.get_caja_by_id(cid)))
            self.box_layout.addWidget(b)
            
        add = QPushButton("+")
        add.setFixedSize(65, 80); add.clicked.connect(self.flow_new_box); self.box_layout.addWidget(add)
        
        if not self.current_box:
            self.btn_print.setEnabled(False); self.txt_prod.setEnabled(False); self.lbl_prod_name.setText("⚠️ SELECCIONE CAJA")
        else:
            still = next((c for c in cajas_ab if c['id'] == self.current_box['id']), None)
            if still: self.flow_select_box(self.db.get_caja_by_id(still['id']))
            else: self.current_box = None; self.refresh_context()

    def refresh_table(self):
        self.table.setRowCount(0)
        if not self.current_box: return
        items = self.db.get_contenido_caja(self.current_box['id'])
        self.table.setRowCount(len(items))
        for r, i in enumerate(items):
            item_n = QTableWidgetItem(str(i['consecutivo']))
            item_n.setData(Qt.UserRole, i['id'])
            self.table.setItem(r, 0, item_n)
            self.table.setItem(r, 1, QTableWidgetItem(i['codigo_producto']))
            self.table.setItem(r, 2, QTableWidgetItem(i['nombre_producto']))
            self.table.setItem(r, 3, QTableWidgetItem(f"{i['peso']:.2f}"))
            self.table.setItem(r, 4, QTableWidgetItem(i['hora']))
        self.lbl_total.setText(f"TOTAL: {self.current_box['peso_acumulado']:.2f} Kg")
        self.table.scrollToBottom()

    def logic_delete_row(self):
        r = self.table.currentRow()
        if r < 0: return
        pid = self.table.item(r, 0).data(Qt.UserRole)
        if QMessageBox.question(self, "Borrar", "¿Eliminar registro?") == QMessageBox.Yes:
            self.db.borrar_pieza(pid)
            self.current_box = self.db.get_caja_by_id(self.current_box['id'])
            self.refresh_context()
            self.refresh_table()

    def logic_reprint(self):
        r = self.table.currentRow()
        if r < 0: return
        pid = self.table.item(r, 0).data(Qt.UserRole)
        p = self.db.get_pieza_by_id(pid)
        self.hw_mgr.print_ticket(p, self.current_box, self.current_canal, {'nombre':p['nombre_producto'],'codigo':p['codigo_producto'],'especie':'REIMP'})

    def update_stats(self):
        s = self.db.get_estadisticas_generales()
        self.k_h.itemAt(1).widget().setText(str(s['piezas_hoy']))
        self.k_p.itemAt(1).widget().setText(f"{s['peso_hoy']:.1f} Kg")

    def update_kpis(self):
        d = datetime.datetime.now() - self.last_activity
        m, s = divmod(int(d.total_seconds()), 60)
        self.k_t.itemAt(1).widget().setText(f"{m:02d}:{s:02d}")

    def flow_open_admin(self):
        panel = AdminPanel(self.db, self); panel.exec()
        if panel.box_to_open_in_main:
            self.current_canal = panel.channel_to_open_in_main
            self.current_box = panel.box_to_open_in_main
            self.refresh_context()
        elif self.current_canal:
            self.refresh_context()
