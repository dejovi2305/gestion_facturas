from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QDialog, QMessageBox, QLineEdit
from PyQt6.uic import loadUi
from config.database import autenticar_usuario
from utils.ui import resolve_ui_path

class LoginWindow(QDialog):
    def __init__(self):
        super().__init__()
        import os, sys
        # Resolver rutas de UI e ícono de forma robusta
        ui_path = resolve_ui_path(__file__)
        # Ícono: intentar resolver en MEIPASS/src y MEIPASS directo
        icon_path = None
        if getattr(sys, 'frozen', False):
            base_path = getattr(sys, '_MEIPASS', None)
            if base_path:
                for cand in [
                    os.path.join(base_path, 'src', 'assets', 'icon.ico'),
                    os.path.join(base_path, 'assets', 'icon.ico'),
                ]:
                    if os.path.exists(cand):
                        icon_path = cand
                        break
        if not icon_path:
            # Desarrollo
            src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
            cand = os.path.join(src_dir, 'assets', 'icon.ico')
            icon_path = cand if os.path.exists(cand) else None

        if icon_path:
            self.setWindowIcon(QIcon(icon_path))
        loadUi(ui_path, self)
        self.setWindowTitle("Login")
        self.pushButton_login.clicked.connect(self.attempt_login)
        self.lineEdit_password.setEchoMode(QLineEdit.EchoMode.Password)

    def attempt_login(self):
        nombre_usuario = self.lineEdit_username.text().strip()
        contrasenna = self.lineEdit_password.text()

        if not nombre_usuario or not contrasenna:
            QMessageBox.warning(self, "Error", "Todos los campos son requeridos")
            return

        # Usar la nueva función de autenticación con contraseñas encriptadas
        autenticado, mensaje, usuario_obj = autenticar_usuario(nombre_usuario, contrasenna)
        
        if autenticado:
            # Guardar el nombre de usuario para usarlo en la ventana principal
            self.logged_username = nombre_usuario
            self.accept()
        else:
            QMessageBox.critical(self, "Error de autenticación", mensaje)
