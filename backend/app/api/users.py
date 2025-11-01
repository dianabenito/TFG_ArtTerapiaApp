from fastapi import APIRouter
from app.models import User

router = APIRouter()

@router.get("/users/{user_id}")
async def read_user(user_id: str):
    return {"user_id": user_id, "name": f"User {user_id}"}

@router.post("/users/")
async def create_user(user: User):
    return {"user": user}
