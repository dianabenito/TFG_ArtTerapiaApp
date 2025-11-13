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
    user_id = decode_access_token(token)
    user = crud.user.get_user(db, user_id=user_id)
    #user = db.get(models.User, token.sub)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user

CurrentUser = Annotated[models.User, Depends(get_current_user)]
