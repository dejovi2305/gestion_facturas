import os, sys
from PyQt6.QtWidgets import QMainWindow, QPushButton, QMessageBox
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.uic import loadUi
from components.facturar.cargar_factura import CargarFacturaWidget
from components.cuentas.cuentas import CuentasWidget
from components.clientes.clientes import ClientesWidget
from components.usuarios.usuarios import UsuariosWidget
from components.consumos.consumos import ConsumosWidget
from components.ordenes_pago.ordenes_pago import OrdenesPagoWidget
from components.alertas.alertas import AlertasWidget

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
        
        # Inicializar widgets de las páginas
        self._init_pages()
        
        # Preparar selección de botones del menú lateral
        self._menu_buttons = [
            getattr(self, name)
            for name in [
                'btn_cargar_factura', 'btn_usuarios',
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
    
    def _init_pages(self):
        """Inicializar las páginas del stackedWidget."""
        if not hasattr(self, 'stackedPages'):
            return
        
        # Limpiar páginas existentes (excepto la primera que es el home)
        while self.stackedPages.count() > 1:
            widget = self.stackedPages.widget(1)
            self.stackedPages.removeWidget(widget)
            widget.deleteLater()
        
        # Agregar página de cargar factura
        self.page_cargar_factura = CargarFacturaWidget()
        self.stackedPages.addWidget(self.page_cargar_factura)

        # Agregar página de cuentas
        self.page_cuentas = CuentasWidget()
        self.stackedPages.addWidget(self.page_cuentas)

        # Agregar página de clientes
        self.page_clientes = ClientesWidget()
        self.stackedPages.addWidget(self.page_clientes)

        # Agregar página de usuarios
        self.page_usuarios = UsuariosWidget()
        self.stackedPages.addWidget(self.page_usuarios)

        # Agregar página de consumos
        self.page_consumos = ConsumosWidget()
        self.stackedPages.addWidget(self.page_consumos)

        # Agregar página de órdenes de pago
        self.page_ordenes_pago = OrdenesPagoWidget()
        self.stackedPages.addWidget(self.page_ordenes_pago)

        # Agregar página de alertas
        self.page_alertas = AlertasWidget()
        self.stackedPages.addWidget(self.page_alertas)

    def _on_menu_clicked(self):
        sender = self.sender()
        if isinstance(sender, QPushButton):
            self._set_active_button(sender)
            # Navegar a la página correspondiente
            self._navigate_to_page(sender)

    def _set_active_button(self, active_btn: QPushButton):
        for btn in self._menu_buttons:
            btn.setChecked(btn is active_btn)
    
    def _navigate_to_page(self, button: QPushButton):
        """Navegar a la página correspondiente según el botón presionado."""
        if not hasattr(self, 'stackedPages'):
            return
        
        # Mapeo de botones a índices de páginas
        page_map = {
            'btn_cargar_factura': 1,  # Índice de la página de cargar factura
            'btn_cuentas': 2,         # Índice de la página de cuentas
            'btn_clientes': 3,        # Índice de la página de clientes
            'btn_usuarios': 4,        # Índice de la página de usuarios
            'btn_consumos': 5,        # Índice de la página de consumos
            'btn_ordenes_pago': 6,    # Índice de la página de órdenes de pago
            'btn_alertas': 7,         # Índice de la página de alertas
        }
        
        button_name = button.objectName()
        page_index = page_map.get(button_name, 0)  # 0 es la página home por defecto
        
        self.stackedPages.setCurrentIndex(page_index)

    def set_user(self, nombre: str | None, avatar_path: str | None = None):
        """Mostrar el nombre de usuario y avatar en el encabezado del menú.
        
        También configura la visibilidad del botón de usuarios según el rol.
        Solo el usuario 'admin' puede ver la opción de gestionar usuarios.
        """
        try:
            if hasattr(self, 'lbl_user_name') and nombre:
                self.lbl_user_name.setText(nombre)

            # Configurar visibilidad del botón de usuarios (solo para admin)
            if hasattr(self, 'btn_usuarios'):
                is_admin = nombre and nombre.lower() == 'admin'
                self.btn_usuarios.setVisible(is_admin)
                
                # Si el usuario no es admin y está en la página de usuarios, redirigir a home
                if not is_admin and hasattr(self, 'stackedPages'):
                    if self.stackedPages.currentIndex() == 4:  # Índice de página de usuarios
                        self.stackedPages.setCurrentIndex(0)
                        if self._menu_buttons:
                            self._set_active_button(self._menu_buttons[0])

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
