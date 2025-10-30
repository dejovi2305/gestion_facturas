from pathlib import Path
from PyQt6.uic import loadUi
from PyQt6.QtWidgets import (
    QWidget, QTableWidget, QTableWidgetItem,
    QPushButton, QComboBox, QDialog, QFormLayout, QDialogButtonBox,
    QLineEdit, QMessageBox, QHeaderView, QDateEdit
)
from PyQt6.QtCore import Qt, QDate

from config.database import (
    listar_consumos, obtener_consumo_por_id, actualizar_consumo, eliminar_consumo,
    listar_cuentas, listar_ordenes_pago
)
from decimal import Decimal


class ConsumoDialog(QDialog):
    def __init__(self, parent=None, *, titulo="Consumo", consumo_data: dict | None = None):
        super().__init__(parent)
        self.setWindowTitle(titulo)
        self.setMinimumWidth(450)
        form = QFormLayout(self)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.es_edicion = consumo_data is not None

        # CUFE
        if self.es_edicion:
            # Edición: CUFE solo lectura
            self.ed_cufe = QLineEdit(self)
            self.ed_cufe.setReadOnly(True)
            self.ed_cufe.setText(consumo_data.get("cufe", ""))
            form.addRow("CUFE:", self.ed_cufe)
        else:
            # Creación: CUFE editable
            self.ed_cufe = QLineEdit(self)
            self.ed_cufe.setPlaceholderText("CUFE/UUID único de la factura")
            form.addRow("CUFE:", self.ed_cufe)

        # Cuenta
        if self.es_edicion:
            # Edición: Cuenta solo lectura
            self.ed_cuenta = QLineEdit(self)
            self.ed_cuenta.setReadOnly(True)
            self.ed_cuenta.setText(str(consumo_data.get("cuenta", "")))
            form.addRow("Cuenta:", self.ed_cuenta)
        else:
            # Creación: Combo de cuentas activas
            self.combo_cuenta = QComboBox(self)
            self.combo_cuenta.setMinimumWidth(250)
            self.combo_cuenta.addItem("-- Seleccione una cuenta --", None)
            cuentas = listar_cuentas(activo=True)
            for c in cuentas:
                self.combo_cuenta.addItem(str(c.numero_cuenta), c.numero_cuenta)
            form.addRow("Cuenta:", self.combo_cuenta)

        # Consumo kWh
        self.ed_consumo_kwh = QLineEdit(self)
        self.ed_consumo_kwh.setPlaceholderText("Consumo en kWh")
        self.ed_consumo_kwh.setText(str(consumo_data.get("consumo_kwh", "")) if consumo_data else "")

        # Valor kWh
        self.ed_valor_kwh = QLineEdit(self)
        self.ed_valor_kwh.setPlaceholderText("Valor por kWh")
        self.ed_valor_kwh.setText(str(consumo_data.get("valor_kwh", "")) if consumo_data else "")

        # Valor kWh subsidiado
        self.ed_valor_kwh_sub = QLineEdit(self)
        self.ed_valor_kwh_sub.setPlaceholderText("Valor kWh subsidiado")
        self.ed_valor_kwh_sub.setText(str(consumo_data.get("valor_kwh_subsidiado", "")) if consumo_data else "")

        # Fecha máxima de pago
        self.date_max_pago = QDateEdit(self)
        self.date_max_pago.setCalendarPopup(True)
        self.date_max_pago.setDisplayFormat("yyyy-MM-dd")
        if consumo_data and consumo_data.get("fecha_maxima_pago"):
            fecha_str = consumo_data["fecha_maxima_pago"]
            if isinstance(fecha_str, str):
                try:
                    parts = fecha_str.split('-')
                    qdate = QDate(int(parts[0]), int(parts[1]), int(parts[2]))
                    self.date_max_pago.setDate(qdate)
                except Exception:
                    self.date_max_pago.setDate(QDate.currentDate())
            else:
                self.date_max_pago.setDate(QDate.currentDate())
        else:
            self.date_max_pago.setDate(QDate.currentDate())

        # Valor total
        self.ed_valor_total = QLineEdit(self)
        self.ed_valor_total.setPlaceholderText("Valor total")
        self.ed_valor_total.setText(str(consumo_data.get("valor_total", "")) if consumo_data else "")

        # Valor total a pagar
        self.ed_total_pagar = QLineEdit(self)
        self.ed_total_pagar.setPlaceholderText("Total a pagar")
        self.ed_total_pagar.setText(str(consumo_data.get("valor_total_pagar", "")) if consumo_data else "")

        # Intereses de mora
        self.ed_intereses = QLineEdit(self)
        self.ed_intereses.setPlaceholderText("Intereses de mora")
        self.ed_intereses.setText(str(consumo_data.get("intereses_mora", "")) if consumo_data else "")

        # Orden de pago (combo)
        self.combo_orden_pago = QComboBox(self)
        self.combo_orden_pago.setMinimumWidth(250)
        ordenes = listar_ordenes_pago()
        for orden in ordenes:
            # Mostrar: "Orden #123 - $1,234.56"
            texto = f"Orden #{orden.numero_orden} - ${float(orden.valor):.2f}"
            self.combo_orden_pago.addItem(texto, orden.id)
        
        # Seleccionar orden actual en modo edición
        if consumo_data and consumo_data.get("orden_pago_id"):
            index = self.combo_orden_pago.findData(consumo_data["orden_pago_id"])
            if index >= 0:
                self.combo_orden_pago.setCurrentIndex(index)

        form.addRow("Consumo kWh:", self.ed_consumo_kwh)
        form.addRow("Valor kWh:", self.ed_valor_kwh)
        form.addRow("Valor kWh Sub.:", self.ed_valor_kwh_sub)
        form.addRow("Fecha Máx. Pago:", self.date_max_pago)
        form.addRow("Valor Total:", self.ed_valor_total)
        form.addRow("Total a Pagar:", self.ed_total_pagar)
        form.addRow("Intereses Mora:", self.ed_intereses)
        form.addRow("Orden de Pago:", self.combo_orden_pago)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel,
            parent=self
        )
        buttons.accepted.connect(self._validar_y_aceptar)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def _validar_y_aceptar(self):
        """Valida datos antes de aceptar."""
        # Validar CUFE
        cufe = self.ed_cufe.text().strip()
        if not cufe:
            QMessageBox.warning(self, "Validación", "El CUFE es obligatorio.")
            return
        if len(cufe) < 10:
            QMessageBox.warning(self, "Validación", "El CUFE debe tener al menos 10 caracteres.")
            return

        # Validar cuenta (solo en creación)
        if not self.es_edicion:
            cuenta = self.combo_cuenta.currentData()
            if cuenta is None:
                QMessageBox.warning(self, "Validación", "Seleccione una cuenta válida.")
                return

        # Validar consumo kWh
        try:
            consumo = int(self.ed_consumo_kwh.text().strip())
            if consumo < 0:
                raise ValueError()
        except Exception:
            QMessageBox.warning(self, "Validación", "Ingrese un consumo kWh válido (número entero positivo).")
            return

        # Validar valores numéricos
        try:
            float(self.ed_valor_kwh.text().strip())
            float(self.ed_valor_kwh_sub.text().strip())
            float(self.ed_valor_total.text().strip())
            float(self.ed_total_pagar.text().strip())
            float(self.ed_intereses.text().strip())
        except Exception:
            QMessageBox.warning(self, "Validación", "Verifique que todos los valores numéricos sean válidos.")
            return
        
        # Validar orden de pago
        orden_pago_id = self.combo_orden_pago.currentData()
        if orden_pago_id is None:
            QMessageBox.warning(self, "Validación", "Seleccione una orden de pago válida.")
            return

        self.accept()

    def values(self) -> dict:
        valores = {
            "cufe": self.ed_cufe.text().strip(),
            "consumo_kwh": int(self.ed_consumo_kwh.text().strip()),
            "valor_kwh": float(self.ed_valor_kwh.text().strip()),
            "valor_kwh_subsidiado": float(self.ed_valor_kwh_sub.text().strip()),
            "fecha_maxima_pago": self.date_max_pago.date().toString("yyyy-MM-dd"),
            "valor_total": float(self.ed_valor_total.text().strip()),
            "valor_total_pagar": float(self.ed_total_pagar.text().strip()),
            "intereses_mora": float(self.ed_intereses.text().strip()),
            "orden_pago_id": self.combo_orden_pago.currentData(),
        }
        
        # Agregar cuenta solo en modo creación
        if not self.es_edicion:
            valores["cuenta"] = self.combo_cuenta.currentData()
        
        return valores


class ConsumosWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Cargar UI desde archivo .ui
        ui_path = Path(__file__).with_suffix('.ui')
        loadUi(str(ui_path), self)

        # Referencias a widgets del .ui
        self.combo_filtro_cuenta: QComboBox
        self.tbl_consumos: QTableWidget
        self.btn_crear: QPushButton
        self.btn_editar: QPushButton
        self.btn_eliminar: QPushButton
        self.btn_refrescar: QPushButton

        # Conexiones
        self.combo_filtro_cuenta.currentIndexChanged.connect(self._refrescar)
        self.btn_crear.clicked.connect(self._crear)
        self.btn_editar.clicked.connect(self._editar)
        self.btn_eliminar.clicked.connect(self._eliminar)
        self.btn_refrescar.clicked.connect(self._refrescar)

        # Configurar tabla
        self.tbl: QTableWidget = self.tbl_consumos
        self.tbl.setColumnCount(8)
        self.tbl.setHorizontalHeaderLabels([
            "ID", "Cuenta", "CUFE", "Consumo kWh", "Valor kWh", 
            "Fecha Max. Pago", "Orden Pago", "Total a Pagar"
        ])
        self.tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tbl.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tbl.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.tbl.verticalHeader().setVisible(False)
        header = self.tbl.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(True)
        # Establecer anchos iniciales
        self.tbl.setColumnWidth(0, 50)   # ID
        self.tbl.setColumnWidth(1, 100)  # Cuenta
        self.tbl.setColumnWidth(2, 200)  # CUFE
        self.tbl.setColumnWidth(3, 100)  # Consumo kWh
        self.tbl.setColumnWidth(4, 100)  # Valor kWh
        self.tbl.setColumnWidth(5, 120)  # Fecha
        self.tbl.setColumnWidth(6, 100)  # Orden Pago
        self.tbl.setColumnWidth(7, 100)  # Total a Pagar

        # Cargar combo de cuentas
        self._cargar_combo_cuentas()
        self._refrescar()

    def _cargar_combo_cuentas(self):
        """Carga el combo con todas las cuentas activas."""
        self.combo_filtro_cuenta.clear()
        self.combo_filtro_cuenta.addItem("-- Todas las cuentas --", None)
        
        cuentas = listar_cuentas(activo=True)
        for c in cuentas:
            self.combo_filtro_cuenta.addItem(str(c.numero_cuenta), c.numero_cuenta)

    def showEvent(self, event):
        """Refrescar la lista cada vez que se muestra la página."""
        super().showEvent(event)
        self._cargar_combo_cuentas()
        self._refrescar()

    def _refrescar(self):
        # Obtener cuenta seleccionada del filtro
        cuenta_filtro = self.combo_filtro_cuenta.currentData()
        
        # Listar consumos
        consumos = listar_consumos(cuenta=cuenta_filtro)

        # Evitar parpadeos durante actualización
        self.tbl.setUpdatesEnabled(False)
        try:
            self.tbl.setRowCount(len(consumos))
            for i, c in enumerate(consumos):
                id_item = QTableWidgetItem(str(c.id))
                id_item.setData(Qt.ItemDataRole.UserRole, c.id)
                
                cuenta_item = QTableWidgetItem(str(c.cuenta))
                cuenta_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                
                cufe_item = QTableWidgetItem(c.cufe[:20] + "..." if len(c.cufe) > 20 else c.cufe)
                cufe_item.setToolTip(c.cufe)
                
                consumo_item = QTableWidgetItem(str(c.consumo_kwh))
                consumo_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                
                valor_kwh_item = QTableWidgetItem(f"${float(c.valor_kwh):.2f}")
                valor_kwh_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                
                fecha_item = QTableWidgetItem(c.fecha_maxima_pago.strftime("%Y-%m-%d"))
                fecha_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                
                orden_texto = f"#{c.orden_pago_rel.numero_orden}" if c.orden_pago_rel else "N/A"
                orden_item = QTableWidgetItem(orden_texto)
                orden_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                
                pagar_item = QTableWidgetItem(f"${float(c.Valor_total_pagar):.2f}")
                pagar_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                
                self.tbl.setItem(i, 0, id_item)
                self.tbl.setItem(i, 1, cuenta_item)
                self.tbl.setItem(i, 2, cufe_item)
                self.tbl.setItem(i, 3, consumo_item)
                self.tbl.setItem(i, 4, valor_kwh_item)
                self.tbl.setItem(i, 5, fecha_item)
                self.tbl.setItem(i, 6, orden_item)
                self.tbl.setItem(i, 7, pagar_item)
        finally:
            self.tbl.setUpdatesEnabled(True)

    def _selected_id(self) -> int | None:
        sel = self.tbl.currentRow()
        if sel < 0:
            return None
        item = self.tbl.item(sel, 0)  # Columna 0 contiene el ID
        if not item:
            return None
        return int(item.data(Qt.ItemDataRole.UserRole))

    def _crear(self):
        """Crea un nuevo consumo manualmente."""
        dlg = ConsumoDialog(self, titulo="Crear consumo")
        if dlg.exec():
            vals = dlg.values()
            
            # Usar la función guardar_consumo existente
            from config.database import guardar_consumo
            
            ok, msg, consumo_id = guardar_consumo(
                numero_cuenta=vals["cuenta"],
                cufe=vals["cufe"],
                consumo_kwh=vals["consumo_kwh"],
                valor_kwh=vals["valor_kwh"],
                valor_kwh_subsidiado=vals["valor_kwh_subsidiado"],
                fecha_maxima_pago=vals["fecha_maxima_pago"],
                valor_total=vals["valor_total"],
                valor_total_pagar=vals["valor_total_pagar"],
                intereses_mora=vals["intereses_mora"],
                orden_pago_id=vals["orden_pago_id"]
            )
            
            if ok:
                QMessageBox.information(self, "Crear consumo", msg)
                self._refrescar()
            else:
                QMessageBox.warning(self, "Crear consumo", msg)

    def _editar(self):
        cid = self._selected_id()
        if not cid:
            QMessageBox.warning(self, "Editar consumo", "Seleccione un consumo.")
            return
        
        # Obtener consumo completo de la BD
        consumo = obtener_consumo_por_id(cid)
        if not consumo:
            QMessageBox.warning(self, "Editar consumo", "No se pudo cargar el consumo.")
            return
        
        consumo_data = {
            "cufe": consumo.cufe,
            "cuenta": consumo.cuenta,
            "consumo_kwh": consumo.consumo_kwh,
            "valor_kwh": float(consumo.valor_kwh),
            "valor_kwh_subsidiado": float(consumo.valor_kwh_subsidiado),
            "fecha_maxima_pago": consumo.fecha_maxima_pago.strftime("%Y-%m-%d"),
            "valor_total": float(consumo.valor_total),
            "valor_total_pagar": float(consumo.Valor_total_pagar),
            "intereses_mora": float(consumo.intereses_mora),
            "orden_pago_id": consumo.orden_pago_id,
        }
        
        dlg = ConsumoDialog(self, titulo="Editar consumo", consumo_data=consumo_data)
        if dlg.exec():
            vals = dlg.values()
            ok, msg = actualizar_consumo(
                consumo_id=cid,
                consumo_kwh=vals["consumo_kwh"],
                valor_kwh=vals["valor_kwh"],
                valor_kwh_subsidiado=vals["valor_kwh_subsidiado"],
                fecha_maxima_pago=vals["fecha_maxima_pago"],
                valor_total=vals["valor_total"],
                valor_total_pagar=vals["valor_total_pagar"],
                intereses_mora=vals["intereses_mora"],
                orden_pago_id=vals["orden_pago_id"]
            )
            if ok:
                QMessageBox.information(self, "Editar consumo", msg)
                self._refrescar()
            else:
                QMessageBox.warning(self, "Editar consumo", msg)

    def _eliminar(self):
        cid = self._selected_id()
        if not cid:
            QMessageBox.warning(self, "Eliminar consumo", "Seleccione un consumo.")
            return
        
        # Obtener CUFE para el mensaje
        row = self.tbl.currentRow()
        cufe = self.tbl.item(row, 2).toolTip() if self.tbl.item(row, 2) else "consumo"
        
        msg = QMessageBox()
        msg.setWindowTitle("Confirmar eliminación")
        msg.setText(f"¿Eliminar definitivamente el consumo?\n\nCUFE: {cufe[:30]}...")
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.setDefaultButton(QMessageBox.StandardButton.No)
        yes = msg.button(QMessageBox.StandardButton.Yes)
        no = msg.button(QMessageBox.StandardButton.No)
        yes.setText("Sí")
        no.setText("No")
        res = msg.exec()
        
        if res != QMessageBox.StandardButton.Yes:
            return
        
        ok, detalle = eliminar_consumo(cid)
        if ok:
            QMessageBox.information(self, "Eliminar consumo", detalle)
            self._refrescar()
        else:
            QMessageBox.warning(self, "Eliminar consumo", detalle)
