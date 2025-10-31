import os
import sys
from PyQt6.QtWidgets import QWidget, QFileDialog, QMessageBox
from PyQt6.uic import loadUi
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
    extraer_cufe,
)
from .consumo_dialog import ConsumoDialog
from config.database import guardar_cuenta_si_no_existe
from config.database import guardar_cliente_si_no_existe
from config.database import guardar_consumo
from config.database import existe_cuenta, existe_cliente_para_cuenta

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
            "XML (*.xml)"
        )
        
        if archivo:
            self.ruta_archivo = archivo
            self.txt_ruta_archivo.setText(archivo)
            self.btn_procesar.setEnabled(True)
            self.txt_resultado.clear()
    
    # Eliminado: soporte y utilidades de PDF
    
    def _procesar_archivo(self):
        """Decide el flujo según el tipo de archivo (PDF o XML) y delega al método correspondiente."""
        if not self.ruta_archivo:
            QMessageBox.warning(self, "Error", "No se ha seleccionado ningún archivo.")
            return

        _, ext = os.path.splitext(self.ruta_archivo)
        if ext.lower() == ".xml":
            return self._procesar_xml_extraer_datos()
        else:
            QMessageBox.warning(self, "Tipo de archivo no soportado", "Solo se admite XML (*.xml). No se realizará extracción.")
            return

    # Eliminado: extracción de datos desde PDF

    def _procesar_xml_extraer_datos(self):
        """Procesa el archivo XML y extrae datos específicos usando el helper V2."""
        try:
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(20)
            self.txt_resultado.clear()
            self.txt_resultado.setPlainText("Procesando XML...")

            # 1) Siempre: extraer número de cuenta primero
            numero_cuenta, detalles = extraer_numero_cuenta(self.ruta_archivo)
            if not numero_cuenta:
                self.txt_resultado.setPlainText("No se encontró número de cuenta en el XML.")
                self.progress_bar.setValue(100)
                return

            # 2) Consultar existencia en BD
            try:
                numero_cuenta_int = int(numero_cuenta)
            except Exception:
                self.txt_resultado.setPlainText(f"Número de cuenta inválido: {numero_cuenta}")
                self.progress_bar.setValue(100)
                return

            cuenta_existe = existe_cuenta(numero_cuenta_int)
            cliente_existe = existe_cliente_para_cuenta(numero_cuenta_int)

            # Variables por si se requieren
            nombre_cliente = direccion = estrato = numero_medidor = None
            detalles_nombre = detalles_dir = detalles_estrato = detalles_medidor = []

            # 3) Si no existen, extraer datos de Cliente y persistir
            if not (cuenta_existe and cliente_existe):
                nombre_cliente, detalles_nombre = extraer_nombre_cliente(self.ruta_archivo)
                direccion, detalles_dir = extraer_direccion_cliente(self.ruta_archivo)
                estrato, detalles_estrato = extraer_estrato_cliente(self.ruta_archivo)
                numero_medidor, detalles_medidor = extraer_numero_medidor(self.ruta_archivo)

                # Guardar la cuenta si no existe
                try:
                    cuenta_nueva, mensaje = guardar_cuenta_si_no_existe(numero_cuenta_int)
                except Exception as e:
                    cuenta_nueva, mensaje = False, f"Error registrando cuenta: {e}"

                # Guardar/actualizar cliente
                try:
                    cliente_nuevo, mensaje_cliente = guardar_cliente_si_no_existe(
                        numero_cuenta=numero_cuenta_int,
                        nombre=nombre_cliente if nombre_cliente else None,
                        direccion=direccion if direccion else None,
                        estrato=str(estrato) if estrato is not None else None,
                        numero_medidor=numero_medidor if numero_medidor else None,
                    )
                except Exception as e:
                    cliente_nuevo, mensaje_cliente = False, f"Error cliente: {e}"
            else:
                cuenta_nueva = False
                mensaje = "Cuenta existente"
                cliente_nuevo = False
                mensaje_cliente = "Cliente existente"

            # 4) Extraer SIEMPRE datos de consumo
            consumo_kwh_lista, detalles_consumo = extraer_consumo_kwh(self.ruta_archivo)
            valor_kwh_lista, detalles_valor = extraer_valor_kwh(self.ruta_archivo)
            fecha_maxima_pago, detalles_fecha = extraer_fecha_maxima_pago(self.ruta_archivo)
            valor_total_xml, detalles_total = extraer_valor_total(self.ruta_archivo)
            valor_total_pagar_xml, detalles_total_pagar = extraer_valor_total_pagar(self.ruta_archivo)
            cufe_xml, detalles_cufe = extraer_cufe(self.ruta_archivo)

            self.progress_bar.setValue(70)

            if numero_cuenta:
                resultado = "===== DATOS EXTRAÍDOS (XML) =====\n\n"
                resultado += f"📄 Número de Cuenta: {numero_cuenta}\n\n"
                if not (cuenta_existe and cliente_existe):
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
                if cufe_xml:
                    resultado += f"🔑 CUFE/CUDE: {cufe_xml}\n\n"
                
                # Reportar estado de cuenta/cliente según caso
                resultado += f"{'='*30}\n\n"
                if cuenta_nueva:
                    resultado += "✓ Nueva cuenta registrada\n"
                else:
                    resultado += "ℹ️ Cuenta existente\n"
                if mensaje:
                    resultado += f"   → {mensaje}\n"

                if cliente_nuevo:
                    resultado += "✓ Nuevo cliente registrado\n"
                else:
                    resultado += "ℹ️ Cliente existente\n"
                if mensaje_cliente:
                    resultado += f"   → {mensaje_cliente}\n"

                # Diálogo para revisar/editar CONSUMO antes de guardar
                try:
                    consumo_val = consumo_kwh_lista[0] if (consumo_kwh_lista and len(consumo_kwh_lista) > 0) else 0
                    valor_kwh_val = valor_kwh_lista[0] if (valor_kwh_lista and len(valor_kwh_lista) > 0) else 0.0

                    dlg = ConsumoDialog(
                        self,
                        cufe=cufe_xml,
                        consumo_kwh=consumo_val,
                        valor_kwh=valor_kwh_val,
                        valor_kwh_subsidiado=None,
                        fecha_maxima_pago=fecha_maxima_pago if fecha_maxima_pago else None,
                        valor_total=valor_total_xml if 'valor_total_xml' in locals() else None,
                        valor_total_pagar=valor_total_pagar_xml if 'valor_total_pagar_xml' in locals() else None,
                        intereses_mora=None,
                        orden_pago_id=1,  # Orden semilla por defecto
                    )
                    if dlg.exec():
                        vals = dlg.values()
                        creado_consumo, msg_consumo, id_consumo = guardar_consumo(
                            numero_cuenta=numero_cuenta_int,
                            cufe=vals["cufe"],
                            consumo_kwh=vals["consumo_kwh"],
                            valor_kwh=vals["valor_kwh"],
                            valor_kwh_subsidiado=vals["valor_kwh_subsidiado"],
                            fecha_maxima_pago=vals["fecha_maxima_pago"],
                            valor_total=vals["valor_total"],
                            valor_total_pagar=vals["valor_total_pagar"],
                            intereses_mora=vals["intereses_mora"],
                            orden_pago_id=vals.get("orden_pago_id", 1),  # Default a orden semilla
                            pago_realizado=vals.get("pago_realizado", False),
                        )
                        if creado_consumo:
                            resultado += f"✓ Consumo registrado (id={id_consumo})\n"
                        else:
                            resultado += f"⚠️ No se registró consumo: {msg_consumo}\n"
                    else:
                        resultado += "⏸ Registro de consumo cancelado por el usuario\n"
                except Exception as e:
                    resultado += f"⚠️ Error registrando consumo: {e}\n"

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
