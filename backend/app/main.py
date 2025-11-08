from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr, HttpUrl, field_validator
import re, os
from app.api import users, items, comfy
import app.models as models
from .database import engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title = "App ArtTerapia", 
    contact = {
        "name": "Diana Benito",
        "email": "dbenitre56@alumnes.ub.edu",
    }, 
)

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Asegurar que la carpeta de imágenes existe
images_path = os.path.abspath("../frontend/src/assets/generated_images")
os.makedirs(images_path, exist_ok=True)
app.mount("/images", StaticFiles(directory=images_path), name="images")

app.include_router(items.router, prefix="/items", tags=["items"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(comfy.router, prefix="/comfy", tags=["comfy"])

@app.get("/")
async def root():
    return {"message": "Hello World"}
