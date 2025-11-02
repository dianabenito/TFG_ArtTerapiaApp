from fastapi import APIRouter, Path, Query, Body, HTTPException
from typing import Optional, List
from pydantic import BaseModel, HttpUrl, field_validator
import app.schemas as schemas
from sqlalchemy.orm import Session
from app.dependencies import SessionDep
import app.crud as crud


router = APIRouter()

@router.post("/users/{user_id}/items/", response_model=schemas.Item)
async def create_item_for_user(
    db: SessionDep, user_id: int, item: schemas.ItemCreate,
):
    db_user = crud.user.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return crud.item.create_user_item(db=db, item=item, user_id=user_id)

@router.get("/items/", response_model=List[schemas.Item])
async def read_items(db: SessionDep, skip: int = 0, limit: int = 10):
    items = crud.item.get_items(db, skip=skip, limit=limit)
    return items


@router.put("/items/{item_id}", response_model=schemas.Item)
async def update_item(db: SessionDep, item_id: int, item: schemas.Item):    
    db_item = crud.item.update_item(db, item_id=item_id, item=item)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item

@router.delete("/items/{item_id}")
async def delete_item(db: SessionDep, item_id: int):
    success = crud.item.delete_item(db, item_id=item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"detail": "Item deleted successfully"}
