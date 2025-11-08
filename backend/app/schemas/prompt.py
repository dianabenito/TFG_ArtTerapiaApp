from pydantic import BaseModel

class Prompt(BaseModel):
    promptText: str

class ImageGenerationResponse(BaseModel):
    message: str
    file: str
    fullPath: str

class ImageGenerationError(BaseModel):
    error: str
    status: int