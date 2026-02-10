# styles.py

# --- PALETA DE COLORES "INDUSTRIAL" ---
COLOR_BACKGROUND = "#e6e6e6"       # Gris Claro de fondo
COLOR_TEXT_MAIN = "#000000"        # Negro Puro
COLOR_BOX_OPEN = "#28a745"         # Verde
COLOR_BOX_ACTIVE = "#3399ff"       # Azul
COLOR_BTN_DANGER = "#dc3545"       # Rojo
COLOR_BTN_WARN = "#ffc107"         # Amarillo
COLOR_BTN_PRINT = "#005bb5"        # Azul Fuerte
COLOR_BORDER = "#666666"           # Gris Oscuro para bordes

# --- HOJA DE ESTILOS GLOBAL ---
MAIN_STYLESHEET = f"""
/* 1. RESET GLOBAL */
QMainWindow, QDialog, QMessageBox, QInputDialog, QWidget {{
    background-color: {COLOR_BACKGROUND};
    color: {COLOR_TEXT_MAIN};
    font-family: 'Segoe UI', 'Segoe UI Emoji', sans-serif;
}}

/* 2. INPUTS DE TEXTO */
QLineEdit {{
    background-color: #ffffff;
    color: #000000;
    border: 2px solid #555;
    border-radius: 0px;
    padding: 4px;
    font-weight: bold;
    font-size: 16px;
}}

/* 3. ETIQUETAS Y TEXTOS */
QLabel {{
    color: #000000;
    background-color: transparent;
    font-weight: bold;
}}
QLabel[class="kpiTitle"] {{
    color: #444444;
    font-size: 11px;
    font-weight: normal;
    text-transform: uppercase;
}}
QLabel[class="kpiValue"] {{
    color: {COLOR_BTN_PRINT};
    font-size: 24px;
    font-weight: 900;
}}

/* 4. COMBOBOX Y CHECKBOX (INDUSTRIAL) */
QComboBox {{
    background-color: #ffffff;
    color: #000000;
    border: 2px solid #555;
    padding: 4px;
}}
QComboBox QAbstractItemView {{
    background-color: #ffffff;
    color: #000000;
    selection-background-color: {COLOR_BOX_ACTIVE};
}}

/* Estilo Base Checkbox */
QCheckBox {{
    color: #000000;
    font-weight: bold;
    spacing: 8px;
}}

/* Estilo Específico Industrial (#ChkIndustrial) */
QCheckBox#ChkIndustrial {{
    padding-top: 2px; /* Alineación fina */
}}
QCheckBox#ChkIndustrial::indicator {{
    width: 24px; 
    height: 24px;
    border: 2px solid #333;
    border-radius: 4px;
    background-color: #e0e0e0;
}}
QCheckBox#ChkIndustrial::indicator:checked {{
    background-color: #28a745; /* Verde Solido ON */
    border: 2px solid #145226;
}}
QCheckBox#ChkIndustrial::indicator:disabled {{
    background-color: #b0b0b0; /* Gris Apagado OFF/Disabled */
    border: 2px solid #888;
}}

/* 5. MARCOS Y DELIMITADORES */
QFrame, QGroupBox {{
    border: 2px solid {COLOR_BORDER};
    border-radius: 4px;
    background-color: #dcdcdc; 
    color: #000000;
}}
QFrame#TopBar {{ background-color: #cccccc; border-bottom: 4px solid #444; }}
QFrame#KpiPanel {{ background-color: #d0d0d0; border: 3px solid #888; }}
QSplitter::handle {{ background-color: #999; border: 1px solid #555; width: 4px; }}

/* 6. BOTONES CON RELIEVE */
QPushButton {{
    background-color: #f0f0f0;
    color: #000000;
    border: 2px solid #555;
    border-bottom: 3px solid #333;
    border-radius: 4px;
    padding: 6px 12px;
    font-weight: bold;
    min-height: 40px;
}}
QPushButton:pressed {{
    border-bottom: 2px solid #333;
    background-color: #ddd;
}}

/* 7. TABLAS (GRID) */
QTableWidget {{
    background-color: #ffffff;
    color: #000000;
    border: 2px solid #444;
    gridline-color: #999;
}}
QTableWidget::item:selected {{
    background-color: {COLOR_BOX_ACTIVE};
    color: #ffffff;
}}
QHeaderView::section {{
    background-color: #444;
    color: #ffffff;
    padding: 6px;
    border: 1px solid #222;
    font-weight: bold;
}}

/* 8. PESO DIGITAL */
QLineEdit#WeightField {{
    background-color: #000000;
    color: #00ff00;
    font-family: 'DS-Digital';
    font-size: 110px;
    border: 6px solid #333;
}}

/* CLASES BOTONES */
QPushButton#BtnPrint {{ background-color: {COLOR_BTN_PRINT}; color: white; border-bottom: 4px solid #002244; }}
QPushButton#BtnClose {{ background-color: {COLOR_BTN_DANGER}; color: white; border-bottom: 4px solid #75141d; }}
"""

STYLE_BOX_ACTIVE = f"background-color: {COLOR_BOX_ACTIVE}; color: black; border: 4px solid black; font-weight: 900;"
STYLE_BOX_OPEN = f"background-color: {COLOR_BOX_OPEN}; color: black; border: 2px solid #145523; border-bottom: 4px solid #0f3d19;"