from pathlib import Path
from PyQt6.uic import loadUi
from PyQt6.QtWidgets import (
    QWidget, QTableWidget, QTableWidgetItem,
    QPushButton, QCheckBox, QDialog, QFormLayout, QDialogButtonBox,
    QLineEdit, QMessageBox, QHeaderView, QComboBox
)
from PyQt6.QtCore import Qt, QRegularExpression
from PyQt6.QtGui import QRegularExpressionValidator
from config.database import (
    listar_clientes, crear_cliente, actualizar_cliente, eliminar_cliente,
    listar_cuentas
)


class ClienteDialog(QDialog):
    def __init__(self, parent=None, *, titulo="Cliente", cliente_data: dict | None = None):
        super().__init__(parent)
        self.setWindowTitle(titulo)
        self.setMinimumWidth(400)
        form = QFormLayout(self)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        # Si es edición
        self.es_edicion = cliente_data is not None
        
        # Número de cuenta: siempre mostrar combo pero con comportamiento diferente
        self.combo_cuenta = QComboBox(self)
        self.combo_cuenta.setMinimumWidth(250)
        
        if self.es_edicion:
            # Modo edición: combo con todas las cuentas activas, preseleccionar la actual
            # y permitir cambio a otra cuenta disponible
            cuenta_actual = cliente_data.get("cuenta", 0)
            cuentas_disponibles = self._obtener_cuentas_disponibles_edicion(cuenta_actual)
            
            for c in cuentas_disponibles:
                self.combo_cuenta.addItem(str(c.numero_cuenta), c.numero_cuenta)
            
            # Preseleccionar la cuenta actual
            idx = self.combo_cuenta.findData(cuenta_actual)
            if idx >= 0:
                self.combo_cuenta.setCurrentIndex(idx)
        else:
            # Modo creación: combo con cuentas activas sin cliente
            cuentas_disponibles = self._obtener_cuentas_disponibles()
            
            self.combo_cuenta.addItem("-- Seleccione una cuenta --", None)
            for c in cuentas_disponibles:
                self.combo_cuenta.addItem(str(c.numero_cuenta), c.numero_cuenta)

        form.addRow("Cuenta:", self.combo_cuenta)

        # Campos de cliente
        self.ed_nombre = QLineEdit(self)
        self.ed_nombre.setPlaceholderText("Nombre del cliente")
        self.ed_nombre.setText(cliente_data.get("nombre", "") if cliente_data else "")
        
        self.ed_direccion = QLineEdit(self)
        self.ed_direccion.setPlaceholderText("Dirección")
        self.ed_direccion.setText(cliente_data.get("direccion", "") if cliente_data else "")
        
        self.ed_estrato = QLineEdit(self)
        self.ed_estrato.setPlaceholderText("Estrato (ej: 1, 2, 3...)")
        self.ed_estrato.setText(cliente_data.get("estrato", "") if cliente_data else "")
        
        self.ed_numero_medidor = QLineEdit(self)
        self.ed_numero_medidor.setPlaceholderText("Número de medidor")
        self.ed_numero_medidor.setText(cliente_data.get("numero_medidor", "") if cliente_data else "")
        
        self.chk_activo = QCheckBox(self)
        self.chk_activo.setChecked(cliente_data.get("activo", True) if cliente_data else True)

        form.addRow("Nombre:", self.ed_nombre)
        form.addRow("Dirección:", self.ed_direccion)
        form.addRow("Estrato:", self.ed_estrato)
        form.addRow("Núm. Medidor:", self.ed_numero_medidor)
        form.addRow("Activo:", self.chk_activo)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel,
            parent=self
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def _obtener_cuentas_disponibles(self):
        """Obtiene cuentas activas que no tienen cliente asociado (para crear)."""
        from config.database import SessionLocal
        from models.cuenta import Cuenta
        from models.cliente import Cliente
        from sqlalchemy import select
        
        db = SessionLocal()
        try:
            # Obtener todas las cuentas activas
            todas_cuentas = db.query(Cuenta).filter(Cuenta.activo.is_(True)).all()
            
            # Obtener números de cuenta que ya tienen cliente
            cuentas_con_cliente = set(db.query(Cliente.cuenta).all())
            cuentas_con_cliente_nums = {c[0] for c in cuentas_con_cliente}
            
            # Filtrar cuentas que no tienen cliente
            cuentas_disponibles = [
                c for c in todas_cuentas 
                if c.numero_cuenta not in cuentas_con_cliente_nums
            ]
            
            return sorted(cuentas_disponibles, key=lambda x: x.numero_cuenta)
        except Exception as e:
            print(f"Error obteniendo cuentas disponibles: {e}")
            return []
        finally:
            db.close()

    def _obtener_cuentas_disponibles_edicion(self, cuenta_actual: int):
        """Obtiene cuentas disponibles para edición: la actual + las que no tienen cliente."""
        from config.database import SessionLocal
        from models.cuenta import Cuenta
        from models.cliente import Cliente
        
        db = SessionLocal()
        try:
            # Obtener todas las cuentas activas
            todas_cuentas = db.query(Cuenta).filter(Cuenta.activo.is_(True)).all()
            
            # Obtener números de cuenta que tienen cliente (excluyendo la actual)
            cuentas_con_cliente = db.query(Cliente.cuenta).filter(
                Cliente.cuenta != cuenta_actual
            ).all()
            cuentas_con_cliente_nums = {c[0] for c in cuentas_con_cliente}
            
            # Filtrar: incluir la cuenta actual + cuentas sin cliente
            cuentas_disponibles = [
                c for c in todas_cuentas 
                if c.numero_cuenta == cuenta_actual or c.numero_cuenta not in cuentas_con_cliente_nums
            ]
            
            return sorted(cuentas_disponibles, key=lambda x: x.numero_cuenta)
        except Exception as e:
            print(f"Error obteniendo cuentas para edición: {e}")
            return []
        finally:
            db.close()

    def values(self) -> dict:
        cuenta = self.combo_cuenta.currentData()
        if cuenta is None:
            cuenta = 0

        return {
            "cuenta": cuenta,
            "nombre": self.ed_nombre.text().strip() or None,
            "direccion": self.ed_direccion.text().strip() or None,
            "estrato": self.ed_estrato.text().strip() or None,
            "numero_medidor": self.ed_numero_medidor.text().strip() or None,
            "activo": bool(self.chk_activo.isChecked()),
        }


class ClientesWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Cargar UI desde archivo .ui (robusto para modo frozen/dev)
        from utils.ui import resolve_ui_path
        ui_path = resolve_ui_path(__file__)
        loadUi(ui_path, self)

        # Referencias a widgets del .ui
        self.chk_mostrar_inactivos: QCheckBox
        self.tbl_clientes: QTableWidget
        self.btn_crear: QPushButton
        self.btn_editar: QPushButton
        self.btn_eliminar: QPushButton
        self.btn_refrescar: QPushButton

        # Conexiones
        self.chk_mostrar_inactivos.stateChanged.connect(self._refrescar)
        self.btn_crear.clicked.connect(self._crear)
        self.btn_editar.clicked.connect(self._editar)
        self.btn_eliminar.clicked.connect(self._eliminar)
        self.btn_refrescar.clicked.connect(self._refrescar)

        # Configurar tabla
        self.tbl: QTableWidget = self.tbl_clientes
        self.tbl.setColumnCount(7)
        self.tbl.setHorizontalHeaderLabels([
            "ID", "Cuenta", "Nombre", "Dirección", "Estrato", "Núm. Medidor", "Activo"
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
        self.tbl.setColumnWidth(2, 150)  # Nombre
        self.tbl.setColumnWidth(3, 200)  # Dirección
        self.tbl.setColumnWidth(4, 70)   # Estrato
        self.tbl.setColumnWidth(5, 120)  # Núm. Medidor
        self.tbl.setColumnWidth(6, 60)   # Activo

        self._refrescar()

    def showEvent(self, event):
        """Refrescar la lista cada vez que se muestra la página."""
        super().showEvent(event)
        self._refrescar()

    def _refrescar(self):
        # Si el checkbox está marcado: mostrar solo inactivos (activo=False)
        # Si está desmarcado: mostrar solo activos (activo=True)
        activo_flag = False if self.chk_mostrar_inactivos.isChecked() else True
        clientes = listar_clientes(activo=activo_flag)

        # Evitar parpadeos durante actualización
        self.tbl.setUpdatesEnabled(False)
        try:
            self.tbl.setRowCount(len(clientes))
            for i, c in enumerate(clientes):
                id_item = QTableWidgetItem(str(c.id))
                id_item.setData(Qt.ItemDataRole.UserRole, c.id)
                cuenta_item = QTableWidgetItem(str(c.cuenta))
                nombre_item = QTableWidgetItem(c.nombre or "")
                direccion_item = QTableWidgetItem(c.direccion or "")
                estrato_item = QTableWidgetItem(c.estrato or "")
                medidor_item = QTableWidgetItem(c.numero_medidor or "")
                activo_item = QTableWidgetItem("Sí" if c.activo else "No")
                activo_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                self.tbl.setItem(i, 0, id_item)
                self.tbl.setItem(i, 1, cuenta_item)
                self.tbl.setItem(i, 2, nombre_item)
                self.tbl.setItem(i, 3, direccion_item)
                self.tbl.setItem(i, 4, estrato_item)
                self.tbl.setItem(i, 5, medidor_item)
                self.tbl.setItem(i, 6, activo_item)
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
        # Verificar si hay cuentas disponibles antes de abrir el diálogo
        from config.database import SessionLocal
        from models.cuenta import Cuenta
        from models.cliente import Cliente
        
        db = SessionLocal()
        try:
            todas_cuentas = db.query(Cuenta).filter(Cuenta.activo.is_(True)).count()
            cuentas_con_cliente = db.query(Cliente).count()
            cuentas_disponibles_count = todas_cuentas - cuentas_con_cliente
            
            if cuentas_disponibles_count <= 0:
                QMessageBox.warning(
                    self, 
                    "Crear cliente",
                    "No hay cuentas disponibles.\n\n"
                    "Todas las cuentas activas ya tienen un cliente asignado.\n"
                    "Cree nuevas cuentas en 'Gestionar cuentas' primero."
                )
                return
        finally:
            db.close()
        
        dlg = ClienteDialog(self, titulo="Crear cliente")
        if dlg.exec():
            vals = dlg.values()
            # Validar cuenta
            if vals["cuenta"] <= 0 or len(str(vals["cuenta"])) < 6:
                QMessageBox.warning(self, "Crear cliente", "Seleccione una cuenta válida.")
                return
            ok, msg, _id = crear_cliente(
                numero_cuenta=vals["cuenta"],
                nombre=vals["nombre"],
                direccion=vals["direccion"],
                estrato=vals["estrato"],
                numero_medidor=vals["numero_medidor"],
                activo=vals["activo"]
            )
            QMessageBox.information(self, "Crear cliente", msg)
            if ok:
                self._refrescar()

    def _editar(self):
        cid = self._selected_id()
        if not cid:
            QMessageBox.warning(self, "Editar cliente", "Seleccione un cliente.")
            return
        
        # Pre-cargar datos desde tabla
        row = self.tbl.currentRow()
        cliente_data = {
            "cuenta": int(self.tbl.item(row, 1).text()) if self.tbl.item(row, 1) else 0,
            "nombre": self.tbl.item(row, 2).text() if self.tbl.item(row, 2) else "",
            "direccion": self.tbl.item(row, 3).text() if self.tbl.item(row, 3) else "",
            "estrato": self.tbl.item(row, 4).text() if self.tbl.item(row, 4) else "",
            "numero_medidor": self.tbl.item(row, 5).text() if self.tbl.item(row, 5) else "",
            "activo": self.tbl.item(row, 6).text() == "Sí" if self.tbl.item(row, 6) else True,
        }
        
        dlg = ClienteDialog(self, titulo="Editar cliente", cliente_data=cliente_data)
        if dlg.exec():
            vals = dlg.values()
            # Permitir cambio de cuenta también
            ok, msg = actualizar_cliente(
                cliente_id=cid,
                numero_cuenta=vals["cuenta"],
                nombre=vals["nombre"],
                direccion=vals["direccion"],
                estrato=vals["estrato"],
                numero_medidor=vals["numero_medidor"],
                activo=vals["activo"]
            )
            if ok:
                QMessageBox.information(self, "Editar cliente", msg)
                self._refrescar()
            else:
                QMessageBox.warning(self, "Editar cliente", msg)

    def _eliminar(self):
        cid = self._selected_id()
        if not cid:
            QMessageBox.warning(self, "Eliminar cliente", "Seleccione un cliente.")
            return
        
        msg = QMessageBox()
        msg.setWindowTitle("Confirmar eliminación")
        msg.setText("¿Eliminar definitivamente el cliente seleccionado?")
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
        
        ok, detalle = eliminar_cliente(cid)
        if ok:
            QMessageBox.information(self, "Eliminar cliente", detalle)
            self._refrescar()
        else:
            QMessageBox.warning(self, "Eliminar cliente", detalle)
