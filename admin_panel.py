import sys
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel, 
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, 
    QGroupBox, QFormLayout, QSplitter, QTreeWidget, QTreeWidgetItem, 
    QStackedWidget, QFrame, QAbstractItemView, QDoubleSpinBox, QGridLayout
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont, QGuiApplication

import hardware 
from box_domain import (
    ESTADO_ABIERTA,
    ESTADO_CERRADA,
    puede_cerrar_caja,
    puede_reabrir_caja
)
from box_service import cerrar_caja, reabrir_caja
from piece_service import PieceService
from product_service import ProductService

# --- ESTILOS "HEAVY INDUSTRY" PARA ADMIN ---
ADMIN_STYLE = """
QDialog, QWidget { 
    background-color: #e0e0e0; 
    color: #000000; 
    font-family: 'Segoe UI', 'Segoe UI Emoji'; 
}

/* ÁRBOL Y ESTRUCTURA */
QTreeWidget { 
    background-color: #ffffff; 
    color: #000000;
    border: 2px solid #666; /* Borde visible */
    font-size: 13px; 
}
QTreeWidget::item { 
    padding: 6px; 
    border-bottom: 1px solid #eee; /* Líneas entre items */
}
QTreeWidget::item:selected { background-color: #005bb5; color: white; }

/* DIVISORES */
QSplitter::handle {
    background-color: #999;
    border: 1px solid #777;
    width: 6px; /* Divisor grueso */
}

/* TABLAS */
QTableWidget { 
    background-color: #ffffff; 
    color: #000000;
    border: 2px solid #666; 
    font-size: 12px; 
    gridline-color: #ccc; 
}
QHeaderView::section { 
    background-color: #444; 
    color: #fff; 
    padding: 5px; 
    font-weight: bold; 
    border-right: 1px solid #777;
}

/* PANELES AGRUPADORES */
QGroupBox { 
    font-weight: bold; 
    border: 2px solid #888; /* Borde fuerte */
    border-radius: 4px; 
    margin-top: 20px; 
    background: #dcdcdc; 
    padding-top: 15px;
}
QGroupBox::title { 
    subcontrol-origin: margin; 
    left: 10px; 
    padding: 0 5px; 
    background-color: #dcdcdc; /* Para que el titulo corte la linea */
    color: #333;
}

/* BADGES DE ESTADO */
QLabel#BadgeClosed { 
    background-color: #b30000; color: white; border: 2px solid #500; border-radius: 4px; 
    padding: 4px 8px; font-weight: bold; font-size: 12px; 
}
QLabel#BadgeOpen { 
    background-color: #28a745; color: white; border: 2px solid #1e5c30; border-radius: 4px; 
    padding: 4px 8px; font-weight: bold; font-size: 12px; 
}

/* BOTONES CON RELIEVE */
QPushButton { 
    color: #000000;
    border: 2px solid #666; 
    border-bottom: 3px solid #444; /* Efecto botón físico */
    background: #fcfcfc; 
    min-height: 32px; 
    font-size: 11px; 
    font-weight: bold;
    border-radius: 4px;
}
QPushButton:hover { background: #e0e0e0; }
QPushButton:pressed { 
    border-bottom: 2px solid #444; /* Fix: Solo cambiamos borde, quitamos transform */
}

QPushButton#BtnAction { background-color: #005bb5; color: white; border: 2px solid #003e7e; }
QPushButton#BtnDanger { background-color: #dc3545; color: white; border: 2px solid #7a1c25; }
QPushButton#BtnSuccess { background-color: #28a745; color: white; border: 2px solid #145226; }
"""

