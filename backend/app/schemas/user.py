from typing import Optional, List
from pydantic import BaseModel, field_validator, Field, EmailStr
import re
from datetime import datetime
from .item import Item

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    items: List[Item] = []
    class Config:
        orm_mode = True

