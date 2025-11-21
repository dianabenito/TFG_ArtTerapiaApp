from sqlalchemy.orm import Session
from fastapi import HTTPException
import app.models as models
import app.schemas as schemas
import app.services as services

def create_user_image(db: Session, prompt: schemas.Prompt, user_id: int):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user.type != 'patient':
        raise HTTPException(status_code=404, detail="Therapists cannot have images")
    image = services.image_generation.generar_imagen(prompt.promptText)
    db_image = models.Image(fileName=image["file"], seed = image["seed"], owner_id=user_id)
    db.add(db_image)
    db.commit()
    db.refresh(db_image)
    return image
