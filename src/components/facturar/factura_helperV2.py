"""
Helper para extracción de datos de facturas electrónicas en formato XML.
Este módulo procesa archivos XML de facturas electrónicas (UBL) y extrae la información relevante.
"""

import xml.etree.ElementTree as ET
import re
from typing import Optional, Dict, Any, List, Tuple, Callable


# Definición de namespaces comunes en facturas electrónicas UBL
NAMESPACES = {
    'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
    'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
    'ext': 'urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2',
    'sts': 'dian:gov:co:facturaelectronica:Structures-2-1',
    'ds': 'http://www.w3.org/2000/09/xmldsig#',
    'xades': 'http://uri.etsi.org/01903/v1.3.2#',
    'xades141': 'http://uri.etsi.org/01903/v1.4.1#',
    '': 'urn:oasis:names:specification:ubl:schema:xsd:AttachedDocument-2',
    'invoice': 'urn:oasis:names:specification:ubl:schema:xsd:Invoice-2'
}


def imprimir_nodos_xml(ruta_archivo: str, nivel_max: Optional[int] = None) -> None:
    """
    Lee un archivo XML y imprime todos sus nodos con estructura jerárquica.
    
    Args:
        ruta_archivo: Ruta completa al archivo XML
        nivel_max: Nivel máximo de profundidad a imprimir (None = sin límite)
    """
    try:
        # Parsear el archivo XML
        tree = ET.parse(ruta_archivo)
        root = tree.getroot()
        
        print(f"\n{'='*80}")
        print(f"ESTRUCTURA DEL XML: {ruta_archivo}")
        print(f"{'='*80}\n")
        
        print(f"Nodo raíz: {_limpiar_tag(root.tag)}")
        print(f"Atributos raíz: {root.attrib if root.attrib else 'Ninguno'}")
        print()
        
        # Imprimir árbol de nodos
        _imprimir_nodo_recursivo(root, nivel=0, nivel_max=nivel_max)
        
        print(f"\n{'='*80}")
        print("FIN DE LA ESTRUCTURA")
        print(f"{'='*80}\n")
        
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo '{ruta_archivo}'")
    except ET.ParseError as e:
        print(f"Error al parsear el XML: {e}")
    except Exception as e:
        print(f"Error inesperado: {e}")


def _imprimir_nodo_recursivo(elemento: ET.Element, nivel: int = 0, nivel_max: Optional[int] = None) -> None:
    """
    Imprime recursivamente un nodo y sus hijos con indentación.
    
    Args:
        elemento: Elemento XML a imprimir
        nivel: Nivel actual de profundidad
        nivel_max: Nivel máximo a imprimir
    """
    if nivel_max is not None and nivel > nivel_max:
        return
    
    indent = "  " * nivel
    tag_limpio = _limpiar_tag(elemento.tag)
    
    # Obtener texto del nodo (si existe y no es solo espacios en blanco)
    texto = elemento.text.strip() if elemento.text and elemento.text.strip() else None
    
    # Construir línea de información del nodo
    info_nodo = f"{indent}├─ {tag_limpio}"
    
    # Agregar atributos si existen
    if elemento.attrib:
        atributos_str = ", ".join([f"{k}='{v}'" for k, v in elemento.attrib.items()])
        info_nodo += f" [{atributos_str}]"
    
    # Agregar texto si existe y es corto
    if texto:
        if len(texto) <= 80:
            info_nodo += f": {texto}"
        else:
            info_nodo += f": {texto[:77]}..."
    
    print(info_nodo)
    
    # Procesar hijos recursivamente
    for hijo in elemento:
        _imprimir_nodo_recursivo(hijo, nivel + 1, nivel_max)


def _limpiar_tag(tag: str) -> str:
    """
    Limpia el tag XML eliminando el namespace.
    
    Args:
        tag: Tag completo con namespace
        
    Returns:
        Tag sin namespace
    """
    if '}' in tag:
        return tag.split('}')[1]
    return tag


