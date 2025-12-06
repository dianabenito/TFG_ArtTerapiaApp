from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, field_validator, Field, EmailStr
import re
from datetime import datetime
from .item import Item

class UserType(str, Enum):
    patient = "patient"
    therapist = "therapist"

class UserBase(BaseModel):
    email: EmailStr
    full_name: str

    @field_validator('full_name')
    @classmethod
    def full_name_not_empty(cls, v: str):
        if not v or not v.strip():
            raise ValueError("full_name must not be empty")
        return v.strip()

class UserCreate(UserBase):
    password: str
    type: UserType

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(UserBase):
    id: int
    type: UserType
    is_active: bool
    created_at: datetime
    items: List[Item] = []
    class Config:
        orm_mode = True
