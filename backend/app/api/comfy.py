from fastapi import APIRouter, UploadFile, File, Depends
from app.dependencies import SessionDep
import app.schemas as schemas
import app.crud as crud

router = APIRouter()


@router.post("/users/{user_id}/images/", response_model=schemas.ImageGenerationResponse)
async def generate_image_for_user(db: SessionDep, user_id: int, prompt: schemas.Prompt):
    """
    Genera una imagen usando ComfyUI basándose en el prompt proporcionado.
    """
    db_user = crud.user.get_user(db, user_id=user_id)
    return crud.comfy.create_user_image(db=db, prompt=prompt, user_id=user_id)


@router.post('/users/{user_id}/images/upload', response_model=schemas.ImageGenerationResponse)
async def upload_image_for_user(db: SessionDep, user_id: int, file: UploadFile = File(...)):
    """Endpoint para que el usuario suba una imagen desde su galería."""
    return crud.comfy.create_user_uploaded_image(db=db, upload_file=file, user_id=user_id)
