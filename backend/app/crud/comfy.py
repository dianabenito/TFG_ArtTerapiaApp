from sqlalchemy.orm import Session
from fastapi import HTTPException
import app.models as models
import app.schemas as schemas
import app.services as services
import os
from pathlib import Path

def create_user_image(db: Session, prompt: schemas.Prompt, user_id: int, session_id: int):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user.type != 'patient':
        raise HTTPException(status_code=404, detail="Los terapeutas no pueden tener imágenes")
    
    # Validar que la sesión existe y pertenece al usuario
    if session_id is not None:
        db_session = db.query(models.Session).filter(models.Session.id == session_id).first()
        if not db_session:
            raise HTTPException(status_code=404, detail="Sesión no encontrada")
        if db_session.patient_id != user_id and db_session.therapist_id != user_id:
            raise HTTPException(status_code=403, detail="El usuario no es parte de esta sesión")
        if db_session.ended_at is not None:
            raise HTTPException(status_code=400, detail="No se pueden agregar imágenes a una sesión finalizada")
    
    try:
        image = services.image_generation.generar_imagen(prompt.promptText, user_id=user_id, prompt_seed=prompt.seed, input_img=prompt.inputImage)
        gen_seed = image.get("seed") if isinstance(image, dict) else None
        db_image = models.Image(fileName=image["file"], seed=gen_seed, owner_id=user_id, session_id=session_id)
        db.add(db_image)
        db.commit()
        db.refresh(db_image)
        return image
    except HTTPException:
        # Re-raise HTTP exceptions (from image generation service)
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error al crear imagen: {str(e)}"
        )

def create_user_sketch_image(db: Session, prompt: schemas.SketchPrompt, user_id: int, session_id: int):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user.type != 'patient':
        raise HTTPException(status_code=404, detail="Los terapeutas no pueden tener imágenes")
    
    # Validar que la sesión existe y pertenece al usuario
    if session_id is not None:
        db_session = db.query(models.Session).filter(models.Session.id == session_id).first()
        if not db_session:
            raise HTTPException(status_code=404, detail="Sesión no encontrada")
        if db_session.patient_id != user_id and db_session.therapist_id != user_id:
            raise HTTPException(status_code=403, detail="El usuario no es parte de esta sesión")
        if db_session.ended_at is not None:
            raise HTTPException(status_code=400, detail="No se pueden agregar imágenes a una sesión finalizada")
    
    try:
        image = services.image_generation.convertir_boceto_imagen(prompt.sketchImage, prompt.sketchText, user_id=user_id)
        gen_seed = image.get("seed") if isinstance(image, dict) else None
        db_image = models.Image(fileName=image["file"], seed=gen_seed, owner_id=user_id, session_id=session_id)
        db.add(db_image)
        db.commit()
        db.refresh(db_image)
        return image
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error al crear imagen desde boceto: {str(e)}"
        )


def create_user_uploaded_image(db: Session, upload_file, user_id: int, isDrawn: bool = False):
    """Save an uploaded file to the generated_images folder and create DB record."""
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user or db_user.type != 'patient':
        raise HTTPException(status_code=404, detail="Los terapeutas no pueden tener imágenes o usuario no encontrado")

    try:
        image = services.image_generation.publicar_imagen(upload_file, isDrawn=isDrawn)

        # create DB record
        db_image = models.Image(fileName=image["file"], seed = image["seed"], owner_id=user_id)
        db.add(db_image)
        db.commit()
        db.refresh(db_image)

        return image
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error al subir imagen: {str(e)}"
        )

def create_user_drawn_image(db: Session, upload_file, user_id: int):
    """Save a drawn image to drawn_images and create DB record."""
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user or db_user.type != 'patient':
        raise HTTPException(status_code=404, detail="Los terapeutas no pueden tener imágenes o usuario no encontrado")

    try:
        image = services.image_generation.publicar_dibujo(upload_file)

        db_image = models.Image(fileName=image["file"], seed = image.get("seed"), owner_id=user_id)
        db.add(db_image)
        db.commit()
        db.refresh(db_image)

        return image
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error al guardar imagen dibujada: {str(e)}"
        )

def get_images_for_user(db: Session, user_id: int):
    """Retrieve all images for a given user."""
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    images = db.query(models.Image).filter(models.Image.owner_id == user_id).all()
    return {
        "data": images,
        "count": len(images)
    }

def get_template_images():
    """Retrieve all template images from the template directory."""
    return services.image_generation.obtener_imagenes_plantilla()

def get_images_for_user(db: Session, user_id: int):
    """Retrieve all images for a given user."""
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    images = db.query(models.Image).filter(models.Image.owner_id == user_id).all()
    return {
        "data": images,
        "count": len(images)
    }
def create_user_img_by_mult_images(db: Session, images: schemas.TemplateImagesIn, user_id: int, session_id: int):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user.type != 'patient':
        raise HTTPException(status_code=404, detail="Los terapeutas no pueden tener imágenes")
    
    # Validar que la sesión existe y pertenece al usuario
    if session_id is not None:
        db_session = db.query(models.Session).filter(models.Session.id == session_id).first()
        if not db_session:
            raise HTTPException(status_code=404, detail="Sesión no encontrada")
        if db_session.patient_id != user_id and db_session.therapist_id != user_id:
            raise HTTPException(status_code=403, detail="El usuario no es parte de esta sesión")
        if db_session.ended_at is not None:
            raise HTTPException(status_code=400, detail="No se pueden agregar imágenes a una sesión finalizada")
    
    try:
        image = services.image_generation.generate_image_by_mult_images(images.data, count=len(images.data), user_id=user_id)    
        gen_seed = image.get("seed") if isinstance(image, dict) else None
        db_image = models.Image(fileName=image["file"], seed=gen_seed, owner_id=user_id, session_id=session_id)
        db.add(db_image)
        db.commit()
        db.refresh(db_image)
        return image
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error al crear imagen desde múltiples imágenes: {str(e)}"
        )
