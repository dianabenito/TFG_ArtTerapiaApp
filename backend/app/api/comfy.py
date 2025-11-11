from fastapi import APIRouter
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
    return crud.comfy.create_user_image(db=db, prompt = prompt, user_id=user_id)
