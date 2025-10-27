import re
from typing import Optional
import fitz  # PyMuPDF


def extraer_dato_por_posicion(
    pagina: "fitz.Page",
    etiqueta: str,
    patron_regex: str = r"\b(\d{6,12})\b",
    offset_x0: float = -40,
    offset_y0: float = 5,
    offset_x1: float = 320,
    offset_y1: float = 85
) -> Optional[str]:
    """Extrae un dato específico basándose en la posición de una etiqueta en el PDF.

    Args:
        pagina: Página de PyMuPDF donde buscar.
        etiqueta: Texto de la etiqueta a buscar (ej: "Número de Cuenta").
        patron_regex: Patrón regex para extraer el dato del texto encontrado.
        offset_x0: Offset izquierdo desde la etiqueta (negativo = más a la izquierda).
        offset_y0: Offset superior desde la etiqueta (positivo = más abajo).
        offset_x1: Offset derecho desde la etiqueta (positivo = más a la derecha).
        offset_y1: Offset inferior desde la etiqueta (positivo = más abajo).

    Returns:
        El dato extraído o None si no se encuentra.

    Estrategia:
    1. Buscar el rectángulo de la etiqueta en la página.
    2. Definir un rectángulo de búsqueda usando los offsets proporcionados.
    3. Leer palabras dentro de ese rectángulo.
    4. Aplicar el patrón regex para extraer el dato.
    5. Si falla, intentar búsqueda global en toda la página como respaldo.
    """
    try:
        # 1) Ubicar la etiqueta
        labels = pagina.search_for(etiqueta)
        if labels:
            label_rect = labels[0]
            
            # 2) Definir rectángulo de búsqueda con offsets personalizables
            area_busqueda = fitz.Rect(
                label_rect.x0 + offset_x0,
                label_rect.y1 + offset_y0,
                label_rect.x1 + offset_x1,
                label_rect.y1 + offset_y1
            )

            # 3) Extraer palabras en esa región
            palabras = pagina.get_text("words")  # (x0, y0, x1, y1, word, block, line, word_no)
            candidatos = []
            for x0, y0, x1, y1, w, *_ in palabras:
                if fitz.Rect(x0, y0, x1, y1).intersects(area_busqueda):
                    candidatos.append(w)

            # 4) Aplicar regex en el texto encontrado
            if candidatos:
                zona = " ".join(candidatos)
                match = re.search(patron_regex, zona, re.IGNORECASE)
                if match:
                    return match.group(1)

        # 5) Respaldo: buscar en toda la página
        texto_completo = pagina.get_text()
        match = re.search(patron_regex, texto_completo, re.IGNORECASE)
        if match:
            return match.group(1)
            
    except Exception:
        return None

    return None

