import sys
sys.dont_write_bytecode = True
from PyQt6.QtWidgets import QApplication, QDialog
from config.database import initialize_database
from config.backup_manager import inicializar_backup_manager, obtener_backup_manager
from components.usuario.login import LoginWindow
from components.main.main import MainWindow

if __name__ == "__main__":
    initialize_database()
    
    # Inicializar sistema de backup automático
    backup_manager = inicializar_backup_manager(
        db_path="app.db",
        backup_dir="backups",
        interval_minutes=30,      # Backup cada 30 minutos
        keep_hourly=48,          # Mantener últimas 48 horas (24 horas)
        keep_daily=7,            # Mantener últimos 7 días
        keep_weekly=4,           # Mantener últimas 4 semanas
        keep_monthly=6,          # Mantener últimos 6 meses
        compress_old=True        # Comprimir backups de más de 7 días
    )
    backup_manager.iniciar_backup_automatico()
    
    # Crear backup inicial al iniciar
    try:
        backup_manager.crear_backup("hourly")
    except Exception as e:
        print(f"⚠ No se pudo crear backup inicial: {e}")
    
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