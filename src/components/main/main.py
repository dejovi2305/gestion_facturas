import os, sys
from PyQt6.QtWidgets import QMainWindow, QPushButton, QMessageBox
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.uic import loadUi

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
            ui_path = os.path.join(base_path, 'src', 'components', 'main', 'main.ui')
            icon_path = os.path.join(base_path, 'src', 'assets', 'icon.ico')
        else:
            src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
            ui_path = os.path.join(src_dir, 'components', 'main', 'main.ui')
            icon_path = os.path.join(src_dir, 'assets', 'icon.ico')
            
        if not os.path.exists(ui_path):
            raise FileNotFoundError(f"Archivo .ui no encontrado: {ui_path}")

        loadUi(ui_path, self)
        self.setWindowIcon(QIcon(icon_path))
        self.setWindowTitle("Ventana Principal")
        # Preparar selección de botones del menú lateral
        self._menu_buttons = [
            getattr(self, name)
            for name in [
                'btn_cargar_factura', 'btn_gestionar_factura', 'btn_usuarios',
                'btn_cuentas', 'btn_clientes', 'btn_consumos',
                'btn_ordenes_pago', 'btn_reportes', 'btn_alertas'
            ]
            if hasattr(self, name)
        ]

        for btn in self._menu_buttons:
            if isinstance(btn, QPushButton):
                btn.setCheckable(True)
                btn.clicked.connect(self._on_menu_clicked)

        # Selección inicial
        if self._menu_buttons:
            self._set_active_button(self._menu_buttons[0])
        
        # Conectar botón de salir
        if hasattr(self, 'btn_salir'):
            self.btn_salir.clicked.connect(self._on_salir)

    def _on_menu_clicked(self):
        sender = self.sender()
        if isinstance(sender, QPushButton):
            self._set_active_button(sender)

    def _set_active_button(self, active_btn: QPushButton):
        for btn in self._menu_buttons:
            btn.setChecked(btn is active_btn)

    def set_user(self, nombre: str | None, avatar_path: str | None = None):
        """Mostrar el nombre de usuario y avatar en el encabezado del menú."""
        try:
            if hasattr(self, 'lbl_user_name') and nombre:
                self.lbl_user_name.setText(nombre)

            # Resolver ruta por defecto de avatar
            if not avatar_path:
                if getattr(sys, 'frozen', False):
                    base = sys._MEIPASS
                    avatar_path = os.path.join(base, 'src', 'assets', 'icon.ico')
                else:
                    src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
                    avatar_path = os.path.join(src_dir, 'assets', 'icon.ico')

            if hasattr(self, 'avatar') and os.path.exists(avatar_path):
                pix = QPixmap(avatar_path)
                self.avatar.setPixmap(pix)
        except Exception:
            # No bloquear la UI si algo falla al cargar avatar/nombre
            pass
    
    def _on_salir(self):
        """Confirmar y cerrar la aplicación."""
        msg = QMessageBox()
        msg.setWindowTitle('Confirmar salida')
        msg.setText('¿Está seguro de que desea salir?')
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.setDefaultButton(QMessageBox.StandardButton.No)

        # Cambiar texto de los botones
        yes_button = msg.button(QMessageBox.StandardButton.Yes)
        no_button = msg.button(QMessageBox.StandardButton.No)
        yes_button.setText("Sí")
        no_button.setText("No")

        reply = msg.exec()

        if reply == QMessageBox.StandardButton.Yes:
            self.close()
