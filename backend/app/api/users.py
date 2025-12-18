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
    users = crud.user.get_users(db)
    return users

@router.get("/users/me", response_model=schemas.User)
def read_user_me(db: SessionDep, current_user: CurrentUser):
    """
    Get current user.
    """
    return current_user

@router.get("/users/{user_id}", response_model=schemas.User)
async def read_user(db: SessionDep, user_id: int):
    db_user = crud.user.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.post("/users/", response_model=schemas.User)
async def create_user(db: SessionDep, user: schemas.UserCreate):
    db_user = crud.user.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="El correo ya está registrado")
    return crud.user.create_user(db=db, user=user)

@router.post("/login/")
async def login_access_token(db: SessionDep, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    return crud.user.login_user(db=db, email=form_data.username, password=form_data.password)