from pathlib import Path
from PyQt6.uic import loadUi
from PyQt6.QtWidgets import (
    QWidget, QTableWidget, QTableWidgetItem,
    QPushButton, QDialog, QFormLayout, QDialogButtonBox,
    QLineEdit, QMessageBox, QHeaderView, QDateEdit
)
from PyQt6.QtCore import Qt, QDate
from config.database import (
    listar_ordenes_pago, obtener_orden_pago_por_id, actualizar_orden_pago, 
    eliminar_orden_pago, crear_orden_pago
)
from decimal import Decimal


class OrdenPagoDialog(QDialog):
    def __init__(self, parent=None, *, titulo="Orden de Pago", orden_data: dict | None = None):
        super().__init__(parent)
        self.setWindowTitle(titulo)
        self.setMinimumWidth(400)
        form = QFormLayout(self)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.es_edicion = orden_data is not None

        # Número de orden
        self.ed_numero_orden = QLineEdit(self)
        self.ed_numero_orden.setPlaceholderText("Número de orden único")
        if orden_data:
            self.ed_numero_orden.setText(str(orden_data.get("numero_orden", "")))

        # Fecha
        self.date_fecha = QDateEdit(self)
        self.date_fecha.setCalendarPopup(True)
        self.date_fecha.setDisplayFormat("yyyy-MM-dd")
        if orden_data and orden_data.get("fecha"):
            fecha_str = orden_data["fecha"]
            if isinstance(fecha_str, str):
                try:
                    parts = fecha_str.split('-')
                    qdate = QDate(int(parts[0]), int(parts[1]), int(parts[2]))
                    self.date_fecha.setDate(qdate)
                except Exception:
                    self.date_fecha.setDate(QDate.currentDate())
            else:
                self.date_fecha.setDate(QDate.currentDate())
        else:
            self.date_fecha.setDate(QDate.currentDate())

        # Valor
        self.ed_valor = QLineEdit(self)
        self.ed_valor.setPlaceholderText("Valor de la orden")
        if orden_data:
            self.ed_valor.setText(str(orden_data.get("valor", "")))

        form.addRow("Núm. Orden:", self.ed_numero_orden)
        form.addRow("Fecha:", self.date_fecha)
        form.addRow("Valor:", self.ed_valor)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel,
            parent=self
        )
        buttons.accepted.connect(self._validar_y_aceptar)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def _validar_y_aceptar(self):
        """Valida datos antes de aceptar."""
        # Validar número de orden
        try:
            orden = int(self.ed_numero_orden.text().strip())
            if orden <= 0:
                raise ValueError()
        except Exception:
            QMessageBox.warning(self, "Validación", "Ingrese un número de orden válido (entero positivo).")
            return

        # Validar valor
        try:
            valor = float(self.ed_valor.text().strip())
            if valor < 0:
                raise ValueError()
        except Exception:
            QMessageBox.warning(self, "Validación", "Ingrese un valor válido (número positivo).")
            return

        self.accept()

    def values(self) -> dict:
        return {
            "numero_orden": int(self.ed_numero_orden.text().strip()),
            "fecha": self.date_fecha.date().toString("yyyy-MM-dd"),
            "valor": float(self.ed_valor.text().strip()),
        }


class OrdenesPagoWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Cargar UI desde archivo .ui
        ui_path = Path(__file__).with_suffix('.ui')
        loadUi(str(ui_path), self)

        # Referencias a widgets del .ui
        self.tbl_ordenes: QTableWidget
        self.btn_crear: QPushButton
        self.btn_editar: QPushButton
        self.btn_eliminar: QPushButton
        self.btn_refrescar: QPushButton

        # Conexiones
        self.btn_crear.clicked.connect(self._crear)
        self.btn_editar.clicked.connect(self._editar)
        self.btn_eliminar.clicked.connect(self._eliminar)
        self.btn_refrescar.clicked.connect(self._refrescar)

        # Configurar tabla
        self.tbl: QTableWidget = self.tbl_ordenes
        self.tbl.setColumnCount(4)
        self.tbl.setHorizontalHeaderLabels([
            "ID", "Núm. Orden", "Fecha", "Valor"
        ])
        self.tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tbl.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tbl.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.tbl.verticalHeader().setVisible(False)
        header = self.tbl.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(True)
        # Establecer anchos iniciales
        self.tbl.setColumnWidth(0, 80)   # ID
        self.tbl.setColumnWidth(1, 150)  # Núm. Orden
        self.tbl.setColumnWidth(2, 150)  # Fecha
        self.tbl.setColumnWidth(3, 200)  # Valor

        self._refrescar()

    def showEvent(self, event):
        """Refrescar la lista cada vez que se muestra la página."""
        super().showEvent(event)
        self._refrescar()

    def _refrescar(self):
        # Listar órdenes de pago
        ordenes = listar_ordenes_pago()

        # Evitar parpadeos durante actualización
        self.tbl.setUpdatesEnabled(False)
        try:
            self.tbl.setRowCount(len(ordenes))
            for i, o in enumerate(ordenes):
                id_item = QTableWidgetItem(str(o.id))
                id_item.setData(Qt.ItemDataRole.UserRole, o.id)
                orden_item = QTableWidgetItem(str(o.numero_orden))
                orden_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                fecha_item = QTableWidgetItem(o.fecha.strftime("%Y-%m-%d"))
                valor_item = QTableWidgetItem(f"${float(o.valor):.2f}")
                valor_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

                self.tbl.setItem(i, 0, id_item)
                self.tbl.setItem(i, 1, orden_item)
                self.tbl.setItem(i, 2, fecha_item)
                self.tbl.setItem(i, 3, valor_item)
        finally:
            self.tbl.setUpdatesEnabled(True)

    def _selected_id(self) -> int | None:
        sel = self.tbl.currentRow()
        if sel < 0:
            return None
        item = self.tbl.item(sel, 0)
        if not item:
            return None
        return int(item.data(Qt.ItemDataRole.UserRole))

    def _crear(self):
        """Crea una nueva orden de pago."""
        dlg = OrdenPagoDialog(self, titulo="Crear orden de pago")
        if dlg.exec():
            vals = dlg.values()
            
            ok, msg = crear_orden_pago(
                numero_orden=vals["numero_orden"],
                fecha=vals["fecha"],
                valor=vals["valor"]
            )
            
            if ok:
                QMessageBox.information(self, "Crear orden de pago", msg)
                self._refrescar()
            else:
                QMessageBox.warning(self, "Crear orden de pago", msg)

    def _editar(self):
        oid = self._selected_id()
        if not oid:
            QMessageBox.warning(self, "Editar orden de pago", "Seleccione una orden de pago.")
            return
        
        # Obtener orden completa de la BD
        orden = obtener_orden_pago_por_id(oid)
        if not orden:
            QMessageBox.warning(self, "Editar orden de pago", "No se pudo cargar la orden de pago.")
            return
        
        orden_data = {
            "numero_orden": orden.numero_orden,
            "fecha": orden.fecha.strftime("%Y-%m-%d"),
            "valor": float(orden.valor),
        }
        
        dlg = OrdenPagoDialog(self, titulo="Editar orden de pago", orden_data=orden_data)
        if dlg.exec():
            vals = dlg.values()
            ok, msg = actualizar_orden_pago(
                orden_id=oid,
                numero_orden=vals["numero_orden"],
                fecha=vals["fecha"],
                valor=vals["valor"]
            )
            if ok:
                QMessageBox.information(self, "Editar orden de pago", msg)
                self._refrescar()
            else:
                QMessageBox.warning(self, "Editar orden de pago", msg)

    def _eliminar(self):
        oid = self._selected_id()
        if not oid:
            QMessageBox.warning(self, "Eliminar orden de pago", "Seleccione una orden de pago.")
            return
        
        # Obtener número de orden para el mensaje
        row = self.tbl.currentRow()
        num_orden = self.tbl.item(row, 1).text() if self.tbl.item(row, 1) else "orden"
        
        msg = QMessageBox()
        msg.setWindowTitle("Confirmar eliminación")
        msg.setText(f"¿Eliminar definitivamente la orden de pago?\n\nNúm. Orden: {num_orden}")
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
        
        ok, detalle = eliminar_orden_pago(oid)
        if ok:
            QMessageBox.information(self, "Eliminar orden de pago", detalle)
            self._refrescar()
        else:
            QMessageBox.warning(self, "Eliminar orden de pago", detalle)
