# hardware.py
import sys
import serial
import serial.tools.list_ports
import re
import time
import win32print
import datetime
from PySide6.QtCore import QThread, Signal

# =============================================================================
# SECCIÓN BÁSCULA
# =============================================================================
class ScaleWorker(QThread):
    weight_received = Signal(float)
    status_changed = Signal(str)

    def __init__(self, port, baudrate=9600):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.is_running = True
        self.serial_conn = None
        self.pattern = re.compile(r"(\d+\.\d+)")

    def run(self):
        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1
            )
            self.status_changed.emit(f"✅ CONECTADO: {self.port}")
            while self.is_running:
                if not self.serial_conn.is_open: break
                try:
                    line_bytes = self.serial_conn.readline()
                    line_str = line_bytes.decode('utf-8', errors='ignore').strip()
                    if line_str:
                        match = self.pattern.search(line_str)
                        if match:
                            self.weight_received.emit(float(match.group(1)))
                except Exception as e:
                    self.status_changed.emit(f"⚠️ Error lectura: {e}")
                    time.sleep(1)
        except Exception as e:
            self.status_changed.emit(f"❌ ERROR: {e}")
        finally:
            self.close_conn()

    def stop(self):
        self.is_running = False
        self.wait()

    def close_conn(self):
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()

def get_com_ports():
    return [p.device for p in serial.tools.list_ports.comports()]

