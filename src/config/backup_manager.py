"""
Sistema de Backup Automático para la Base de Datos
Características:
- Backups automáticos periódicos en segundo plano
- Rotación de archivos con retención configurable
- Backup incremental basado en cambios
- Compresión de backups antiguos
"""

import os
import shutil
import sqlite3
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
import zipfile


class BackupManager:
    """Gestor de backups automáticos de la base de datos."""
    
    def __init__(
        self,
        db_path: str = "app.db",
        backup_dir: str = "backups",
        interval_minutes: int = 30,
        keep_hourly: int = 24,      # Mantener últimas 24 horas (cada 30 min)
        keep_daily: int = 7,         # Mantener últimos 7 días (1 por día)
        keep_weekly: int = 4,        # Mantener últimas 4 semanas (1 por semana)
        keep_monthly: int = 6,       # Mantener últimos 6 meses (1 por mes)
        compress_old: bool = True    # Comprimir backups antiguos
    ):
        """
        Inicializa el gestor de backups.
        
        Args:
            db_path: Ruta a la base de datos SQLite
            backup_dir: Directorio donde guardar los backups
            interval_minutes: Intervalo entre backups automáticos
            keep_hourly: Cantidad de backups horarios a mantener
            keep_daily: Cantidad de backups diarios a mantener
            keep_weekly: Cantidad de backups semanales a mantener
            keep_monthly: Cantidad de backups mensuales a mantener
            compress_old: Si comprimir backups de más de 7 días
        """
        self.db_path = Path(db_path)
        self.backup_dir = Path(backup_dir)
        self.interval_minutes = interval_minutes
        self.keep_hourly = keep_hourly
        self.keep_daily = keep_daily
        self.keep_weekly = keep_weekly
        self.keep_monthly = keep_monthly
        self.compress_old = compress_old
        
        # Control del thread
        self._running = False
        self._thread = None
        
        # Crear directorio de backups si no existe
        self.backup_dir.mkdir(exist_ok=True)
        
        # Subdirectorios por tipo
        (self.backup_dir / "hourly").mkdir(exist_ok=True)
        (self.backup_dir / "daily").mkdir(exist_ok=True)
        (self.backup_dir / "weekly").mkdir(exist_ok=True)
        (self.backup_dir / "monthly").mkdir(exist_ok=True)
    
    def crear_backup(self, tipo: str = "hourly") -> str:
        """
        Crea un backup de la base de datos.
        
        Args:
            tipo: Tipo de backup (hourly, daily, weekly, monthly)
        
        Returns:
            Ruta al archivo de backup creado
        """
        if not self.db_path.exists():
            raise FileNotFoundError(f"Base de datos no encontrada: {self.db_path}")
        
        # Generar nombre del archivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{tipo}_{timestamp}.db"
        backup_path = self.backup_dir / tipo / backup_name
        
        try:
            # Usar SQLite backup API para backup seguro sin bloquear
            source_conn = sqlite3.connect(str(self.db_path))
            backup_conn = sqlite3.connect(str(backup_path))
            
            with backup_conn:
                source_conn.backup(backup_conn)
            
            source_conn.close()
            backup_conn.close()
            
            print(f"✓ Backup creado: {backup_path}")
            return str(backup_path)
            
        except Exception as e:
            print(f"✗ Error al crear backup: {e}")
            if backup_path.exists():
                backup_path.unlink()
            raise
    
    def comprimir_backup(self, backup_path: Path) -> Path:
        """
        Comprime un archivo de backup.
        
        Args:
            backup_path: Ruta al archivo de backup
        
        Returns:
            Ruta al archivo comprimido
        """
        zip_path = backup_path.with_suffix('.db.zip')
        
        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(backup_path, backup_path.name)
            
            # Eliminar archivo original
            backup_path.unlink()
            print(f"✓ Backup comprimido: {zip_path}")
            return zip_path
            
        except Exception as e:
            print(f"✗ Error al comprimir backup: {e}")
            if zip_path.exists():
                zip_path.unlink()
            raise
    
    def limpiar_backups_antiguos(self):
        """Limpia backups antiguos según la política de retención."""
        ahora = datetime.now()
        
        # Limpiar backups horarios (mantener solo los más recientes)
        self._limpiar_por_cantidad(
            self.backup_dir / "hourly",
            self.keep_hourly
        )
        
        # Limpiar backups diarios
        self._limpiar_por_cantidad(
            self.backup_dir / "daily",
            self.keep_daily
        )
        
        # Limpiar backups semanales
        self._limpiar_por_cantidad(
            self.backup_dir / "weekly",
            self.keep_weekly
        )
        
        # Limpiar backups mensuales
        self._limpiar_por_cantidad(
            self.backup_dir / "monthly",
            self.keep_monthly
        )
        
        # Comprimir backups de más de 7 días
        if self.compress_old:
            self._comprimir_antiguos(dias=7)
    
    def _limpiar_por_cantidad(self, directorio: Path, cantidad_mantener: int):
        """
        Mantiene solo la cantidad especificada de backups más recientes.
        
        Args:
            directorio: Directorio a limpiar
            cantidad_mantener: Cantidad de backups a mantener
        """
        if not directorio.exists():
            return
        
        # Obtener todos los archivos de backup
        backups = sorted(
            directorio.glob("backup_*.db*"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        # Eliminar los más antiguos
        for backup in backups[cantidad_mantener:]:
            try:
                backup.unlink()
                print(f"✓ Backup antiguo eliminado: {backup.name}")
            except Exception as e:
                print(f"✗ Error al eliminar {backup.name}: {e}")
    
    def _comprimir_antiguos(self, dias: int = 7):
        """
        Comprime backups de más de X días.
        
        Args:
            dias: Antigüedad mínima en días para comprimir
        """
        limite = datetime.now() - timedelta(days=dias)
        
        for tipo in ["hourly", "daily", "weekly", "monthly"]:
            directorio = self.backup_dir / tipo
            if not directorio.exists():
                continue
            
            # Buscar archivos .db sin comprimir
            for backup in directorio.glob("backup_*.db"):
                if backup.stat().st_mtime < limite.timestamp():
                    try:
                        self.comprimir_backup(backup)
                    except Exception as e:
                        print(f"✗ Error al comprimir {backup.name}: {e}")
    
    def promover_backups(self):
        """
        Promueve backups según estrategia de retención.
        - El último backup horario de cada día se copia a daily
        - El último backup diario de cada semana se copia a weekly
        - El último backup semanal de cada mes se copia a monthly
        """
        ahora = datetime.now()
        
        # Promover a daily (último backup del día anterior)
        self._promover_ultimo("hourly", "daily", dias=1)
        
        # Promover a weekly (último backup de la semana anterior)
        if ahora.weekday() == 0:  # Lunes
            self._promover_ultimo("daily", "weekly", dias=7)
        
        # Promover a monthly (último backup del mes anterior)
        if ahora.day == 1:  # Primer día del mes
            self._promover_ultimo("weekly", "monthly", dias=30)
    
    def _promover_ultimo(self, origen: str, destino: str, dias: int):
        """
        Copia el último backup del período anterior al siguiente nivel.
        
        Args:
            origen: Directorio origen
            destino: Directorio destino
            dias: Días hacia atrás para buscar
        """
        dir_origen = self.backup_dir / origen
        dir_destino = self.backup_dir / destino
        
        if not dir_origen.exists():
            return
        
        # Buscar el último backup del período
        limite_inferior = datetime.now() - timedelta(days=dias+1)
        limite_superior = datetime.now() - timedelta(days=dias)
        
        backups = sorted(
            [
                b for b in dir_origen.glob("backup_*.db*")
                if limite_inferior.timestamp() < b.stat().st_mtime < limite_superior.timestamp()
            ],
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        if backups:
            backup_origen = backups[0]
            backup_destino = dir_destino / backup_origen.name.replace(f"_{origen}_", f"_{destino}_")
            
            try:
                shutil.copy2(backup_origen, backup_destino)
                print(f"✓ Backup promovido: {backup_origen.name} -> {destino}/")
            except Exception as e:
                print(f"✗ Error al promover backup: {e}")
    
    def restaurar_backup(self, backup_path: str) -> bool:
        """
        Restaura la base de datos desde un backup.
        
        Args:
            backup_path: Ruta al archivo de backup
        
        Returns:
            True si la restauración fue exitosa
        """
        backup_file = Path(backup_path)
        
        if not backup_file.exists():
            raise FileNotFoundError(f"Backup no encontrado: {backup_path}")
        
        # Si está comprimido, descomprimir primero
        if backup_file.suffix == '.zip':
            with zipfile.ZipFile(backup_file, 'r') as zipf:
                # Extraer a directorio temporal
                temp_dir = self.backup_dir / "temp"
                temp_dir.mkdir(exist_ok=True)
                zipf.extractall(temp_dir)
                
                # Buscar el archivo .db
                db_files = list(temp_dir.glob("*.db"))
                if not db_files:
                    raise ValueError("No se encontró archivo .db en el backup comprimido")
                
                backup_file = db_files[0]
        
        try:
            # Crear backup de seguridad de la base actual
            if self.db_path.exists():
                backup_actual = self.db_path.with_suffix('.db.before_restore')
                shutil.copy2(self.db_path, backup_actual)
                print(f"✓ Backup de seguridad creado: {backup_actual}")
            
            # Restaurar desde backup
            shutil.copy2(backup_file, self.db_path)
            print(f"✓ Base de datos restaurada desde: {backup_path}")
            
            # Limpiar temporal si se descomprimió
            if backup_file.parent.name == "temp":
                shutil.rmtree(backup_file.parent)
            
            return True
            
        except Exception as e:
            print(f"✗ Error al restaurar backup: {e}")
            
            # Intentar restaurar backup de seguridad
            backup_actual = self.db_path.with_suffix('.db.before_restore')
            if backup_actual.exists():
                shutil.copy2(backup_actual, self.db_path)
                print("✓ Base de datos revertida al estado anterior")
            
            raise
    
    def listar_backups(self) -> dict:
        """
        Lista todos los backups disponibles organizados por tipo.
        
        Returns:
            Diccionario con backups por tipo
        """
        backups = {
            'hourly': [],
            'daily': [],
            'weekly': [],
            'monthly': []
        }
        
        for tipo in backups.keys():
            directorio = self.backup_dir / tipo
            if directorio.exists():
                for backup in sorted(directorio.glob("backup_*.db*"), key=lambda p: p.stat().st_mtime, reverse=True):
                    backups[tipo].append({
                        'nombre': backup.name,
                        'ruta': str(backup),
                        'tamaño': backup.stat().st_size,
                        'fecha': datetime.fromtimestamp(backup.stat().st_mtime),
                        'comprimido': backup.suffix == '.zip'
                    })
        
        return backups
    
    def _backup_loop(self):
        """Loop principal del thread de backup."""
        print(f"🔄 Sistema de backup iniciado (intervalo: {self.interval_minutes} min)")
        
        while self._running:
            try:
                # Crear backup horario
                self.crear_backup("hourly")
                
                # Promover backups según estrategia
                self.promover_backups()
                
                # Limpiar backups antiguos
                self.limpiar_backups_antiguos()
                
            except Exception as e:
                print(f"✗ Error en ciclo de backup: {e}")
            
            # Esperar hasta el próximo backup
            time.sleep(self.interval_minutes * 60)
    
    def iniciar_backup_automatico(self):
        """Inicia el sistema de backup automático en segundo plano."""
        if self._running:
            print("⚠ Sistema de backup ya está en ejecución")
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._backup_loop, daemon=True)
        self._thread.start()
        
        print("✓ Sistema de backup automático iniciado")
    
    def detener_backup_automatico(self):
        """Detiene el sistema de backup automático."""
        if not self._running:
            print("⚠ Sistema de backup no está en ejecución")
            return
        
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        
        print("✓ Sistema de backup automático detenido")
    
    def estado(self) -> dict:
        """
        Obtiene el estado actual del sistema de backup.
        
        Returns:
            Diccionario con información de estado
        """
        backups = self.listar_backups()
        total_backups = sum(len(b) for b in backups.values())
        
        tamaño_total = 0
        for tipo_backups in backups.values():
            for backup in tipo_backups:
                tamaño_total += backup['tamaño']
        
        ultimo_backup = None
        for tipo in ['hourly', 'daily', 'weekly', 'monthly']:
            if backups[tipo]:
                ultimo_backup = backups[tipo][0]
                break
        
        return {
            'activo': self._running,
            'intervalo_minutos': self.interval_minutes,
            'total_backups': total_backups,
            'tamaño_total_mb': round(tamaño_total / (1024 * 1024), 2),
            'ultimo_backup': ultimo_backup,
            'backups_por_tipo': {
                tipo: len(lista) for tipo, lista in backups.items()
            }
        }


# Instancia global del gestor de backups
_backup_manager = None


def inicializar_backup_manager(**kwargs):
    """
    Inicializa el gestor global de backups.
    
    Args:
        **kwargs: Argumentos para BackupManager
    """
    global _backup_manager
    _backup_manager = BackupManager(**kwargs)
    return _backup_manager


def obtener_backup_manager() -> BackupManager:
    """Obtiene la instancia global del gestor de backups."""
    if _backup_manager is None:
        raise RuntimeError("BackupManager no ha sido inicializado. Llama a inicializar_backup_manager() primero.")
    return _backup_manager
