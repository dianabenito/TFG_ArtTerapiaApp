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

def create_user_sketch_image(db: Session, prompt: schemas.SketchPrompt, user_id: int):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user.type != 'patient':
        raise HTTPException(status_code=404, detail="Therapists cannot have images")
    image = services.image_generation.convertir_boceto_imagen(prompt.sketchImage)
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

def create_user_drawn_image(db: Session, upload_file, user_id: int):
    """Save a drawn image to drawn_images and create DB record."""
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user or db_user.type != 'patient':
        raise HTTPException(status_code=404, detail="Therapists cannot have images or user not found")

    image = services.image_generation.publicar_dibujo(upload_file)

    db_image = models.Image(fileName=image["file"], seed = image.get("seed"), owner_id=user_id)
    db.add(db_image)
    db.commit()
    db.refresh(db_image)

    return image

def get_images_for_user(db: Session, user_id: int):
    """Retrieve all images for a given user."""
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    images = db.query(models.Image).filter(models.Image.owner_id == user_id).all()
    return {
        "data": images,
        "count": len(images)
    }

def get_template_images():
    """Retrieve all template images from the template directory."""
    return services.image_generation.obtener_imagenes_plantilla()


def create_user_img_by_mult_images(db: Session, images: schemas.TemplateImagesIn, user_id: int):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user.type != 'patient':
        raise HTTPException(status_code=404, detail="Therapists cannot have images")
    image = services.image_generation.generate_image_by_mult_images(images.data, count=len(images.data))    
    gen_seed = image.get("seed") if isinstance(image, dict) else None
    db_image = models.Image(fileName=image["file"], seed=gen_seed, owner_id=user_id)
    db.add(db_image)
    db.commit()
    db.refresh(db_image)
    return image
