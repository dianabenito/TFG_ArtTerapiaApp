from sqlalchemy.orm import Session
from fastapi import HTTPException
import app.models as models
import app.schemas as schemas
import app.services as services
import os
from pathlib import Path

def create_user_image(db: Session, prompt: schemas.Prompt, user_id: int):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user.type != 'patient':
        raise HTTPException(status_code=404, detail="Therapists cannot have images")
    image = services.image_generation.generar_imagen(prompt.promptText, prompt_seed=prompt.seed, input_img=prompt.inputImage)
    gen_seed = image.get("seed") if isinstance(image, dict) else None
    db_image = models.Image(fileName=image["file"], seed=gen_seed, owner_id=user_id)
    db.add(db_image)
    db.commit()
    db.refresh(db_image)
    return image


def create_user_uploaded_image(db: Session, upload_file, user_id: int):
    """Save an uploaded file to the generated_images folder and create DB record."""
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user or db_user.type != 'patient':
        raise HTTPException(status_code=404, detail="Therapists cannot have images or user not found")

    image = services.image_generation.publicar_imagen(upload_file)

    # create DB record
    db_image = models.Image(fileName=image["file"], seed = image["seed"], owner_id=user_id)
    db.add(db_image)
    db.commit()
    db.refresh(db_image)

    return image
