import re
from typing import Optional, Any


def extraer_dato_por_posicion(
    pagina: Any,  # pdfplumber page object
    etiqueta: str = None,
    patron_regex: str = r"\b(\d{6,12})\b",
    offset_x0: float = -40,
    offset_y0: float = 5,
    offset_x1: float = 320,
    offset_y1: float = 85,
    x0_absoluto: float = None,
    y0_absoluto: float = None,
    x1_absoluto: float = None,
    y1_absoluto: float = None
) -> Optional[str]:
    """Extrae un dato específico basándose en coordenadas absolutas o relativas a una etiqueta.

    Args:
        pagina: Página de pdfplumber donde buscar.
        etiqueta: Texto de la etiqueta a buscar (ej: "Número de Cuenta"). Opcional si se usan coordenadas absolutas.
        patron_regex: Patrón regex para extraer el dato del texto encontrado.
        offset_x0: Offset izquierdo desde la etiqueta (negativo = más a la izquierda).
        offset_y0: Offset superior desde la etiqueta (positivo = más abajo).
        offset_x1: Offset derecho desde la etiqueta (positivo = más a la derecha).
        offset_y1: Offset inferior desde la etiqueta (positivo = más abajo).
        x0_absoluto: Coordenada x izquierda absoluta (si se proporciona, ignora etiqueta y offsets).
        y0_absoluto: Coordenada y superior absoluta.
        x1_absoluto: Coordenada x derecha absoluta.
        y1_absoluto: Coordenada y inferior absoluta.

    Returns:
        El dato extraído o None si no se encuentra.

    Estrategia:
    - Si se proporcionan coordenadas absolutas, úsalas directamente.
    - Si no, buscar la etiqueta y usar offsets relativos.
    """
    try:
        # Extraer todas las palabras con coordenadas
        palabras = pagina.extract_words()
        
        # Determinar las coordenadas del área de búsqueda
        if x0_absoluto is not None and y0_absoluto is not None and x1_absoluto is not None and y1_absoluto is not None:
            # Usar coordenadas absolutas
            x0_busqueda = x0_absoluto
            y0_busqueda = y0_absoluto
            x1_busqueda = x1_absoluto
            y1_busqueda = y1_absoluto
        elif etiqueta:
            # Buscar la etiqueta y usar offsets
            etiqueta_encontrada = None
            for palabra in palabras:
                if etiqueta.lower() in palabra['text'].lower():
                    etiqueta_encontrada = palabra
                    break
            
            if not etiqueta_encontrada:
                # Si no se encuentra la etiqueta, intentar búsqueda global
                texto_completo = pagina.extract_text()
                if texto_completo:
                    match = re.search(patron_regex, texto_completo, re.IGNORECASE)
                    if match:
                        return match.group(1)
                return None
            
            # Calcular área con offsets
            x0_busqueda = etiqueta_encontrada['x0'] + offset_x0
            y0_busqueda = etiqueta_encontrada['bottom'] + offset_y0
            x1_busqueda = etiqueta_encontrada['x1'] + offset_x1
            y1_busqueda = etiqueta_encontrada['bottom'] + offset_y1
        else:
            # No se proporcionó ni etiqueta ni coordenadas absolutas
            return None
        
        # Extraer palabras en esa región
        candidatos = []
        for palabra in palabras:
            # Verificar si la palabra está dentro del área de búsqueda
            if (palabra['x0'] >= x0_busqueda and 
                palabra['x1'] <= x1_busqueda and
                palabra['top'] >= y0_busqueda and 
                palabra['bottom'] <= y1_busqueda):
                candidatos.append(palabra['text'])
        
        # Aplicar regex en el texto encontrado
        if candidatos:
            zona = " ".join(candidatos)
            match = re.search(patron_regex, zona, re.IGNORECASE)
            if match:
                return match.group(1)
        
        # Respaldo: buscar en toda la página
        texto_completo = pagina.extract_text()
        if texto_completo:
            match = re.search(patron_regex, texto_completo, re.IGNORECASE)
            if match:
                return match.group(1)
                
    except Exception:
        return None

    return None

