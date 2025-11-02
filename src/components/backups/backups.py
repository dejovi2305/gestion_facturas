"""Widget de gestión de backups de la base de datos."""

import os
import subprocess
from pathlib import Path
from PyQt6.uic import loadUi
from PyQt6.QtWidgets import (
    QWidget, QTableWidget, QTableWidgetItem, QPushButton,
    QLabel, QMessageBox, QHeaderView, QTabWidget
)
from PyQt6.QtCore import Qt, QTimer
from config.backup_manager import obtener_backup_manager


class BackupsWidget(QWidget):
    """Widget para gestión de backups automáticos."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Cargar UI
        from utils.ui import resolve_ui_path
        ui_path = resolve_ui_path(__file__, ui_filename="backups.ui")
        loadUi(ui_path, self)
        
        # Referencias a widgets
        self.lbl_estado: QLabel
        self.lbl_intervalo: QLabel
        self.lbl_total: QLabel
        self.lbl_tamanio: QLabel
        self.lbl_ultimo: QLabel
        
        self.btn_crear_backup: QPushButton
        self.btn_restaurar: QPushButton
        self.btn_abrir_carpeta: QPushButton
        self.btn_refrescar: QPushButton
        
        self.tabWidget: QTabWidget
        self.tbl_horarios: QTableWidget
        self.tbl_diarios: QTableWidget
        self.tbl_semanales: QTableWidget
        self.tbl_mensuales: QTableWidget
        
        self.lbl_info: QLabel
        
        # Obtener gestor de backups
        try:
            self.backup_manager = obtener_backup_manager()
        except RuntimeError:
            QMessageBox.critical(
                self, "Error",
                "Sistema de backup no inicializado. Reinicia la aplicación."
            )
            self.backup_manager = None
            return
        
        # Mapeo de tablas
        self.tablas = {
            'hourly': self.tbl_horarios,
            'daily': self.tbl_diarios,
            'weekly': self.tbl_semanales,
            'monthly': self.tbl_mensuales
        }
        
        # Configurar tablas
        for tabla in self.tablas.values():
            tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
            tabla.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
            tabla.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
            tabla.itemSelectionChanged.connect(self._on_seleccion_changed)
        
        # Conectar señales
        self.btn_crear_backup.clicked.connect(self._crear_backup_manual)
        self.btn_restaurar.clicked.connect(self._restaurar_backup)
        self.btn_abrir_carpeta.clicked.connect(self._abrir_carpeta)
        self.btn_refrescar.clicked.connect(self._refrescar)
        
        # Timer para actualizar estado automáticamente
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._refrescar_estado)
        self.timer.start(60000)  # Actualizar cada minuto
        
        # Cargar datos iniciales
        self._refrescar()
    
    def _refrescar(self):
        """Refresca la información de backups."""
        if not self.backup_manager:
            return
        
        self._refrescar_estado()
        self._refrescar_backups()
    
    def _refrescar_estado(self):
        """Actualiza el estado del sistema de backup."""
        if not self.backup_manager:
            return
        
        estado = self.backup_manager.estado()
        
        # Estado
        if estado['activo']:
            self.lbl_estado.setText("🟢 Activo")
            self.lbl_estado.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.lbl_estado.setText("🔴 Inactivo")
            self.lbl_estado.setStyleSheet("color: red; font-weight: bold;")
        
        # Intervalo
        self.lbl_intervalo.setText(f"{estado['intervalo_minutos']} minutos")
        
        # Total de backups
        backups_por_tipo = estado['backups_por_tipo']
        texto_total = f"{estado['total_backups']} backups ("
        texto_total += f"H:{backups_por_tipo['hourly']}, "
        texto_total += f"D:{backups_por_tipo['daily']}, "
        texto_total += f"S:{backups_por_tipo['weekly']}, "
        texto_total += f"M:{backups_por_tipo['monthly']})"
        self.lbl_total.setText(texto_total)
        
        # Tamaño total
        self.lbl_tamanio.setText(f"{estado['tamaño_total_mb']} MB")
        
        # Último backup
        if estado['ultimo_backup']:
            fecha = estado['ultimo_backup']['fecha']
            self.lbl_ultimo.setText(fecha.strftime("%Y-%m-%d %H:%M:%S"))
        else:
            self.lbl_ultimo.setText("Sin backups")
    
    def _refrescar_backups(self):
        """Actualiza las tablas de backups."""
        if not self.backup_manager:
            return
        
        backups = self.backup_manager.listar_backups()
        
        for tipo, tabla in self.tablas.items():
            tabla.setRowCount(0)
            
            for i, backup in enumerate(backups[tipo]):
                tabla.insertRow(i)
                
                # Nombre
                item_nombre = QTableWidgetItem(backup['nombre'])
                item_nombre.setData(Qt.ItemDataRole.UserRole, backup['ruta'])
                tabla.setItem(i, 0, item_nombre)
                
                # Fecha
                fecha_str = backup['fecha'].strftime("%Y-%m-%d %H:%M:%S")
                item_fecha = QTableWidgetItem(fecha_str)
                tabla.setItem(i, 1, item_fecha)
                
                # Tamaño
                tamaño_mb = round(backup['tamaño'] / (1024 * 1024), 2)
                item_tamanio = QTableWidgetItem(f"{tamaño_mb} MB")
                item_tamanio.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                tabla.setItem(i, 2, item_tamanio)
                
                # Estado
                estado = "📦 Comprimido" if backup['comprimido'] else "📄 Normal"
                item_estado = QTableWidgetItem(estado)
                tabla.setItem(i, 3, item_estado)
    
    def _on_seleccion_changed(self):
        """Maneja el cambio de selección en las tablas."""
        # Habilitar botón de restaurar si hay algo seleccionado
        tiene_seleccion = False
        for tabla in self.tablas.values():
            if tabla.selectedItems():
                tiene_seleccion = True
                break
        
        self.btn_restaurar.setEnabled(tiene_seleccion)
    
    def _crear_backup_manual(self):
        """Crea un backup manual."""
        if not self.backup_manager:
            return
        
        respuesta = QMessageBox.question(
            self, "Crear Backup",
            "¿Deseas crear un backup manual de la base de datos?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if respuesta == QMessageBox.StandardButton.Yes:
            try:
                ruta = self.backup_manager.crear_backup("hourly")
                if not ruta:
                    # Se omitió la creación porque el backup sería idéntico
                    QMessageBox.information(
                        self, "Backup omitido",
                        "No se creó un nuevo backup porque es idéntico al último backup existente."
                    )
                    return

                QMessageBox.information(
                    self, "Éxito",
                    f"Backup creado exitosamente:\n{Path(ruta).name}"
                )
                self._refrescar()
            except Exception as e:
                QMessageBox.critical(
                    self, "Error",
                    f"Error al crear backup:\n{str(e)}"
                )
    
    def _restaurar_backup(self):
        """Restaura un backup seleccionado."""
        if not self.backup_manager:
            return
        
        # Obtener backup seleccionado
        ruta_backup = None
        nombre_backup = None
        
        for tabla in self.tablas.values():
            items = tabla.selectedItems()
            if items:
                ruta_backup = tabla.item(items[0].row(), 0).data(Qt.ItemDataRole.UserRole)
                nombre_backup = tabla.item(items[0].row(), 0).text()
                break
        
        if not ruta_backup:
            return
        
        # Confirmar restauración
        respuesta = QMessageBox.warning(
            self, "⚠️ Restaurar Backup",
            f"¿Estás seguro de restaurar este backup?\n\n"
            f"Archivo: {nombre_backup}\n\n"
            f"⚠️ ADVERTENCIA: Esto reemplazará todos los datos actuales.\n"
            f"Se creará un backup de seguridad antes de restaurar.\n\n"
            f"¿Deseas continuar?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if respuesta == QMessageBox.StandardButton.Yes:
            try:
                self.backup_manager.restaurar_backup(ruta_backup)
                QMessageBox.information(
                    self, "Éxito",
                    "Base de datos restaurada exitosamente.\n\n"
                    "Se recomienda reiniciar la aplicación."
                )
                self._refrescar()
            except Exception as e:
                QMessageBox.critical(
                    self, "Error",
                    f"Error al restaurar backup:\n{str(e)}"
                )
    
    def _abrir_carpeta(self):
        """Abre la carpeta de backups en el explorador."""
        if not self.backup_manager:
            return
        
        carpeta = str(self.backup_manager.backup_dir.absolute())
        
        try:
            if os.name == 'nt':  # Windows
                os.startfile(carpeta)
            elif os.name == 'posix':  # Linux/Mac
                subprocess.run(['xdg-open', carpeta])
        except Exception as e:
            QMessageBox.warning(
                self, "Advertencia",
                f"No se pudo abrir la carpeta:\n{carpeta}\n\n{str(e)}"
            )
