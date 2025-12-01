# Sistema de Alertas de Vencimiento

Este documento describe el sistema de alertas automáticas implementado para notificar sobre consumos próximos a vencer.

## Funcionalidad Implementada

### 1. Cálculo Automático de Estado de Alerta

El sistema calcula automáticamente el estado de cada consumo basándose en:

- **Fecha actual** vs **Fecha máxima de pago** del consumo
- **Días hábiles** configurados en el modelo Alerta para cada cuenta

#### Estados del Semáforo

| Estado      | Emoji | Color    | Descripción                                                 |
| ----------- | ----- | -------- | ----------------------------------------------------------- |
| **VENCIDO** | 🔴    | Rojo     | Fecha máxima de pago ya pasó (días restantes < 0)           |
| **HOY**     | 🟠    | Naranja  | Vence hoy (días restantes = 0)                              |
| **PRÓXIMO** | 🟡    | Amarillo | Dentro del período de alerta (fecha_actual >= fecha_alerta) |
| **OK**      | 🟢    | Verde    | Aún no está en período de alerta                            |

#### Cálculo de Fecha de Alerta

```
fecha_alerta = fecha_maxima_pago - dias_habiles
```

Si hoy es mayor o igual a la fecha de alerta, el consumo se marca como "PRÓXIMO".

### 2. Funciones Agregadas en `config/database.py`

#### `calcular_estado_alerta_consumo(consumo, fecha_actual=None)`

Calcula el estado de alerta para un consumo individual.

**Returns:**

```python
{
    'estado': 'vencido' | 'urgente' | 'proximo' | 'ok',
    'dias_restantes': int,  # Negativo si vencido
    'fecha_alerta': date,    # Fecha en que se debe alertar
    'dias_habiles': int      # Días hábiles configurados (0 si no hay alerta)
}
```

#### `obtener_consumos_con_alertas(cuenta=None, solo_alertas=False)`

Obtiene consumos con su información de alerta calculada.

**Args:**

- `cuenta`: Filtrar por cuenta específica
- `solo_alertas`: Si True, solo retorna consumos en estado vencido, urgente o próximo

**Returns:**

- Lista de tuplas `(consumo, info_alerta)`

#### `obtener_resumen_alertas_por_cuenta()`

Obtiene un resumen de alertas agrupadas por cuenta.

**Returns:**

```python
{
    numero_cuenta: {
        'vencidos': cantidad,
        'urgentes': cantidad,
        'proximos': cantidad,
        'ok': cantidad,
        'total': cantidad
    }
}
```

### 3. Vista de Consumos Actualizada

#### Cambios en la Tabla

Se agregaron **2 nuevas columnas**:

1. **Estado** (posición 0): Muestra el semáforo con colores de fondo

   - Tooltip con información detallada (estado, días restantes, días hábiles, fecha alerta)

2. **Días Restantes** (posición 7): Muestra cuántos días faltan
   - "Hoy" si vence hoy
   - "X días" si está pendiente
   - "X días atrasado" si está vencido
   - Color de fondo según estado

#### Estructura de la Tabla

| #   | Columna         | Descripción                                     |
| --- | --------------- | ----------------------------------------------- |
| 0   | Estado          | 🟢🟡🟠🔴 Semáforo visual                        |
| 1   | ID              | ID del consumo                                  |
| 2   | Cuenta          | Número de cuenta                                |
| 3   | CUFE            | UUID de la factura (truncado, tooltip completo) |
| 4   | Consumo kWh     | Consumo en kilovatios                           |
| 5   | Valor kWh       | Precio por kWh                                  |
| 6   | Fecha Max. Pago | Fecha límite de pago                            |
| 7   | Días Restantes  | Días hasta/desde vencimiento                    |
| 8   | Orden Pago      | Número de orden asociada                        |
| 9   | Total a Pagar   | Valor total                                     |

### 4. Diálogo de Alertas al Inicio

#### `DialogoAlertasVencimiento`

Nuevo diálogo que se muestra automáticamente al iniciar la aplicación si hay consumos en alerta.

**Características:**

- Se muestra 500ms después de que la ventana principal se carga
- Solo aparece si hay consumos vencidos, urgentes o próximos
- Muestra resumen en la parte superior: "🔴 X vencidos | 🟠 X hoy | 🟡 X próximos"
- Tabla con todos los consumos en alerta

#### `mostrar_alertas_si_existen(parent=None)`

Función helper que verifica si hay alertas y muestra el diálogo.

**Returns:**

- `True` si se mostraron alertas
- `False` si no había alertas

### 5. Integración en Main Window

Se agregó en `main.py`:

```python
# Import
from components.alertas.dialogo_vencimientos import mostrar_alertas_si_existen

# En __init__
QTimer.singleShot(500, self._mostrar_alertas_inicio)

# Nuevo método
def _mostrar_alertas_inicio(self):
    """Muestra el diálogo de alertas de vencimiento al iniciar."""
    try:
        mostrar_alertas_si_existen(self)
    except Exception as e:
        print(f"Error al mostrar alertas: {e}")
```

## Flujo de Trabajo

1. **Usuario configura días hábiles** en el CRUD de Alertas para cada cuenta
2. **Sistema calcula automáticamente** al refrescar la vista de consumos:
   - Fecha de alerta = Fecha vencimiento - Días hábiles
   - Estado según días restantes
3. **Vista de consumos muestra semáforo** en tiempo real
4. **Al abrir la aplicación**, se muestra diálogo con alertas pendientes

## Ejemplo de Uso

### Configurar Alerta

- Cuenta: 12345
- Días hábiles: 5

### Consumo con Fecha de Vencimiento: 2025-11-15

| Fecha Actual | Días Restantes | Fecha Alerta | Estado     |
| ------------ | -------------- | ------------ | ---------- |
| 2025-11-01   | 14             | 2025-11-10   | 🟢 OK      |
| 2025-11-10   | 5              | 2025-11-10   | 🟡 PRÓXIMO |
| 2025-11-14   | 1              | 2025-11-10   | 🟡 PRÓXIMO |
| 2025-11-15   | 0              | 2025-11-10   | 🟠 HOY     |
| 2025-11-16   | -1             | 2025-11-10   | 🔴 VENCIDO |

## Archivos Modificados

### Nuevos Archivos

- `components/alertas/dialogo_vencimientos.py` - Diálogo de alertas al inicio

### Archivos Modificados

- `config/database.py` - Funciones de cálculo de alertas
- `components/consumos/consumos.ui` - 2 columnas adicionales
- `components/consumos/consumos.py` - Lógica de semáforo y visualización
- `components/main/main.py` - Mostrar alertas al inicio
- `components/alertas/__init__.py` - Exports actualizados

## Consideraciones

- Si no hay alerta configurada para una cuenta, `dias_habiles = 0`
- El estado será "PRÓXIMO" solo el día de vencimiento (ya que fecha_alerta = fecha_vencimiento)
- Los colores de fondo ayudan a identificar rápidamente consumos críticos
- El diálogo de inicio es no-bloqueante (catch exceptions)
- Las alertas se recalculan cada vez que se refresca la tabla
