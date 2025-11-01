import csv
from pathlib import Path
from datetime import date
from PyQt6.uic import loadUi
from PyQt6.QtWidgets import (
    QWidget, QTableWidget, QTableWidgetItem, QPushButton, 
    QComboBox, QDateEdit, QLabel, QFileDialog, QMessageBox, QHeaderView
)
from PyQt6.QtWidgets import QSpinBox
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont
from config.database import (
    generar_reporte_consumos_por_periodo,
    generar_reporte_consumos_por_cuenta,
    generar_reporte_consumos_por_orden,
    generar_reporte_resumen_cuentas,
    generar_reporte_clientes,
    generar_reporte_ordenes_pago,
    generar_reporte_valor_total_por_mes,
    listar_cuentas,
    listar_ordenes_pago
)


class ReportesWidget(QWidget):
    """Widget para generación y exportación de reportes."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Cargar UI (robusto para modo frozen/dev)
        from utils.ui import resolve_ui_path
        ui_path = resolve_ui_path(__file__, ui_filename="reportes.ui")
        loadUi(ui_path, self)
        
        # Referencias a widgets
        self.cmb_tipo_reporte: QComboBox
        self.dt_fecha_inicio: QDateEdit
        self.dt_fecha_fin: QDateEdit
        self.cmb_cuenta: QComboBox
        self.btn_generar: QPushButton
        self.btn_exportar: QPushButton
        self.tbl_vista_previa: QTableWidget
        self.lbl_info: QLabel
        
        # Datos del reporte actual
        self.datos_reporte = []
        self.headers_reporte = []
        
        # Configurar fechas por defecto (último mes)
        hoy = QDate.currentDate()
        hace_un_mes = hoy.addMonths(-1)
        self.dt_fecha_inicio.setDate(hace_un_mes)
        self.dt_fecha_fin.setDate(hoy)
        
        # Cargar cuentas en el combo
        self._cargar_cuentas()

        # Configurar controles mes/año (si existen en UI)
        try:
            hoy_q = QDate.currentDate()
            # cmb_mes: 0-based index (Enero=0)
            self.cmb_mes.setCurrentIndex(hoy_q.month() - 1)
            self.spn_ano.setValue(hoy_q.year())
        except Exception:
            # Si UI no tiene esos controles por alguna razón, ignorar
            pass
        
        # Conectar señales
        self.btn_generar.clicked.connect(self._generar_reporte)
        self.btn_exportar.clicked.connect(self._exportar_csv)
        self.cmb_tipo_reporte.currentIndexChanged.connect(self._on_tipo_reporte_changed)
        
        # Configurar visibilidad inicial de filtros
        self._on_tipo_reporte_changed()
    
    def _cargar_cuentas(self):
        """Carga las cuentas activas en el combo."""
        self.cmb_cuenta.clear()
        self.cmb_cuenta.addItem("Todas las cuentas", None)
        
        cuentas = listar_cuentas(activo=True)
        for cuenta in cuentas:
            self.cmb_cuenta.addItem(
                f"Cuenta {cuenta.numero_cuenta}",
                cuenta.numero_cuenta
            )
    
    def _on_tipo_reporte_changed(self):
        """Maneja el cambio de tipo de reporte para mostrar/ocultar filtros."""
        tipo = self.cmb_tipo_reporte.currentIndex()
        
        # 0: Consumos por Período (fecha inicio, fecha fin, cuenta opcional)
        # 1: Consumos por Cuenta (solo cuenta)
        # 2: Consumos por Orden de Pago (ninguno, se selecciona después)
        # 3: Resumen de Cuentas (ninguno)
        # 4: Listado de Clientes (ninguno)
        # 5: Órdenes de Pago (fecha inicio, fecha fin opcional)
    # 6: Valor Total a Pagar por Mes (mes, año)
        
        # Mostrar/ocultar según tipo
        if tipo == 0:  # Consumos por Período
            self.dt_fecha_inicio.setEnabled(True)
            self.dt_fecha_fin.setEnabled(True)
            self.cmb_cuenta.setEnabled(True)
        elif tipo == 1:  # Consumos por Cuenta
            self.dt_fecha_inicio.setEnabled(False)
            self.dt_fecha_fin.setEnabled(False)
            self.cmb_cuenta.setEnabled(True)
            # Permitir seleccionar "Todas las cuentas"
        elif tipo == 2:  # Consumos por Orden
            self.dt_fecha_inicio.setEnabled(False)
            self.dt_fecha_fin.setEnabled(False)
            self.cmb_cuenta.setEnabled(False)
        elif tipo == 3:  # Resumen de Cuentas
            self.dt_fecha_inicio.setEnabled(False)
            self.dt_fecha_fin.setEnabled(False)
            self.cmb_cuenta.setEnabled(False)
        elif tipo == 4:  # Listado de Clientes
            self.dt_fecha_inicio.setEnabled(False)
            self.dt_fecha_fin.setEnabled(False)
            self.cmb_cuenta.setEnabled(False)
        elif tipo == 5:  # Órdenes de Pago
            self.dt_fecha_inicio.setEnabled(True)
            self.dt_fecha_fin.setEnabled(True)
            self.cmb_cuenta.setEnabled(False)
        elif tipo == 6:  # Valor Total por Mes
            # Usar controles mes/año
            # Deshabilitar los DateEdits y habilitar cmb_mes/spn_ano
            self.dt_fecha_inicio.setEnabled(False)
            self.dt_fecha_fin.setEnabled(False)
            self.cmb_cuenta.setEnabled(False)
            try:
                self.cmb_mes.setEnabled(True)
                self.spn_ano.setEnabled(True)
            except Exception:
                pass
    
    def _generar_reporte(self):
        """Genera el reporte seleccionado y lo muestra en la tabla."""
        tipo = self.cmb_tipo_reporte.currentIndex()
        
        try:
            if tipo == 0:  # Consumos por Período
                self._generar_consumos_por_periodo()
            elif tipo == 1:  # Consumos por Cuenta
                self._generar_consumos_por_cuenta()
            elif tipo == 2:  # Consumos por Orden de Pago
                self._generar_consumos_por_orden()
            elif tipo == 3:  # Resumen de Cuentas
                self._generar_resumen_cuentas()
            elif tipo == 4:  # Listado de Clientes
                self._generar_listado_clientes()
            elif tipo == 5:  # Órdenes de Pago
                self._generar_ordenes_pago()
            elif tipo == 6:  # Valor Total a Pagar por Mes
                self._generar_valor_total_por_mes()
            
            # Habilitar botón de exportar si hay datos
            self.btn_exportar.setEnabled(len(self.datos_reporte) > 0)
            
            if len(self.datos_reporte) > 0:
                self.lbl_info.setText(f"✓ {len(self.datos_reporte)} registros generados")
            else:
                self.lbl_info.setText("No se encontraron datos para los criterios seleccionados")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al generar reporte: {str(e)}")
    
    def _generar_consumos_por_periodo(self):
        """Genera reporte de consumos por período."""
        fecha_inicio = self.dt_fecha_inicio.date().toPyDate()
        fecha_fin = self.dt_fecha_fin.date().toPyDate()
        cuenta = self.cmb_cuenta.currentData()
        
        self.datos_reporte = generar_reporte_consumos_por_periodo(
            fecha_inicio, fecha_fin, cuenta
        )
        self.headers_reporte = [
            'ID', 'Cuenta', 'CUFE', 'Consumo kWh', 'Valor kWh',
            'Fecha Máx. Pago', 'Núm. Orden', 'Total a Pagar'
        ]
        self._mostrar_en_tabla()
    
    def _generar_consumos_por_cuenta(self):
        """Genera reporte de consumos por cuenta."""
        cuenta = self.cmb_cuenta.currentData()
        
        # Permitir None para mostrar todas las cuentas
        self.datos_reporte = generar_reporte_consumos_por_cuenta(cuenta)
        self.headers_reporte = [
            'ID', 'Cuenta', 'CUFE', 'Consumo kWh', 'Valor kWh',
            'Fecha Máx. Pago', 'Núm. Orden', 'Total a Pagar'
        ]
        self._mostrar_en_tabla()
    
    def _generar_consumos_por_orden(self):
        """Genera reporte de consumos por orden de pago."""
        # Solicitar número de orden
        ordenes = listar_ordenes_pago()
        if not ordenes or len(ordenes) == 0:
            QMessageBox.warning(self, "Advertencia", "No hay órdenes de pago disponibles")
            return
        
        from PyQt6.QtWidgets import QInputDialog
        items = [f"Orden {o.numero_orden}" for o in ordenes if o.id != 1]
        
        if not items:
            QMessageBox.warning(self, "Advertencia", "No hay órdenes de pago disponibles")
            return
        
        item, ok = QInputDialog.getItem(
            self, "Seleccionar Orden", "Número de Orden:", items, 0, False
        )
        
        if ok and item:
            numero_orden = int(item.split()[1])
            self.datos_reporte = generar_reporte_consumos_por_orden(numero_orden)
            self.headers_reporte = [
                'ID', 'Cuenta', 'CUFE', 'Consumo kWh', 'Valor kWh',
                'Fecha Máx. Pago', 'Núm. Orden', 'Total a Pagar'
            ]
            self._mostrar_en_tabla()
    
    def _generar_resumen_cuentas(self):
        """Genera reporte resumen de cuentas."""
        self.datos_reporte = generar_reporte_resumen_cuentas()
        self.headers_reporte = [
            'ID Cuenta', 'Número Cuenta', 'Activa', 'Último CUFE',
            'Último Consumo kWh', 'Última Fecha Pago', 'Último Valor a Pagar'
        ]
        self._mostrar_en_tabla()
    
    def _generar_listado_clientes(self):
        """Genera reporte de clientes."""
        self.datos_reporte = generar_reporte_clientes()
        self.headers_reporte = ['ID', 'Cuenta', 'Nombre', 'Dirección', 'Estrato', 'Núm. Medidor', 'Activo']
        self._mostrar_en_tabla()
    
    def _generar_ordenes_pago(self):
        """Genera reporte de órdenes de pago."""
        fecha_inicio = self.dt_fecha_inicio.date().toPyDate()
        fecha_fin = self.dt_fecha_fin.date().toPyDate()
        
        self.datos_reporte = generar_reporte_ordenes_pago(fecha_inicio, fecha_fin)
        self.headers_reporte = ['ID', 'Número Orden', 'Núm. Consumos', 'Total']
        self._mostrar_en_tabla()

    def _generar_valor_total_por_mes(self):
        """Genera reporte que muestra el total a pagar por cuenta para un mes y año dados."""
        try:
            mes = int(self.cmb_mes.currentIndex()) + 1
            ano = int(self.spn_ano.value())

            datos = generar_reporte_valor_total_por_mes(mes, ano)
            # datos: lista de dicts { 'numero_cuenta': int, 'total_a_pagar': float }
            self.datos_reporte = datos
            self.headers_reporte = ['Número Cuenta', 'Total a Pagar']
            # Mostrar detalle por cuenta
            self._mostrar_en_tabla()

            # Calcular suma total del mes y mostrar en la etiqueta de info
            try:
                total_mes = sum(float(d.get('total_a_pagar', 0) or 0) for d in datos)
                self.lbl_info.setText(f"✓ {len(datos)} registros generados — Suma total mes: ${total_mes:,.2f}")
            except Exception:
                # Si falla formato, mostrar mensaje simple
                self.lbl_info.setText(f"✓ {len(datos)} registros generados")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al generar reporte por mes: {e}")
    
    def _mostrar_en_tabla(self):
        """Muestra los datos del reporte en la tabla de vista previa."""
        if not self.datos_reporte:
            self.tbl_vista_previa.setRowCount(0)
            self.tbl_vista_previa.setColumnCount(0)
            return
        
        # Configurar tabla
        self.tbl_vista_previa.setRowCount(len(self.datos_reporte))
        self.tbl_vista_previa.setColumnCount(len(self.headers_reporte))
        self.tbl_vista_previa.setHorizontalHeaderLabels(self.headers_reporte)
        
        # Llenar datos
        for i, fila in enumerate(self.datos_reporte):
            for j, header in enumerate(self.headers_reporte):
                # Obtener clave del dict (convertir header a snake_case)
                key = self._header_to_key(header)
                valor = str(fila.get(key, ''))
                
                item = QTableWidgetItem(valor)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tbl_vista_previa.setItem(i, j, item)
        
        # Si el reporte contiene la columna total_a_pagar, agregar fila TOTAL al final
        try:
            # Determinar si alguno de los headers corresponde a total_a_pagar
            columns_keys = [self._header_to_key(h) for h in self.headers_reporte]
            if 'total_a_pagar' in columns_keys:
                # Calcular suma
                total_mes = sum(float(row.get('total_a_pagar', 0) or 0) for row in self.datos_reporte)
                # Añadir fila final
                last_row = self.tbl_vista_previa.rowCount()
                self.tbl_vista_previa.insertRow(last_row)
                # Colocar etiqueta TOTAL en la primera columna
                item_total_label = QTableWidgetItem('TOTAL')
                font_b = QFont()
                font_b.setBold(True)
                item_total_label.setFont(font_b)
                item_total_label.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tbl_vista_previa.setItem(last_row, 0, item_total_label)

                # Colocar suma en la columna correspondiente
                col_index = columns_keys.index('total_a_pagar')
                item_total_val = QTableWidgetItem(f"{total_mes:,.2f}")
                item_total_val.setFont(font_b)
                item_total_val.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tbl_vista_previa.setItem(last_row, col_index, item_total_val)
        except Exception:
            pass

        # Ajustar columnas
        self.tbl_vista_previa.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
    
    def _header_to_key(self, header):
        """Convierte un header de tabla a la clave del diccionario."""
        mapping = {
            'ID': 'id',
            'Cuenta': 'cuenta',
            'CUFE': 'cufe',
            'Consumo kWh': 'consumo_kwh',
            'Valor kWh': 'valor_kwh',
            'Fecha Máx. Pago': 'fecha_maxima_pago',
            'Núm. Orden': 'numero_orden',
            'Total a Pagar': 'valor_total_pagar',
            'ID Cuenta': 'id_cuenta',
            'Número Cuenta': 'numero_cuenta',
            'Activa': 'activa',
            'Último CUFE': 'ultimo_cufe',
            'Último Consumo kWh': 'ultimo_consumo_kwh',
            'Última Fecha Pago': 'ultima_fecha_pago',
            'Último Valor a Pagar': 'ultimo_valor_pagar',
            'Total a Pagar': 'total_a_pagar',
            'Nombre': 'nombre',
            'Email': 'email',
            'Teléfono': 'telefono',
            'Dirección': 'direccion',
            'Estrato': 'estrato',
            'Núm. Medidor': 'numero_medidor',
            'Activo': 'activo',
            'Número Orden': 'numero_orden',
            'Núm. Consumos': 'num_consumos',
            'Total': 'total'
        }
        return mapping.get(header, header.lower().replace(' ', '_'))
    
    def _exportar_csv(self):
        """Exporta el reporte actual a un archivo CSV."""
        if not self.datos_reporte:
            QMessageBox.warning(self, "Advertencia", "No hay datos para exportar")
            return
        
        # Solicitar ubicación del archivo
        tipo_reporte = self.cmb_tipo_reporte.currentText().replace(' ', '_').lower()
        nombre_sugerido = f"reporte_{tipo_reporte}_{date.today().strftime('%Y%m%d')}.csv"
        
        ruta, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar Reporte CSV",
            nombre_sugerido,
            "Archivos CSV (*.csv)"
        )
        
        if not ruta:
            return
        
        try:
            with open(ruta, 'w', newline='', encoding='utf-8-sig') as archivo:
                writer = csv.DictWriter(archivo, fieldnames=[
                    self._header_to_key(h) for h in self.headers_reporte
                ])
                
                # Escribir headers con nombres amigables
                writer.writerow({
                    self._header_to_key(h): h for h in self.headers_reporte
                })
                
                # Escribir datos
                writer.writerows(self.datos_reporte)

                # Si el reporte contiene total_a_pagar, escribir fila TOTAL al final
                try:
                    keys = [self._header_to_key(h) for h in self.headers_reporte]
                    if 'total_a_pagar' in keys:
                        total = sum(float(d.get('total_a_pagar', 0) or 0) for d in self.datos_reporte)
                        total_row = {k: '' for k in keys}
                        # Poner etiqueta TOTAL en la primera columna
                        total_row[keys[0]] = 'TOTAL'
                        total_row['total_a_pagar'] = f"{total:.2f}"
                        writer.writerow(total_row)
                except Exception:
                    pass
            
            QMessageBox.information(
                self, "Éxito",
                f"Reporte exportado exitosamente a:\n{ruta}"
            )
        except Exception as e:
            QMessageBox.critical(
                self, "Error",
                f"Error al exportar el reporte: {str(e)}"
            )
