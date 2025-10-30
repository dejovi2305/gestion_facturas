from pathlib import Path
from PyQt6.uic import loadUi
from PyQt6.QtWidgets import (
    QWidget, QTableWidget, QTableWidgetItem,
    QPushButton, QCheckBox, QDialog, QFormLayout, QDialogButtonBox,
    QLineEdit, QMessageBox, QHeaderView
)
from PyQt6.QtCore import Qt
from config.database import listar_usuarios, crear_usuario, actualizar_usuario, eliminar_usuario
from datetime import datetime


class UsuarioDialog(QDialog):
    def __init__(self, parent=None, *, titulo="Usuario", usuario_data: dict | None = None):
        super().__init__(parent)
        self.setWindowTitle(titulo)
        self.setMinimumWidth(400)
        form = QFormLayout(self)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.es_edicion = usuario_data is not None

        # Nombre de usuario
        self.ed_nombre_usuario = QLineEdit(self)
        self.ed_nombre_usuario.setPlaceholderText("Nombre de usuario único")
        self.ed_nombre_usuario.setMaxLength(50)
        if usuario_data:
            self.ed_nombre_usuario.setText(usuario_data.get("nombre_usuario", ""))

        # Correo
        self.ed_correo = QLineEdit(self)
        self.ed_correo.setPlaceholderText("correo@ejemplo.com")
        if usuario_data:
            self.ed_correo.setText(usuario_data.get("correo", ""))

        # Contraseña
        self.ed_contrasena = QLineEdit(self)
        self.ed_contrasena.setEchoMode(QLineEdit.EchoMode.Password)
        if self.es_edicion:
            self.ed_contrasena.setPlaceholderText("Dejar vacío para no cambiar")
        else:
            self.ed_contrasena.setPlaceholderText("Mínimo 4 caracteres")
        
        # Confirmar contraseña
        self.ed_confirmar = QLineEdit(self)
        self.ed_confirmar.setEchoMode(QLineEdit.EchoMode.Password)
        if self.es_edicion:
            self.ed_confirmar.setPlaceholderText("Confirmar nueva contraseña")
        else:
            self.ed_confirmar.setPlaceholderText("Repetir contraseña")

        # Checkbox mostrar contraseña
        self.chk_mostrar_pwd = QCheckBox("Mostrar contraseñas", self)
        self.chk_mostrar_pwd.stateChanged.connect(self._toggle_password_visibility)

        # Estado activo
        self.chk_activo = QCheckBox(self)
        self.chk_activo.setChecked(usuario_data.get("activo", True) if usuario_data else True)

        form.addRow("Usuario:", self.ed_nombre_usuario)
        form.addRow("Correo:", self.ed_correo)
        form.addRow("Contraseña:", self.ed_contrasena)
        form.addRow("Confirmar:", self.ed_confirmar)
        form.addRow("", self.chk_mostrar_pwd)
        form.addRow("Activo:", self.chk_activo)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel,
            parent=self
        )
        buttons.accepted.connect(self._validar_y_aceptar)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def _toggle_password_visibility(self):
        """Alterna la visibilidad de las contraseñas."""
        if self.chk_mostrar_pwd.isChecked():
            self.ed_contrasena.setEchoMode(QLineEdit.EchoMode.Normal)
            self.ed_confirmar.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.ed_contrasena.setEchoMode(QLineEdit.EchoMode.Password)
            self.ed_confirmar.setEchoMode(QLineEdit.EchoMode.Password)

    def _validar_y_aceptar(self):
        """Valida datos antes de aceptar."""
        # Validar nombre de usuario
        nombre = self.ed_nombre_usuario.text().strip()
        if not nombre:
            QMessageBox.warning(self, "Validación", "Ingrese un nombre de usuario.")
            return

        # Validar correo
        correo = self.ed_correo.text().strip()
        if not correo or '@' not in correo:
            QMessageBox.warning(self, "Validación", "Ingrese un correo electrónico válido.")
            return

        # Validar contraseña (solo en creación o si se ingresó algo en edición)
        pwd = self.ed_contrasena.text()
        conf = self.ed_confirmar.text()
        
        if not self.es_edicion:
            # Creación: contraseña obligatoria
            if not pwd:
                QMessageBox.warning(self, "Validación", "Ingrese una contraseña.")
                return
            if len(pwd) < 4:
                QMessageBox.warning(self, "Validación", "La contraseña debe tener al menos 4 caracteres.")
                return
        
        # Si se ingresó contraseña (creación o edición), validar confirmación
        if pwd or conf:
            if pwd != conf:
                QMessageBox.warning(self, "Validación", "Las contraseñas no coinciden.")
                return
            if len(pwd) < 4:
                QMessageBox.warning(self, "Validación", "La contraseña debe tener al menos 4 caracteres.")
                return

        self.accept()

    def values(self) -> dict:
        pwd = self.ed_contrasena.text().strip()
        return {
            "nombre_usuario": self.ed_nombre_usuario.text().strip(),
            "correo": self.ed_correo.text().strip(),
            "contrasena": pwd if pwd else None,
            "activo": bool(self.chk_activo.isChecked()),
        }


class UsuariosWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Cargar UI desde archivo .ui
        ui_path = Path(__file__).with_suffix('.ui')
        loadUi(str(ui_path), self)

        # Referencias a widgets del .ui
        self.chk_mostrar_inactivos: QCheckBox
        self.tbl_usuarios: QTableWidget
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
        self.tbl: QTableWidget = self.tbl_usuarios
        self.tbl.setColumnCount(5)
        self.tbl.setHorizontalHeaderLabels([
            "ID", "Usuario", "Correo", "Fecha Registro", "Activo"
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
        self.tbl.setColumnWidth(1, 150)  # Usuario
        self.tbl.setColumnWidth(2, 200)  # Correo
        self.tbl.setColumnWidth(3, 150)  # Fecha
        self.tbl.setColumnWidth(4, 60)   # Activo

        self._refrescar()

    def showEvent(self, event):
        """Refrescar la lista cada vez que se muestra la página."""
        super().showEvent(event)
        self._refrescar()

    def _refrescar(self):
        # Si el checkbox está marcado: mostrar solo inactivos (activo=False)
        # Si está desmarcado: mostrar solo activos (activo=True)
        activo_flag = False if self.chk_mostrar_inactivos.isChecked() else True
        usuarios = listar_usuarios(activo=activo_flag)

        # Evitar parpadeos durante actualización
        self.tbl.setUpdatesEnabled(False)
        try:
            self.tbl.setRowCount(len(usuarios))
            for i, u in enumerate(usuarios):
                id_item = QTableWidgetItem(str(u.id))
                id_item.setData(Qt.ItemDataRole.UserRole, u.id)
                usuario_item = QTableWidgetItem(u.nombre_usuario)
                correo_item = QTableWidgetItem(u.correo)
                fecha_item = QTableWidgetItem(u.fecha_registro.strftime("%Y-%m-%d %H:%M"))
                activo_item = QTableWidgetItem("Sí" if u.activo else "No")
                activo_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                self.tbl.setItem(i, 0, id_item)
                self.tbl.setItem(i, 1, usuario_item)
                self.tbl.setItem(i, 2, correo_item)
                self.tbl.setItem(i, 3, fecha_item)
                self.tbl.setItem(i, 4, activo_item)
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
        dlg = UsuarioDialog(self, titulo="Crear usuario")
        if dlg.exec():
            vals = dlg.values()
            ok, msg, _id = crear_usuario(
                nombre_usuario=vals["nombre_usuario"],
                correo=vals["correo"],
                contrasena_plana=vals["contrasena"],
                activo=vals["activo"]
            )
            if ok:
                QMessageBox.information(self, "Crear usuario", msg)
                self._refrescar()
            else:
                QMessageBox.warning(self, "Crear usuario", msg)

    def _editar(self):
        uid = self._selected_id()
        if not uid:
            QMessageBox.warning(self, "Editar usuario", "Seleccione un usuario.")
            return
        
        # Pre-cargar datos desde tabla
        row = self.tbl.currentRow()
        usuario_data = {
            "nombre_usuario": self.tbl.item(row, 1).text() if self.tbl.item(row, 1) else "",
            "correo": self.tbl.item(row, 2).text() if self.tbl.item(row, 2) else "",
            "activo": self.tbl.item(row, 4).text() == "Sí" if self.tbl.item(row, 4) else True,
        }
        
        dlg = UsuarioDialog(self, titulo="Editar usuario", usuario_data=usuario_data)
        if dlg.exec():
            vals = dlg.values()
            ok, msg = actualizar_usuario(
                usuario_id=uid,
                nombre_usuario=vals["nombre_usuario"],
                correo=vals["correo"],
                contrasena_plana=vals["contrasena"],
                activo=vals["activo"]
            )
            if ok:
                QMessageBox.information(self, "Editar usuario", msg)
                self._refrescar()
            else:
                QMessageBox.warning(self, "Editar usuario", msg)

    def _eliminar(self):
        uid = self._selected_id()
        if not uid:
            QMessageBox.warning(self, "Eliminar usuario", "Seleccione un usuario.")
            return
        
        # Obtener nombre de usuario para el mensaje
        row = self.tbl.currentRow()
        nombre = self.tbl.item(row, 1).text() if self.tbl.item(row, 1) else "usuario"
        
        msg = QMessageBox()
        msg.setWindowTitle("Confirmar eliminación")
        msg.setText(f"¿Eliminar definitivamente al usuario '{nombre}'?")
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
        
        ok, detalle = eliminar_usuario(uid)
        if ok:
            QMessageBox.information(self, "Eliminar usuario", detalle)
            self._refrescar()
        else:
            QMessageBox.warning(self, "Eliminar usuario", detalle)
