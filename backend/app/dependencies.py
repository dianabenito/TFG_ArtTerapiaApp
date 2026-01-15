"""Dependencias reutilizables para inyección de dependencias de FastAPI.

Este módulo proporciona dependencias comunes utilizadas en los endpoints,
incluyendo sesiones de base de datos y autenticación de usuarios.

Attributes:
    SessionDep (Annotated[Session, Depends(get_db)]): Tipo anotado para inyección de sesión DB.
    AuthDep (Annotated[str, Depends(oauth2_scheme)]): Tipo anotado para token JWT.
    CurrentUser (Annotated[models.User, Depends(get_current_user)]): Tipo anotado para usuario autenticado.
    oauth2_scheme (OAuth2PasswordBearer): Esquema OAuth2 para autenticación.
"""

from typing import Annotated
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from .database import SessionLocal
from app.security import decode_access_token
import app.crud as crud
from fastapi import HTTPException, status
import app.models as models

def get_db():
    """Generador de sesiones de base de datos.
    
    Yields:
        Session: Sesión de SQLAlchemy para operaciones de base de datos.
    
    Note:
        La sesión se cierra automáticamente al finalizar la petición.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

SessionDep = Annotated[Session, Depends(get_db)]

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")

AuthDep = Annotated[str, Depends(oauth2_scheme)]

def get_current_user(
    db: SessionDep,
    token: AuthDep
):
    """Obtiene el usuario actual desde el token JWT.
    
    Args:
        db (Session): Sesión de base de datos.
        token (str): Token JWT del header Authorization.
    
    Returns:
        models.User: Usuario autenticado (Patient o Therapist).
    
    Raises:
        HTTPException: 401 si el token es inválido o el usuario no existe.
    """
    user_id = decode_access_token(token)
    user = crud.user.get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no encontrado")
    return user

CurrentUser = Annotated[models.User, Depends(get_current_user)]
