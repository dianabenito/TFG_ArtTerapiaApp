"""Módulo principal de la aplicación FastAPI de arteterapia.

Este módulo configura la aplicación FastAPI principal, incluyendo:
- Inicialización de la base de datos
- Configuración de CORS
- Montaje de archivos estáticos
- Registro de routers de API

Attributes:
    app (FastAPI): Instancia principal de la aplicación FastAPI.
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr, HttpUrl, field_validator
import re, os
from app.api import users, comfy, ws, sessions
import app.models as models
from .database import engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="App ArtTerapia",
    description="API REST para aplicación de arteterapia con generación de imágenes mediante IA",
    version="1.0.0",
    contact={
        "name": "Diana Benito",
        "email": "dbenitre56@alumnes.ub.edu",
    },
)

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Asegurar que la carpeta de imágenes existe
images_path = os.path.abspath("../frontend/src/assets/images")
os.makedirs(images_path, exist_ok=True)
app.mount("/images", StaticFiles(directory=images_path), name="images")

app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(comfy.router, prefix="/comfy", tags=["comfy"])
app.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
app.include_router(ws.router, tags=["websocket"])

@app.get("/", tags=["root"])
async def root():
    """Endpoint raíz de la API.
    
    Returns:
        dict: Mensaje de bienvenida.
    
    Example:
        >>> GET /
        {"message": "Hello World"}
    """
    return {"message": "Hello World"}