def extraer_datos_factura(ruta_archivo: str) -> Dict[str, Any]:
    """
    Extrae los datos principales de una factura electrónica XML.
    
    Args:
        ruta_archivo: Ruta completa al archivo XML
        
    Returns:
        Diccionario con los datos extraídos de la factura
    """
    try:
        tree = ET.parse(ruta_archivo)
        root = tree.getroot()
        
        # Registrar namespaces
        for prefix, uri in NAMESPACES.items():
            if prefix:  # No registrar el namespace vacío
                ET.register_namespace(prefix, uri)
        
        datos = {
            'numero_factura': None,
            'uuid': None,
            'fecha_emision': None,
            'hora_emision': None,
            'proveedor': {},
            'cliente': {},
            'totales': {},
            'items': []
        }
        
        # TODO: Implementar extracción de datos específicos
        # Por ahora solo retorna estructura vacía
        
        return datos
        
    except Exception as e:
        print(f"Error al extraer datos: {e}")
        return {}


def _es_numero_cuenta(texto: str) -> bool:
    """Heurística simple para validar un número de cuenta (solo dígitos, 6-12 long.)."""
    if not texto:
        return False
    texto_limpio = texto.strip()
    return bool(re.fullmatch(r"\d{6,12}", texto_limpio))


def _ruta_elemento(elem: ET.Element, parent_map: Dict[ET.Element, ET.Element]) -> str:
    """Construye una ruta simple del elemento hasta la raíz usando tags sin namespace."""
    partes: List[str] = []
    actual: Optional[ET.Element] = elem
    while actual is not None:
        partes.append(_limpiar_tag(actual.tag))
        actual = parent_map.get(actual)
    return "/".join(reversed(partes))


def _candidatos_numero_cuenta_en_raiz(root: ET.Element) -> List[Tuple[str, str]]:
    """Devuelve lista de candidatos (valor, ruta) buscando en un árbol XML dado."""
    parent_map: Dict[ET.Element, ET.Element] = {hijo: padre for padre in root.iter() for hijo in padre}
    candidatos: List[Tuple[str, str]] = []

    for elem in root.iter():
        tag = _limpiar_tag(elem.tag)
        texto = elem.text.strip() if elem.text else ""

        # 1) ID dentro de Services_* o *_SPD
        if tag == "ID" and _es_numero_cuenta(texto):
            padre = parent_map.get(elem)
            padre_tag = _limpiar_tag(padre.tag) if padre is not None else ""
            if (
                "Services" in padre_tag
                or padre_tag.endswith("_SPD")
                or padre_tag.startswith("OTHERCOMPANY")
            ):
                candidatos.append((texto, _ruta_elemento(elem, parent_map)))

        # 2) Notes con etiquetas relevantes
        if tag == "Note":
            lang = elem.attrib.get("languageLocaleID")
            if (lang in {"Contrato", "ReferentePago"}) and _es_numero_cuenta(texto):
                candidatos.append((texto, _ruta_elemento(elem, parent_map)))
            # también considerar cualquier Note con 6-12 dígitos (evita perder candidatos)
            elif _es_numero_cuenta(texto):
                candidatos.append((texto, _ruta_elemento(elem, parent_map)))

        # 3) AccountingCostCode
        if tag == "AccountingCostCode" and _es_numero_cuenta(texto):
            candidatos.append((texto, _ruta_elemento(elem, parent_map)))

    # Fallback amplio: cualquier texto 6-12 dígitos
    if not candidatos:
        for elem in root.iter():
            texto = elem.text.strip() if elem.text else ""
            if _es_numero_cuenta(texto):
                candidatos.append((texto, _ruta_elemento(elem, parent_map)))

    return candidatos


def extraer_numero_cuenta(ruta_archivo: str) -> Tuple[Optional[str], List[Tuple[str, str]]]:
    """Wrapper especializado que usa el extractor genérico para número de cuenta."""
    targets = [
        {"tag": "ID", "ruta_contiene": ["Services_SPD/ID"]},
        {"tag": "ID", "ruta_contiene": ["OTHERCOMPANY_SPD/ID"]},
        {"tag": "Note", "atributos": {"languageLocaleID": "Contrato"}},
        {"tag": "Note", "atributos": {"languageLocaleID": "ReferentePago"}},
        {"tag": "AccountingCostCode"},
    ]
    return extraer_valor_xml(
        ruta_archivo=ruta_archivo,
        targets=targets,
        validar=_es_numero_cuenta,
        incluir_embebidos=True,
        fallback_regex=r"\d{6,12}",
    )


def _candidatos_nombre_en_raiz(root: ET.Element) -> List[Tuple[str, str]]:
    """Deprecado: mantenido por compatibilidad. Usa extraer_valor_xml en su lugar."""
    return []


