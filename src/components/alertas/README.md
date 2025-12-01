# Componente de Alertas

Este componente implementa el CRUD completo para la gestión de alertas asociadas a cuentas.

## Archivos creados

- `alertas.ui`: Interfaz gráfica con tabla de 3 columnas (ID, Cuenta, Días Hábiles) y filtro por cuenta
- `alertas.py`: Widget principal y diálogo de creación/edición
- `__init__.py`: Exporta AlertasWidget

## Características

### Widget AlertasWidget

- **Tabla**: Muestra todas las alertas con sus datos
- **Filtro**: Combo para filtrar alertas por cuenta específica
- **Botones CRUD**: Crear, Editar, Eliminar, Refrescar

### Diálogo AlertaDialog

- **Selección de cuenta**: Combo con todas las cuentas disponibles
- **Días hábiles**: SpinBox (0-365) para configurar los días de alerta
- **Validaciones**:
  - Cuenta obligatoria
  - Una sola alerta por cuenta (no se permiten duplicados)

## Funciones en database.py

- `listar_alertas(cuenta=None)`: Lista todas las alertas o filtra por cuenta
- `obtener_alerta_por_id(alerta_id)`: Obtiene una alerta específica
- `crear_alerta(cuenta, dias_habiles)`: Crea una nueva alerta con validaciones
- `actualizar_alerta(alerta_id, cuenta=None, dias_habiles=None)`: Actualiza una alerta
- `eliminar_alerta(alerta_id)`: Elimina una alerta

## Validaciones

1. Al crear/editar: Verifica que la cuenta existe en la base de datos
2. No permite múltiples alertas para la misma cuenta
3. Días hábiles debe estar entre 0 y 365

## Integración

El componente está integrado en `main.py`:

- Importado como `AlertasWidget`
- Agregado al stackedPages (índice 7)
- Mapeado al botón `btn_alertas`
