from PyQt6.QtWidgets import QMainWindow
from PyQt6.uic import loadUi

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        import os, sys
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
            ui_path = os.path.join(base_path, 'src', 'components', 'main', 'main.ui')
        else:
            src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
            ui_path = os.path.join(src_dir, 'components', 'main', 'main.ui')

        if not os.path.exists(ui_path):
            raise FileNotFoundError(f"Archivo .ui no encontrado: {ui_path}")

        loadUi(ui_path, self)
        self.setWindowTitle("Ventana Principal")
        # Configura aquí tus componentes de la ventana principal
