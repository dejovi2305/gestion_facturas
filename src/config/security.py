"""
Módulo de seguridad para encriptación de contraseñas.
Usa hash SHA-256 con salt aleatorio y clave secreta para máxima seguridad.
"""
import hashlib
import base64
import os
from typing import Tuple

# Clave secreta para el sistema (en producción, esto debería estar en variable de entorno)
_SECRET_KEY = "GF2024_SECRET_KEY_UNIR_FACTURAS_SISTEMA"


def generar_salt() -> str:
    """Genera un salt aleatorio de 16 bytes codificado en base64."""
    return base64.b64encode(os.urandom(16)).decode('utf-8')


def encriptar_contrasena(contrasena: str, salt: str | None = None) -> Tuple[str, str]:
    """
    Encripta una contraseña usando SHA-256 con salt y clave secreta.
    
    Args:
        contrasena: Contraseña en texto plano
        salt: Salt opcional (si no se proporciona, se genera uno nuevo)
    
    Returns:
        Tupla (hash_encriptado, salt_usado)
    """
    if not contrasena:
        raise ValueError("La contraseña no puede estar vacía")
    
    # Generar salt si no se proporciona
    if salt is None:
        salt = generar_salt()
    
    # Combinar contraseña + salt + clave secreta
    texto_combinado = f"{contrasena}{salt}{_SECRET_KEY}"
    
    # Generar hash SHA-256
    hash_obj = hashlib.sha256(texto_combinado.encode('utf-8'))
    hash_bytes = hash_obj.digest()
    
    # Codificar en base64 para almacenamiento
    hash_base64 = base64.b64encode(hash_bytes).decode('utf-8')
    
    # Retornar hash y salt separados
    return hash_base64, salt


def verificar_contrasena(contrasena_plana: str, hash_almacenado: str, salt: str) -> bool:
    """
    Verifica si una contraseña coincide con su hash almacenado.
    
    Args:
        contrasena_plana: Contraseña ingresada por el usuario
        hash_almacenado: Hash almacenado en la base de datos
        salt: Salt almacenado en la base de datos
    
    Returns:
        True si la contraseña coincide, False en caso contrario
    """
    try:
        # Generar hash de la contraseña ingresada usando el salt almacenado
        hash_generado, _ = encriptar_contrasena(contrasena_plana, salt)
        
        # Comparar hashes
        return hash_generado == hash_almacenado
    except Exception:
        return False


def codificar_para_almacenamiento(hash_base64: str, salt: str) -> str:
    """
    Combina hash y salt en un solo string para almacenar en BD.
    Formato: salt$hash
    
    Args:
        hash_base64: Hash en base64
        salt: Salt en base64
    
    Returns:
        String combinado para almacenar
    """
    return f"{salt}${hash_base64}"


def decodificar_de_almacenamiento(contrasena_almacenada: str) -> Tuple[str, str]:
    """
    Extrae hash y salt de un string almacenado.
    
    Args:
        contrasena_almacenada: String en formato salt$hash
    
    Returns:
        Tupla (salt, hash)
    """
    partes = contrasena_almacenada.split('$', 1)
    if len(partes) != 2:
        raise ValueError("Formato de contraseña almacenada inválido")
    return partes[0], partes[1]


def es_contrasena_encriptada(contrasena: str) -> bool:
    """
    Verifica si una contraseña ya está en formato encriptado.
    
    Args:
        contrasena: String a verificar
    
    Returns:
        True si está encriptada (contiene $), False si es texto plano
    """
    return '$' in contrasena and len(contrasena) > 40
