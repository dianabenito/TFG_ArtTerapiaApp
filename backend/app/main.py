from fastapi import FastAPI, Path, Query, Body
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr, HttpUrl, field_validator
import re
from app.api import products, users, items


app = FastAPI(
    title = "App ArtTerapia", 
    contact = {
        "name": "Diana Benito",
        "email": "dbenitre56@alumnes.ub.edu",
    }, 
)

app.include_router(products.router, prefix="/products", tags=["products"])
app.include_router(items.router, prefix="/items", tags=["items"])
app.include_router(users.router, prefix="/users", tags=["users"])


@app.get("/")
async def root():
    return {"message": "Hello World"}
