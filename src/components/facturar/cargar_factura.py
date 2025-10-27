import os
import sys
from PyQt6.QtWidgets import QWidget, QFileDialog, QMessageBox
from PyQt6.uic import loadUi
import fitz  # PyMuPDF
from .factura_helper import extraer_dato_por_posicion
from config.database import guardar_cuenta_si_no_existe

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
        """Procesa el archivo PDF y extrae datos por posición."""
        if not self.ruta_pdf:
            QMessageBox.warning(self, "Error", "No se ha seleccionado ningún archivo PDF.")
            return
        
        try:
            # Mostrar barra de progreso
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(30)
            self.txt_resultado.clear()
            self.txt_resultado.setPlainText("Procesando PDF...")
            
            # Abrir el PDF con PyMuPDF
            documento = fitz.open(self.ruta_pdf)
            self.progress_bar.setValue(50)
            
            # Extraer número de cuenta de la primera página
            if len(documento) > 0:
                pagina = documento[0]
                numero_cuenta = extraer_dato_por_posicion(
                    pagina=pagina,
                    etiqueta="Número de Cuenta",
                    patron_regex=r"\b(\d{6,12})\b",
                    offset_x0=-40,
                    offset_y0=5,
                    offset_x1=320,
                    offset_y1=85
                )
                
                self.progress_bar.setValue(80)
                
                # Mostrar resultado
                if numero_cuenta:
                    # Guardar la cuenta en la base de datos
                    try:
                        numero_cuenta_int = int(numero_cuenta)
                        cuenta_nueva, mensaje = guardar_cuenta_si_no_existe(numero_cuenta_int)
                    except ValueError:
                        cuenta_nueva = False
                        mensaje = f"Error: '{numero_cuenta}' no es un número válido"
                    
                    resultado = f"===== DATOS EXTRAÍDOS =====\n\n"
                    resultado += f"📄 Número de Cuenta: {numero_cuenta}\n\n"
                    resultado += f"{'='*30}\n\n"
                    resultado += f"💾 Base de datos: {mensaje}\n"
                    
                    if cuenta_nueva:
                        resultado += f"✓ Nueva cuenta registrada\n"
                    else:
                        resultado += f"ℹ️ Cuenta existente\n"
                    
                    self.txt_resultado.setPlainText(resultado)
                else:
                    self.txt_resultado.setPlainText(
                        "No se pudo extraer el número de cuenta.\n"
                        "Verifica que el PDF contenga la etiqueta 'Número de Cuenta'."
                    )
            else:
                self.txt_resultado.setPlainText("El PDF no contiene páginas.")
            
            # Cerrar el documento
            documento.close()
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



