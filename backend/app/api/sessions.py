from fastapi import APIRouter, Depends, HTTPException
from typing import List
import app.schemas as schemas
from sqlalchemy.orm import Session
from app.dependencies import SessionDep
import app.crud as crud

router = APIRouter()

@router.post("/session/{patient_id}/{therapist_id}", response_model=schemas.Session)
def create_session(db: SessionDep, patient_id: int, therapist_id: int, session: schemas.SessionCreate):
    return crud.session.create_session_for_users(db=db, patient_id=patient_id, therapist_id=therapist_id, session=session)