def extraer_nombre_cliente(ruta_archivo: str) -> Tuple[Optional[str], List[Tuple[str, str]]]:
    """Wrapper especializado que usa el extractor genérico para nombre del cliente."""
    targets = [
        {"tag": "Name", "ruta_contiene": ["SubscriberParty/PartyName/Name"]},
        {"tag": "Name", "ruta_contiene": ["AccountingCustomerParty/Party/PartyName/Name"]},
        {"tag": "Name", "ruta_termina_con": "PartyName/Name"},
    ]
    return extraer_valor_xml(
        ruta_archivo=ruta_archivo,
        targets=targets,
        validar=lambda s: bool(s and s.strip()),
        incluir_embebidos=True,
        fallback_regex=r".+",
    )


def extraer_direccion_cliente(ruta_archivo: str) -> Tuple[Optional[str], List[Tuple[str, str]]]:
    """Extrae la dirección del cliente. Preferencia: StreetName o AddressLine/Line del cliente."""
    targets = [
        {"tag": "StreetName", "ruta_contiene": ["SubscriberParty/PostalAddress/StreetName"]},
        {"tag": "Line", "ruta_contiene": ["SubscriberParty/PostalAddress/AddressLine/Line"]},
        {"tag": "Line", "ruta_contiene": ["AccountingCustomerParty/Party/PhysicalLocation/Address/AddressLine/Line"]},
        {"tag": "StreetName", "ruta_contiene": ["AccountingCustomerParty/Party/PhysicalLocation/Address/StreetName"]},
        {"tag": "StreetName", "ruta_contiene": ["PhysicalLocation/Address/StreetName"]},
        {"tag": "Line", "ruta_contiene": ["PhysicalLocation/Address/AddressLine/Line"]},
    ]
    val, det = extraer_valor_xml(
        ruta_archivo=ruta_archivo,
        targets=targets,
        validar=lambda s: bool(s and s.strip()),
        incluir_embebidos=True,
        fallback_regex=None,
    )
    if val:
        val = " ".join(val.split()).strip()
    return val, det


def extraer_estrato_cliente(ruta_archivo: str) -> Tuple[Optional[str], List[Tuple[str, str]]]:
    """Extrae el estrato del cliente (ResidentialStratum). Devuelve texto (e.g., '0', '1', ...)."""
    targets = [
        {"tag": "ResidentialStratum", "ruta_contiene": ["SubscriberParty/PostalAddress/ResidentialStratum"]},
        {"tag": "ResidentialStratum", "ruta_contiene": ["AccountingCustomerParty/Party/PhysicalLocation/Address/ResidentialStratum"]},
    ]
    return extraer_valor_xml(
        ruta_archivo=ruta_archivo,
        targets=targets,
        validar=lambda s: bool(re.fullmatch(r"\d+", s.strip()) if s else False),
        incluir_embebidos=True,
        fallback_regex=r"\d+",
    )


def extraer_numero_medidor(ruta_archivo: str) -> Tuple[Optional[str], List[Tuple[str, str]]]:
    """Intenta extraer el número de medidor si existe. Si no se encuentra, retorna (None, [])."""
    targets = [
        {"tag": "MeterNumber"},
        {"tag": "Meter"},
        {"tag": "SerialNumber"},
        {"tag": "DeviceID"},
        {"tag": "ID", "ruta_contiene": ["Meter"]},
        {"tag": "ID", "ruta_contiene": ["Medidor"]},
    ]
    return extraer_valor_xml(
        ruta_archivo=ruta_archivo,
        targets=targets,
        validar=lambda s: bool(re.fullmatch(r"[A-Za-z0-9\-]{4,20}", s.strip()) if s else False),
        incluir_embebidos=True,
        fallback_regex=None,
    )


def extraer_fecha_maxima_pago(ruta_archivo: str) -> Tuple[Optional[str], List[Tuple[str, str]]]:
    """
    Extrae la fecha máxima de pago de la factura.
    Busca: <cbc:DueDate>2025-11-12</cbc:DueDate>
    
    Returns:
        (fecha_maxima_pago, detalles) donde fecha_maxima_pago es una cadena con formato YYYY-MM-DD.
        Si no se encuentra, retorna (None, []).
    """
    targets = [
        {"tag": "DueDate"},
        {"tag": "PaymentDueDate"},
    ]
    return extraer_valor_xml(
        ruta_archivo=ruta_archivo,
        targets=targets,
        validar=lambda s: bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", s.strip()) if s else False),
        incluir_embebidos=True,
        fallback_regex=r"\d{4}-\d{2}-\d{2}",
    )


