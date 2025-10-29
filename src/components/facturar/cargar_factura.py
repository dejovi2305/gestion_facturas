import os
import sys
import re
from PyQt6.QtWidgets import QWidget, QFileDialog, QMessageBox
from PyQt6.uic import loadUi
import pdfplumber
from .factura_helper import extraer_dato_por_posicion
from config.database import guardar_cuenta_si_no_existe
from config.database import guardar_cliente_si_no_existe

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
        self.btn_procesar.clicked.connect(self._procesar_pdf_extraer_datos)  # Cambio a la función de extracción
        # Si quieres la versión debug, cambia a: self._procesar_pdf
    
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
        """VERSIÓN DEBUG: Extrae y muestra todo el texto del PDF."""
        if not self.ruta_pdf:
            QMessageBox.warning(self, "Error", "No se ha seleccionado ningún archivo PDF.")
            return
        
        try:
            # Mostrar barra de progreso
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(30)
            self.txt_resultado.clear()
            self.txt_resultado.setPlainText("Procesando PDF...")
            
            # Abrir el PDF con pdfplumber
            with pdfplumber.open(self.ruta_pdf) as documento:
                self.progress_bar.setValue(50)
                
                # FUNCIÓN TEMPORAL: Extraer todo el texto del PDF
                if len(documento.pages) > 0:
                    pagina = documento.pages[0]
                    
                    # Extraer texto completo
                    texto_completo = pagina.extract_text()
                    
                    # Extraer también las palabras con sus coordenadas
                    palabras = pagina.extract_words()
                    
                    resultado = "===== TEXTO COMPLETO DEL PDF =====\n\n"
                    resultado += texto_completo
                    resultado += "\n\n===== PALABRAS CON COORDENADAS (primeras 100) =====\n\n"
                    
                    for i, palabra in enumerate(palabras[:100]):  # Mostrar las primeras 100 palabras
                        resultado += f"{i+1}. '{palabra['text']}' -> x0={palabra['x0']:.1f}, top={palabra['top']:.1f}, x1={palabra['x1']:.1f}, bottom={palabra['bottom']:.1f}\n"
                    
                    if len(palabras) > 100:
                        resultado += f"\n... y {len(palabras) - 100} palabras más\n"
                    
                    resultado += f"\n\nTotal de palabras en el PDF: {len(palabras)}\n"
                    
                    self.txt_resultado.setPlainText(resultado)
                else:
                    self.txt_resultado.setPlainText("El PDF no contiene páginas.")
            
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
    
    def _procesar_pdf_extraer_datos(self):
        """Procesa el archivo PDF y extrae datos específicos de la factura."""
        if not self.ruta_pdf:
            QMessageBox.warning(self, "Error", "No se ha seleccionado ningún archivo PDF.")
            return
        
        try:
            # Mostrar barra de progreso
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(30)
            self.txt_resultado.clear()
            self.txt_resultado.setPlainText("Procesando PDF...")
            
            # Abrir el PDF con pdfplumber
            with pdfplumber.open(self.ruta_pdf) as documento:
                self.progress_bar.setValue(50)
                
                # Extraer datos de la(s) página(s)
                if len(documento.pages) > 0:
                    pagina = documento.pages[0]
                    numero_medidor = None
                    if len(documento.pages) > 1:
                        pagina2 = documento.pages[1]
                        
                        # Extraer número de medidor (página 2) con coordenadas absolutas
                        # Hallado con el script: palabra '84350535' en aprox
                        # x0=356.7, y0=752.9, x1=383.2, y1=761.9
                        numero_medidor = extraer_dato_por_posicion(
                            pagina=pagina2,
                            patron_regex=r"\b(\d{6,12})\b",
                            x0_absoluto=356,
                            y0_absoluto=752,
                            x1_absoluto=384,
                            y1_absoluto=762
                        )
                    
                    # Extraer número de cuenta
                    numero_cuenta = extraer_dato_por_posicion(
                        pagina=pagina,
                        etiqueta="Número de Cuenta",
                        patron_regex=r"\b(\d{6,12})\b",
                        offset_x0=-40,
                        offset_y0=5,
                        offset_x1=320,
                        offset_y1=85
                    )
                    
                    # Extraer nombre del cliente
                    # Usando coordenadas absolutas encontradas con el script
                    nombre_cliente = extraer_dato_por_posicion(
                        pagina=pagina,
                        patron_regex=r"([A-ZÁÉÍÓÚÜÑ\s]{10,})",
                        x0_absoluto=30,
                        y0_absoluto=108,
                        x1_absoluto=190,
                        y1_absoluto=120
                    )
                    if nombre_cliente:
                        nombre_cliente = " ".join(nombre_cliente.split()).strip()
                    
                    # Extraer dirección
                    # Usando coordenadas absolutas encontradas con el script
                    # Área completa detectada: x0≈31, y0≈136, x1≈180, y1≈143
                    direccion = extraer_dato_por_posicion(
                        pagina=pagina,
                        patron_regex=r"([A-ZÁÉÍÓÚÜÑ][A-ZÁÉÍÓÚÜÑ0-9\s\.,-]{8,})",
                        x0_absoluto=31,
                        y0_absoluto=136,
                        x1_absoluto=260,
                        y1_absoluto=144
                    )
                    if direccion:
                        direccion = " ".join(direccion.split()).strip()
                        # Remover el punto final si existe
                        direccion = direccion.rstrip('.')
                        # Remover espacios antes de puntos
                        direccion = direccion.replace(' .', '.')
                    
                    # Extraer estrato
                    estrato = extraer_dato_por_posicion(
                        pagina=pagina,
                        etiqueta="Estrato",
                        patron_regex=r"(Comercial|Residencial|Industrial)",
                        offset_x0=0,
                        offset_y0=0,
                        offset_x1=120,
                        offset_y1=20
                    )
                    
                    # Extraer consumo kWh
                    # Coordenadas encontradas: x0=34.1, y0=326.7, x1=47.4, y1=334.7
                    consumo_kwh = extraer_dato_por_posicion(
                        pagina=pagina,
                        patron_regex=r"(\d+(?:\.\d+)?)",
                        x0_absoluto=34,
                        y0_absoluto=326,
                        x1_absoluto=48,
                        y1_absoluto=335
                    )
                    # Convertir a número si se encontró
                    if consumo_kwh:
                        try:
                            consumo_kwh = float(consumo_kwh)
                        except ValueError:
                            consumo_kwh = None
                    
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
                        
                        # Guardar cliente si no existe (por número de cuenta)
                        cliente_nuevo = False
                        try:
                            cliente_nuevo, mensaje_cliente = guardar_cliente_si_no_existe(
                                numero_cuenta=numero_cuenta_int,
                                nombre=nombre_cliente,
                                direccion=direccion,
                                estrato=estrato,
                                numero_medidor=numero_medidor,
                            )
                        except Exception:
                            mensaje_cliente = "No se pudo registrar/actualizar el cliente"
                        
                        resultado = "===== DATOS EXTRAÍDOS =====\n\n"
                        resultado += f"📄 Número de Cuenta: {numero_cuenta}\n\n"
                        resultado += f"👤 Nombre del Cliente: {nombre_cliente}\n\n"
                        resultado += f"📍 Dirección: {direccion}\n\n"
                        resultado += f"🏢 Estrato: {estrato}\n\n"
                        resultado += f"📄 Número de Medidor: {numero_medidor}\n\n"
                        resultado += f"⚡ Consumo kWh: {consumo_kwh if consumo_kwh is not None else 'No disponible'}\n\n"
                        resultado += f"{'='*30}\n\n"
                        
                        if cuenta_nueva:
                            resultado += "✓ Nueva cuenta registrada\n"
                        else:
                            resultado += "ℹ️ Cuenta existente\n"
                        
                        # Mensajes detallados
                        if 'mensaje' in locals() and mensaje:
                            resultado += f"   → {mensaje}\n"

                        if cliente_nuevo:
                            resultado += "✓ Nuevo cliente registrado\n"
                        else:
                            resultado += "ℹ️ Cliente existente\n"
                        if 'mensaje_cliente' in locals() and mensaje_cliente:
                            resultado += f"   → {mensaje_cliente}\n"
                        
                        self.txt_resultado.setPlainText(resultado)
                    else:
                        self.txt_resultado.setPlainText(
                            "No se pudo extraer el número de cuenta.\n"
                            "Verifica que el PDF contenga la etiqueta 'Número de Cuenta'."
                        )
                else:
                    self.txt_resultado.setPlainText("El PDF no contiene páginas.")
            
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