# =============================================================================
# SECCIÓN IMPRESORA (MEJORADA CON FALLBACK DEFENSIVO)
# =============================================================================
class HardwareManager:
    def __init__(self, printer_name="ZDesigner GC420t"):
        self.printer_name = printer_name
        self._find_zebra_printer()

    def _find_zebra_printer(self):
        """Busca la impresora por nombre, keywords o fallback a Default de Windows"""
        try:
            # Enumerar impresoras locales y de red
            printers = [p[2] for p in win32print.EnumPrinters(
                win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
            )]
            
            # 1. Si el nombre exacto ya está, terminar
            if self.printer_name in printers:
                print(f"🖨️ Impresora exacta encontrada: {self.printer_name}")
                return

            # 2. Buscar por palabras clave industriales
            for p in printers:
                p_up = p.upper()
                if any(k in p_up for k in ["ZEBRA", "ZTC", "ZDESIGNER", "GC420"]):
                    self.printer_name = p
                    print(f"🖨️ Impresora detectada por keyword: {self.printer_name}")
                    return
            
            # 3. FALLBACK: Usar la predeterminada de Windows
            default_p = win32print.GetDefaultPrinter()
            if default_p:
                self.printer_name = default_p
                print(f"⚠️ Alerta: Usando impresora predeterminada de Windows: {self.printer_name}")
                
        except Exception as e:
            print(f"❌ Error buscando impresora: {e}")

    def send_raw_zpl(self, zpl_code):
        try:
            hPrinter = win32print.OpenPrinter(self.printer_name)
            try:
                hJob = win32print.StartDocPrinter(hPrinter, 1, ("Etiqueta TIF", None, "RAW"))
                try:
                    win32print.StartPagePrinter(hPrinter)
                    win32print.WritePrinter(hPrinter, zpl_code.encode('utf-8'))
                    win32print.EndPagePrinter(hPrinter)
                finally:
                    win32print.EndDocPrinter(hPrinter)
            finally:
                win32print.ClosePrinter(hPrinter)
            return True, "OK"
        except Exception as e:
            return False, f"Fallo al abrir impresora '{self.printer_name}': {str(e)}"

    def print_ticket(self, pieza_data, caja_data, canal_data, producto_data):
        fecha_actual = datetime.datetime.now().strftime("%d/%m/%Y")
        empresa = "CENTRAL COMERCIALIZADORA DE CARNES SA DE CV"
        producto = producto_data['nombre']
        codigo = producto_data['codigo'] 
        peso = pieza_data['peso']
        especie = producto_data['especie']
        lote_dia = canal_data['lote_dia']       
        # Si el siniiga es compuesto (intro-lote), mostramos solo la parte limpia
        siniiga_display = canal_data['siniiga'].split("-")[0]
        
        caja_visual = f"{caja_data['numero_caja']} (#{pieza_data['consecutivo']})"
        
        # Código de barras simplificado
        siniiga_last4 = siniiga_display[-4:] if len(siniiga_display) >= 4 else siniiga_display.zfill(4)
        caja_padded = str(caja_data['numero_caja']).zfill(2)
        peso_padded = int(peso * 100) 
        codigo_barras = f"{lote_dia}_{siniiga_last4}{caja_padded}{codigo}{peso_padded:04d}"

        zpl = "^XA^PW480^LL768^CI28"
        zpl += "^FO435,0^A0R,22,22^FB768,1,0,C,0^FD" + empresa + "^FS"
        zpl += "^FO345,20^A0R,40,40^FB740,1,0,C,0^FD" + producto + "^FS"
        zpl += "^FO335,20^GB0,720,3^FS"
        zpl += "^FO285,50^A0R,25,25^FDCODIGO^FS"
        zpl += "^FO285,180^A0R,30,30^FD" + str(codigo) + "^FS"
        zpl += "^FO265,50^GB0,250,2^FS"
        zpl += "^FO205,50^A0R,25,25^FDPESO^FS"
        zpl += "^FO145,50^A0R,60,60^FD" + f"{peso:.2f} Kg" + "^FS"
        zpl += "^FO135,330^GB200,0,3^FS" 
        zpl += "^FO295,360^A0R,20,20^FDFECHA:^FS^FO295,480^A0R,25,25^FD" + fecha_actual + "^FS"
        zpl += "^FO265,360^A0R,20,20^FDESPECIE:^FS^FO265,480^A0R,22,22^FD" + especie + "^FS"
        zpl += "^FO235,360^A0R,20,20^FDLOTE:^FS^FO235,480^A0R,30,30^FD" + lote_dia + "^FS"
        zpl += "^FO205,360^A0R,20,20^FDSINIIGA:^FS^FO205,480^A0R,22,22^FD" + siniiga_display + "^FS"
        zpl += "^FO175,360^A0R,20,20^FDCAJA(PZA):^FS^FO170,480^A0R,30,30^FD" + caja_visual + "^FS"
        zpl += "^FO40,80^BCR,80,Y,N,N^FD" + codigo_barras + "^FS"
        zpl += "^XZ"
        return self.send_raw_zpl(zpl)

    def print_master(self, caja_data, canal_data, contenido_piezas, peso_manual_override=None):
        empresa = "CENTRAL COMERCIALIZADORA DE CARNES SA DE CV"
        fecha_actual = datetime.datetime.now().strftime("%d/%m/%Y")
        
        peso_calculado = sum(p['peso'] for p in contenido_piezas)
        peso_final = peso_manual_override if peso_manual_override and peso_manual_override > 0 else peso_calculado
            
        piezas = len(contenido_piezas)
        siniiga_display = canal_data['siniiga'].split("-")[0]
        
        nombres = set([p['nombre_producto'] for p in contenido_piezas])
        if len(nombres) > 1:
            producto_visual, especie_visual = "MULTIPRODUCTO", "VARIOS"
        else:
            producto_visual = contenido_piezas[0]['nombre_producto'] if contenido_piezas else "VACIA"
            especie_visual = "CORTE PRIMARIO"

        caja_padded = str(caja_data['numero_caja']).zfill(2)
        peso_barcode = int(peso_final * 100)
        barcode_caja = f"M{canal_data['lote_dia']}{caja_padded}{peso_barcode:04d}"

        zpl = "^XA^PW480^LL768^CI28"
        zpl += "^FO425,20^A0R,20,20^FB728,1,0,C,0^FD" + empresa + "^FS"
        zpl += "^FO365,20^A0R,50,50^FB728,1,0,C,0^FD" + producto_visual + "^FS"
        zpl += "^FO325,20^A0R,25,25^FB728,1,0,C,0^FD" + especie_visual + "  |  " + fecha_actual + "^FS"
        zpl += "^FO310,20^GB0,728,3^FS"
        zpl += "^FO90,410^GB220,0,3^FS"
        zpl += "^FO275,40^A0R,30,30^FDCAJA No.^FS"
        zpl += "^FO215,220^A0R,85,85^FD" + caja_padded + "^FS"
        zpl += "^FO275,430^A0R,28,28^FDLOTE: " + canal_data['lote_dia'] + "^FS"
        zpl += "^FO235,430^A0R,25,25^FDSINIIGA: " + siniiga_display + "^FS"
        zpl += "^FO200,20^GB0,728,2^FS"
        zpl += "^FO165,40^A0R,30,30^FDPESO NETO:^FS"
        zpl += "^FO115,160^A0R,50,50^FD" + f"{peso_final:.2f} Kg.^FS"
        zpl += "^FO165,430^A0R,30,30^FDCANTIDAD:^FS"
        zpl += "^FO120,430^A0R,45,45^FD" + str(piezas) + " Pzas^FS"
        zpl += "^FO90,20^GB0,728,3^FS"
        zpl += "^FO25,120^BCR,60,Y,N,N^FD" + barcode_caja + "^FS"
        zpl += "^XZ"
        return self.send_raw_zpl(zpl)