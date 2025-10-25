import os
import sys
import re
from PyQt6.QtWidgets import QWidget, QFileDialog, QMessageBox
from PyQt6.uic import loadUi
import fitz  # PyMuPDF

class CargarFacturaWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Cargar UI
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
            ui_path = os.path.join(base_path, 'src', 'components', 'facturar', 'cargar_factura.ui')
        else:
            src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
            ui_path = os.path.join(src_dir, 'components', 'facturar', 'cargar_factura.ui')
        
        if not os.path.exists(ui_path):
            raise FileNotFoundError(f"Archivo .ui no encontrado: {ui_path}")
        
        loadUi(ui_path, self)
        
        # Variables de instancia
        self.ruta_pdf = None
        
        # Conectar señales
        self.btn_seleccionar.clicked.connect(self._seleccionar_archivo)
        self.btn_procesar.clicked.connect(self._procesar_pdf)
    
    def _extraer_datos_factura(self, texto):
        """Extrae datos específicos de la factura usando expresiones regulares."""
        datos = {
            'numero_cuenta': None,
            'nombre_cliente': None,
            'direccion': None,
            'numero_medidor': None,
            'municipio': None,
            'valor_total': None,
            'fecha_factura': None,
            'fecha_maxima_pago': None,
            'consumo_energia': None,
            'periodo': None
        }
        
        # Número de Cuenta (ejemplo: 991195414)
        match = re.search(r'N[uú]mero\s+de\s+Cuenta[:\s]*(\d+)', texto, re.IGNORECASE)
        if match:
            datos['numero_cuenta'] = match.group(1)
        
        # Nombre del Cliente
        match = re.search(r'Nombre[:\s]*(.*?)(?:\n|Direcci[oó]n)', texto, re.IGNORECASE)
        if match:
            datos['nombre_cliente'] = match.group(1).strip()
        
        # Dirección
        match = re.search(r'Direcci[oó]n[:\s]*(.*?)(?:\n|N[uú]mero)', texto, re.IGNORECASE)
        if match:
            datos['direccion'] = match.group(1).strip()
        
        # Número de Medidor
        match = re.search(r'N[uú]mero\s+[Dd]e\s+[Mm]edidor[:\s]*(\d+)', texto, re.IGNORECASE)
        if match:
            datos['numero_medidor'] = match.group(1)
        
        # Municipio
        match = re.search(r'Municipio[:\s]*(.*?)(?:\n|Estrato)', texto, re.IGNORECASE)
        if match:
            datos['municipio'] = match.group(1).strip()
        
        # Valor Total (ejemplo: $2.284 o $2,284)
        match = re.search(r'Valor\s+Total[:\s]*\$?\s*([\d,\.]+)', texto, re.IGNORECASE)
        if match:
            # Limpiar formato de número
            valor = match.group(1).replace(',', '').replace('.', '')
            datos['valor_total'] = float(valor)
        
        # Fecha de Factura (ejemplo: 08/NOV/2024)
        match = re.search(r'Factura\s+del\s+mes\s+de[:\s]*(\d{2}/\w+/\d{4})', texto, re.IGNORECASE)
        if match:
            datos['fecha_factura'] = match.group(1)
        
        # Fecha Máxima de Pago (ejemplo: 25/NOV/2024)
        match = re.search(r'Fecha\s+M[aá]xima\s+de\s+Pago[:\s]*(\d{2}/\w+/\d{4})', texto, re.IGNORECASE)
        if match:
            datos['fecha_maxima_pago'] = match.group(1)
        
        # Consumo de Energía (ejemplo: 30 días de Consumo)
        match = re.search(r'(\d+)\s*d[ií]as?\s+de\s+[Cc]onsumo', texto, re.IGNORECASE)
        if match:
            datos['consumo_energia'] = match.group(1)
        
        # Periodo de consumo
        match = re.search(r'Consumo\s+desde\s*-\s*hasta[:\s]*(\d{2}/\w+/\d{4})\s*-\s*(\d{2}/\w+/\d{4})', texto, re.IGNORECASE)
        if match:
            datos['periodo'] = f"{match.group(1)} - {match.group(2)}"
        
        return datos
    
    def _formatear_datos_extraidos(self, datos):
        """Formatea los datos extraídos para mostrarlos de forma legible."""
        resultado = "===== DATOS EXTRAÍDOS DE LA FACTURA =====\n\n"
        
        if datos['numero_cuenta']:
            resultado += f"📄 Número de Cuenta: {datos['numero_cuenta']}\n"
        
        if datos['nombre_cliente']:
            resultado += f"👤 Cliente: {datos['nombre_cliente']}\n"
        
        if datos['direccion']:
            resultado += f"📍 Dirección: {datos['direccion']}\n"
        
        if datos['numero_medidor']:
            resultado += f"⚡ Número de Medidor: {datos['numero_medidor']}\n"
        
        if datos['municipio']:
            resultado += f"🏙️ Municipio: {datos['municipio']}\n"
        
        if datos['valor_total']:
            resultado += f"💰 Valor Total: ${datos['valor_total']:,.0f}\n"
        
        if datos['fecha_factura']:
            resultado += f"📅 Fecha de Factura: {datos['fecha_factura']}\n"
        
        if datos['fecha_maxima_pago']:
            resultado += f"⏰ Fecha Máxima de Pago: {datos['fecha_maxima_pago']}\n"
        
        if datos['consumo_energia']:
            resultado += f"⚡ Días de Consumo: {datos['consumo_energia']}\n"
        
        if datos['periodo']:
            resultado += f"📊 Periodo: {datos['periodo']}\n"
        
        resultado += "\n" + "="*45 + "\n"
        
        return resultado
    
    def _seleccionar_archivo(self):
        """Abre un diálogo para seleccionar el archivo PDF de la factura."""
        archivo, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar Factura PDF",
            "",
            "Archivos PDF (*.pdf)"
        )
        
        if archivo:
            self.ruta_pdf = archivo
            self.txt_ruta_archivo.setText(archivo)
            self.btn_procesar.setEnabled(True)
            self.txt_resultado.clear()
    
    def _procesar_pdf(self):
        """Procesa el archivo PDF y extrae el texto."""
        if not self.ruta_pdf:
            QMessageBox.warning(self, "Error", "No se ha seleccionado ningún archivo PDF.")
            return
        
        try:
            # Mostrar barra de progreso
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(20)
            self.txt_resultado.clear()
            self.txt_resultado.setPlainText("Procesando PDF...")
            
            # Abrir el PDF con PyMuPDF
            documento = fitz.open(self.ruta_pdf)
            total_paginas = len(documento)
            self.progress_bar.setValue(40)
            
            # Extraer texto de cada página
            texto_completo = []
            
            for num_pagina in range(total_paginas):
                pagina = documento[num_pagina]
                texto_pagina = pagina.get_text()
                
                if texto_pagina.strip():
                    texto_completo.append(f"--- Página {num_pagina + 1} ---\n{texto_pagina}\n")
                
                # Actualizar progreso
                progreso = 40 + int(((num_pagina + 1) / total_paginas) * 50)
                self.progress_bar.setValue(progreso)
            
            # Cerrar el documento
            documento.close()
            self.progress_bar.setValue(95)
            
            # Extraer datos específicos de la factura
            texto_completo_str = "\n".join(texto_completo) if texto_completo else ""
            datos_extraidos = self._extraer_datos_factura(texto_completo_str)
            
            # Mostrar el texto extraído
            if texto_completo:
                # Formatear datos extraídos
                datos_formateados = self._formatear_datos_extraidos(datos_extraidos)
                
                # Mostrar primero los datos extraídos, luego el texto completo
                texto_final = datos_formateados + "\n\n===== TEXTO COMPLETO =====\n\n" + "\n".join(texto_completo)
                self.txt_resultado.setPlainText(texto_final)
            else:
                self.txt_resultado.setPlainText(
                    "No se pudo extraer texto del PDF.\n"
                    "El archivo puede ser una imagen escaneada sin texto seleccionable."
                )
            
            self.progress_bar.setValue(100)
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Error al procesar el PDF:\n{str(e)}"
            )
            self.txt_resultado.setPlainText(f"Error: {str(e)}")
        finally:
            self.progress_bar.setVisible(False)
            self.progress_bar.setValue(0)
