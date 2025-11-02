from fastapi import APIRouter, Depends, HTTPException
from typing import List
import app.schemas as schemas
from sqlalchemy.orm import Session
from app.dependencies import SessionDep
import app.crud as crud

router = APIRouter()

@router.get("/users/", response_model=List[schemas.User])
async def read_users(db: SessionDep, skip: int = 0, limit: int = 10):
    users = crud.user.get_users(db, skip=skip, limit=limit)
    return users

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
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.user.create_user(db=db, user=user)