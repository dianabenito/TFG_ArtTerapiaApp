from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class ItemBase(BaseModel):
    title: str
    description: Optional[str] = None

class ItemCreate(ItemBase):
    pass

class Item(BaseModel):
    id: int
    owner_id: int
    title: str
    description: Optional[str] = None
    class Config:
        orm_mode = True
    