import os
import sys
import re
from PyQt6.QtWidgets import QWidget, QFileDialog, QMessageBox
from PyQt6.uic import loadUi
import pdfplumber
from .factura_helper import extraer_dato_por_posicion
from .factura_helperV2 import (
    extraer_numero_cuenta,
    extraer_nombre_cliente,
    extraer_direccion_cliente,
    extraer_estrato_cliente,
    extraer_numero_medidor,
    extraer_consumo_kwh,
    extraer_valor_kwh,
    extraer_valor_total,
    extraer_valor_total_pagar,
    extraer_fecha_maxima_pago,
)
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
        self.ruta_archivo = None  # Puede ser PDF o XML
        
        # Conectar señales
        self.btn_seleccionar.clicked.connect(self._seleccionar_archivo)
        self.btn_procesar.clicked.connect(self._procesar_archivo)  # Decide por tipo (PDF/XML) y delega a métodos separados
        # Si quieres la versión debug, cambia a: self._procesar_pdf
    
    def _seleccionar_archivo(self):
        """Abre un diálogo para seleccionar el archivo de la factura (PDF o XML)."""
        archivo, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar Factura (PDF o XML)",
            "",
            "Archivos PDF o XML (*.pdf *.xml);;PDF (*.pdf);;XML (*.xml)"
        )
        
        if archivo:
            self.ruta_archivo = archivo
            self.txt_ruta_archivo.setText(archivo)
            self.btn_procesar.setEnabled(True)
            self.txt_resultado.clear()
    
    def _procesar_pdf(self):
        """VERSIÓN DEBUG: Extrae y muestra todo el texto del PDF."""
        if not self.ruta_archivo:
            QMessageBox.warning(self, "Error", "No se ha seleccionado ningún archivo PDF.")
            return
        
        try:
            # Mostrar barra de progreso
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(30)
            self.txt_resultado.clear()
            self.txt_resultado.setPlainText("Procesando PDF...")
            
            # Abrir el PDF con pdfplumber
            with pdfplumber.open(self.ruta_archivo) as documento:
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
    
    def _procesar_archivo(self):
        """Decide el flujo según el tipo de archivo (PDF o XML) y delega al método correspondiente."""
        if not self.ruta_archivo:
            QMessageBox.warning(self, "Error", "No se ha seleccionado ningún archivo.")
            return

        _, ext = os.path.splitext(self.ruta_archivo)
        if ext.lower() == ".xml":
            return self._procesar_xml_extraer_datos()
        elif ext.lower() == ".pdf":
            return self._procesar_pdf_extraer_datos()
        else:
            QMessageBox.warning(self, "Tipo de archivo no soportado", "Selecciona un archivo .pdf o .xml")
            return

    def _procesar_pdf_extraer_datos(self):
        """Procesa un archivo PDF y extrae datos específicos de la factura."""
        if not self.ruta_archivo:
            QMessageBox.warning(self, "Error", "No se ha seleccionado ningún archivo.")
            return
        
        try:
            # Mostrar barra de progreso
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(30)
            self.txt_resultado.clear()
            self.txt_resultado.setPlainText("Procesando PDF...")
            
            # Abrir el PDF con pdfplumber
            with pdfplumber.open(self.ruta_archivo) as documento:
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
                    
                    # Extraer valor kWh (precio por kWh)
                    # Coordenadas: x0=70, y0=327, x1=100, y1=336
                    valor_kwh = extraer_dato_por_posicion(
                        pagina=pagina,
                        patron_regex=r"(\d+(?:,\d+)?(?:\.\d+)?)",
                        x0_absoluto=70,
                        y0_absoluto=327,
                        x1_absoluto=100,
                        y1_absoluto=336
                    )
                    # Convertir a número si se encontró
                    if valor_kwh:
                        try:
                            # Reemplazar coma por punto para formato decimal
                            valor_kwh = float(valor_kwh.replace(',', '.'))
                        except (ValueError, AttributeError):
                            valor_kwh = None
                    
                    # Extraer valor total
                    # Coordenadas: x0=326, y0=216, x1=389, y1=232.5
                    valor_total = extraer_dato_por_posicion(
                        pagina=pagina,
                        patron_regex=r"(\$?\d+(?:[.,]\d+)*(?:[.,]\d+)?)",
                        x0_absoluto=326,
                        y0_absoluto=216,
                        x1_absoluto=389,
                        y1_absoluto=233
                    )
                    # Convertir a número si se encontró
                    if valor_total:
                        try:
                            # Limpiar el valor: remover $ y puntos de miles, cambiar coma por punto
                            valor_total = valor_total.replace('$', '').replace('.', '').replace(',', '.')
                            valor_total = float(valor_total)
                        except (ValueError, AttributeError):
                            valor_total = None
                    
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
                        resultado += f"💰 Valor kWh: ${valor_kwh if valor_kwh is not None else 'No disponible'}\n\n"
                        resultado += f"💵 Valor Total: ${valor_total if valor_total is not None else 'No disponible'}\n\n"
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

    def _procesar_xml_extraer_datos(self):
        """Procesa el archivo XML y extrae datos específicos usando el helper V2."""
        try:
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(20)
            self.txt_resultado.clear()
            self.txt_resultado.setPlainText("Procesando XML...")

            numero_cuenta, detalles = extraer_numero_cuenta(self.ruta_archivo)
            nombre_cliente, detalles_nombre = extraer_nombre_cliente(self.ruta_archivo)
            direccion, detalles_dir = extraer_direccion_cliente(self.ruta_archivo)
            estrato, detalles_estrato = extraer_estrato_cliente(self.ruta_archivo)
            numero_medidor, detalles_medidor = extraer_numero_medidor(self.ruta_archivo)
            consumo_kwh_lista, detalles_consumo = extraer_consumo_kwh(self.ruta_archivo)
            valor_kwh_lista, detalles_valor = extraer_valor_kwh(self.ruta_archivo)
            fecha_maxima_pago, detalles_fecha = extraer_fecha_maxima_pago(self.ruta_archivo)
            valor_total_xml, detalles_total = extraer_valor_total(self.ruta_archivo)
            valor_total_pagar_xml, detalles_total_pagar = extraer_valor_total_pagar(self.ruta_archivo)

            self.progress_bar.setValue(70)

            if numero_cuenta:
                resultado = "===== DATOS EXTRAÍDOS (XML) =====\n\n"
                resultado += f"📄 Número de Cuenta: {numero_cuenta}\n\n"
                if nombre_cliente:
                    resultado += f"👤 Nombre del Cliente: {nombre_cliente}\n\n"
                if direccion:
                    resultado += f"📍 Dirección: {direccion}\n\n"
                if estrato is not None:
                    resultado += f"🏢 Estrato: {estrato}\n\n"
                if numero_medidor:
                    resultado += f"📄 Número de Medidor: {numero_medidor}\n\n"
                
                # Mostrar consumo y valor kWh
                if consumo_kwh_lista:
                    resultado += "⚡ Consumo kWh por línea:\n"
                    for i, consumo in enumerate(consumo_kwh_lista, 1):
                        resultado += f"   Línea {i}: {consumo} kWh\n"
                    resultado += "\n"
                
                if valor_kwh_lista:
                    resultado += "💰 Valor kWh por línea:\n"
                    for i, valor in enumerate(valor_kwh_lista, 1):
                        resultado += f"   Línea {i}: ${valor:,.2f} COP\n"
                    resultado += "\n"
                
                if fecha_maxima_pago:
                    resultado += f"📅 Fecha Máxima de Pago: {fecha_maxima_pago}\n\n"

                if valor_total_xml is not None:
                    resultado += f"💵 Valor Total (LineExtensionAmount): ${valor_total_xml:,.2f} COP\n"
                if valor_total_pagar_xml is not None:
                    resultado += f"🧾 Valor Total a Pagar (PayableAmount): ${valor_total_pagar_xml:,.2f} COP\n\n"
                
                resultado += "Detalles de hallazgos (valor, ruta):\n"
                for val, ruta in detalles:
                    resultado += f"  - {val} @ {ruta}\n"
                if detalles_nombre:
                    resultado += "\nDetalles de hallazgos de nombre (valor, ruta):\n"
                    for val, ruta in detalles_nombre:
                        resultado += f"  - {val} @ {ruta}\n"
                if detalles_dir:
                    resultado += "\nDetalles de hallazgos de dirección (valor, ruta):\n"
                    for val, ruta in detalles_dir:
                        resultado += f"  - {val} @ {ruta}\n"
                if detalles_estrato:
                    resultado += "\nDetalles de hallazgos de estrato (valor, ruta):\n"
                    for val, ruta in detalles_estrato:
                        resultado += f"  - {val} @ {ruta}\n"
                if detalles_medidor:
                    resultado += "\nDetalles de hallazgos de medidor (valor, ruta):\n"
                    for val, ruta in detalles_medidor:
                        resultado += f"  - {val} @ {ruta}\n"
                
                if detalles_consumo:
                    resultado += "\nDetalles de hallazgos de consumo kWh (valor, ruta):\n"
                    for val, ruta in detalles_consumo:
                        resultado += f"  - {val} @ {ruta}\n"
                
                if detalles_valor:
                    resultado += "\nDetalles de hallazgos de valor kWh (valor, ruta):\n"
                    for val, ruta in detalles_valor:
                        resultado += f"  - {val} @ {ruta}\n"
                
                if detalles_fecha:
                    resultado += "\nDetalles de hallazgos de fecha máxima de pago (valor, ruta):\n"
                    for val, ruta in detalles_fecha:
                        resultado += f"  - {val} @ {ruta}\n"

                if detalles_total:
                    resultado += "\nDetalles de hallazgos de valor total (LineExtensionAmount):\n"
                    for val, ruta in detalles_total:
                        resultado += f"  - {val} @ {ruta}\n"
                if detalles_total_pagar:
                    resultado += "\nDetalles de hallazgos de valor total a pagar (PayableAmount):\n"
                    for val, ruta in detalles_total_pagar:
                        resultado += f"  - {val} @ {ruta}\n"

                # Guardar la cuenta en la base de datos
                try:
                    numero_cuenta_int = int(numero_cuenta)
                    cuenta_nueva, mensaje = guardar_cuenta_si_no_existe(numero_cuenta_int)
                    resultado += "\n"
                    if cuenta_nueva:
                        resultado += "✓ Nueva cuenta registrada\n"
                    else:
                        resultado += "ℹ️ Cuenta existente\n"
                    if mensaje:
                        resultado += f"   → {mensaje}\n"
                except Exception as e:
                    resultado += f"\n⚠️ No se pudo registrar la cuenta: {e}\n"

                # Guardar/actualizar cliente con valores (permitiendo None si no existen)
                try:
                    cliente_nuevo, mensaje_cliente = guardar_cliente_si_no_existe(
                        numero_cuenta=numero_cuenta_int,
                        nombre=nombre_cliente if nombre_cliente else None,
                        direccion=direccion if direccion else None,
                        estrato=str(estrato) if estrato is not None else None,
                        numero_medidor=numero_medidor if numero_medidor else None,
                    )
                    if cliente_nuevo:
                        resultado += "✓ Nuevo cliente registrado\n"
                    else:
                        resultado += "ℹ️ Cliente existente\n"
                    if mensaje_cliente:
                        resultado += f"   → {mensaje_cliente}\n"
                except Exception as e:
                    resultado += f"⚠️ No se pudo registrar/actualizar el cliente: {e}\n"

                self.txt_resultado.setPlainText(resultado)
            else:
                self.txt_resultado.setPlainText("No se encontró número de cuenta en el XML.")

            self.progress_bar.setValue(100)
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Error al procesar el XML:\n{str(e)}"
            )
            self.txt_resultado.setPlainText(f"Error: {str(e)}")
        finally:
            self.progress_bar.setVisible(False)
            self.progress_bar.setValue(0)
