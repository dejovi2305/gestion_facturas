import sys
sys.dont_write_bytecode = True
from PyQt6.QtWidgets import QApplication, QDialog
from config.database import initialize_database
from components.usuario.login import LoginWindow
from components.main.main import MainWindow

if __name__ == "__main__":
    initialize_database()
    app = QApplication(sys.argv)
    login_window = LoginWindow()
    if login_window.exec() == QDialog.DialogCode.Accepted:
        main_window = MainWindow()
        # Pasar el nombre del usuario autenticado (si fue capturado)
        user_name = getattr(login_window, 'logged_username', None)
        try:
            main_window.set_user(user_name)
        except Exception:
            pass
        main_window.show()
        sys.exit(app.exec())
    else:
        sys.exit(0)