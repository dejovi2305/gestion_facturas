from pathlib import Path
from PyQt6.uic import loadUi
from PyQt6.QtWidgets import (
    QWidget, QTableWidget, QTableWidgetItem,
    QPushButton, QCheckBox, QDialog, QFormLayout, QDialogButtonBox,
    QLineEdit, QMessageBox, QHeaderView
)
from PyQt6.QtCore import Qt, QRegularExpression
from PyQt6.QtGui import QRegularExpressionValidator, QColor, QBrush
from config.database import (
    listar_cuentas, crear_cuenta, actualizar_cuenta, eliminar_cuenta,
    obtener_ultimo_consumo_por_cuenta, calcular_estado_alerta_consumo, SessionLocal
)
from models import Alerta
from utils.ui import resolve_ui_path


class CuentaDialog(QDialog):
    def __init__(self, parent=None, *, titulo="Cuenta", numero_cuenta: int | None = None, activo: bool = True):
        super().__init__(parent)
        self.setWindowTitle(titulo)
        form = QFormLayout(self)
        # Usar QLineEdit con validador regex para permitir hasta 12 dígitos (evita límite int32 de QSpinBox)
        self.ed_numero = QLineEdit(self)
        self.ed_numero.setPlaceholderText("Solo dígitos (6-12)")
        self.ed_numero.setMaxLength(12)
        self.ed_numero.setValidator(QRegularExpressionValidator(QRegularExpression(r"^\d{0,12}$"), self))
        if numero_cuenta is not None:
            try:
                self.ed_numero.setText(str(int(numero_cuenta)))
            except Exception:
                self.ed_numero.setText("")
        self.chk_activo = QCheckBox("Activa", self)
        self.chk_activo.setChecked(bool(activo))
        form.addRow("Número de cuenta", self.ed_numero)
        form.addRow("Estado", self.chk_activo)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel, parent=self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def values(self) -> dict:
        txt = self.ed_numero.text().strip()
        numero = int(txt) if txt.isdigit() else 0
        return {
            "numero_cuenta": numero,
            "activo": bool(self.chk_activo.isChecked()),
        }


class CuentasWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Cargar UI desde archivo .ui (robusto para modo frozen/dev)
        ui_path = resolve_ui_path(__file__)
        loadUi(ui_path, self)

        # Referencias a widgets del .ui
        self.chk_mostrar_inactivas: QCheckBox
        self.tbl_cuentas: QTableWidget
        self.btn_crear: QPushButton
        self.btn_editar: QPushButton
        self.btn_eliminar: QPushButton
        self.btn_refrescar: QPushButton

        # Conexiones
        self.chk_mostrar_inactivas.stateChanged.connect(self._refrescar)
        self.btn_crear.clicked.connect(self._crear)
        self.btn_editar.clicked.connect(self._editar)
        self.btn_eliminar.clicked.connect(self._eliminar)
        self.btn_refrescar.clicked.connect(self._refrescar)

        # Configurar tabla para estabilidad de tamaño (no cambiar ancho en cada refresh)
        self.tbl: QTableWidget = self.tbl_cuentas
        self.tbl.setColumnCount(5)
        self.tbl.setHorizontalHeaderLabels(["Estado", "ID", "Número de cuenta", "Días Restantes", "Activa"])
        self.tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tbl.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tbl.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.tbl.verticalHeader().setVisible(False)
        header = self.tbl.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(True)
        # Establecer anchos iniciales estables
        self.tbl.setColumnWidth(0, 120)  # Estado
        self.tbl.setColumnWidth(1, 60)   # ID
        self.tbl.setColumnWidth(2, 150)  # Número de cuenta
        self.tbl.setColumnWidth(3, 150)  # Días Restantes
        self.tbl.setColumnWidth(4, 80)   # Activa

        self._refrescar()

    def showEvent(self, event):
        """Refrescar la lista cada vez que se muestra la página."""
        super().showEvent(event)
        self._refrescar()

    def _refrescar(self):
        # Si el checkbox está marcado: mostrar solo inactivas (activo=False)
        # Si está desmarcado: mostrar solo activas (activo=True)
        activo_flag = False if self.chk_mostrar_inactivas.isChecked() else True
        cuentas = listar_cuentas(activo=activo_flag)

        # Obtener TODAS las alertas configuradas de una vez (optimización)
        db = SessionLocal()
        try:
            alertas_dict = {}
            for alerta in db.query(Alerta).all():
                alertas_dict[alerta.cuenta] = alerta.dias_habiles
        finally:
            db.close()

        # Evitar parpadeos/redimensionado durante la actualización
        self.tbl.setUpdatesEnabled(False)
        try:
            self.tbl.setRowCount(len(cuentas))
            for i, c in enumerate(cuentas):
                # Obtener último consumo y calcular estado de alerta
                ultimo_consumo = obtener_ultimo_consumo_por_cuenta(c.numero_cuenta)
                
                if ultimo_consumo:
                    # Obtener días hábiles configurados para esta cuenta
                    dias_habiles = alertas_dict.get(c.numero_cuenta, 0)
                    info_alerta = calcular_estado_alerta_consumo(ultimo_consumo, dias_habiles)
                    estado = info_alerta['estado']
                    dias_restantes = info_alerta['dias_restantes']
                    
                    # Determinar color y texto del semáforo
                    if estado == 'vencido':
                        estado_texto = "🔴 VENCIDO"
                        color_fondo = QColor(255, 200, 200)
                    elif estado == 'urgente':
                        estado_texto = "🟠 HOY"
                        color_fondo = QColor(255, 220, 150)
                    elif estado == 'proximo':
                        estado_texto = "🟡 PRÓXIMO"
                        color_fondo = QColor(255, 255, 200)
                    else:
                        estado_texto = "🟢 OK"
                        color_fondo = QColor(200, 255, 200)
                    
                    # Texto de días restantes
                    if dias_restantes < 0:
                        dias_texto = f"{abs(dias_restantes)} días atrasado"
                    elif dias_restantes == 0:
                        dias_texto = "Hoy"
                    else:
                        dias_texto = f"{dias_restantes} días"
                else:
                    estado_texto = "⚪ Sin consumos"
                    color_fondo = QColor(240, 240, 240)
                    dias_texto = "N/A"
                
                # Crear items
                estado_item = QTableWidgetItem(estado_texto)
                estado_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                estado_item.setBackground(QBrush(color_fondo))
                
                id_item = QTableWidgetItem(str(c.id))
                id_item.setData(Qt.ItemDataRole.UserRole, c.id)
                
                num_item = QTableWidgetItem(str(c.numero_cuenta))
                num_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                
                dias_item = QTableWidgetItem(dias_texto)
                dias_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                dias_item.setBackground(QBrush(color_fondo))
                
                act_item = QTableWidgetItem("Sí" if c.activo else "No")
                act_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                
                self.tbl.setItem(i, 0, estado_item)
                self.tbl.setItem(i, 1, id_item)
                self.tbl.setItem(i, 2, num_item)
                self.tbl.setItem(i, 3, dias_item)
                self.tbl.setItem(i, 4, act_item)
        finally:
            self.tbl.setUpdatesEnabled(True)

    def _selected_id(self) -> int | None:
        sel = self.tbl.currentRow()
        if sel < 0:
            return None
        item = self.tbl.item(sel, 1)  # Columna 1 ahora tiene el ID
        if not item:
            return None
        return int(item.data(Qt.ItemDataRole.UserRole))

    def _crear(self):
        dlg = CuentaDialog(self, titulo="Crear cuenta")
        if dlg.exec():
            vals = dlg.values()
            # Validar número de cuenta (6-12 dígitos)
            if vals["numero_cuenta"] <= 0 or len(str(vals["numero_cuenta"])) < 6:
                QMessageBox.warning(self, "Crear cuenta", "Ingrese un número de cuenta válido (6-12 dígitos).")
                return
            ok, msg, _id = crear_cuenta(vals["numero_cuenta"], vals["activo"])
            QMessageBox.information(self, "Crear cuenta", msg)
            if ok:
                self._refrescar()

    def _editar(self):
        cid = self._selected_id()
        if not cid:
            QMessageBox.warning(self, "Editar cuenta", "Seleccione una cuenta.")
            return
        # Pre-cargar desde tabla
        row = self.tbl.currentRow()
        num_txt = self.tbl.item(row, 2).text() if self.tbl.item(row, 2) else "0"
        act_txt = self.tbl.item(row, 4).text() if self.tbl.item(row, 4) else "No"
        dlg = CuentaDialog(self, titulo="Editar cuenta", numero_cuenta=int(num_txt), activo=(act_txt == "Sí"))
        if dlg.exec():
            vals = dlg.values()
            if vals["numero_cuenta"] <= 0 or len(str(vals["numero_cuenta"])) < 6:
                QMessageBox.warning(self, "Editar cuenta", "Ingrese un número de cuenta válido (6-12 dígitos).")
                return
            ok, msg = actualizar_cuenta(cid, numero_cuenta=vals["numero_cuenta"], activo=vals["activo"]) 
            if ok:
                QMessageBox.information(self, "Editar cuenta", msg)
                self._refrescar()
            else:
                QMessageBox.warning(self, "Editar cuenta", msg)

    def _eliminar(self):
        cid = self._selected_id()
        if not cid:
            QMessageBox.warning(self, "Eliminar cuenta", "Seleccione una cuenta.")
            return
        msg = QMessageBox()
        msg.setWindowTitle("Confirmar eliminación")
        msg.setText("¿Eliminar definitivamente la cuenta seleccionada?")
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
        ok, detalle = eliminar_cuenta(cid)
        if ok:
            QMessageBox.information(self, "Eliminar cuenta", detalle)
            self._refrescar()
        else:
            QMessageBox.warning(self, "Eliminar cuenta", detalle)
