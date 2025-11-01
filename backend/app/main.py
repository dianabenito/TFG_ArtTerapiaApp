from fastapi import FastAPI, Path, Query, Body
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr, HttpUrl, field_validator
import re


app = FastAPI(
    title = "App ArtTerapia", 
    contact = {
        "name": "Diana Benito",
        "email": "dbenitre56@alumnes.ub.edu",
    }, 
)

class Item(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    tax: Optional[float] = None

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

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/items/")
async def read_items(skip: int = 0, limit: int = 10, q: Optional[str] = None):
    results = {"skip": skip, "limit": limit}
    if q:
        results.update({"q": q})
    return results

@app.get("/items/{item_id}")
async def read_item(
    item_id: int = Path(..., title="ID del item", ge=1),  # item_id must be greater than or equal to 1
    q: Optional[str] = Query(None, min_length=3, max_length=50),  # q is an optional query parameter with max length 50
    size: Optional[float] = Query(None, gt=0, lt=100)  # size must be greater than 0 and less than 1000
):
    results = {"item_id": item_id}
    if q:
        results.update({"q": q})
    if size:
        results.update({"size": size})
    return results

@app.put("/items/{item_id}")
async def update_item(
    item_id: int, 
    item: Item = Body(
        ..., 
        example={
            "name": "Smartphone",
            "description": "A brand new smartphone",
            "price": 699.99,
            "tax": 59.99
        }
    )
):
    return {"item_id": item_id, "item": item}

@app.post("/items/{item_id}")
async def create_item(item_id: int, item: Item, user: User):
    return {"item_id": item_id, "item": item, "user": user}

@app.delete("/items/{item_id}")
async def delete_item(item_id: int):
    return {"item_id": item_id, "deleted": True}

@app.get("/users/{user_id}")
async def read_user(user_id: str):
    return {"user_id": user_id, "name": f"User {user_id}"}

@app.post("/users/")
async def create_user(user: User):
    return {"user": user}

@app.post("/productos/")
async def create_producto(producto: Producto):
    precio_final = producto.precio_con_impuestos()
    return {"producto": producto, "precio_final": round(precio_final, 2)}