# Factura Helper - Guía de Uso

Este módulo proporciona funciones reutilizables para extraer datos de facturas PDF.

## Funciones Principales

### 1. `extraer_dato_por_posicion()` - Extractor Genérico

Extrae cualquier dato basándose en la posición de una etiqueta en el PDF.

**Parámetros:**

- `pagina`: Página de PyMuPDF donde buscar
- `etiqueta`: Texto de la etiqueta a buscar (ej: "Número de Cuenta", "Valor Total")
- `patron_regex`: Patrón regex para extraer el dato (default: números de 6-12 dígitos)
- `offset_x0`: Offset izquierdo desde la etiqueta (negativo = más a la izquierda)
- `offset_y0`: Offset superior desde la etiqueta (positivo = más abajo)
- `offset_x1`: Offset derecho desde la etiqueta (positivo = más a la derecha)
- `offset_y1`: Offset inferior desde la etiqueta (positivo = más abajo)

**Ejemplo de uso:**

```python
import fitz
from components.facturar.factura_helper import extraer_dato_por_posicion

# Abrir PDF
documento = fitz.open("factura.pdf")
pagina = documento[0]

# Extraer número de cuenta
numero_cuenta = extraer_dato_por_posicion(
    pagina=pagina,
    etiqueta="Número de Cuenta",
    patron_regex=r"\b(\d{6,12})\b",
    offset_x0=-40,
    offset_y0=5,
    offset_x1=320,
    offset_y1=85
)

# Extraer valor total
valor_total = extraer_dato_por_posicion(
    pagina=pagina,
    etiqueta="Valor Total",
    patron_regex=r"\$?\s*([\d\.,]+)",
    offset_x0=-20,
    offset_y0=5,
    offset_x1=200,
    offset_y1=60
)

# Extraer fecha
fecha = extraer_dato_por_posicion(
    pagina=pagina,
    etiqueta="Fecha Máxima de Pago",
    patron_regex=r"(\d{2}/\w+/\d{4})",
    offset_x0=-10,
    offset_y0=5,
    offset_x1=150,
    offset_y1=50
)

print(f"Cuenta: {numero_cuenta}")
print(f"Valor: ${valor_total}")
print(f"Fecha: {fecha}")

documento.close()
```

### 2. `extraer_numero_cuenta_por_posicion()` - Función de Conveniencia

Función específica para extraer número de cuenta con parámetros preconfigurados.

```python
from components.facturar.factura_helper import extraer_numero_cuenta_por_posicion

numero_cuenta = extraer_numero_cuenta_por_posicion(pagina)
```

### 3. `extraer_datos_factura()` - Extracción por Regex

Extrae múltiples campos usando expresiones regulares en el texto plano.

```python
from components.facturar.factura_helper import extraer_datos_factura

texto = pagina.get_text()
datos = extraer_datos_factura(texto)

print(datos['numero_cuenta'])
print(datos['nombre_cliente'])
print(datos['valor_total'])
```

### 4. `formatear_datos_extraidos()` - Formato de Salida

Formatea un diccionario de datos para mostrar de forma legible.

```python
from components.facturar.factura_helper import formatear_datos_extraidos

texto_formateado = formatear_datos_extraidos(datos)
print(texto_formateado)
```

## Estrategia de Extracción

1. **Por posición (recomendado)**: Más preciso cuando el layout es consistente

   - Busca la etiqueta
   - Lee el contenido en un rectángulo definido por offsets
   - Aplica regex al contenido extraído

2. **Por regex (fallback)**: Cuando la posición no es confiable
   - Busca patrones en todo el texto
   - Menos preciso pero más flexible

## Ajuste de Offsets

Para ajustar los rectángulos de búsqueda, experimenta con los valores:

```python
# Valores positivos mueven hacia abajo/derecha
# Valores negativos mueven hacia arriba/izquierda

extraer_dato_por_posicion(
    pagina=pagina,
    etiqueta="Tu Etiqueta",
    patron_regex=r"tu_patron",
    offset_x0=-40,  # Mueve 40px a la izquierda del inicio de la etiqueta
    offset_y0=5,    # Mueve 5px abajo del fin de la etiqueta
    offset_x1=320,  # Extiende 320px a la derecha del fin de la etiqueta
    offset_y1=85    # Extiende 85px abajo del fin de la etiqueta
)
```

## Patrones Regex Comunes

```python
# Números de cuenta (6-12 dígitos)
r"\b(\d{6,12})\b"

# Valores monetarios
r"\$?\s*([\d\.,]+)"

# Fechas formato DD/MMM/YYYY
r"(\d{2}/\w+/\d{4})"

# Nombres (letras y espacios)
r"([A-ZÁÉÍÓÚÑ\s]+)"

# Direcciones (alfanumérico con espacios)
r"([A-Z0-9\s\-\.]+)"
```

## Ejemplos de Uso Avanzado

### Extraer múltiples campos por posición

```python
documento = fitz.open("factura.pdf")
pagina = documento[0]

campos = {
    'numero_cuenta': {
        'etiqueta': 'Número de Cuenta',
        'patron': r"\b(\d{6,12})\b",
        'offsets': (-40, 5, 320, 85)
    },
    'valor_total': {
        'etiqueta': 'Valor Total',
        'patron': r"\$?\s*([\d\.,]+)",
        'offsets': (-20, 5, 200, 60)
    },
    'municipio': {
        'etiqueta': 'Municipio',
        'patron': r"([A-ZÁÉÍÓÚÑ\s]+)",
        'offsets': (-10, 5, 150, 50)
    }
}

datos = {}
for campo, config in campos.items():
    valor = extraer_dato_por_posicion(
        pagina=pagina,
        etiqueta=config['etiqueta'],
        patron_regex=config['patron'],
        offset_x0=config['offsets'][0],
        offset_y0=config['offsets'][1],
        offset_x1=config['offsets'][2],
        offset_y1=config['offsets'][3]
    )
    datos[campo] = valor

print(datos)
documento.close()
```

## Notas

- Los offsets deben ajustarse según el diseño específico de cada proveedor
- La extracción por posición requiere layouts consistentes
- Siempre incluir un fallback con regex para mayor robustez
