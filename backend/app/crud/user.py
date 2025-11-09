from sqlalchemy.orm import Session
from fastapi import HTTPException
import app.models as models
import app.schemas as schemas

def get_user(db: Session, user_id: int):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserCreate):
    # validate requested type: only patient or therapist allowed
    if not hasattr(user, 'type') or user.type not in (schemas.UserType.patient, schemas.UserType.therapist):
        raise HTTPException(status_code=400, detail="Invalid or missing user type; must be 'patient' or 'therapist'")

    fake_hashed_password = user.password + "notreallyhashed"
    # create appropriate subtype
    if user.type == schemas.UserType.patient:
        db_user = models.Patient(email=user.email, hashed_password=fake_hashed_password)
    else:
        db_user = models.Therapist(email=user.email, hashed_password=fake_hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user