from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QBrush, QFont
from config.database import obtener_alertas_ultimos_consumos


class WidgetResumenAlertas(QWidget):
    """Widget que muestra un resumen de alertas de las cuentas.
    
    Muestra solo el último consumo de cada cuenta con su estado de alerta.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self.refrescar()
    
    def _init_ui(self):
        """Inicializa la interfaz del widget."""
        layout = QVBoxLayout(self)
        
        # Título
        titulo_layout = QHBoxLayout()
        titulo = QLabel("📊 Estado de Alertas por Cuenta")
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        titulo.setFont(font)
        titulo_layout.addWidget(titulo)
        
        # Botón refrescar
        btn_refrescar = QPushButton("🔄")
        btn_refrescar.setMaximumWidth(40)
        btn_refrescar.setToolTip("Refrescar alertas")
        btn_refrescar.clicked.connect(self.refrescar)
        titulo_layout.addWidget(btn_refrescar)
        
        layout.addLayout(titulo_layout)
        
        # Subtítulo
        subtitulo = QLabel("Cuentas dentro del rango de días configurado para alertas")
        subtitulo.setStyleSheet("color: gray; font-style: italic; font-size: 10px;")
        layout.addWidget(subtitulo)
        
        # Resumen rápido
        self.lbl_resumen = QLabel()
        self.lbl_resumen.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_resumen)
        
        # Tabla
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(5)
        self.tabla.setHorizontalHeaderLabels([
            "Cuenta", "Estado", "Fecha Vencimiento", "Días Restantes", "Total a Pagar"
        ])
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setMaximumHeight(300)
        
        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self.tabla)
    
    def refrescar(self):
        """Refresca los datos de alertas."""
        # Obtener SOLO alertas dentro del rango configurado (solo_alertas=True)
        alertas_criticas = obtener_alertas_ultimos_consumos(solo_alertas=True)
        
        # Calcular resumen
        vencidos = sum(1 for _, info in alertas_criticas if info['estado'] == 'vencido')
        urgentes = sum(1 for _, info in alertas_criticas if info['estado'] == 'urgente')
        proximos = sum(1 for _, info in alertas_criticas if info['estado'] == 'proximo')
        
        # Actualizar resumen
        resumen_html = f"<b>Alertas Activas: {len(alertas_criticas)}</b> | "
        resumen_html += f"<span style='color: red;'>🔴 {vencidos} vencidos</span> | "
        resumen_html += f"<span style='color: orange;'>🟠 {urgentes} hoy</span> | "
        resumen_html += f"<span style='color: #DAA520;'>🟡 {proximos} próximos</span>"
        self.lbl_resumen.setText(resumen_html)
        
        # Llenar tabla con todas las alertas críticas (ya están filtradas)
        self.tabla.setRowCount(len(alertas_criticas))
        
        for i, (consumo, info_alerta) in enumerate(alertas_criticas):
            estado = info_alerta['estado']
            dias_restantes = info_alerta['dias_restantes']
            
            # Cuenta
            cuenta_item = QTableWidgetItem(str(consumo.cuenta))
            cuenta_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
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
            
            # Fecha vencimiento
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
            
            # Total a pagar
            pagar_item = QTableWidgetItem(f"${float(consumo.Valor_total_pagar):.2f}")
            pagar_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            
            self.tabla.setItem(i, 0, cuenta_item)
            self.tabla.setItem(i, 1, estado_item)
            self.tabla.setItem(i, 2, fecha_item)
            self.tabla.setItem(i, 3, dias_item)
            self.tabla.setItem(i, 4, pagar_item)
        
        # Si no hay alertas críticas, mostrar mensaje
        if len(alertas_criticas) == 0:
            self.tabla.setRowCount(1)
            msg_item = QTableWidgetItem("✓ No hay cuentas dentro del rango de alerta configurado.")
            msg_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla.setSpan(0, 0, 1, 5)
            self.tabla.setItem(0, 0, msg_item)
