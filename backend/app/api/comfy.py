"""Router de API para generación de imágenes con ComfyUI.

Endpoints para generar imágenes usando Stable Diffusion XL a través de ComfyUI.
Soporta diferentes workflows: txt2img, img2img, sketch2img, y combinaciones de múltiples imágenes.
"""

from fastapi import APIRouter, UploadFile, File, Depends, Query
from app.dependencies import SessionDep, CurrentUser
import app.schemas as schemas
import app.crud as crud

router = APIRouter()


@router.post("/users/{user_id}/session-images/link", response_model=schemas.ImageGenerationResponse)
async def link_image_to_session(db: SessionDep, user_id: int, current_user: CurrentUser, image_file_name: str = Query(...), session_id: int = Query(...)):
    """Asocia una imagen existente a una sesión sin duplicar el archivo.
    
    Args:
        db (Session): Sesión de base de datos.
        user_id (int): ID del usuario propietario de la imagen.
        current_user (CurrentUser): Usuario autenticado.
        image_file_name (str): Nombre del archivo de imagen existente.
        session_id (int): ID de la sesión a la que asociar la imagen.
    
    Returns:
        schemas.ImageGenerationResponse: Respuesta con información de la imagen vinculada.
    """
    return crud.comfy.link_image_to_session(db=db, image_file_name=image_file_name, user_id=user_id, session_id=session_id)


@router.post("/users/{user_id}/images", response_model=schemas.ImageGenerationResponse)
async def generate_image_for_user(db: SessionDep, user_id: int, prompt: schemas.Prompt, current_user: CurrentUser, session_id: int | None = None):
    """Genera imagen usando ComfyUI workflow txt2img.
    
    Args:
        db (Session): Sesión de base de datos.
        user_id (int): ID del usuario para el que se genera la imagen.
        prompt (schemas.Prompt): Prompt de texto y parámetros de generación.
        current_user (CurrentUser): Usuario autenticado.
        session_id (int, optional): ID de sesión asociada. Default None.
    
    Returns:
        schemas.ImageGenerationResponse: Imagen generada con metadata.
    """
    db_user = crud.user.get_user(db, user_id=user_id)
    return crud.comfy.create_user_image(db=db, prompt=prompt, user_id=user_id, session_id=session_id)

@router.post("/users/{user_id}/sketch-images/", response_model=schemas.ImageGenerationResponse)
async def generate_sketch_image_for_user(db: SessionDep, user_id: int, prompt: schemas.SketchPrompt, current_user: CurrentUser, session_id: int | None = None):
    """Genera imagen usando ComfyUI workflow sketch2img o img2img.
    
    Args:
        db (Session): Sesión de base de datos.
        user_id (int): ID del usuario para el que se genera la imagen.
        prompt (schemas.SketchPrompt): Prompt con imagen base y parámetros.
        current_user (CurrentUser): Usuario autenticado.
        session_id (int, optional): ID de sesión asociada. Default None.
    
    Returns:
        schemas.ImageGenerationResponse: Imagen generada con metadata.
    """
    db_user = crud.user.get_user(db, user_id=user_id)
    return crud.comfy.create_user_sketch_image(db=db, prompt=prompt, user_id=user_id, session_id=session_id)

@router.post("/users/{user_id}/multiple-images/", response_model=schemas.ImageGenerationResponse)
async def generate_image_for_user_multiple(db: SessionDep, user_id: int, images: schemas.TemplateImagesIn, current_user: CurrentUser, session_id: int | None = None):
    """Genera imagen combinando múltiples imágenes (2, 3 o 4).
    
    Args:
        db (Session): Sesión de base de datos.
        user_id (int): ID del usuario para el que se genera la imagen.
        images (schemas.TemplateImagesIn): Lista de imágenes y parámetros.
        current_user (CurrentUser): Usuario autenticado.
        session_id (int, optional): ID de sesión asociada. Default None.
    
    Returns:
        schemas.ImageGenerationResponse: Imagen generada combinando las fuentes.
    """
    db_user = crud.user.get_user(db, user_id=user_id)
    return crud.comfy.create_user_img_by_mult_images(db=db, images=images, user_id=user_id, session_id=session_id)


@router.post('/users/{user_id}/images/upload', response_model=schemas.ImageGenerationResponse)
async def upload_image_for_user(db: SessionDep, user_id: int, current_user: CurrentUser, file: UploadFile = File(...), isDrawn: bool = False):
    """Sube una imagen desde el cliente al servidor.
    
    Args:
        db (Session): Sesión de base de datos.
        user_id (int): ID del usuario propietario.
        current_user (CurrentUser): Usuario autenticado.
        file (UploadFile): Archivo de imagen a subir.
        isDrawn (bool): Si es un dibujo creado en canvas. Default False.
    
    Returns:
        schemas.ImageGenerationResponse: Información de la imagen subida.
    """
    return crud.comfy.create_user_uploaded_image(db=db, upload_file=file, user_id=user_id, isDrawn=isDrawn)


@router.post('/users/{user_id}/images/drawn', response_model=schemas.ImageGenerationResponse)
async def upload_drawn_image_for_user(db: SessionDep, user_id: int, current_user: CurrentUser, file: UploadFile = File(...)):
    """Guarda un dibujo creado en canvas.
    
    Args:
        db (Session): Sesión de base de datos.
        user_id (int): ID del usuario propietario.
        current_user (CurrentUser): Usuario autenticado.
        file (UploadFile): Archivo del dibujo.
    
    Returns:
        schemas.ImageGenerationResponse: Información del dibujo guardado.
    """
    return crud.comfy.create_user_drawn_image(db=db, upload_file=file, user_id=user_id)

@router.get('/users/{user_id}/images', response_model=schemas.ImagesOut)
async def get_images_for_user(db: SessionDep, user_id: int, current_user: CurrentUser):
    """Obtiene todas las imágenes de un usuario.
    
    Args:
        db (Session): Sesión de base de datos.
        user_id (int): ID del usuario.
        current_user (CurrentUser): Usuario autenticado.
    
    Returns:
        schemas.ImagesOut: Lista de imágenes del usuario.
    """
    return crud.comfy.get_images_for_user(db=db, user_id=user_id)

@router.get("/template-images")
def get_template_images():
    """Obtiene lista de imágenes plantilla disponibles.
    
    Returns:
        list: Nombres de archivos de imágenes plantilla.
    """
    return crud.comfy.get_template_images()
