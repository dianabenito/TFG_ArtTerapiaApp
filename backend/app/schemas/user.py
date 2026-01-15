"""Schemas Pydantic para validación de datos de usuarios.

Define los modelos de datos para:
- Creación de usuarios (UserCreate)
- Login (UserLogin)
- Respuesta de usuario (User)
- Enum de tipos de usuario (UserType)
"""

from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, field_validator, Field, EmailStr
import re
from datetime import datetime

class UserType(str, Enum):
    """Tipos de usuario en el sistema.
    
    Attributes:
        patient: Usuario paciente que recibe terapia.
        therapist: Usuario terapeuta que conduce sesiones.
    """
    patient = "patient"
    therapist = "therapist"

class UserBase(BaseModel):
    """Schema base para usuarios con campos comunes.
    
    Attributes:
        email (EmailStr): Correo electrónico del usuario.
        full_name (str): Nombre completo del usuario.
    """
    email: EmailStr
    full_name: str

    @field_validator('full_name')
    @classmethod
    def full_name_not_empty(cls, v: str):
        """Valida que full_name no esté vacío."""
        if not v or not v.strip():
            raise ValueError("full_name must not be empty")
        return v.strip()

class UserCreate(UserBase):
    """Schema para creación de usuarios.
    
    Attributes:
        password (str): Contraseña en texto plano (se hasheará).
        type (UserType): Tipo de usuario (patient o therapist).
    """
    password: str
    type: UserType

class UserLogin(BaseModel):
    """Schema para login de usuarios.
    
    Attributes:
        email (EmailStr): Correo electrónico.
        password (str): Contraseña en texto plano.
    """
    email: EmailStr
    password: str

class User(UserBase):
    """Schema de respuesta para usuarios.
    
    Attributes:
        id (int): ID único del usuario.
        type (UserType): Tipo de usuario.
        is_active (bool): Si la cuenta está activa.
        created_at (datetime): Fecha de creación.
    """
    id: int
    type: UserType
    is_active: bool
    created_at: datetime
    class Config:
        orm_mode = True