class AdminPanel(QDialog):
    data_changed = Signal()

    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.piece_service = PieceService(self.db)
        self.product_service = ProductService(self.db)
        self.hw = hardware.HardwareManager() 
        
        self.box_to_open_in_main = None
        self.channel_to_open_in_main = None
        
        self.current_canal_data = None
        self.current_box_data = None
        
        self.setup_window()
        self.setup_ui()
        self.load_tree_data()

    def setup_window(self):
        self.setWindowTitle("PANEL DE GESTIÓN Y SUPERVISIÓN")
        self.setStyleSheet(ADMIN_STYLE)
        self.setWindowFlags(Qt.Window | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint)
        
        screen = QGuiApplication.primaryScreen().availableGeometry()
        w, h = min(1150, screen.width() * 0.95), min(700, screen.height() * 0.9)
        self.resize(w, h)

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        
        nav = QHBoxLayout()
        self.btn_nav_super = QPushButton("👁️ SUPERVISIÓN")
        self.btn_nav_super.setCheckable(True); self.btn_nav_super.setChecked(True)
        self.btn_nav_super.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        
        self.btn_nav_catalog = QPushButton("📦 CATÁLOGO")
        self.btn_nav_catalog.setCheckable(True)
        self.btn_nav_catalog.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        
        btn_exit = QPushButton("SALIR")
        btn_exit.clicked.connect(self.reject)
        
        nav.addWidget(self.btn_nav_super); nav.addWidget(self.btn_nav_catalog); nav.addStretch(); nav.addWidget(btn_exit)
        main_layout.addLayout(nav)

        self.stack = QStackedWidget()
        self.stack.addWidget(self.create_supervision_view()) 
        self.stack.addWidget(self.create_catalog_view())     
        main_layout.addWidget(self.stack)

        self.stack.currentChanged.connect(self.on_tab_changed)

    def on_tab_changed(self, idx):
        self.btn_nav_super.setChecked(idx == 0)
        self.btn_nav_catalog.setChecked(idx == 1)
        active_st = "background-color: #444; color: white; border: 2px solid #222;"
        normal_st = "background-color: #fff; color: black;"
        self.btn_nav_super.setStyleSheet(active_st if idx == 0 else normal_st)
        self.btn_nav_catalog.setStyleSheet(active_st if idx == 1 else normal_st)

    def create_supervision_view(self):
        panel = QWidget(); lay = QHBoxLayout(panel)
        splitter = QSplitter(Qt.Horizontal)
        
        left_w = QWidget(); lv = QVBoxLayout(left_w); lv.setContentsMargins(0,0,0,0)
        lv.addWidget(QLabel("Jerarquía:"))
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Elemento"])
        self.tree.itemClicked.connect(self.on_tree_select)
        lv.addWidget(self.tree)
        btn_ref = QPushButton("🔄 REFRESCAR"); btn_ref.clicked.connect(self.load_tree_data)
        lv.addWidget(btn_ref)
        splitter.addWidget(left_w)
        
        self.detail_stack = QStackedWidget()
        self.detail_stack.addWidget(QLabel("Seleccione un elemento del árbol...")) 
        self.detail_stack.addWidget(self.setup_siniiga_panel())         
        self.detail_stack.addWidget(self.setup_caja_panel())            
        splitter.addWidget(self.detail_stack)
        
        splitter.setSizes([300, 850])
        lay.addWidget(splitter)
        return panel

    def load_tree_data(self):
        self.tree.clear()
        canales = self.db.get_all_canales(incluir_cerrados=True)
        for c in canales:
            item_c = QTreeWidgetItem(self.tree)
            icon = "🟢" if c['estado'] == 'ACTIVO' else "🔒"
            item_c.setText(0, f"{icon} {c['siniiga']}")
            item_c.setData(0, Qt.UserRole, {'type': 'canal', 'id': c['id']})
            
            cajas = self.db.get_all_cajas_canal(c['id'], incluir_cerradas=True)
            for b in cajas:
                item_b = QTreeWidgetItem(item_c)
                st = "📦" if puede_cerrar_caja(b['estado']) else "🔒"
                item_b.setText(0, f"    {st} Caja #{b['numero_caja']} ({b['num_piezas']})")
                item_b.setData(0, Qt.UserRole, {'type': 'caja', 'id': b['id'], 'pid': c['id']})
        self.tree.expandAll()

    def on_tree_select(self, item, col):
        data = item.data(0, Qt.UserRole)
        if not data: return
        if data['type'] == 'canal':
            self.current_canal_data = self.db.get_canal_by_id(data['id'])
            self.show_canal_details()
        elif data['type'] == 'caja':
            self.current_box_data = self.db.get_caja_by_id(data['id'])
            self.current_canal_data = self.db.get_canal_by_id(data['pid'])
            self.show_box_details()

    def setup_siniiga_panel(self):
        w = QWidget(); l = QVBoxLayout(w)
        self.lbl_s_title = QLabel("SINIIGA")
        self.lbl_s_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #005bb5;")
        l.addWidget(self.lbl_s_title)
        
        gb = QGroupBox("Resumen"); fl = QFormLayout(gb)
        self.lbl_s_cajas = QLabel("-"); self.lbl_s_peso = QLabel("-")
        fl.addRow("Cajas:", self.lbl_s_cajas); fl.addRow("Peso:", self.lbl_s_peso)
        l.addWidget(gb)
        
        self.btn_s_toggle = QPushButton("ACCION")
        self.btn_s_toggle.clicked.connect(self.action_toggle_canal)
        l.addWidget(self.btn_s_toggle); l.addStretch()
        return w

    def setup_caja_panel(self):
        w = QWidget(); l = QVBoxLayout(w)
        top = QHBoxLayout()
        self.lbl_b_badge = QLabel("ESTADO"); self.lbl_b_badge.setFixedHeight(25)
        self.lbl_b_title = QLabel("CAJA #X")
        self.lbl_b_title.setStyleSheet("font-size: 22px; font-weight: bold;")
        top.addWidget(self.lbl_b_badge); top.addWidget(self.lbl_b_title); top.addStretch()
        l.addLayout(top)
        
        # KPI GRID con marco
        grid = QGridLayout()
        def mk_val(): 
            l = QLabel("-"); l.setStyleSheet("font-size: 16px; font-weight: bold; color: #000;"); return l
        self.kv_peso = mk_val(); self.kv_pzas = mk_val()
        grid.addWidget(QLabel("PESO:"), 0, 0); grid.addWidget(self.kv_peso, 0, 1)
        grid.addWidget(QLabel("PIEZAS:"), 0, 2); grid.addWidget(self.kv_pzas, 0, 3)
        frm = QFrame(); frm.setLayout(grid); frm.setStyleSheet("background: #fdfdfd; border: 2px solid #aaa; border-radius: 4px;")
        l.addWidget(frm)

        self.tbl_p = QTableWidget(0, 4)
        self.tbl_p.setHorizontalHeaderLabels(["#", "Producto", "Peso (Kg)", "Hora"])
        self.tbl_p.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tbl_p.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl_p.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tbl_p.itemSelectionChanged.connect(self.on_piece_selection_changed)
        l.addWidget(self.tbl_p)

        self.edit_piece_panel = QGroupBox("Edición de pieza")
        edit_layout = QVBoxLayout(self.edit_piece_panel)
        edit_layout.addWidget(QLabel("Editar pieza seleccionada"))

        self.spn_piece_weight = QDoubleSpinBox()
        self.spn_piece_weight.setDecimals(2)
        self.spn_piece_weight.setMinimum(0.01)
        self.spn_piece_weight.setSingleStep(0.01)
        edit_layout.addWidget(self.spn_piece_weight)

        edit_buttons = QHBoxLayout()
        self.btn_save_piece = QPushButton("Guardar cambios")
        self.btn_save_piece.setObjectName("BtnAction")
        self.btn_save_piece.clicked.connect(self.action_save_piece)
        self.btn_delete_piece = QPushButton("Borrar pieza")
        self.btn_delete_piece.setObjectName("BtnDanger")
        self.btn_delete_piece.clicked.connect(self.action_delete_piece)
        edit_buttons.addWidget(self.btn_save_piece)
        edit_buttons.addWidget(self.btn_delete_piece)
        edit_layout.addLayout(edit_buttons)
        l.addWidget(self.edit_piece_panel)

        act_box = QGroupBox("Acciones Disponibles")
        hl = QHBoxLayout(act_box)
        self.btn_prod = QPushButton("🚀 PRODUCCIÓN"); self.btn_prod.setObjectName("BtnSuccess")
        self.btn_prod.clicked.connect(self.action_jump_prod)
        
        self.btn_reprint_tag = QPushButton("🏷️ ETIQUETA"); self.btn_reprint_tag.setObjectName("BtnAction")
        self.btn_reprint_tag.clicked.connect(self.action_reprint_tag)
        
        self.btn_print_master = QPushButton("📦 MASTER"); self.btn_print_master.setObjectName("BtnAction")
        self.btn_print_master.clicked.connect(self.action_reprint_master)
        
        self.btn_toggle_box = QPushButton("CERRAR"); self.btn_toggle_box.clicked.connect(self.action_toggle_box)
        self.btn_del_box = QPushButton("🗑️ BORRAR"); self.btn_del_box.setObjectName("BtnDanger")
        self.btn_del_box.clicked.connect(self.action_delete_box)

        hl.addWidget(self.btn_prod); hl.addWidget(self.btn_reprint_tag)
        hl.addWidget(self.btn_print_master); hl.addWidget(self.btn_toggle_box)
        hl.addStretch(); hl.addWidget(self.btn_del_box)
        l.addWidget(act_box)
        return w

    def show_canal_details(self):
        c = self.current_canal_data
        stats = self.db.get_resumen_canal(c['id'])
        self.lbl_s_title.setText(f"SINIIGA: {c['siniiga']}")
        self.lbl_s_cajas.setText(str(stats['total_cajas']))
        self.lbl_s_peso.setText(f"{stats['peso_total']:.2f} Kg")
        self.btn_s_toggle.setText("🔒 ARCHIVAR" if c['estado'] == 'ACTIVO' else "🔓 REACTIVAR")
        self.detail_stack.setCurrentIndex(1)

    def show_box_details(self):
        bid = self.current_box_data['id']
        b = self.db.get_caja_by_id(bid) 
        self.current_box_data = b 
        self.lbl_b_title.setText(f"CAJA #{b['numero_caja']}")
        is_open = (b['estado'] == ESTADO_ABIERTA)
        
        self.lbl_b_badge.setText(b['estado'])
        self.lbl_b_badge.setObjectName("BadgeOpen" if is_open else "BadgeClosed")
        self.lbl_b_badge.style().unpolish(self.lbl_b_badge); self.lbl_b_badge.style().polish(self.lbl_b_badge)
        
        self.kv_peso.setText(f"{b['peso_acumulado']:.2f} kg")
        self.kv_pzas.setText(str(b['num_piezas']))

        piezas = self.db.get_contenido_caja(bid)
        self.tbl_p.setRowCount(0)
        for p in piezas:
            r = self.tbl_p.rowCount(); self.tbl_p.insertRow(r)
            item_num = QTableWidgetItem(str(p['consecutivo']))
            item_num.setData(Qt.UserRole, p['id'])
            self.tbl_p.setItem(r, 0, item_num)
            self.tbl_p.setItem(r, 1, QTableWidgetItem(p['nombre_producto']))
            self.tbl_p.setItem(r, 2, QTableWidgetItem(f"{p['peso']:.2f}"))
            self.tbl_p.setItem(r, 3, QTableWidgetItem(p['hora']))

        self.tbl_p.clearSelection()
        self.spn_piece_weight.setValue(0.01)
        self.update_piece_edit_panel_state(is_open)
            
        self.btn_toggle_box.setText("🔒 CERRAR" if is_open else "🔓 REABRIR")
        self.btn_toggle_box.setEnabled(True)
        self.btn_print_master.setVisible(not is_open)
        self.btn_del_box.setEnabled(is_open)
        self.detail_stack.setCurrentIndex(2)

    def update_piece_edit_panel_state(self, is_open):
        self.edit_piece_panel.setVisible(is_open)
        self.edit_piece_panel.setEnabled(is_open)

    def on_piece_selection_changed(self):
        row = self.tbl_p.currentRow()
        if row < 0:
            return

        item_weight = self.tbl_p.item(row, 2)
        if item_weight:
            self.spn_piece_weight.setValue(float(item_weight.text()))

    def action_save_piece(self):
        row = self.tbl_p.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Aviso", "Seleccione una pieza para editar.")
            return

        pieza_id = self.tbl_p.item(row, 0).data(Qt.UserRole)
        nuevo_peso = self.spn_piece_weight.value()

        try:
            self.piece_service.editar_pieza(pieza_id, nuevo_peso)
        except ValueError as e:
            QMessageBox.warning(self, "Aviso", str(e))
            return

        self.show_box_details()
        self.data_changed.emit()

    def action_delete_piece(self):
        row = self.tbl_p.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Aviso", "Seleccione una pieza para borrar.")
            return

        pieza_id = self.tbl_p.item(row, 0).data(Qt.UserRole)

        if QMessageBox.question(self, "Confirmar borrado", "¿Desea borrar la pieza seleccionada?") != QMessageBox.Yes:
            return

        try:
            self.piece_service.borrar_pieza(pieza_id)
        except ValueError as e:
            QMessageBox.warning(self, "Aviso", str(e))
            return

        self.show_box_details()
        self.data_changed.emit()

    def action_reprint_tag(self):
        row = self.tbl_p.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Aviso", "Seleccione una fila de la tabla.")
            return
        pid = self.tbl_p.item(row, 0).data(Qt.UserRole)
        pieza = self.db.get_pieza_by_id(pid)
        if pieza:
            mock = {'nombre': pieza['nombre_producto'], 'codigo': pieza['codigo_producto'], 'especie': 'REIMP'}
            self.hw.print_ticket(pieza, self.current_box_data, self.current_canal_data, mock)

    def action_reprint_master(self):
        if not self.current_box_data: return
        piezas = self.db.get_contenido_caja(self.current_box_data['id'])
        if piezas:
            info = f"Caja: {self.current_box_data['numero_caja']}\nPeso: {self.current_box_data['peso_acumulado']:.2f} kg\nPiezas: {len(piezas)}"
            if QMessageBox.question(self, "Reimprimir Master", f"{info}\n\n¿Confirmar?") == QMessageBox.Yes:
                self.hw.print_master(self.current_box_data, self.current_canal_data, piezas)

    def action_jump_prod(self):
        bid = self.current_box_data['id']
        box_fresh = self.db.get_caja_by_id(bid)
        if puede_reabrir_caja(box_fresh['estado']):
            if QMessageBox.question(self, "Reabrir", "¿Reabrir caja?") == QMessageBox.Yes:
                reabrir_caja(self.db, box_fresh)
                box_fresh = self.db.get_caja_by_id(bid)
            else: return
        self.box_to_open_in_main = box_fresh
        self.channel_to_open_in_main = self.current_canal_data
        self.accept()

    def action_toggle_box(self):
        bid = self.current_box_data['id']
        box_fresh = self.db.get_caja_by_id(bid)

        if box_fresh['estado'] == ESTADO_ABIERTA:
            contenido = self.db.get_contenido_caja(bid)
            if not contenido:
                QMessageBox.warning(self, "Aviso", "La caja no tiene piezas para cerrar.")
                return
            peso_final = box_fresh['peso_acumulado']
            cerrar_caja(self.db, self.hw, box_fresh, self.current_canal_data, contenido, peso_final)
        elif box_fresh['estado'] == ESTADO_CERRADA:
            reabrir_caja(self.db, box_fresh)
        else:
            return

        self.load_tree_data()
        self.data_changed.emit()
        self.show_box_details()

    def action_delete_box(self):
        if self.current_box_data['estado'] != ESTADO_ABIERTA:
            QMessageBox.warning(self, "Aviso", "Solo se pueden borrar cajas ABIERTAS.")
            return

        if QMessageBox.critical(self, "Eliminar", "¿Borrar caja?", QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:
            self.db.eliminar_caja(self.current_box_data['id'])
            self.load_tree_data(); self.detail_stack.setCurrentIndex(0); self.data_changed.emit()

    def action_toggle_canal(self):
        cid = self.current_canal_data['id']
        if self.current_canal_data['estado'] == 'ACTIVO': self.db.cerrar_canal(cid)
        else: self.db.reabrir_canal(cid)
        self.load_tree_data(); self.detail_stack.setCurrentIndex(0); self.data_changed.emit()

    def create_catalog_view(self):
        w = QWidget(); lay = QHBoxLayout(w)
        self.tbl_cat = QTableWidget(0, 3)
        self.tbl_cat.setHorizontalHeaderLabels(["Código", "Nombre", "Especie"])
        self.tbl_cat.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tbl_cat.itemClicked.connect(self.on_cat_select)
        gb = QGroupBox("Editor"); fl = QFormLayout(gb)
        self.inp_cod = QLineEdit(); self.inp_nom = QLineEdit(); self.inp_esp = QLineEdit()
        btn_save = QPushButton("💾 GUARDAR"); btn_save.setObjectName("BtnAction"); btn_save.clicked.connect(self.save_product)
        btn_del = QPushButton("🗑️ BORRAR"); btn_del.setObjectName("BtnDanger"); btn_del.clicked.connect(self.del_product)
        fl.addRow("Cod:", self.inp_cod); fl.addRow("Nom:", self.inp_nom); fl.addRow("Esp:", self.inp_esp)
        fl.addRow(btn_save); fl.addRow(btn_del)
        lay.addWidget(self.tbl_cat, 1); lay.addWidget(gb, 0)
        self.load_catalog()
        return w

    def load_catalog(self):
        self.tbl_cat.setRowCount(0)
        prods = self.product_service.list_all(include_inactive=True)
        for p in prods:
            r = self.tbl_cat.rowCount(); self.tbl_cat.insertRow(r)
            self.tbl_cat.setItem(r,0, QTableWidgetItem(str(p['codigo'])))
            self.tbl_cat.setItem(r,1, QTableWidgetItem(p['nombre']))
            self.tbl_cat.setItem(r,2, QTableWidgetItem(p['especie']))

    def on_cat_select(self):
        r = self.tbl_cat.currentRow()
        if r >= 0:
            self.inp_cod.setText(self.tbl_cat.item(r,0).text()); self.inp_cod.setReadOnly(True); self.inp_nom.setText(self.tbl_cat.item(r,1).text()); self.inp_esp.setText(self.tbl_cat.item(r,2).text())

    def save_product(self):
        codigo = self.inp_cod.text()
        if not codigo:
            return

        try:
            if self.product_service.get(codigo):
                self.product_service.update(codigo, self.inp_nom.text(), self.inp_esp.text())
            else:
                self.product_service.create(codigo, self.inp_nom.text(), self.inp_esp.text())
        except ValueError as e:
            QMessageBox.warning(self, "Aviso", str(e))
            return

        self.load_catalog()
        self.inp_cod.clear(); self.inp_nom.clear(); self.inp_esp.clear()
        self.inp_cod.setReadOnly(False)

    def del_product(self):
        codigo = self.inp_cod.text()
        if not codigo:
            return

        if QMessageBox.question(self, "Borrar", "¿?") != QMessageBox.Yes:
            return

        try:
            self.product_service.delete_if_unused(codigo)
        except ValueError as e:
            QMessageBox.warning(self, "Aviso", str(e))
            return

        self.load_catalog()
        self.inp_cod.clear(); self.inp_nom.clear(); self.inp_esp.clear()
        self.inp_cod.setReadOnly(False)
