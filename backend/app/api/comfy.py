from fastapi import APIRouter, UploadFile, File, Depends, Query
from app.dependencies import SessionDep, CurrentUser
import app.schemas as schemas
import app.crud as crud

router = APIRouter()


@router.post("/users/{user_id}/session-images/link", response_model=schemas.ImageGenerationResponse)
async def link_image_to_session(db: SessionDep, user_id: int, current_user: CurrentUser, image_file_name: str = Query(...), session_id: int = Query(...)):
    """Asocia una imagen existente a una sesión sin duplicar el archivo."""
    return crud.comfy.link_image_to_session(db=db, image_file_name=image_file_name, user_id=user_id, session_id=session_id)


@router.post("/users/{user_id}/images", response_model=schemas.ImageGenerationResponse)
async def generate_image_for_user(db: SessionDep, user_id: int, prompt: schemas.Prompt, current_user: CurrentUser, session_id: int | None = None):
    """
    Genera una imagen usando ComfyUI basándose en el prompt proporcionado.
    """
    db_user = crud.user.get_user(db, user_id=user_id)
    return crud.comfy.create_user_image(db=db, prompt=prompt, user_id=user_id, session_id=session_id)

@router.post("/users/{user_id}/sketch-images/", response_model=schemas.ImageGenerationResponse)
async def generate_sketch_image_for_user(db: SessionDep, user_id: int, prompt: schemas.SketchPrompt, current_user: CurrentUser, session_id: int | None = None):
    """
    Genera una imagen usando ComfyUI basándose en el prompt proporcionado.
    """
    db_user = crud.user.get_user(db, user_id=user_id)
    return crud.comfy.create_user_sketch_image(db=db, prompt=prompt, user_id=user_id, session_id=session_id)

@router.post("/users/{user_id}/multiple-images/", response_model=schemas.ImageGenerationResponse)
async def generate_image_for_user(db: SessionDep, user_id: int, images: schemas.TemplateImagesIn, current_user: CurrentUser, session_id: int | None = None):
    """
    Genera una imagen usando ComfyUI basándose en el prompt proporcionado.
    """
    db_user = crud.user.get_user(db, user_id=user_id)
    return crud.comfy.create_user_img_by_mult_images(db=db, images=images, user_id=user_id, session_id=session_id)


@router.post('/users/{user_id}/images/upload', response_model=schemas.ImageGenerationResponse)
async def upload_image_for_user(db: SessionDep, user_id: int, current_user: CurrentUser, file: UploadFile = File(...), isDrawn: bool = False):
    """Endpoint para que el usuario suba una imagen desde su galería."""
    return crud.comfy.create_user_uploaded_image(db=db, upload_file=file, user_id=user_id, isDrawn=isDrawn)


@router.post('/users/{user_id}/images/drawn', response_model=schemas.ImageGenerationResponse)
async def upload_drawn_image_for_user(db: SessionDep, user_id: int, current_user: CurrentUser, file: UploadFile = File(...)):
    """Endpoint para guardar un dibujo creado en Canvas."""
    return crud.comfy.create_user_drawn_image(db=db, upload_file=file, user_id=user_id)

@router.get('/users/{user_id}/images', response_model=schemas.ImagesOut)
async def get_images_for_user(db: SessionDep, user_id: int, current_user: CurrentUser):
    """Endpoint para que el usuario suba una imagen desde su galería."""
    return crud.comfy.get_images_for_user(db=db, user_id=user_id)

@router.get("/template-images")
def get_template_images():
    return crud.comfy.get_template_images()
