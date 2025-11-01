from typing import Optional 
from pydantic import BaseModel, field_validator, Field, EmailStr
import re

class User(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    age: int = Field(..., gt=0, lt=99)
    full_name: Optional[str] = None
    codigo_postal: str

    @field_validator('codigo_postal')
    def validate_codigo_postal(cls, v):
        if not re.match(r'^\d{5}$', v):
            raise ValueError('codigo_postal must be a 5 digit number') 
        return v