def extraer_consumo_kwh(ruta_archivo: str) -> Tuple[Optional[List[float]], List[Tuple[str, str]]]:
    """
    Extrae el consumo en kWh de cada InvoiceLine.
    Busca: <cbc:BaseQuantity unitCode="KWH">148.00</cbc:BaseQuantity>
    
    Returns:
        (lista_consumos, detalles) donde lista_consumos contiene los valores float de cada línea.
        Si no hay líneas con unitCode="KWH", retorna (None, []).
    """
    try:
        tree = ET.parse(ruta_archivo)
        root = tree.getroot()
        
        consumos = []
        detalles = []
        parent_map: Dict[ET.Element, ET.Element] = {hijo: padre for padre in root.iter() for hijo in padre}
        
        # Buscar en el XML principal
        for invoice_line in root.iter():
            if _limpiar_tag(invoice_line.tag) == "InvoiceLine":
                for elem in invoice_line.iter():
                    if _limpiar_tag(elem.tag) == "BaseQuantity" and elem.attrib.get("unitCode") == "KWH":
                        texto = elem.text.strip() if elem.text else ""
                        if texto:
                            try:
                                valor = float(texto)
                                consumos.append(valor)
                                ruta = _ruta_elemento(elem, parent_map)
                                detalles.append((texto, ruta))
                            except ValueError:
                                pass
        
        # Buscar en XMLs embebidos
        for desc in root.iter():
            if _limpiar_tag(desc.tag) == "Description" and desc.text:
                contenido = desc.text.strip()
                if contenido.startswith("<") and ("<Invoice" in contenido or contenido.startswith("<?xml")):
                    for payload in (contenido, contenido.lstrip("\ufeff\n\r\t ")):
                        try:
                            sub_root = ET.fromstring(payload)
                            sub_parent_map: Dict[ET.Element, ET.Element] = {hijo: padre for padre in sub_root.iter() for hijo in padre}
                            for invoice_line in sub_root.iter():
                                if _limpiar_tag(invoice_line.tag) == "InvoiceLine":
                                    for elem in invoice_line.iter():
                                        if _limpiar_tag(elem.tag) == "BaseQuantity" and elem.attrib.get("unitCode") == "KWH":
                                            texto = elem.text.strip() if elem.text else ""
                                            if texto:
                                                try:
                                                    valor = float(texto)
                                                    consumos.append(valor)
                                                    ruta = _ruta_elemento(elem, sub_parent_map)
                                                    detalles.append((texto, ruta + " [embebido]"))
                                                except ValueError:
                                                    pass
                            break
                        except Exception:
                            continue
        
        if not consumos:
            return None, []
        
        return consumos, detalles
    except Exception as e:
        print(f"Error en extraer_consumo_kwh: {e}")
        return None, []


