from fastapi import FastAPI
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr, HttpUrl, field_validator
import re
from app.api import users, items
import app.model as model
from .database import engine

model.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title = "App ArtTerapia", 
    contact = {
        "name": "Diana Benito",
        "email": "dbenitre56@alumnes.ub.edu",
    }, 
)

app.include_router(items.router, prefix="/items", tags=["items"])
app.include_router(users.router, prefix="/users", tags=["users"])

@app.get("/")
async def root():
    return {"message": "Hello World"}
