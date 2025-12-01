from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QBrush, QFont
from config.database import obtener_alertas_ultimos_consumos, obtener_resumen_alertas_por_cuenta


class DialogoAlertasVencimiento(QDialog):
    """Diálogo que muestra alertas de consumos próximos a vencer al iniciar la aplicación."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚠️ Alertas de Vencimiento")
        self.setMinimumSize(800, 500)
        
        layout = QVBoxLayout(self)
        
        # Título
        titulo = QLabel("⚠️ Alertas de Vencimiento - Últimos Consumos por Cuenta")
        font_titulo = QFont()
        font_titulo.setPointSize(14)
        font_titulo.setBold(True)
        titulo.setFont(font_titulo)
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titulo)
        
        # Nota informativa
        nota = QLabel("Se muestra el último consumo registrado de cada cuenta con alertas activas")
        nota.setStyleSheet("color: gray; font-style: italic;")
        nota.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(nota)
        
        # Subtítulo con resumen
        self.lbl_resumen = QLabel()
        self.lbl_resumen.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_resumen)
        
        # Tabla de alertas
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(4)
        self.tabla.setHorizontalHeaderLabels([
            "Estado", "Cuenta", "Fecha Vencimiento", "Días Restantes"
        ])
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.verticalHeader().setVisible(False)
        
        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(True)
        self.tabla.setColumnWidth(0, 120)  # Estado
        self.tabla.setColumnWidth(1, 150)  # Cuenta
        self.tabla.setColumnWidth(2, 150)  # Fecha
        self.tabla.setColumnWidth(3, 150)  # Días
        
        layout.addWidget(self.tabla)
        
        # Botón cerrar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.clicked.connect(self.accept)
        btn_layout.addWidget(btn_cerrar)
        layout.addLayout(btn_layout)
        
        # Cargar datos
        self._cargar_alertas()
    
    def _cargar_alertas(self):
        """Carga las alertas de consumos próximos a vencer (solo últimos consumos por cuenta)."""
        # Obtener solo últimos consumos con alerta
        consumos_alertas = obtener_alertas_ultimos_consumos(solo_alertas=True)
        
        # Calcular resumen
        vencidos = sum(1 for _, info in consumos_alertas if info['estado'] == 'vencido')
        urgentes = sum(1 for _, info in consumos_alertas if info['estado'] == 'urgente')
        proximos = sum(1 for _, info in consumos_alertas if info['estado'] == 'proximo')
        
        # Actualizar etiqueta de resumen
        resumen_texto = f"<span style='color: red;'>🔴 {vencidos} vencidos</span> | "
        resumen_texto += f"<span style='color: orange;'>🟠 {urgentes} hoy</span> | "
        resumen_texto += f"<span style='color: #DAA520;'>🟡 {proximos} próximos</span>"
        self.lbl_resumen.setText(resumen_texto)
        
        # Llenar tabla
        self.tabla.setRowCount(len(consumos_alertas))
        for i, (consumo, info_alerta) in enumerate(consumos_alertas):
            estado = info_alerta['estado']
            dias_restantes = info_alerta['dias_restantes']
            
            # Estado con color
            if estado == 'vencido':
                estado_texto = "🔴 VENCIDO"
                color_fondo = QColor(255, 200, 200)
            elif estado == 'urgente':
                estado_texto = "🟠 HOY"
                color_fondo = QColor(255, 220, 150)
            else:  # proximo
                estado_texto = "🟡 PRÓXIMO"
                color_fondo = QColor(255, 255, 200)
            
            estado_item = QTableWidgetItem(estado_texto)
            estado_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            estado_item.setBackground(QBrush(color_fondo))
            
            cuenta_item = QTableWidgetItem(str(consumo.cuenta))
            cuenta_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            fecha_item = QTableWidgetItem(consumo.fecha_maxima_pago.strftime("%Y-%m-%d"))
            fecha_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # Días restantes
            if dias_restantes < 0:
                dias_texto = f"{abs(dias_restantes)} días atrasado"
            elif dias_restantes == 0:
                dias_texto = "Hoy"
            else:
                dias_texto = f"{dias_restantes} días"
            dias_item = QTableWidgetItem(dias_texto)
            dias_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            dias_item.setBackground(QBrush(color_fondo))
            
            self.tabla.setItem(i, 0, estado_item)
            self.tabla.setItem(i, 1, cuenta_item)
            self.tabla.setItem(i, 2, fecha_item)
            self.tabla.setItem(i, 3, dias_item)


def mostrar_alertas_si_existen(parent=None) -> bool:
    """Muestra el diálogo de alertas si hay cuentas con últimos consumos próximos a vencer.
    
    Args:
        parent: Widget padre para el diálogo
    
    Returns:
        True si se mostraron alertas, False si no había alertas
    """
    # Verificar si hay alertas (solo últimos consumos por cuenta)
    consumos_alertas = obtener_alertas_ultimos_consumos(solo_alertas=True)
    
    if len(consumos_alertas) > 0:
        dialogo = DialogoAlertasVencimiento(parent)
        dialogo.exec()
        return True
    
    return False
