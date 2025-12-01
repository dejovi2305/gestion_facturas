# Ajuste del Sistema de Alertas - Últimos Consumos por Cuenta

## Cambio Importante

El sistema de alertas ha sido ajustado para considerar **SOLO el último consumo registrado de cada cuenta**, en lugar de mostrar alertas para todos los consumos históricos.

## Justificación

- Los consumos se registran **mes a mes** por cuenta
- Solo el **último consumo** es relevante para determinar el estado de vencimiento actual
- Una cuenta puede tener múltiples consumos históricos, pero la alerta debe basarse únicamente en el más reciente

## Ejemplo Práctico

### Antes del Ajuste ❌

**Cuenta 12345** con 3 consumos:

- Consumo de Enero (vencido) → 🔴 VENCIDO
- Consumo de Febrero (vencido) → 🔴 VENCIDO
- Consumo de Marzo (próximo) → 🟡 PRÓXIMO

**Resultado**: Se mostraban 3 alertas para la misma cuenta

### Después del Ajuste ✅

**Cuenta 12345** con 3 consumos:

- Solo se considera el **último**: Consumo de Marzo → 🟡 PRÓXIMO

**Resultado**: Se muestra 1 alerta por cuenta (la más reciente)

## Funciones Actualizadas

### Nueva Función Principal

#### `obtener_ultimo_consumo_por_cuenta(cuenta: int)`

Obtiene el consumo más reciente de una cuenta específica.

```python
# Retorna el Consumo con fecha_maxima_pago más reciente
ultimo = obtener_ultimo_consumo_por_cuenta(12345)
```

#### `obtener_alertas_ultimos_consumos(cuenta=None, solo_alertas=False)`

**FUNCIÓN PRINCIPAL PARA ALERTAS**

Obtiene alertas basadas en el último consumo de cada cuenta.

```python
# Obtener alertas de todas las cuentas (solo últimos consumos)
alertas = obtener_alertas_ultimos_consumos()

# Obtener solo cuentas con alertas críticas
alertas_criticas = obtener_alertas_ultimos_consumos(solo_alertas=True)

# Filtrar por cuenta específica
alertas_cuenta = obtener_alertas_ultimos_consumos(cuenta=12345)
```

**Returns**: Lista de tuplas `(ultimo_consumo, info_alerta)`

### Función Deprecada

#### `obtener_consumos_con_alertas()`

⚠️ **DEPRECADA** - Aún existe para compatibilidad pero calcula alertas para TODOS los consumos.

Se recomienda usar `obtener_alertas_ultimos_consumos()` en su lugar.

### Resumen Actualizado

#### `obtener_resumen_alertas_por_cuenta()`

Ahora retorna información del último consumo de cada cuenta:

```python
{
    numero_cuenta: {
        'estado': 'vencido' | 'urgente' | 'proximo' | 'ok',
        'dias_restantes': int,
        'fecha_vencimiento': date,
        'tiene_alerta': bool,
        'dias_habiles': int
    }
}
```

## Componentes Actualizados

### 1. `dialogo_vencimientos.py`

- Usa `obtener_alertas_ultimos_consumos(solo_alertas=True)`
- Título actualizado: "Alertas de Vencimiento - Últimos Consumos por Cuenta"
- Nota informativa agregada

### 2. `widget_resumen.py` (NUEVO)

Widget para mostrar en página de inicio:

- Resumen rápido: Total de cuentas por estado
- Tabla con cuentas en alerta crítica
- Solo muestra último consumo de cada cuenta
- Botón refrescar integrado

### 3. `consumos.py`

⚠️ **IMPORTANTE**: La vista de consumos AÚN muestra todos los consumos con sus alertas individuales.

**Esto es intencional** para que el usuario pueda ver el historial completo, pero:

- El **diálogo al inicio** solo muestra últimos consumos
- El **widget de resumen** solo muestra últimos consumos
- La **tabla de consumos** muestra todos (para revisión histórica)

## Flujo de Trabajo Actualizado

### Al Iniciar la Aplicación

1. Sistema busca el **último consumo** de cada cuenta activa
2. Calcula estado de alerta solo para esos consumos
3. Si hay alertas críticas (vencido/urgente/próximo), muestra diálogo
4. Diálogo lista **una fila por cuenta** (no múltiples consumos de la misma cuenta)

### En Vista de Consumos

- Se mantiene visualización de **todos los consumos** con semáforo
- Útil para ver historial y consumos antiguos pendientes
- Permite gestionar consumos específicos

### En Widget de Resumen (Home)

- Muestra estado actual de **cada cuenta**
- Basado solo en último consumo
- Actualización con botón refrescar

## Configuración de Alertas

El CRUD de Alertas configura **días hábiles por cuenta**:

```
Cuenta: 12345
Días hábiles: 5

→ Si el último consumo vence el 15-Nov
→ Fecha de alerta: 10-Nov (15 - 5)
→ A partir del 10-Nov se marca como 🟡 PRÓXIMO
```

## Query SQL Equivalente

```sql
-- Obtener último consumo de cada cuenta
SELECT c.*
FROM Consumo c
INNER JOIN (
    SELECT cuenta, MAX(fecha_maxima_pago) as max_fecha
    FROM Consumo
    GROUP BY cuenta
) uc ON c.cuenta = uc.cuenta AND c.fecha_maxima_pago = uc.max_fecha
```

## Beneficios del Ajuste

✅ **Claridad**: Una alerta por cuenta, no múltiples alertas confusas
✅ **Relevancia**: Solo importa el consumo actual, no los históricos
✅ **Precisión**: Refleja el estado real de la cuenta hoy
✅ **Performance**: Menos registros a procesar para alertas
✅ **UX**: Diálogos más limpios y enfocados

## Retrocompatibilidad

- Función `obtener_consumos_con_alertas()` se mantiene como deprecada
- Vista de consumos sigue mostrando todos los registros
- Nuevo código debe usar `obtener_alertas_ultimos_consumos()`
