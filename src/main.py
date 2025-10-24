import sys
from PyQt6.QtWidgets import QApplication, QDialog
from config.database import initialize_database
from components.usuario.login import LoginWindow
from components.main.main import MainWindow

sys.dont_write_bytecode = True

if __name__ == "__main__":
    initialize_database()
    app = QApplication(sys.argv)
    login_window = LoginWindow()
    if login_window.exec() == QDialog.DialogCode.Accepted:
        main_window = MainWindow()
        main_window.show()
        sys.exit(app.exec())
    else:
        sys.exit(0)