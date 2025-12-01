import os
import sys
import zipfile
import tempfile
import shutil
from pathlib import Path
from PyQt6.QtWidgets import QWidget, QFileDialog, QMessageBox, QProgressDialog
from PyQt6.QtCore import Qt
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
        self.ruta_archivo = None  # Puede ser PDF, XML, ZIP o carpeta
        self.modo_masivo = False
        self.archivos_a_procesar = []  # Lista de archivos XML a procesar
        
        # Conectar señales
        self.btn_seleccionar.clicked.connect(self._seleccionar_archivo)
        self.btn_seleccionar_carpeta.clicked.connect(self._seleccionar_carpeta)
        self.btn_procesar.clicked.connect(self._procesar_archivo)
        
        # Conectar cambio de modo
        self.rb_individual.toggled.connect(self._on_modo_changed)
        self.rb_masivo.toggled.connect(self._on_modo_changed)
    
    def _on_modo_changed(self):
        """Maneja el cambio entre modo individual y masivo."""
        self.modo_masivo = self.rb_masivo.isChecked()
        self.btn_seleccionar_carpeta.setVisible(self.modo_masivo)
        
        # Actualizar texto del botón seleccionar
        if self.modo_masivo:
            self.btn_seleccionar.setText("📦 ZIP")
            self.txt_ruta_archivo.setPlaceholderText("Ningún archivo ZIP o carpeta seleccionada")
        else:
            self.btn_seleccionar.setText("Seleccionar")
            self.txt_ruta_archivo.setPlaceholderText("Ningún archivo seleccionado")
        
        # Limpiar selección anterior
        self.ruta_archivo = None
        self.archivos_a_procesar = []
        self.txt_ruta_archivo.clear()
        self.txt_resultado.clear()
        self.btn_procesar.setEnabled(False)
    
    def _seleccionar_archivo(self):
        """Abre un diálogo para seleccionar el archivo de la factura (XML o ZIP)."""
        if self.modo_masivo:
            # Modo masivo: seleccionar archivo ZIP
            archivo, _ = QFileDialog.getOpenFileName(
                self,
                "Seleccionar archivo ZIP con facturas",
                "",
                "Archivos ZIP (*.zip)"
            )
        else:
            # Modo individual: seleccionar archivo XML
            archivo, _ = QFileDialog.getOpenFileName(
                self,
                "Seleccionar Factura XML",
                "",
                "XML (*.xml)"
            )
        
        if archivo:
            self.ruta_archivo = archivo
            self.txt_ruta_archivo.setText(archivo)
            
            if self.modo_masivo:
                # Contar archivos XML en el ZIP
                try:
                    count = self._contar_xml_en_zip(archivo)
                    self.txt_resultado.setPlainText(f"📦 ZIP seleccionado: {count} archivos XML encontrados")
                    self.archivos_a_procesar = []  # Se procesarán después
                    self.btn_procesar.setEnabled(count > 0)
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Error al leer ZIP: {str(e)}")
                    self.btn_procesar.setEnabled(False)
            else:
                self.btn_procesar.setEnabled(True)
                self.txt_resultado.clear()
    
    def _seleccionar_carpeta(self):
        """Abre un diálogo para seleccionar una carpeta con facturas XML."""
        carpeta = QFileDialog.getExistingDirectory(
            self,
            "Seleccionar carpeta con facturas XML"
        )
        
        if carpeta:
            self.ruta_archivo = carpeta
            self.txt_ruta_archivo.setText(carpeta)
            # Buscar archivos XML en la carpeta y dentro de ZIPs en la misma carpeta
            try:
                archivos_xml = list(Path(carpeta).glob("*.xml"))
                zip_files = list(Path(carpeta).glob("*.zip"))

                # Contar XMLs directos
                count = len(archivos_xml)

                # Contar entradas XML dentro de cada ZIP (no extraemos aquí)
                for z in zip_files:
                    try:
                        with zipfile.ZipFile(str(z), 'r') as zip_ref:
                            xml_files_in_zip = [f for f in zip_ref.namelist() if f.lower().endswith('.xml')]
                            count += len(xml_files_in_zip)
                    except Exception:
                        # Ignorar ZIPs corruptos/ilegibles en este punto
                        continue

                # Guardar solo los XML encontrados directamente en la carpeta.
                # Los XML dentro de ZIPs se procesarán al ejecutar _procesar_masivo (se extraerán a un temp dir).
                self.archivos_a_procesar = [str(f) for f in archivos_xml]
                self.txt_resultado.setPlainText(f"📁 Carpeta seleccionada: {count} archivos XML encontrados (incluyendo ZIPs)")
                self.btn_procesar.setEnabled(count > 0)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Error al leer carpeta: {str(e)}")
                self.btn_procesar.setEnabled(False)
    
    def _contar_xml_en_zip(self, zip_path):
        """Cuenta los archivos XML en un ZIP."""
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            xml_files = [f for f in zip_ref.namelist() if f.lower().endswith('.xml')]
            return len(xml_files)
    
    # Eliminado: soporte y utilidades de PDF
    
    def _procesar_archivo(self):
        """Decide el flujo según el modo (individual o masivo)."""
        if not self.ruta_archivo:
            QMessageBox.warning(self, "Error", "No se ha seleccionado ningún archivo o carpeta.")
            return
        
        if self.modo_masivo:
            return self._procesar_masivo()
        else:
            # Modo individual
            _, ext = os.path.splitext(self.ruta_archivo)
            if ext.lower() == ".xml":
                return self._procesar_xml_extraer_datos()
            else:
                QMessageBox.warning(self, "Tipo de archivo no soportado", "Solo se admite XML (*.xml).")
                return

    # Eliminado: extracción de datos desde PDF
    
    def _procesar_masivo(self):
        """Procesa múltiples archivos XML desde ZIP o carpeta."""
        archivos_xml = []
        temp_dir = None
        
        try:
            # Determinar si es ZIP o carpeta
            if os.path.isfile(self.ruta_archivo) and self.ruta_archivo.lower().endswith('.zip'):
                # Extraer ZIP a directorio temporal
                temp_dir = tempfile.mkdtemp()
                with zipfile.ZipFile(self.ruta_archivo, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                
                # Buscar todos los archivos XML
                archivos_xml = list(Path(temp_dir).rglob("*.xml"))
            
            elif os.path.isdir(self.ruta_archivo):
                # Carpeta directa: buscar XMLs y también revisar ZIPs dentro de la carpeta
                archivos_xml = list(Path(self.ruta_archivo).glob("*.xml"))

                # Buscar ZIPs en la carpeta y extraer sus XMLs a un directorio temporal
                zip_files = list(Path(self.ruta_archivo).glob("*.zip"))
                if zip_files:
                    temp_dir = tempfile.mkdtemp()
                    for z in zip_files:
                        try:
                            with zipfile.ZipFile(str(z), 'r') as zip_ref:
                                zip_ref.extractall(temp_dir)
                        except Exception:
                            # Si un ZIP falla al extraer, lo saltamos y seguimos con los demás
                            continue
                    # Agregar XMLs extraídos de los ZIPs
                    archivos_xml_from_zips = list(Path(temp_dir).rglob("*.xml"))
                    archivos_xml.extend(archivos_xml_from_zips)
            
            else:
                QMessageBox.warning(self, "Error", "Selección no válida.")
                return
            
            if not archivos_xml:
                QMessageBox.warning(self, "Advertencia", "No se encontraron archivos XML.")
                return
            
            # Confirmar procesamiento
            respuesta = QMessageBox.question(
                self, "Confirmar Procesamiento Masivo",
                f"Se encontraron {len(archivos_xml)} archivos XML.\n\n"
                f"¿Deseas procesarlos todos?\n\n"
                f"Nota: Se procesarán automáticamente sin confirmación individual.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if respuesta != QMessageBox.StandardButton.Yes:
                return
            
            # Crear diálogo de progreso
            progress = QProgressDialog("Procesando facturas...", "Cancelar", 0, len(archivos_xml), self)
            progress.setWindowTitle("Procesamiento Masivo")
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.setMinimumDuration(0)
            
            # Estadísticas
            exitosos = 0
            errores = 0
            detalles_errores = []
            
            # Procesar cada archivo
            for i, archivo_xml in enumerate(archivos_xml):
                if progress.wasCanceled():
                    break
                
                progress.setValue(i)
                progress.setLabelText(f"Procesando {archivo_xml.name}... ({i+1}/{len(archivos_xml)})")
                
                try:
                    resultado = self._procesar_xml_silencioso(str(archivo_xml))
                    if resultado['exito']:
                        exitosos += 1
                    else:
                        errores += 1
                        detalles_errores.append(f"{archivo_xml.name}: {resultado['mensaje']}")
                except Exception as e:
                    errores += 1
                    detalles_errores.append(f"{archivo_xml.name}: {str(e)}")
            
            progress.setValue(len(archivos_xml))
            
            # Mostrar resumen
            resumen = f"{'='*50}\n"
            resumen += f"PROCESAMIENTO MASIVO COMPLETADO\n"
            resumen += f"{'='*50}\n\n"
            resumen += f"✅ Exitosos: {exitosos}\n"
            resumen += f"❌ Errores: {errores}\n"
            resumen += f"📊 Total procesados: {exitosos + errores}\n\n"
            
            if detalles_errores:
                resumen += f"{'='*50}\n"
                resumen += f"DETALLES DE ERRORES:\n"
                resumen += f"{'='*50}\n\n"
                for detalle in detalles_errores[:10]:  # Mostrar primeros 10 errores
                    resumen += f"• {detalle}\n"
                
                if len(detalles_errores) > 10:
                    resumen += f"\n... y {len(detalles_errores) - 10} errores más.\n"
            
            self.txt_resultado.setPlainText(resumen)
            
            # Mensaje de finalización
            QMessageBox.information(
                self, "Procesamiento Completado",
                f"Procesamiento masivo completado.\n\n"
                f"✅ Exitosos: {exitosos}\n"
                f"❌ Errores: {errores}"
            )
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error en procesamiento masivo:\n{str(e)}")
        
        finally:
            # Limpiar directorio temporal si se creó
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except Exception:
                    pass
    
    def _procesar_xml_silencioso(self, ruta_xml):
        """
        Procesa un archivo XML sin mostrar diálogos de confirmación.
        Retorna dict con 'exito' (bool) y 'mensaje' (str).
        """
        try:
            # Extraer número de cuenta
            numero_cuenta, _ = extraer_numero_cuenta(ruta_xml)
            if not numero_cuenta:
                return {'exito': False, 'mensaje': 'No se encontró número de cuenta'}
            
            try:
                numero_cuenta_int = int(numero_cuenta)
            except Exception:
                return {'exito': False, 'mensaje': f'Número de cuenta inválido: {numero_cuenta}'}
            
            # Verificar existencia
            cuenta_existe = existe_cuenta(numero_cuenta_int)
            cliente_existe = existe_cliente_para_cuenta(numero_cuenta_int)
            
            # Si no existen, crear cuenta y cliente
            if not (cuenta_existe and cliente_existe):
                # Extraer datos de cliente
                nombre_cliente, _ = extraer_nombre_cliente(ruta_xml)
                direccion, _ = extraer_direccion_cliente(ruta_xml)
                estrato, _ = extraer_estrato_cliente(ruta_xml)
                numero_medidor, _ = extraer_numero_medidor(ruta_xml)
                
                # Guardar cuenta
                try:
                    guardar_cuenta_si_no_existe(numero_cuenta_int)
                except Exception as e:
                    return {'exito': False, 'mensaje': f'Error al guardar cuenta: {e}'}
                
                # Guardar cliente
                try:
                    guardar_cliente_si_no_existe(
                        numero_cuenta=numero_cuenta_int,
                        nombre=nombre_cliente if nombre_cliente else None,
                        direccion=direccion if direccion else None,
                        estrato=str(estrato) if estrato is not None else None,
                        numero_medidor=numero_medidor if numero_medidor else None,
                    )
                except Exception as e:
                    return {'exito': False, 'mensaje': f'Error al guardar cliente: {e}'}
            
            # Extraer datos de consumo
            consumo_kwh_lista, _ = extraer_consumo_kwh(ruta_xml)
            valor_kwh_lista, _ = extraer_valor_kwh(ruta_xml)
            fecha_maxima_pago, _ = extraer_fecha_maxima_pago(ruta_xml)
            valor_total_xml, _ = extraer_valor_total(ruta_xml)
            valor_total_pagar_xml, _ = extraer_valor_total_pagar(ruta_xml)
            cufe_xml, _ = extraer_cufe(ruta_xml)
            
            consumo_val = consumo_kwh_lista[0] if (consumo_kwh_lista and len(consumo_kwh_lista) > 0) else 0
            valor_kwh_val = valor_kwh_lista[0] if (valor_kwh_lista and len(valor_kwh_lista) > 0) else 0.0
            
            # Guardar consumo automáticamente (sin diálogo)
            creado_consumo, msg_consumo, id_consumo = guardar_consumo(
                numero_cuenta=numero_cuenta_int,
                cufe=cufe_xml,
                consumo_kwh=consumo_val,
                valor_kwh=valor_kwh_val,
                valor_kwh_subsidiado=None,
                fecha_maxima_pago=fecha_maxima_pago if fecha_maxima_pago else None,
                valor_total=valor_total_xml if valor_total_xml else None,
                valor_total_pagar=valor_total_pagar_xml if valor_total_pagar_xml else None,
                intereses_mora=None,
                orden_pago_id=1,  # Orden semilla por defecto
                pago_realizado=False,
            )
            
            if creado_consumo:
                return {'exito': True, 'mensaje': f'Consumo registrado (ID: {id_consumo})'}
            else:
                return {'exito': False, 'mensaje': msg_consumo}
        
        except Exception as e:
            return {'exito': False, 'mensaje': str(e)}

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
