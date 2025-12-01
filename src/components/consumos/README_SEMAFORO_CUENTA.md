# Ajuste Final: Semáforo a Nivel de Cuenta

## Cambio Implementado

El semáforo de alertas ahora se muestra **exclusivamente a nivel de CUENTA**, no de consumo individual.

## Antes ❌

```
Tabla de consumos:
+--------+----+--------+------+
| Estado | ID | Cuenta | CUFE |...
+--------+----+--------+------+
| 🔴     | 1  | 12345  | abc  |  <- Semáforo en cada consumo
| 🟡     | 2  | 12345  | def  |  <- Semáforo en cada consumo
| 🟢     | 3  | 56789  | ghi  |  <- Semáforo en cada consumo
+--------+----+--------+------+
```

**Problema**: Cada consumo tenía su propio semáforo, causando confusión.

## Después ✅

```
Tabla de consumos:
+--------------------------------------------------+
| ▼ CUENTA 12345 - 🔴 VENCIDO (3 días atrasado)  |  <- Semáforo a nivel cuenta
+----+--------+------+----------+------------------+
| ID | Cuenta | CUFE | Consumo  | Total a Pagar    |
+----+--------+------+----------+------------------+
| 1  | 12345  | abc  | 2755 kWh | $1,250.00       |
| 2  | 12345  | def  | 0 kWh    | $862.80         |
+----+--------+------+----------+------------------+
| ▼ CUENTA 56789 - 🟢 OK (13 días)               |  <- Semáforo a nivel cuenta
+----+--------+------+----------+------------------+
| 3  | 56789  | ghi  | 3200 kWh | $1,500.00       |
+----+--------+------+----------+------------------+
```

**Solución**: El semáforo aparece en la fila de encabezado de cada cuenta, basado en el último consumo registrado.

## Lógica Implementada

### 1. Agrupación por Cuenta

Los consumos se agrupan por número de cuenta en la visualización.

### 2. Cálculo de Estado por Cuenta

Para cada cuenta:

1. Se obtiene el **último consumo** (más reciente por `fecha_maxima_pago`)
2. Se calcula el estado de alerta basado en ese último consumo
3. El semáforo refleja el estado de ese último consumo

### 3. Visualización Jerárquica

```python
▼ CUENTA 12345 - 🔴 VENCIDO (3 días atrasado)
    Consumo 1 (datos del consumo)
    Consumo 2 (datos del consumo)
    Consumo 3 (datos del consumo)

▼ CUENTA 56789 - 🟢 OK (13 días)
    Consumo 1 (datos del consumo)
    Consumo 2 (datos del consumo)
```

## Estados del Semáforo

| Emoji | Estado  | Descripción                      | Color          |
| ----- | ------- | -------------------------------- | -------------- |
| 🔴    | VENCIDO | Último consumo ya venció         | Rojo claro     |
| 🟠    | HOY     | Último consumo vence hoy         | Naranja claro  |
| 🟡    | PRÓXIMO | Dentro del período de alerta     | Amarillo claro |
| 🟢    | OK      | Aún no está en período de alerta | Verde claro    |

## Cambios Técnicos

### consumos.py

#### Estructura de Tabla Actualizada

- **Eliminadas**: Columnas "Estado" y "Días Restantes" individuales
- **Columnas actuales**: ID, Cuenta, CUFE, Consumo kWh, Valor kWh, Fecha Max. Pago, Orden Pago, Total a Pagar

#### Método `_refrescar()` Reimplementado

1. Agrupa consumos por cuenta
2. Para cada cuenta, obtiene el último consumo
3. Calcula estado de alerta del último consumo
4. Crea fila de encabezado con semáforo y estado
5. Lista consumos debajo del encabezado
6. Usa `setSpan()` para merge de columnas en encabezado

```python
# Ejemplo de código
consumos_por_cuenta = {}
estados_cuenta = {}

for c in consumos:
    if cuenta not in consumos_por_cuenta:
        ultimo = obtener_ultimo_consumo_por_cuenta(cuenta)
        info_alerta = calcular_estado_alerta_consumo(ultimo)
        estados_cuenta[cuenta] = info_alerta
    consumos_por_cuenta[cuenta].append(c)
```

#### Método `_selected_id()` Actualizado

- Ahora valida que no se seleccione una fila de encabezado de cuenta
- Solo retorna ID si es una fila de consumo válida

### consumos.ui

- Eliminadas columnas "Estado" y "Días Restantes"
- Solo 8 columnas de datos de consumo

## Ejemplo Real

### Configuración

- **Cuenta 900032159**: Alerta con 5 días hábiles
- **Último consumo**: Fecha vencimiento 2025-10-29
- **Fecha actual**: 2025-10-30

### Cálculo

```
Fecha vencimiento: 2025-10-29
Fecha actual: 2025-10-30
Días restantes: -1 (vencido)
Estado: 🔴 VENCIDO
Mensaje: "1 días atrasado"
```

### Visualización

```
▼ CUENTA 900032159 - 🔴 VENCIDO (1 días atrasado)
+----+-----------+----------------------+-------------+
| 1  | 900032159 | d4cb77c7e318ad9e898f | 0 kWh       |
+----+-----------+----------------------+-------------+
```

## Beneficios

✅ **Claridad Visual**: Un semáforo por cuenta, no múltiples confusos
✅ **Contexto Claro**: El estado se refiere a la cuenta, no a consumos individuales
✅ **Agrupación Lógica**: Consumos organizados por cuenta
✅ **Información Relevante**: Solo el estado del último consumo (actual) importa
✅ **Mejor UX**: Fácil identificar qué cuentas tienen problemas

## Integración con Otros Componentes

### Diálogo de Alertas

- Muestra una fila por cuenta
- Basado en último consumo de cada cuenta
- Consistente con la vista de consumos

### Widget de Resumen

- Muestra estado de cada cuenta
- Basado en último consumo
- Coherente con la lógica implementada

## Notas Importantes

1. **Solo el último consumo importa**: Los consumos históricos se muestran pero no afectan el semáforo de la cuenta
2. **Un semáforo por cuenta**: Aunque una cuenta tenga 10 consumos, solo se muestra un semáforo (del último)
3. **Agrupación visual**: Los consumos se agrupan bajo el encabezado de su cuenta
4. **Selección correcta**: No se puede seleccionar la fila de encabezado, solo consumos individuales

## Compatibilidad

- ✅ Funciones de database.py sin cambios
- ✅ Diálogo de alertas compatible
- ✅ Widget de resumen compatible
- ✅ Operaciones CRUD de consumos funcionan igual
