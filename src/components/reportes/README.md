# Componente de Reportes

Este componente permite generar y exportar reportes en formato CSV de las principales entidades del sistema.

## Tipos de Reportes Disponibles

### 1. Consumos por Período

- **Filtros**: Fecha inicio, fecha fin, cuenta (opcional)
- **Datos**: ID, Cuenta, CUFE, Consumo kWh, Valor kWh, Fecha Máx. Pago, Núm. Orden, Total a Pagar
- **Uso**: Análisis de consumos en un rango de fechas específico

### 2. Consumos por Cuenta

- **Filtros**: Cuenta (requerido)
- **Datos**: ID, Cuenta, CUFE, Consumo kWh, Valor kWh, Fecha Máx. Pago, Núm. Orden, Total a Pagar
- **Uso**: Historial completo de consumos de una cuenta específica

### 3. Consumos por Orden de Pago

- **Filtros**: Número de orden (selector dinámico)
- **Datos**: ID, Cuenta, CUFE, Consumo kWh, Valor kWh, Fecha Máx. Pago, Núm. Orden, Total a Pagar
- **Uso**: Ver todos los consumos asociados a una orden de pago

### 4. Resumen de Cuentas

- **Filtros**: Ninguno (todas las cuentas activas)
- **Datos**: ID Cuenta, Número Cuenta, Activa, Último CUFE, Último Consumo kWh, Última Fecha Pago, Último Valor a Pagar
- **Uso**: Vista general del estado de todas las cuentas con su último consumo

### 5. Listado de Clientes

- **Filtros**: Ninguno
- **Datos**: ID, Nombre, Email, Teléfono
- **Uso**: Exportar base de datos de clientes

### 6. Órdenes de Pago

- **Filtros**: Fecha inicio, fecha fin (opcional)
- **Datos**: ID, Número Orden, Núm. Consumos, Total
- **Uso**: Resumen de órdenes de pago con totales

## Funcionalidad

### Generar Vista Previa

1. Seleccionar tipo de reporte
2. Configurar filtros según el tipo seleccionado
3. Hacer clic en "📊 Generar Vista Previa"
4. Los datos se muestran en la tabla

### Exportar a CSV

1. Generar la vista previa del reporte
2. Hacer clic en "💾 Exportar CSV"
3. Seleccionar ubicación y nombre del archivo
4. El archivo se guarda con encoding UTF-8-SIG (compatible con Excel)

## Estructura de Archivos

```
reportes/
├── __init__.py
├── reportes.ui          # Interfaz gráfica
├── reportes.py          # Lógica del componente
└── README.md            # Este archivo
```

## Funciones en database.py

- `generar_reporte_consumos_por_periodo(fecha_inicio, fecha_fin, cuenta=None)`
- `generar_reporte_consumos_por_cuenta(cuenta)`
- `generar_reporte_consumos_por_orden(numero_orden)`
- `generar_reporte_resumen_cuentas()`
- `generar_reporte_clientes()`
- `generar_reporte_ordenes_pago(fecha_inicio=None, fecha_fin=None)`

## Características Técnicas

- **Formato de Exportación**: CSV con UTF-8-SIG para compatibilidad con Excel
- **Nomenclatura de Archivos**: `reporte_{tipo}_{fecha}.csv`
- **Vista Previa**: Tabla interactiva con scroll para grandes volúmenes
- **Filtros Dinámicos**: Los filtros se habilitan/deshabilitan según el tipo de reporte

## Extensiones Futuras

- Exportación a Excel (.xlsx) con formato
- Gráficos estadísticos
- Filtros avanzados (rangos de valores, búsqueda por texto)
- Reportes programados
- Envío por email
