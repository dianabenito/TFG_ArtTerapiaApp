from pydantic import BaseModel
from typing import Optional


class Prompt(BaseModel):
    promptText: str
    seed: Optional[int] = None
    inputImage: Optional[str] = None


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


class ImageOut(BaseModel):
    fileName: str
    seed: Optional[int] = None
    id: int


class ImagesOut(BaseModel):
    data: list[ImageOut]
    count: int

class ImageTemplate(BaseModel):
    fileName: str

class TemplateImagesIn(BaseModel):
    data: list[ImageTemplate]
    count: int