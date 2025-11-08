from fastapi import APIRouter
import app.schemas as schemas
import app.crud as crud

router = APIRouter()

@router.post("/generate-image", response_model=schemas.ImageGenerationResponse)
async def generate_image(prompt: schemas.Prompt):
    """
    Genera una imagen usando ComfyUI basándose en el prompt proporcionado.
    """
    return crud.comfy.create_image(prompt.promptText)
