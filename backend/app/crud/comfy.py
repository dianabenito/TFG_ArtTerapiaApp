from sqlalchemy.orm import Session
from fastapi import HTTPException
import app.models as models
import app.schemas as schemas
import app.services as services

def create_image(promptText: str):
    return services.image_generation.generar_imagen(promptText)