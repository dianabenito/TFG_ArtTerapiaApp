from sqlalchemy.orm import Session
from fastapi import HTTPException
import app.models as models
import app.schemas as schemas
from app.security import hash_password, verify_password, create_access_token
from datetime import timedelta
import re

def get_user(db: Session, user_id: int):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_users(db: Session):
    return db.query(models.User).all()

def create_user(db: Session, user: schemas.UserCreate):
    if not hasattr(user, 'type') or user.type not in (schemas.UserType.patient, schemas.UserType.therapist):
        raise HTTPException(status_code=400, detail="Tipo de usuario inválido o faltante; debe ser 'patient' o 'therapist'")
    
    # Validar que el email no esté ya registrado
    existing_user = get_user_by_email(db, user.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="El correo ya está registrado")
    
    validate_password_strength(user.password)
    hashed_password = hash_password(user.password)

    try:
        if user.type == schemas.UserType.patient:
            db_user = models.Patient(email=user.email, full_name=user.full_name, hashed_password=hashed_password)
        else:
            db_user = models.Therapist(email=user.email, full_name=user.full_name, hashed_password=hashed_password)

        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error creating user: {str(e)}"
        )

def authenticate_user(db: Session, email: str, password: str):
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

def login_user(db: Session, email: str, password: str):
    user = authenticate_user(db, email, password)
    if not user:
        raise HTTPException(status_code=401, detail="El correo o la contraseña son incorrectos")

    access_token = create_access_token({"sub": str(user.id),  "user_type": user.type})
    return {"access_token": access_token, "token_type": "bearer"}

def validate_password_strength(password: str):
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 8 caracteres.")
    if not re.search(r"[A-Z]", password):
        raise HTTPException(status_code=400, detail="La contraseña debe contener al menos una letra mayúscula.")
    if not re.search(r"\d", password):
        raise HTTPException(status_code=400, detail="La contraseña debe contener al menos un dígito.")
    if not re.search(r"[!@#$%^&*(),.?\":{}<>|]", password):
        raise HTTPException(status_code=400, detail="La contraseña debe contener al menos un carácter especial.")

def get_images_for_user_no_session(db: Session, user_id: int):
    """Retrieve all images for a given user."""
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    images = db.query(models.Image).filter(models.Image.owner_id == user_id).filter(models.Image.session_id == None).all()
    return {
        "data": images,
        "count": len(images)
    }