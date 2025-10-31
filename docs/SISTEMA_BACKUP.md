# Sistema de Backup Automático

## Descripción

El sistema de gestión de facturas cuenta con un sistema de backup automático que protege tus datos creando copias de seguridad periódicas de la base de datos.

## Características

### 🔄 Backup Automático

- **Backups periódicos**: Se crea un backup automáticamente cada 30 minutos
- **Thread en segundo plano**: No interfiere con el uso normal de la aplicación
- **Backup inicial**: Se crea un backup al iniciar la aplicación

### 📦 Estrategia de Retención

El sistema mantiene diferentes niveles de backups:

- **Horarios** (últimas 24-48 horas): Backup cada 30 minutos
- **Diarios** (últimos 7 días): Un backup por día
- **Semanales** (últimas 4 semanas): Un backup por semana
- **Mensuales** (últimos 6 meses): Un backup por mes

### 💾 Gestión Automática

- **Promoción automática**: Los backups horarios se promueven a diarios, los diarios a semanales, y los semanales a mensuales
- **Limpieza automática**: Se eliminan backups antiguos según la política de retención
- **Compresión automática**: Los backups de más de 7 días se comprimen automáticamente en formato ZIP para ahorrar espacio

### 🛡️ Seguridad

- Usa la API nativa de SQLite para backups seguros sin bloquear la base de datos
- Crea backup de seguridad antes de restaurar
- Backup incremental basado en cambios

## Ubicación de los Backups

Los backups se guardan en la carpeta `backups/` en la raíz del proyecto:

```
backups/
├── hourly/          # Backups horarios
├── daily/           # Backups diarios
├── weekly/          # Backups semanales
└── monthly/         # Backups mensuales
```

## Configuración

La configuración del sistema de backup se encuentra en `src/main.py`:

```python
backup_manager = inicializar_backup_manager(
    db_path="app.db",              # Ruta a la base de datos
    backup_dir="backups",          # Directorio de backups
    interval_minutes=30,           # Intervalo entre backups (30 min)
    keep_hourly=48,               # Mantener últimas 48 horas
    keep_daily=7,                 # Mantener últimos 7 días
    keep_weekly=4,                # Mantener últimas 4 semanas
    keep_monthly=6,               # Mantener últimos 6 meses
    compress_old=True             # Comprimir backups antiguos
)
```

### Parámetros Configurables

- **interval_minutes**: Frecuencia de backups automáticos (en minutos)
- **keep_hourly**: Cantidad de backups horarios a mantener
- **keep_daily**: Cantidad de backups diarios a mantener
- **keep_weekly**: Cantidad de backups semanales a mantener
- **keep_monthly**: Cantidad de backups mensuales a mantener
- **compress_old**: Si comprimir backups de más de 7 días

## Uso desde la Interfaz

### Ver Estado de Backups

1. Ir a la sección "Backups" en el menú principal
2. Ver el estado del sistema: activo/inactivo, último backup, espacio usado
3. Navegar entre las pestañas para ver backups por categoría

### Crear Backup Manual

1. Hacer clic en "💾 Crear Backup Manual"
2. Confirmar la acción
3. El backup se guardará en la categoría "Horarios"

### Restaurar un Backup

1. Seleccionar un backup de cualquier categoría
2. Hacer clic en "⏮ Restaurar Backup"
3. **⚠️ IMPORTANTE**: Confirmar la acción (se perderán los datos actuales)
4. Se crea un backup de seguridad antes de restaurar
5. Se recomienda reiniciar la aplicación después de restaurar

### Abrir Carpeta de Backups

- Hacer clic en "📁 Abrir Carpeta" para ver los archivos de backup en el explorador

## Uso Programático

### Crear Backup Manual

```python
from config.backup_manager import obtener_backup_manager

backup_manager = obtener_backup_manager()
ruta = backup_manager.crear_backup("hourly")
print(f"Backup creado: {ruta}")
```

### Restaurar Backup

```python
from config.backup_manager import obtener_backup_manager

backup_manager = obtener_backup_manager()
backup_manager.restaurar_backup("backups/daily/backup_daily_20250131_120000.db")
```

### Obtener Estado

```python
from config.backup_manager import obtener_backup_manager

backup_manager = obtener_backup_manager()
estado = backup_manager.estado()
print(f"Total de backups: {estado['total_backups']}")
print(f"Tamaño total: {estado['tamaño_total_mb']} MB")
```

### Listar Backups

```python
from config.backup_manager import obtener_backup_manager

backup_manager = obtener_backup_manager()
backups = backup_manager.listar_backups()

for tipo, lista in backups.items():
    print(f"\n{tipo.upper()}:")
    for backup in lista:
        print(f"  - {backup['nombre']} ({backup['fecha']})")
```

## Ventajas del Sistema

✅ **Protección automática**: No requiere intervención manual
✅ **Múltiples puntos de restauración**: Puedes volver a cualquier punto guardado
✅ **Eficiente en espacio**: Compresión automática de backups antiguos
✅ **Sin impacto en rendimiento**: Se ejecuta en segundo plano
✅ **Fácil de usar**: Interfaz gráfica intuitiva
✅ **Seguro**: Backup de seguridad antes de restaurar
✅ **Configurable**: Ajusta la frecuencia y retención según tus necesidades

## Recomendaciones

1. **No eliminar la carpeta `backups/`**: Contiene tus copias de seguridad
2. **Copias externas**: Para mayor seguridad, copia la carpeta `backups/` a un dispositivo externo periódicamente
3. **Espacio en disco**: Monitorea el espacio usado por los backups (visible en la interfaz)
4. **Prueba de restauración**: Realiza pruebas periódicas de restauración para verificar que los backups funcionan
5. **Antes de actualizaciones**: Crea un backup manual antes de actualizar la aplicación

## Solución de Problemas

### El sistema de backup no inicia

- Verifica que la base de datos `app.db` exista
- Verifica permisos de escritura en la carpeta del proyecto
- Revisa la consola para mensajes de error

### Error al crear backup

- Verifica espacio en disco disponible
- Verifica que la base de datos no esté corrupta
- Cierra otras aplicaciones que puedan estar usando la base de datos

### Error al restaurar backup

- Verifica que el archivo de backup exista y no esté corrupto
- Cierra todas las ventanas de la aplicación excepto la principal
- Si el archivo está comprimido (.zip), el sistema lo descomprimirá automáticamente

### Backups ocupan mucho espacio

- Los backups antiguos se comprimen automáticamente después de 7 días
- Ajusta la política de retención en la configuración
- Elimina manualmente backups muy antiguos desde la carpeta `backups/`

## Archivos del Sistema

- `src/config/backup_manager.py`: Módulo principal del sistema de backup
- `src/components/backups/backups.py`: Widget de interfaz gráfica
- `src/components/backups/backups.ui`: Diseño de la interfaz
- `backups/`: Directorio de almacenamiento de backups

## Ejemplo de Nombres de Archivo

- `backup_hourly_20250131_143000.db` - Backup horario sin comprimir
- `backup_daily_20250125_120000.db.zip` - Backup diario comprimido
- `backup_weekly_20250120_090000.db.zip` - Backup semanal comprimido
- `backup_monthly_20250101_000000.db.zip` - Backup mensual comprimido
