from pydantic import BaseModel

class Prompt(BaseModel):
    promptText: str