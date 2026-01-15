"""Módulo de seguridad para autenticación y manejo de contraseñas.

Este módulo proporciona funciones para:
- Hashing seguro de contraseñas con bcrypt y SHA-256
- Generación y verificación de tokens JWT
- Validación de credenciales de usuario

Attributes:
    SECRET_KEY (str): Clave secreta para firmar tokens JWT (desde .env).
    ALGORITHM (str): Algoritmo de cifrado para JWT (HS256).
    ACCESS_TOKEN_EXPIRE_MINUTES (int): Tiempo de expiración de tokens en minutos (480 = 8 horas).
"""

from fastapi import HTTPException, status
from datetime import datetime, timedelta
from jose import JWTError, jwt
import os
from dotenv import load_dotenv
load_dotenv()
import hashlib
import logging
import bcrypt

_log = logging.getLogger(__name__)

SECRET_KEY = os.getenv("SECRET_KEY", "changeme")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480


def _prehash_bytes(password: str) -> bytes:
    """Pre-procesa la contraseña con SHA-256 antes del hashing bcrypt.
    
    Args:
        password (str): Contraseña en texto plano.
    
    Returns:
        bytes: Digest SHA-256 de la contraseña.
    
    Note:
        Evita el límite de 72 bytes de bcrypt y garantiza longitud constante.
    """
    return hashlib.sha256(password.encode("utf-8")).digest()


def hash_password(password: str) -> str:
    """Hashea una contraseña usando SHA-256 pre-hash y bcrypt.
    
    Args:
        password (str): Contraseña en texto plano.
    
    Returns:
        str: Hash bcrypt en formato ASCII (UTF-8).
    
    Note:
        Se aplica SHA-256 primero para evitar el límite de 72 bytes de bcrypt
        y asegurar entrada determinística de longitud constante.
    """
    pre = _prehash_bytes(password)
    hashed = bcrypt.hashpw(pre, bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica si una contraseña coincide con su hash.
    
    Args:
        plain_password (str): Contraseña en texto plano a verificar.
        hashed_password (str): Hash bcrypt almacenado.
    
    Returns:
        bool: True si la contraseña coincide, False en caso contrario.
    """
    try:
        pre = _prehash_bytes(plain_password)
        return bcrypt.checkpw(pre, hashed_password.encode("utf-8"))
    except Exception:
        return False

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """Crea un token JWT de acceso.
    
    Args:
        data (dict): Datos a incluir en el payload del token (típicamente {"sub": user_id}).
        expires_delta (timedelta, optional): Tiempo de expiración personalizado.
            Por defecto usa ACCESS_TOKEN_EXPIRE_MINUTES.
    
    Returns:
        str: Token JWT firmado.
    
    Example:
        >>> token = create_access_token({"sub": "123"})
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str):
    """Decodifica y valida un token JWT.
    
    Args:
        token (str): Token JWT a decodificar.
    
    Returns:
        int: ID del usuario extraído del campo "sub".
    
    Raises:
        HTTPException: 401 si el token es inválido, expirado o sin campo "sub".
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return int(user_id)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token or expired")