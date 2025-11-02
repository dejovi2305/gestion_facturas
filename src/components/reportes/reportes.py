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
from PyQt6.QtGui import QFont, QColor
from config.database import (
    generar_reporte_consumos_por_periodo,
    generar_reporte_consumos_por_cuenta,
    generar_reporte_consumos_por_orden,
    generar_reporte_resumen_cuentas,
    generar_reporte_clientes,
    generar_reporte_ordenes_pago,
    generar_reporte_valor_total_por_mes,
    generar_reporte_consumos_por_mes,
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
        elif tipo == 7:  # Consumos por Mes
            # Usar controles mes/año
            self.dt_fecha_inicio.setEnabled(False)
            self.dt_fecha_fin.setEnabled(False)
            self.cmb_cuenta.setEnabled(False)
            try:
                self.cmb_mes.setEnabled(True)
                self.spn_ano.setEnabled(True)
            except Exception:
                pass
        elif tipo == 8:  # Comparativo mensual por cuenta
            # Usar los DateEdits para definir rango inicio/fin (se comparan meses completos)
            self.dt_fecha_inicio.setEnabled(True)
            self.dt_fecha_fin.setEnabled(True)
            self.cmb_cuenta.setEnabled(False)
    
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
            elif tipo == 7:  # Consumos del Mes
                self._generar_consumos_por_mes()
            elif tipo == 8:  # Comparativo mensual por cuenta
                self._generar_comparativo_consumos_rango()
            
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
            # datos: lista de dicts { 'numero_cuenta': int, 'valor_total_pagar': float }
            self.datos_reporte = datos
            self.headers_reporte = ['Número Cuenta', 'Total a Pagar']
            # Mostrar detalle por cuenta
            self._mostrar_en_tabla()

            # Calcular suma total del mes y mostrar en la etiqueta de info
            try:
                total_mes = sum(float(d.get('valor_total_pagar', 0) or 0) for d in datos)
                self.lbl_info.setText(f"✓ {len(datos)} registros generados — Suma total mes: ${total_mes:,.2f}")
            except Exception:
                # Si falla formato, mostrar mensaje simple
                self.lbl_info.setText(f"✓ {len(datos)} registros generados")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al generar reporte por mes: {e}")

    def _generar_consumos_por_mes(self):
        """Genera el reporte con todos los consumos del mes/año seleccionado."""
        try:
            mes = int(self.cmb_mes.currentIndex()) + 1
            ano = int(self.spn_ano.value())

            self.datos_reporte = generar_reporte_consumos_por_mes(mes, ano)
            self.headers_reporte = [
                'ID', 'Cuenta', 'CUFE', 'Consumo kWh', 'Valor kWh',
                'Fecha Máx. Pago', 'Núm. Orden', 'Total a Pagar'
            ]
            self._mostrar_en_tabla()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al generar consumos por mes: {e}")

    def _generar_comparativo_consumos_rango(self):
        """Genera un comparativo mes a mes por cuenta entre dos fechas (usar DateEdits como indicador de mes inicio/fin).

        El comportamiento esperado: si el usuario ingresa Fecha Inicio = 2025-01-01 y Fecha Fin = 2025-12-31,
        el comparativo será [Febrero - Enero], [Marzo - Febrero], ..., [Diciembre - Noviembre].
        """
        from config.database import generar_reporte_comparativo_consumos_rango
        from datetime import date

        fecha_inicio = self.dt_fecha_inicio.date().toPyDate()
        fecha_fin = self.dt_fecha_fin.date().toPyDate()

        if fecha_inicio > fecha_fin:
            QMessageBox.warning(self, "Rango inválido", "La fecha de inicio debe ser anterior o igual a la fecha fin.")
            return

        # Extraer meses y años
        mes_inicio = fecha_inicio.month
        ano_inicio = fecha_inicio.year
        mes_fin = fecha_fin.month
        ano_fin = fecha_fin.year

        datos = generar_reporte_comparativo_consumos_rango(mes_inicio, ano_inicio, mes_fin, ano_fin)

        # datos: lista de dicts {'cuenta','year','month','valor_total_pagar','consumo_kwh'}
        if not datos:
            self.datos_reporte = []
            self.headers_reporte = ['Cuenta', 'Periodo Actual', 'Valor Actual', 'Consumo Actual', 'Periodo Anterior', 'Valor Anterior', 'Consumo Anterior', 'Cambio Valor', 'Cambio Consumo']
            self._mostrar_en_tabla()
            self.lbl_info.setText("No se encontraron datos para el rango seleccionado")
            return

        # Construir estructura por cuenta y por mes ordenado
        from collections import defaultdict, OrderedDict

        cuentas = defaultdict(dict)
        meses_presentes = set()
        for r in datos:
            key = (int(r['year']), int(r['month']))
            cuentas[int(r['cuenta'])][key] = {
                'valor_total_pagar': float(r.get('valor_total_pagar', 0.0) or 0.0),
                'consumo_kwh': float(r.get('consumo_kwh', 0.0) or 0.0)
            }
            meses_presentes.add(key)

        # Generar lista ordenada de meses entre rango
        def generar_rango_meses(start_year, start_month, end_year, end_month):
            y, m = start_year, start_month
            out = []
            while (y < end_year) or (y == end_year and m <= end_month):
                out.append((y, m))
                if m == 12:
                    m = 1
                    y += 1
                else:
                    m += 1
            return out

        meses_ordenados = generar_rango_meses(ano_inicio, mes_inicio, ano_fin, mes_fin)

        resultado = []

        # Para cada cuenta, completar meses faltantes con 0 y luego comparar mes a mes
        for cuenta, datos_mes in sorted(cuentas.items()):
            # Build list of values per month
            valores = []
            for y_m in meses_ordenados:
                v = datos_mes.get(y_m, {'valor_total_pagar': 0.0, 'consumo_kwh': 0.0})
                valores.append((y_m, v['valor_total_pagar'], v['consumo_kwh']))

            # Comparar pares consecutivos
            for idx in range(1, len(valores)):
                (y_prev, m_prev), valor_prev, consumo_prev = valores[idx - 1][0], valores[idx - 1][1], valores[idx - 1][2]
                (y_cur, m_cur), valor_cur, consumo_cur = valores[idx][0], valores[idx][1], valores[idx][2]

                # Determine changes
                delta_valor = valor_cur - valor_prev
                delta_consumo = consumo_cur - consumo_prev

                def cambio_label_and_state(delta):
                    if delta > 0:
                        return ('Subió', 'subio')
                    elif delta < 0:
                        return ('Bajó', 'bajo')
                    else:
                        return ('Igual', 'igual')

                cambio_valor_label, cambio_valor_state = cambio_label_and_state(delta_valor)
                cambio_consumo_label, cambio_consumo_state = cambio_label_and_state(delta_consumo)

                periodo_actual = f"{m_cur:02d}-{y_cur}"
                periodo_anterior = f"{m_prev:02d}-{y_prev}"

                resultado.append({
                    'cuenta': cuenta,
                    'periodo_actual': periodo_actual,
                    'valor_actual': round(valor_cur, 2),
                    'consumo_actual': round(consumo_cur, 2),
                    'periodo_anterior': periodo_anterior,
                    'valor_anterior': round(valor_prev, 2),
                    'consumo_anterior': round(consumo_prev, 2),
                    'cambio_valor': cambio_valor_state,
                    'cambio_consumo': cambio_consumo_state,
                })

        # Preparar headers y datos para mostrar
        self.datos_reporte = resultado
        self.headers_reporte = ['Cuenta', 'Periodo Actual', 'Valor Actual', 'Consumo Actual', 'Periodo Anterior', 'Valor Anterior', 'Consumo Anterior', 'Cambio Valor', 'Cambio Consumo']
        self._mostrar_en_tabla()

    
    def _mostrar_en_tabla(self):
        """Muestra los datos del reporte en la tabla de vista previa."""
        if not self.datos_reporte:
            self.tbl_vista_previa.setRowCount(0)
            self.tbl_vista_previa.setColumnCount(0)
            return
        # Excluir visualmente la columna 'cufe' en la vista previa.
        # Nota: no modificamos self.headers_reporte porque el CSV debe conservar
        # todas las columnas; aquí solo construimos los headers visibles.
        display_headers = [h for h in self.headers_reporte if self._header_to_key(h) != 'cufe']

        # Configurar tabla usando solo los headers visibles
        self.tbl_vista_previa.setRowCount(len(self.datos_reporte))
        self.tbl_vista_previa.setColumnCount(len(display_headers))
        self.tbl_vista_previa.setHorizontalHeaderLabels(display_headers)

        # Llenar datos (usando sólo display_headers)
        for i, fila in enumerate(self.datos_reporte):
            for j, header in enumerate(display_headers):
                key = self._header_to_key(header)
                valor = str(fila.get(key, ''))

                # Render special semaforo cells for comparativo
                item = QTableWidgetItem()
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                if key in ('cambio_valor', 'cambio_consumo'):
                    # Expect values like 'subio', 'bajo', 'igual'
                    state = str(fila.get(key, '')).lower()
                    if state == 'subio':
                        item.setText('Subió')
                        try:
                            item.setBackground(QColor('#ffcccc'))
                        except Exception:
                            pass
                    elif state == 'bajo':
                        item.setText('Bajó')
                        try:
                            item.setBackground(QColor('#ccffcc'))
                        except Exception:
                            pass
                    else:
                        item.setText('Igual')
                        try:
                            item.setBackground(QColor('#efefef'))
                        except Exception:
                            pass
                else:
                    item.setText(valor)

                self.tbl_vista_previa.setItem(i, j, item)
        
    # Si el reporte contiene la columna valor_total_pagar, agregar fila TOTAL al final
        try:
            # Determinar si alguno de los headers visibles corresponde a valor_total_pagar
            display_keys = [self._header_to_key(h) for h in display_headers]
            if 'valor_total_pagar' in display_keys:
                # Calcular suma
                total_mes = sum(float(row.get('valor_total_pagar', 0) or 0) for row in self.datos_reporte)
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
                col_index = display_keys.index('valor_total_pagar')
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
            # NOTE: keep 'Total a Pagar' mapped to 'valor_total_pagar' so consumption rows
            # and aggregated rows share the same key used by the table/export logic.
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

                # Si el reporte contiene valor_total_pagar, escribir fila TOTAL al final
                try:
                    keys = [self._header_to_key(h) for h in self.headers_reporte]
                    if 'valor_total_pagar' in keys:
                        total = sum(float(d.get('valor_total_pagar', 0) or 0) for d in self.datos_reporte)
                        total_row = {k: '' for k in keys}
                        # Poner etiqueta TOTAL en la primera columna
                        total_row[keys[0]] = 'TOTAL'
                        total_row['valor_total_pagar'] = f"{total:.2f}"
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
