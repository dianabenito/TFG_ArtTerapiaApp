"""Router de API para gestión de usuarios.

Endpoints para autenticación, registro y gestión de usuarios.
Incluye operaciones CRUD de usuarios e imágenes sin sesión asociada.
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated, List
import app.schemas as schemas
from sqlalchemy.orm import Session
from app.dependencies import SessionDep, CurrentUser
import app.crud as crud

router = APIRouter()


@router.get("/users/", response_model=List[schemas.User])
async def read_users(db: SessionDep):
    """Obtiene lista de todos los usuarios.
    
    Args:
        db (Session): Sesión de base de datos.
    
    Returns:
        List[schemas.User]: Lista de todos los usuarios registrados.
    """
    users = crud.user.get_users(db)
    return users

@router.get("/users/me", response_model=schemas.User)
def read_user_me(db: SessionDep, current_user: CurrentUser):
    """Obtiene información del usuario actual autenticado.
    
    Args:
        db (Session): Sesión de base de datos.
        current_user (CurrentUser): Usuario autenticado desde token JWT.
    
    Returns:
        schemas.User: Información del usuario actual.
    """
    return current_user


@router.get("/users/{user_id}", response_model=schemas.User)
async def read_user(db: SessionDep, user_id: int, current_user: CurrentUser):
    """Obtiene información de un usuario por ID.
    
    Args:
        db (Session): Sesión de base de datos.
        user_id (int): ID del usuario a consultar.
        current_user (CurrentUser): Usuario autenticado.
    
    Returns:
        schemas.User: Información del usuario solicitado.
    
    Raises:
        HTTPException: 404 si el usuario no existe.
    """
    db_user = crud.user.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return db_user

@router.post("/users/", response_model=schemas.User)
async def create_user(db: SessionDep, user: schemas.UserCreate):
    """Registra un nuevo usuario en el sistema.
    
    Args:
        db (Session): Sesión de base de datos.
        user (schemas.UserCreate): Datos del usuario a crear.
    
    Returns:
        schemas.User: Usuario creado.
    
    Raises:
        HTTPException: 400 si el email ya está registrado.
    """
    db_user = crud.user.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="El correo ya está registrado")
    return crud.user.create_user(db=db, user=user)

@router.post("/login/")
async def login_access_token(db: SessionDep, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    """OAuth2 compatible token login.
    
    Args:
        db (Session): Sesión de base de datos.
        form_data (OAuth2PasswordRequestForm): Credenciales (username=email, password).
    
    Returns:
        dict: Token de acceso JWT y tipo de token.
            - access_token (str): Token JWT.
            - token_type (str): Tipo de token (bearer).
    
    Raises:
        HTTPException: 401 si las credenciales son inválidas.
    """
    return crud.user.login_user(db=db, email=form_data.username, password=form_data.password)



@router.get('/users/{user_id}/free-images', response_model=schemas.ImagesOut)
async def get_images_for_user_no_session(db: SessionDep, user_id: int, current_user: CurrentUser):
    """Obtiene imágenes del usuario sin sesión asociada.
    
    Args:
        db (Session): Sesión de base de datos.
        user_id (int): ID del usuario.
        current_user (CurrentUser): Usuario autenticado.
    
    Returns:
        schemas.ImagesOut: Imágenes del usuario sin session_id.
    """
    return crud.user.get_images_for_user_no_session(db=db, user_id=user_id)