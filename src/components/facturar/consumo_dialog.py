from PyQt6.QtWidgets import (
    QDialog,
    QFormLayout,
    QDialogButtonBox,
    QDoubleSpinBox,
    QSpinBox,
    QDateEdit,
    QVBoxLayout,
    QLineEdit,
)
from PyQt6.QtCore import QDate


class ConsumoDialog(QDialog):
    """
    Diálogo para revisar y ajustar los datos de Consumo antes de guardarlos.

    Campos:
    - consumo_kwh (int)
    - valor_kwh (float, 6 decimales)
    - valor_kwh_subsidiado (float, 6 decimales)
    - fecha_maxima_pago (date)
    - valor_total (float, 2 decimales)
    - valor_total_pagar (float, 2 decimales)
    - intereses_mora (float, 2 decimales)
    - numero_orden (int)
    """

    def __init__(
        self,
        parent=None,
        *,
    cufe: str | None = None,
    consumo_kwh: int | float | None = None,
        valor_kwh: float | None = None,
        valor_kwh_subsidiado: float | None = None,
        fecha_maxima_pago: str | None = None,  # YYYY-MM-DD
        valor_total: float | None = None,
        valor_total_pagar: float | None = None,
        intereses_mora: float | None = None,
        numero_orden: int | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Revisar Consumo")

        layout = QVBoxLayout(self)
        form = QFormLayout()

        # CUFE/UUID
        self.txt_cufe = QLineEdit(self)
        self.txt_cufe.setMaxLength(128)
        if cufe:
            self.txt_cufe.setText(str(cufe))
        form.addRow("CUFE / UUID", self.txt_cufe)

        # Consumo kWh
        self.sp_consumo = QSpinBox(self)
        self.sp_consumo.setRange(0, 10_000_000)
        if consumo_kwh is not None:
            try:
                self.sp_consumo.setValue(int(round(float(consumo_kwh))))
            except Exception:
                pass
        form.addRow("Consumo (kWh)", self.sp_consumo)

        # Valor kWh
        self.sp_valor_kwh = QDoubleSpinBox(self)
        self.sp_valor_kwh.setRange(0.0, 1_000_000.0)
        self.sp_valor_kwh.setDecimals(6)
        self.sp_valor_kwh.setSingleStep(0.0001)
        if valor_kwh is not None:
            try:
                self.sp_valor_kwh.setValue(float(valor_kwh))
            except Exception:
                pass
        form.addRow("Valor kWh (COP)", self.sp_valor_kwh)

        # Valor kWh subsidiado
        self.sp_valor_kwh_sub = QDoubleSpinBox(self)
        self.sp_valor_kwh_sub.setRange(0.0, 1_000_000.0)
        self.sp_valor_kwh_sub.setDecimals(6)
        if valor_kwh_subsidiado is not None:
            try:
                self.sp_valor_kwh_sub.setValue(float(valor_kwh_subsidiado))
            except Exception:
                pass
        form.addRow("Valor kWh subsidiado (COP)", self.sp_valor_kwh_sub)

        # Fecha máxima de pago
        self.dt_fecha = QDateEdit(self)
        self.dt_fecha.setCalendarPopup(True)
        if fecha_maxima_pago:
            try:
                y, m, d = [int(x) for x in fecha_maxima_pago.split("-")]
                self.dt_fecha.setDate(QDate(y, m, d))
            except Exception:
                self.dt_fecha.setDate(QDate.currentDate())
        else:
            self.dt_fecha.setDate(QDate.currentDate())
        form.addRow("Fecha máxima de pago", self.dt_fecha)

        # Valor total
        self.sp_valor_total = QDoubleSpinBox(self)
        self.sp_valor_total.setRange(0.0, 1_000_000_000.0)
        self.sp_valor_total.setDecimals(2)
        if valor_total is not None:
            try:
                self.sp_valor_total.setValue(float(valor_total))
            except Exception:
                pass
        form.addRow("Valor total (COP)", self.sp_valor_total)

        # Valor total pagar
        self.sp_valor_total_pagar = QDoubleSpinBox(self)
        self.sp_valor_total_pagar.setRange(0.0, 1_000_000_000.0)
        self.sp_valor_total_pagar.setDecimals(2)
        if valor_total_pagar is not None:
            try:
                self.sp_valor_total_pagar.setValue(float(valor_total_pagar))
            except Exception:
                pass
        form.addRow("Valor total a pagar (COP)", self.sp_valor_total_pagar)

        # Intereses de mora
        self.sp_mora = QDoubleSpinBox(self)
        self.sp_mora.setRange(0.0, 1_000_000_000.0)
        self.sp_mora.setDecimals(2)
        if intereses_mora is not None:
            try:
                self.sp_mora.setValue(float(intereses_mora))
            except Exception:
                pass
        form.addRow("Intereses de mora (COP)", self.sp_mora)

        # Número de orden
        self.sp_orden = QSpinBox(self)
        self.sp_orden.setRange(0, 1_000_000_000)
        if numero_orden is not None:
            try:
                self.sp_orden.setValue(int(numero_orden))
            except Exception:
                pass
        form.addRow("Número de orden", self.sp_orden)

        layout.addLayout(form)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel,
            parent=self,
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def values(self) -> dict:
        qd = self.dt_fecha.date()
        fecha = f"{qd.year():04d}-{qd.month():02d}-{qd.day():02d}"
        return {
            "cufe": self.txt_cufe.text().strip(),
            "consumo_kwh": int(self.sp_consumo.value()),
            "valor_kwh": float(self.sp_valor_kwh.value()),
            "valor_kwh_subsidiado": float(self.sp_valor_kwh_sub.value()),
            "fecha_maxima_pago": fecha,
            "valor_total": float(self.sp_valor_total.value()),
            "valor_total_pagar": float(self.sp_valor_total_pagar.value()),
            "intereses_mora": float(self.sp_mora.value()),
            "numero_orden": int(self.sp_orden.value()),
        }