def extraer_valor_kwh(ruta_archivo: str) -> Tuple[Optional[List[float]], List[Tuple[str, str]]]:
    """
    Extrae el valor por kWh SOLO de las InvoiceLine que tengan BaseQuantity con unitCode="KWH".
    Esto filtra líneas de otros conceptos (ej: impuestos municipales) que no son consumo eléctrico.
    Busca: <cac:Price><cbc:PriceAmount currencyID="COP">940.394800</cbc:PriceAmount></cac:Price>
    
    Returns:
        (lista_valores, detalles) donde lista_valores contiene los valores float de precio por kWh.
        Si no hay líneas con PriceAmount y unitCode="KWH", retorna (None, []).
    """
    try:
        tree = ET.parse(ruta_archivo)
        root = tree.getroot()
        
        valores = []
        detalles = []
        parent_map: Dict[ET.Element, ET.Element] = {hijo: padre for padre in root.iter() for hijo in padre}
        
        # Buscar en el XML principal
        for invoice_line in root.iter():
            if _limpiar_tag(invoice_line.tag) == "InvoiceLine":
                # Verificar si esta línea tiene BaseQuantity con unitCode="KWH"
                tiene_kwh = False
                for elem in invoice_line.iter():
                    if _limpiar_tag(elem.tag) == "BaseQuantity" and elem.attrib.get("unitCode") == "KWH":
                        tiene_kwh = True
                        break
                
                # Solo extraer el precio si la línea tiene consumo en kWh
                if tiene_kwh:
                    for price in invoice_line.iter():
                        if _limpiar_tag(price.tag) == "Price":
                            for elem in price.iter():
                                if _limpiar_tag(elem.tag) == "PriceAmount" and elem.attrib.get("currencyID") == "COP":
                                    texto = elem.text.strip() if elem.text else ""
                                    if texto:
                                        try:
                                            valor = float(texto)
                                            valores.append(valor)
                                            ruta = _ruta_elemento(elem, parent_map)
                                            detalles.append((texto, ruta))
                                        except ValueError:
                                            pass
        
        # Buscar en XMLs embebidos
        for desc in root.iter():
            if _limpiar_tag(desc.tag) == "Description" and desc.text:
                contenido = desc.text.strip()
                if contenido.startswith("<") and ("<Invoice" in contenido or contenido.startswith("<?xml")):
                    for payload in (contenido, contenido.lstrip("\ufeff\n\r\t ")):
                        try:
                            sub_root = ET.fromstring(payload)
                            sub_parent_map: Dict[ET.Element, ET.Element] = {hijo: padre for padre in sub_root.iter() for hijo in padre}
                            for invoice_line in sub_root.iter():
                                if _limpiar_tag(invoice_line.tag) == "InvoiceLine":
                                    # Verificar si esta línea tiene BaseQuantity con unitCode="KWH"
                                    tiene_kwh = False
                                    for elem in invoice_line.iter():
                                        if _limpiar_tag(elem.tag) == "BaseQuantity" and elem.attrib.get("unitCode") == "KWH":
                                            tiene_kwh = True
                                            break
                                    
                                    # Solo extraer el precio si la línea tiene consumo en kWh
                                    if tiene_kwh:
                                        for price in invoice_line.iter():
                                            if _limpiar_tag(price.tag) == "Price":
                                                for elem in price.iter():
                                                    if _limpiar_tag(elem.tag) == "PriceAmount" and elem.attrib.get("currencyID") == "COP":
                                                        texto = elem.text.strip() if elem.text else ""
                                                        if texto:
                                                            try:
                                                                valor = float(texto)
                                                                valores.append(valor)
                                                                ruta = _ruta_elemento(elem, sub_parent_map)
                                                                detalles.append((texto, ruta + " [embebido]"))
                                                            except ValueError:
                                                                pass
                            break
                        except Exception:
                            continue
        
        if not valores:
            return None, []
        
        return valores, detalles
    except Exception as e:
        print(f"Error en extraer_valor_kwh: {e}")
        return None, []


def _coincide_target(tag: str, ruta: str, elem: ET.Element, target: Dict[str, Any]) -> bool:
    """Evalúa si un elemento coincide con un target de búsqueda."""
    if target.get("tag") and tag != target["tag"]:
        return False
    # Atributos exactos
    attrs: Dict[str, str] = target.get("atributos", {})
    for k, v in attrs.items():
        if elem.attrib.get(k) != v:
            return False
    # La ruta debe contener todos los substrings dados
    for frag in target.get("ruta_contiene", []) or []:
        if frag not in ruta:
            return False
    # O puede terminar con un sufijo
    sufijo = target.get("ruta_termina_con")
    if sufijo and not ruta.endswith(sufijo):
        return False
    return True


def _candidatos_por_targets(root: ET.Element, targets: List[Dict[str, Any]], validar: Optional[Callable[[str], bool]]) -> List[Tuple[str, str, int]]:
    """Devuelve candidatos (valor, ruta, idx_target) que coinciden con alguno de los targets."""
    parent_map: Dict[ET.Element, ET.Element] = {hijo: padre for padre in root.iter() for hijo in padre}
    encontrados: List[Tuple[str, str, int]] = []
    for elem in root.iter():
        tag = _limpiar_tag(elem.tag)
        texto = elem.text.strip() if elem.text else ""
        if not texto:
            continue
        ruta = _ruta_elemento(elem, parent_map)
        for i, t in enumerate(targets):
            if _coincide_target(tag, ruta, elem, t) and (validar(texto) if validar else True):
                encontrados.append((texto, ruta, i))
                break
    return encontrados


