# main_ui.py
import datetime
import traceback
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
from box_service import BoxService
from product_service import ProductService
from piece_service import PieceService
import styles 
import hardware
from peso_policy import calcular_peso_pieza, calcular_peso_caja, PesoInvalidoError, resolver_peso_cierre


class SessionState:
    def __init__(self):
        self.current_canal = None
        self.current_box = None
        self.current_product = None
        self.last_activity = datetime.datetime.now()


class MainUI(QMainWindow):
    BOX_BUTTON_SIZE = (125, 80)

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.setWindowTitle("SISTEMA DE ETIQUETADO TIF - V4.1")
        self.setMinimumSize(900, 600)
        self.setStyleSheet(styles.MAIN_STYLESHEET)
        
        self.db = DatabaseManager()
        self.product_service = ProductService(self.db)
        self.piece_service = PieceService(self.db, self.product_service)
        self.hw_mgr = hardware.HardwareManager(config.get('HARDWARE', 'PRINTER_NAME', fallback='ZDesigner'))
        self.box_service = BoxService(self.db, self.hw_mgr)

        self.state = SessionState()
        
        # Estado de hardware
        self.scale_active = False 
        self.th_scale = None
        self.tm_demo = None
        
        self.init_ui()
        self.update_ui_state()
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
        
        self.btn_sin = QPushButton("SINIIGA: ---\nLOTE: ---\nCAJAS: 0 (0 ABIERTAS / 0 CERRADAS)")
        self.btn_sin.setObjectName("btnSiniiga")
        self.btn_sin.setFixedSize(260, 95)
        self.btn_sin.setStyleSheet("text-align:left; padding:8px 10px;")
        self.btn_sin.clicked.connect(self.open_siniiga_flow)
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

        self.lbl_contexto_activo = QLabel()
        self.lbl_contexto_activo.setObjectName("LblContextoActivo")
        self.lbl_contexto_activo.setStyleSheet(
            "font-size: 18px; "
            "font-weight: bold; "
            "color: black; "
            "background-color: #f0f0f0; "
            "border: 2px solid #cfcfcf; "
            "border-radius: 6px; "
            "padding: 10px;"
        )
        self.lbl_contexto_activo.setWordWrap(True)
        lv.addWidget(self.lbl_contexto_activo)
        self.update_active_context_label()

        self.lbl_estado = QLabel()
        self.lbl_estado.setObjectName("LblEstadoOperativo")
        self.lbl_estado.setFixedHeight(50)
        self.lbl_estado.setAlignment(Qt.AlignCenter)
        lv.addWidget(self.lbl_estado)
        
        kf = QFrame()
        kf.setObjectName("KpiPanel")
        kh = QHBoxLayout(kf)
        self.k_h = self.mk_kpi("PZAS HOY", "0")
        self.k_p = self.mk_kpi("PESO HOY", "0.0")
        self.k_t = self.mk_kpi("CAJA ACTUAL", "0 pzas.")
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
        self.txt_weight.returnPressed.connect(self.save_and_print_piece)
        self.txt_weight.textChanged.connect(self.update_operational_status)
        lv.addWidget(self.txt_weight)
        
        self.btn_print = QPushButton("IMPRIMIR ETIQUETA")
        self.btn_print.setObjectName("BtnPrint")
        self.btn_print.setFixedHeight(85)
        self.btn_print.setEnabled(False)
        self.btn_print.clicked.connect(self.save_and_print_piece)
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
        btn_del.clicked.connect(self.delete_selected_piece)
        
        btn_rep = QPushButton("🏷️ REIMPRIMIR")
        btn_rep.setStyleSheet(f"background:{styles.COLOR_BTN_WARN}; color:black;")
        btn_rep.clicked.connect(self.reprint_selected_piece)
        al.addWidget(btn_del)
        al.addWidget(btn_rep)
        rv.addLayout(al)
        
        self.btn_cls = QPushButton("📦 CERRAR CAJA / ETIQUETA MASTER")
        self.btn_cls.setObjectName("BtnClose")
        self.btn_cls.setFixedHeight(70)
        self.btn_cls.clicked.connect(self.close_box_flow)
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

    def update_ui_state(self):
        has_canal = self.state.current_canal is not None
        has_box = self.state.current_box is not None
        has_product = self.state.current_product is not None

        self.txt_prod.setEnabled(has_box)
        self.txt_weight.setEnabled(has_box and has_product)
        self.btn_print.setEnabled(has_box and has_product)
        self.btn_cls.setEnabled(has_box)
        self.table.setEnabled(has_box)
        self.update_operational_status()

    def update_operational_status(self):
        peso_valido = self._calcular_peso_final(mostrar_errores=False) is not None

        if not self.state.current_canal:
            estado = "SIN_CANAL"
        elif not self.state.current_box:
            estado = "SIN_CAJA"
        elif not self.state.current_product:
            estado = "SIN_PRODUCTO"
        elif not peso_valido:
            estado = "SIN_PESO"
        else:
            estado = "LISTO"

        if estado == "SIN_CANAL":
            texto = "Seleccione SINIIGA"
            color = "#dc3545"
        elif estado == "SIN_CAJA":
            texto = "Seleccione una caja"
            color = "#dc3545"
        elif estado == "SIN_PRODUCTO":
            texto = "Escanee o ingrese un producto"
            color = "#ffc107"
        elif estado == "SIN_PESO":
            texto = "Ingrese el peso de la pieza"
            color = "#ffc107"
        else:
            texto = "Listo para imprimir"
            color = "#28a745"

        self.lbl_estado.setStyleSheet(
            f"""
background-color: {color};
color: black;
font-weight: bold;
font-size: 16px;
border-radius: 6px;
"""
        )
        self.lbl_estado.setText(texto)

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
        return self.product_service.get_producto_activo(code)

    def logic_validate_product(self):
        code = self.txt_prod.text().strip()
        if not code:
            return
        p = self._buscar_producto(code)
        if p:
            self.state.current_product = p
            self.lbl_prod_name.setText(p['nombre'])
            self.lbl_prod_name.setStyleSheet("color:#008000;")
            self.btn_print.setEnabled(True)
            if not self.scale_active:
                self.txt_weight.clear()
        else:
            self.state.current_product = None
            prod_inactivo = self.product_service.get_producto(code)
            if prod_inactivo and prod_inactivo.get('estado') == 'INACTIVO':
                self.lbl_prod_name.setText("PRODUCTO INACTIVO")
                self.lbl_prod_name.setStyleSheet("color: #cc0000;")
            else:
                self.lbl_prod_name.setText("NO ENCONTRADO")
            self.btn_print.setEnabled(False)
            self.txt_prod.selectAll()
        self.update_active_context_label()
        self.update_ui_state()
        self.update_operational_status()
        if p:
            QTimer.singleShot(0, self._focus_weight)

    def _focus_weight(self):
        self.txt_weight.setFocus()
        self.txt_weight.selectAll()

    def _calcular_peso_final(self, mostrar_errores=True):
        txt_w = self.txt_weight.text().strip()
        if not txt_w:
            return None

        try:
            raw_weight = float(txt_w)
        except ValueError:
            if mostrar_errores:
                QMessageBox.warning(self, "Peso", "Valor inválido.")
            return None

        aplicar_correccion_checkbox = self.chk_apply_corr.isChecked()

        try:
            peso_final = calcular_peso_pieza(raw_weight, aplicar_correccion_checkbox)
        except PesoInvalidoError as e:
            if mostrar_errores:
                QMessageBox.warning(self, "Error de peso", str(e))
            return None

        return peso_final

    def _register_piece(self, final_w):
        consec, pid = self.piece_service.registrar_pieza(
            self.state.current_box['id'],
            self.state.current_product['codigo'],
            self.state.current_product['nombre'],
            final_w
        )
        return pid

    def _print_piece(self, pid):
        full = self.db.get_pieza_by_id(pid)
        ok, msg = self.hw_mgr.print_ticket(
            full,
            self.state.current_box,
            self.state.current_canal,
            self.state.current_product
        )
        if not ok:
            QMessageBox.critical(self, "Impresora", msg)

    def _validate_weight(self):
        return self._calcular_peso_final()

    def _apply_weight_policy(self, final_w):
        return final_w

    def _post_print_refresh(self):
        self.state.current_box = self.db.get_caja_by_id(self.state.current_box['id'])
        self.state.last_activity = datetime.datetime.now()
        self.refresh_table()
        self.update_stats()
        self.highlight_buttons(self.state.current_box['numero_caja'])
        self.update_ui_state()

        if self.scale_active:
            self.txt_weight.setFocus()
            return

        self.txt_weight.clear()
        if self.chk_lock_prod.isChecked():
            self.txt_weight.setFocus()
            return

        self.txt_prod.clear()
        self.state.current_product = None
        self.lbl_prod_name.setText("LISTO - ESCANEE PRODUCTO")
        self.lbl_prod_name.setStyleSheet("color: #000;")
        self.btn_print.setEnabled(False)
        self.update_operational_status()
        self.update_active_context_label()
        self.update_ui_state()
        self.txt_prod.setFocus()

    def save_and_print_piece(self):
        if not self.state.current_box or not self.state.current_product:
            return

        final_w = self._validate_weight()
        if final_w is None:
            return

        final_w = self._apply_weight_policy(final_w)
        if not puede_agregar_pieza(self.state.current_box['estado']):
            return

        try:
            pid = self._register_piece(final_w)
            self._print_piece(pid)
        except ValueError as e:
            QMessageBox.warning(self, "Error", str(e))
            return

        self._post_print_refresh()
        self.update_operational_status()

    def _ejecutar_cierre_caja(self, peso_final, contenido):
        self.box_service.cerrar_caja(
            self.state.current_box['id'],
            self.state.current_canal,
            contenido,
            peso_final
        )

    def _validate_close_conditions(self):
        if not self.state.current_box:
            return None
        if not puede_cerrar_caja(self.state.current_box['estado']):
            return
        contenido = self.db.get_contenido_caja(self.state.current_box['id'])
        if not contenido:
            return None
        return contenido

    def _request_manual_override(self, peso_calc):
        peso_f, ok = QInputDialog.getDouble(
            self,
            "Peso Final",
            f"Suma: {peso_calc:.2f} Kg",
            value=peso_calc,
            minValue=0.1,
            maxValue=20.0,
            decimals=2
        )
        if not ok:
            return None

        try:
            return resolver_peso_cierre(peso_calc, peso_f)
        except PesoInvalidoError as e:
            QMessageBox.warning(self, "Error de peso", str(e))
            return None

    def _execute_close(self, peso_final, contenido):
        self._ejecutar_cierre_caja(peso_final, contenido)
        self.state.current_box = None
        self.refresh_context()

    def close_box_flow(self):
        contenido = self._validate_close_conditions()
        if not contenido:
            return

        peso_calc = calcular_peso_caja(contenido)
        resultado = self._request_manual_override(peso_calc)
        if not resultado:
            return

        if resultado["hay_diferencia"]:
            QMessageBox.warning(
                self,
                "Advertencia",
                f"El peso final difiere de la suma calculada por {resultado['delta']:.2f} kg"
            )

        self._execute_close(resultado["peso_final"], contenido)

    def open_siniiga_flow(self):
        d = SiniigaSelectorDialog(self.db, self)
        if d.exec() and d.selected_siniiga:
            data = d.selected_siniiga
            self.state.current_canal = self.db.buscar_o_crear_canal(data['texto']) if 'nuevo' in data else data
            self.state.current_box = None
            self.state.current_product = None
            self.refresh_context()
            self.update_ui_state()

    def open_new_box_flow(self):
        if not self.state.current_canal:
            return
        d = BoxSelectorDialog(self.db, self.state.current_canal['id'], self)
        if d.exec():
            bid = self.box_service.crear_o_recuperar_caja(self.state.current_canal['id'], d.res)
            self.state.current_box = self.db.get_caja_by_id(bid)
            self.refresh_context()
            self.select_box(self.state.current_box)

    def select_box(self, box_data):
        if not box_data:
            return
        self.state.current_box = box_data
        self.state.current_product = None
        self.highlight_buttons(box_data['numero_caja'])
        self.refresh_table()
        self.txt_prod.setEnabled(True)
        self.btn_print.setEnabled(False)
        self.lbl_prod_name.setText("LISTO - ESCANEE PRODUCTO")
        self.txt_prod.setFocus()
        self.txt_weight.clear()
        self.update_active_context_label()
        self.update_ui_state()

    def highlight_buttons(self, num):
        tgt = f"CAJA {num}"
        for i in range(self.box_layout.count()):
            w = self.box_layout.itemAt(i).widget()
            if not isinstance(w, QPushButton):
                continue

            if w.property("box_action") == "new":
                w.setStyleSheet(styles.STYLE_BOX_NEW)
                continue

            if w.property("box_estado") == ESTADO_CERRADA:
                w.setStyleSheet(styles.STYLE_BOX_CLOSED)
                continue

            if "CAJA" in w.text():
                if tgt in w.text().split('\n')[0]:
                    w.setStyleSheet(styles.STYLE_BOX_ACTIVE)
                else:
                    w.setStyleSheet(styles.STYLE_BOX_OPEN)

    def refresh_context(self):
        if not self.state.current_canal:
            self.update_ui_state()
            self.update_operational_status()
            return
        stats = self.db.get_resumen_canal(self.state.current_canal['id'])
        cajas_canal = self.db.get_all_cajas_canal(self.state.current_canal['id'])
        siniiga_display = self.state.current_canal['siniiga'].split("-")[0]
        
        num_ab = sum(1 for c in cajas_canal if c['estado'] == ESTADO_ABIERTA)
        num_ce = sum(1 for c in cajas_canal if c['estado'] == ESTADO_CERRADA)
        header = f"SINIIGA: {siniiga_display}\nLOTE: {self.state.current_canal['lote_dia']}\nCAJAS: {stats['total_cajas']} ({num_ab} A / {num_ce} C)"
        
        self.btn_sin.setText(header)
        self.btn_sin.setStyleSheet(
            "background-color:#28a745; color:black; border:3px solid #1e7e34; "
            "text-align:left; padding:8px 10px; font-size:14px; font-weight:bold;"
        )
        
        self._rebuild_box_buttons(cajas_canal)
        self._sync_selected_box(cajas_canal)
        self.update_active_context_label()
        self.update_ui_state()
        self.update_operational_status()

    def update_active_context_label(self):
        siniiga_actual = "---"
        if self.state.current_canal:
            siniiga_actual = self.state.current_canal.get('siniiga', '---').split("-")[0]

        caja_actual = "---"
        if self.state.current_box:
            caja_actual = str(self.state.current_box.get('numero_caja', '---'))

        producto_actual = "---"
        if self.state.current_product:
            producto_actual = self.state.current_product.get('nombre', '---')

        self.lbl_contexto_activo.setText(
            f"SINIIGA: {siniiga_actual} | CAJA: {caja_actual} | PROD: {producto_actual}"
        )

    def _build_box_button(self, caja_data):
        if caja_data['estado'] == ESTADO_CERRADA:
            total_piezas = 0
            if 'total_piezas' in caja_data.keys() and caja_data['total_piezas'] is not None:
                total_piezas = caja_data['total_piezas']
            btn_text = f"CAJA {caja_data['numero_caja']}\nCERRADA\n{total_piezas} pzas."
        else:
            btn_text = f"CAJA {caja_data['numero_caja']}\n{caja_data['peso_acumulado']:.1f}kg"

        btn = QPushButton(btn_text)
        btn.setProperty("class", "boxBtn")
        btn.setProperty("box_estado", caja_data['estado'])
        btn.setFixedSize(*self.BOX_BUTTON_SIZE)

        if caja_data['estado'] == ESTADO_CERRADA:
            btn.setStyleSheet(styles.STYLE_BOX_CLOSED)
            btn.setEnabled(False)
            return btn

        btn.setStyleSheet(styles.STYLE_BOX_OPEN)
        cid = caja_data['id']
        btn.clicked.connect(lambda ch, cid=cid: self.select_box(self.db.get_caja_by_id(cid)))
        return btn

    def _build_new_box_button(self):
        btn = QPushButton("NUEVA CAJA")
        btn.setProperty("class", "boxBtn")
        btn.setProperty("box_action", "new")
        btn.setFixedSize(*self.BOX_BUTTON_SIZE)
        btn.setStyleSheet(styles.STYLE_BOX_NEW)
        btn.clicked.connect(self.open_new_box_flow)
        return btn

    def _rebuild_box_buttons(self, cajas_canal):
        while self.box_layout.count():
            it = self.box_layout.takeAt(0)
            w = it.widget()
            if w:
                w.deleteLater()

        for c in sorted(cajas_canal, key=lambda x: x['numero_caja']):
            self.box_layout.addWidget(self._build_box_button(c))

        self.box_layout.addWidget(self._build_new_box_button())

    def _sync_selected_box(self, cajas_canal):
        if not self.state.current_box:
            self.btn_print.setEnabled(False)
            self.txt_prod.setEnabled(False)
            self.lbl_prod_name.setText("⚠️ SELECCIONE CAJA")
            self.update_active_context_label()
            return

        still = next(
            (
                c for c in cajas_canal
                if c['id'] == self.state.current_box['id'] and c['estado'] == ESTADO_ABIERTA
            ),
            None
        )
        if still:
            self.select_box(self.db.get_caja_by_id(still['id']))
        else:
            self.state.current_box = None
            self.refresh_context()

    def refresh_table(self):
        self.table.setRowCount(0)
        if not self.state.current_box:
            return
        items = self._fetch_box_items()
        self._render_table(items)

    def _fetch_box_items(self):
        return self.db.get_contenido_caja(self.state.current_box['id'])

    def _render_table(self, items):
        self.table.setRowCount(len(items))
        for r, i in enumerate(items):
            item_n = QTableWidgetItem(str(i['consecutivo']))
            item_n.setData(Qt.UserRole, i['id'])
            self.table.setItem(r, 0, item_n)
            self.table.setItem(r, 1, QTableWidgetItem(i['codigo_producto']))
            self.table.setItem(r, 2, QTableWidgetItem(i['nombre_producto']))
            self.table.setItem(r, 3, QTableWidgetItem(f"{i['peso']:.2f}"))
            self.table.setItem(r, 4, QTableWidgetItem(i['hora']))
        self.lbl_total.setText(f"TOTAL: {self.state.current_box['peso_acumulado']:.2f} Kg")
        self.table.scrollToBottom()

    def delete_selected_piece(self):
        r = self.table.currentRow()
        if r < 0:
            return
        pid = self.table.item(r, 0).data(Qt.UserRole)
        if QMessageBox.question(self, "Borrar", "¿Eliminar registro?") == QMessageBox.Yes:
            self.db.borrar_pieza(pid)
            self.state.current_box = self.db.get_caja_by_id(self.state.current_box['id'])
            self.refresh_context()
            self.refresh_table()

    def reprint_selected_piece(self):
        r = self.table.currentRow()
        if r < 0:
            return
        pid = self.table.item(r, 0).data(Qt.UserRole)
        p = self.db.get_pieza_by_id(pid)
        self.hw_mgr.print_ticket(
            p,
            self.state.current_box,
            self.state.current_canal,
            {'nombre': p['nombre_producto'], 'codigo': p['codigo_producto'], 'especie': 'REIMP'}
        )

    def update_stats(self):
        s = self.db.get_estadisticas_generales()
        self.k_h.itemAt(1).widget().setText(str(s['piezas_hoy']))
        self.k_p.itemAt(1).widget().setText(f"{s['peso_hoy']:.1f} Kg")

    def update_kpis(self):
        self.update_stats()
        if not self.state.current_box:
            self.k_t.itemAt(1).widget().setText("-- pzas.")
            return
        piezas = (
            self.state.current_box.get('num_piezas')
            or self.state.current_box.get('total_piezas')
            or 0
        )
        self.k_t.itemAt(1).widget().setText(f"{piezas} pzas.")

    def flow_open_admin(self):
        print("ADMIN CLICKED")
        try:
            print("Creating AdminPanel")
            panel = AdminPanel(self.db, self)
            print("Before exec")
            panel.exec()
            print("After exec")
            if panel.box_to_open_in_main:
                self.state.current_canal = panel.channel_to_open_in_main
                self.state.current_box = panel.box_to_open_in_main
                self.refresh_context()
            elif self.state.current_canal:
                self.refresh_context()
        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(self, "Error en ADMIN", f"Ocurrió un error al abrir ADMIN:\n{e}")
