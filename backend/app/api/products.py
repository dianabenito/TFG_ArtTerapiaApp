from fastapi import APIRouter
from typing import Optional, List
from pydantic import BaseModel, HttpUrl, field_validator

router = APIRouter()

class Imagen(BaseModel):
    url: HttpUrl
    nombre: str

    @field_validator('nombre')
    def validate_nombre(cls, v):
        if len(v) > 100:
            raise ValueError('nombre must be at most 100 characters long')
        return v
    
class Tag(BaseModel):
    id: int
    nombre: str

class Producto(BaseModel):
    nombre: str
    precio: float
    descripcion: Optional[str] = None
    impuestos: Optional[float] = None
    tags: List[Tag] = []
    imagenes: List[Imagen] = []

    def precio_con_impuestos(self) -> float:
        if self.impuestos:
            return self.precio * (1 + self.impuestos)
        return self.precio
    

@router.post("/productos/")
async def create_producto(producto: Producto):
    precio_final = producto.precio_con_impuestos()
    return {"producto": producto, "precio_final": round(precio_final, 2)}