def extraer_valor_xml(
    ruta_archivo: str,
    targets: List[Dict[str, Any]],
    validar: Optional[Callable[[str], bool]] = None,
    incluir_embebidos: bool = True,
    fallback_regex: Optional[str] = None,
) -> Tuple[Optional[str], List[Tuple[str, str]]]:
    """
    Extractor genérico de valores desde un XML (UBL o similar) con soporte de:
    - Búsqueda por tag, atributos y patrones de ruta
    - Parseo de XML embebido en CDATA (cbc:Description)
    - Fallback por regex si no se encuentran targets

    targets: Lista de reglas dict con claves opcionales
        - tag: nombre del tag objetivo (sin namespace)
        - atributos: dict de atributos que deben coincidir
        - ruta_contiene: lista de substrings que deben estar en la ruta del elemento
        - ruta_termina_con: sufijo que debe cumplir la ruta

    Returns:
        (valor_elegido, detalles) donde detalles es [(valor, ruta), ...]
    """
    try:
        tree = ET.parse(ruta_archivo)
        root = tree.getroot()

        # 1) Buscar en la raíz
        candidatos_ex: List[Tuple[str, str, int]] = _candidatos_por_targets(root, targets, validar)

        # 2) Buscar en XML embebidos
        if incluir_embebidos:
            for desc in root.iter():
                if _limpiar_tag(desc.tag) == "Description" and desc.text:
                    contenido = desc.text.strip()
                    if contenido.startswith("<") and ("<Invoice" in contenido or contenido.startswith("<?xml")):
                        for payload in (contenido, contenido.lstrip("\ufeff\n\r\t ")):
                            try:
                                sub_root = ET.fromstring(payload)
                                candidatos_ex.extend(_candidatos_por_targets(sub_root, targets, validar))
                                break
                            except Exception:
                                continue

        # 3) Fallback por regex si sigue vacío
        if not candidatos_ex and fallback_regex:
            patron = re.compile(fallback_regex)
            parent_map: Dict[ET.Element, ET.Element] = {hijo: padre for padre in root.iter() for hijo in padre}
            for elem in root.iter():
                texto = elem.text.strip() if elem.text else ""
                if texto and patron.fullmatch(texto):
                    candidatos_ex.append((texto, _ruta_elemento(elem, parent_map), len(targets)))

        if not candidatos_ex:
            return None, []

        # Selección del valor: por frecuencia; desempate por índice de target (menor = mayor prioridad) y orden de aparición
        conteo: Dict[str, int] = {}
        mejor_idx_target: Dict[str, int] = {}
        for val, _ruta, idx in candidatos_ex:
            conteo[val] = conteo.get(val, 0) + 1
            if val not in mejor_idx_target:
                mejor_idx_target[val] = idx
            else:
                mejor_idx_target[val] = min(mejor_idx_target[val], idx)

        valor_elegido = max(conteo.items(), key=lambda kv: (kv[1], -mejor_idx_target.get(kv[0], 1_000_000)))[0]
        detalles = [(v, r) for (v, r, _i) in candidatos_ex]
        return valor_elegido, detalles
    except Exception as e:
        print(f"Error en extraer_valor_xml: {e}")
        return None, []


if __name__ == "__main__":
    # Script de prueba
    import os
    import sys
    
    # Buscar archivo XML de prueba
    # Permitir pasar la ruta por argumento; por defecto usar el de prueba
    ruta_test = sys.argv[1] if len(sys.argv) > 1 else r"c:\Users\edrib\Documents\Repos\UNIR\gestion_facturas\test\1.xml"
    
    if os.path.exists(ruta_test):
        # 1) Imprimir opcionalmente estructura (comentar si no se desea verbosidad)
        # imprimir_nodos_xml(ruta_test, nivel_max=4)

        # 2) Extraer y mostrar numero_cuenta
        numero, detalles = extraer_numero_cuenta(ruta_test)
        if numero:
            print(f"numero_cuenta: {numero}")
            # Mostrar de dónde se obtuvo
            # Deduplicar rutas por valor repetido
            print("Detalles de hallazgos (valor, ruta):")
            for val, ruta in detalles:
                print(f"  - {val} @ {ruta}")
        else:
            print("No se encontró numero_cuenta en el XML.")

        # 3) Extraer y mostrar nombre_cliente
        nombre, detalles_nombre = extraer_nombre_cliente(ruta_test)
        if nombre:
            print(f"nombre_cliente: {nombre}")
            print("Detalles de hallazgos de nombre (valor, ruta):")
            for val, ruta in detalles_nombre:
                print(f"  - {val} @ {ruta}")
        else:
            print("No se encontró nombre de cliente en el XML.")
        
        # Opción: imprimir solo primeros 3 niveles
        # print("\nImprimiendo solo primeros 3 niveles...\n")
        # imprimir_nodos_xml(ruta_test, nivel_max=3)
    else:
        print(f"No se encontró el archivo de prueba en: {ruta_test}")
