from fastapi import APIRouter, Path, Query, Body
from typing import Optional, List
from pydantic import BaseModel, HttpUrl, field_validator
from app.models import User

router = APIRouter()

class Item(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    tax: Optional[float] = None


@router.get("/items/")
async def read_items(skip: int = 0, limit: int = 10, q: Optional[str] = None):
    results = {"skip": skip, "limit": limit}
    if q:
        results.update({"q": q})
    return results

@router.get("/items/{item_id}")
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

@router.put("/items/{item_id}")
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

@router.post("/items/{item_id}")
async def create_item(item_id: int, item: Item, user: User):
    return {"item_id": item_id, "item": item, "user": user}

@router.delete("/items/{item_id}")
async def delete_item(item_id: int):
    return {"item_id": item_id, "deleted": True}