from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QDialog, QMessageBox, QLineEdit
from PyQt6.uic import loadUi
from sqlalchemy.orm import sessionmaker
from config.database import SessionLocal
from models.usuario import Usuario

def validate_user(nombre_usuario: str, contrasenna: str) -> bool:
    db = SessionLocal()
    try:
        user = db.query(Usuario).filter(
            Usuario.nombre_usuario == nombre_usuario,
            Usuario.contrasenna == contrasenna,
            Usuario.activo == True
        ).first()
        return user is not None
    except Exception as e:
        print(f"Error validating user: {e}")
        return False
    finally:
        db.close()

class LoginWindow(QDialog):
    def __init__(self):
        super().__init__()
        import os, sys
        # Determinar rutas distintas para desarrollo y para ejecutable (PyInstaller)
        if getattr(sys, 'frozen', False):
            # Cuando está 'frozen' PyInstaller extrae los datos en _MEIPASS
            base_path = sys._MEIPASS
            ui_path = os.path.join(base_path, 'src', 'components', 'usuario', 'login.ui')
            icon_path = os.path.join(base_path, 'src', 'assets', 'icon.ico')
        else:
            # En desarrollo, partir desde la carpeta 'src' (dos niveles arriba del paquete)
            src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
            ui_path = os.path.join(src_dir, 'components', 'usuario', 'login.ui')
            icon_path = os.path.join(src_dir, 'assets', 'icon.ico')

        # Comprobar si el UI existe y cargarlo (en caso de error PyQt6 dará excepción)
        if not os.path.exists(ui_path):
            raise FileNotFoundError(f"Archivo .ui no encontrado: {ui_path}")

        self.setWindowIcon(QIcon(icon_path))
        loadUi(ui_path, self)
        self.setWindowTitle("Login")
        self.pushButton_login.clicked.connect(self.attempt_login)
        self.lineEdit_password.setEchoMode(QLineEdit.EchoMode.Password)

    def attempt_login(self):
        nombre_usuario = self.lineEdit_username.text()
        contrasenna = self.lineEdit_password.text()

        if not nombre_usuario or not contrasenna:
            QMessageBox.warning(self, "Error", "Todos los campos son requeridos")
            return

        if validate_user(nombre_usuario, contrasenna):
            # Guardar el nombre de usuario para usarlo en la ventana principal
            self.logged_username = nombre_usuario
            self.accept()
        else:
            QMessageBox.critical(self, "Error", "Usuario ó Contraseña incorrectos")
