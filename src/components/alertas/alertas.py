from pathlib import Path
from PyQt6.uic import loadUi
from PyQt6.QtWidgets import (
    QWidget, QTableWidget, QTableWidgetItem,
    QPushButton, QDialog, QFormLayout, QDialogButtonBox,
    QLineEdit, QMessageBox, QHeaderView, QComboBox, QSpinBox
)
from PyQt6.QtCore import Qt
from config.database import (
    listar_alertas, obtener_alerta_por_id, actualizar_alerta, 
    eliminar_alerta, crear_alerta, listar_cuentas
)


class AlertaDialog(QDialog):
    def __init__(self, parent=None, *, titulo="Alerta", alerta_data: dict | None = None):
        super().__init__(parent)
        self.setWindowTitle(titulo)
        self.setMinimumWidth(400)
        form = QFormLayout(self)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.es_edicion = alerta_data is not None

        # Combo de cuentas
        self.combo_cuenta = QComboBox(self)
        cuentas = listar_cuentas()
        for c in cuentas:
            self.combo_cuenta.addItem(f"Cuenta {c.numero_cuenta}", c.numero_cuenta)
        
        if alerta_data and alerta_data.get("cuenta"):
            idx = self.combo_cuenta.findData(alerta_data["cuenta"])
            if idx >= 0:
                self.combo_cuenta.setCurrentIndex(idx)

        # Días hábiles
        self.spin_dias = QSpinBox(self)
        self.spin_dias.setMinimum(0)
        self.spin_dias.setMaximum(365)
        self.spin_dias.setValue(alerta_data.get("dias_habiles", 0) if alerta_data else 0)

        form.addRow("Cuenta:", self.combo_cuenta)
        form.addRow("Días Hábiles:", self.spin_dias)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel,
            parent=self
        )
        buttons.accepted.connect(self._validar_y_aceptar)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def _validar_y_aceptar(self):
        """Valida datos antes de aceptar."""
        if self.combo_cuenta.currentIndex() < 0:
            QMessageBox.warning(self, "Validación", "Seleccione una cuenta.")
            return

        self.accept()

    def values(self) -> dict:
        return {
            "cuenta": self.combo_cuenta.currentData(),
            "dias_habiles": self.spin_dias.value(),
        }


class AlertasWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Cargar UI desde archivo .ui (robusto para modo frozen/dev)
        from utils.ui import resolve_ui_path
        ui_path = resolve_ui_path(__file__)
        loadUi(ui_path, self)

        # Referencias a widgets del .ui
        self.tbl_alertas: QTableWidget
        self.combo_cuenta: QComboBox
        self.btn_crear: QPushButton
        self.btn_editar: QPushButton
        self.btn_eliminar: QPushButton
        self.btn_refrescar: QPushButton

        # Conexiones
        self.btn_crear.clicked.connect(self._crear)
        self.btn_editar.clicked.connect(self._editar)
        self.btn_eliminar.clicked.connect(self._eliminar)
        self.btn_refrescar.clicked.connect(self._refrescar)
        self.combo_cuenta.currentIndexChanged.connect(self._refrescar)

        # Configurar tabla
        self.tbl: QTableWidget = self.tbl_alertas
        self.tbl.setColumnCount(3)
        self.tbl.setHorizontalHeaderLabels([
            "ID", "Cuenta", "Días Hábiles"
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
        self.tbl.setColumnWidth(1, 150)  # Cuenta
        self.tbl.setColumnWidth(2, 200)  # Días Hábiles

        # Cargar cuentas en el combo
        self._cargar_cuentas()
        self._refrescar()

    def _cargar_cuentas(self):
        """Carga las cuentas disponibles en el combo de filtro."""
        self.combo_cuenta.clear()
        self.combo_cuenta.addItem("Todas las cuentas", None)
        cuentas = listar_cuentas()
        for c in cuentas:
            self.combo_cuenta.addItem(f"Cuenta {c.numero_cuenta}", c.numero_cuenta)

    def showEvent(self, event):
        """Refrescar la lista cada vez que se muestra la página."""
        super().showEvent(event)
        self._refrescar()

    def _refrescar(self):
        # Obtener cuenta seleccionada para filtro
        cuenta_filtro = self.combo_cuenta.currentData()
        
        # Listar alertas
        alertas = listar_alertas(cuenta=cuenta_filtro)

        # Evitar parpadeos durante actualización
        self.tbl.setUpdatesEnabled(False)
        try:
            self.tbl.setRowCount(len(alertas))
            for i, a in enumerate(alertas):
                id_item = QTableWidgetItem(str(a.id))
                id_item.setData(Qt.ItemDataRole.UserRole, a.id)
                cuenta_item = QTableWidgetItem(str(a.cuenta))
                cuenta_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                dias_item = QTableWidgetItem(str(a.dias_habiles))
                dias_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                self.tbl.setItem(i, 0, id_item)
                self.tbl.setItem(i, 1, cuenta_item)
                self.tbl.setItem(i, 2, dias_item)
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
        """Crea una nueva alerta."""
        dlg = AlertaDialog(self, titulo="Crear alerta")
        if dlg.exec():
            vals = dlg.values()
            
            ok, msg = crear_alerta(
                cuenta=vals["cuenta"],
                dias_habiles=vals["dias_habiles"]
            )
            
            if ok:
                QMessageBox.information(self, "Crear alerta", msg)
                self._refrescar()
            else:
                QMessageBox.warning(self, "Crear alerta", msg)

    def _editar(self):
        aid = self._selected_id()
        if not aid:
            QMessageBox.warning(self, "Editar alerta", "Seleccione una alerta.")
            return
        
        # Obtener alerta completa de la BD
        alerta = obtener_alerta_por_id(aid)
        if not alerta:
            QMessageBox.warning(self, "Editar alerta", "No se pudo cargar la alerta.")
            return
        
        alerta_data = {
            "cuenta": alerta.cuenta,
            "dias_habiles": alerta.dias_habiles,
        }
        
        dlg = AlertaDialog(self, titulo="Editar alerta", alerta_data=alerta_data)
        if dlg.exec():
            vals = dlg.values()
            ok, msg = actualizar_alerta(
                alerta_id=aid,
                cuenta=vals["cuenta"],
                dias_habiles=vals["dias_habiles"]
            )
            if ok:
                QMessageBox.information(self, "Editar alerta", msg)
                self._refrescar()
            else:
                QMessageBox.warning(self, "Editar alerta", msg)

    def _eliminar(self):
        aid = self._selected_id()
        if not aid:
            QMessageBox.warning(self, "Eliminar alerta", "Seleccione una alerta.")
            return
        
        # Obtener cuenta para el mensaje
        row = self.tbl.currentRow()
        cuenta = self.tbl.item(row, 1).text() if self.tbl.item(row, 1) else "alerta"
        
        msg = QMessageBox()
        msg.setWindowTitle("Confirmar eliminación")
        msg.setText(f"¿Eliminar definitivamente la alerta?\n\nCuenta: {cuenta}")
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
        
        ok, detalle = eliminar_alerta(aid)
        if ok:
            QMessageBox.information(self, "Eliminar alerta", detalle)
            self._refrescar()
        else:
            QMessageBox.warning(self, "Eliminar alerta", detalle)
