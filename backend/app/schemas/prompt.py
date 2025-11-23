from pydantic import BaseModel
from typing import Optional


class Prompt(BaseModel):
    promptText: str


class ImageGenerationResponse(BaseModel):
    message: str
    file: str
    fullPath: str
    seed: Optional[int] = None


class ImageGenerationError(BaseModel):
    error: str
    status: int


class UploadedFile(BaseModel):
    filename: str