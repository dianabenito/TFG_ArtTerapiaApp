from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
import app.schemas as schemas
from sqlalchemy.orm import Session
from app.dependencies import SessionDep, CurrentUser
import app.crud as crud
import app.models as models
from datetime import datetime

router = APIRouter()

@router.post("/session/{patient_id}/{therapist_id}", response_model=schemas.Session)
def create_session(db: SessionDep, patient_id: int, therapist_id: int, session: schemas.SessionCreate):
    return crud.session.create_session_for_users(db=db, patient_id=patient_id, therapist_id=therapist_id, session=session)

@router.post("/session/{patient_id}", response_model=schemas.Session)
def create_session_for_patient(patient_id: int, 
                               db: SessionDep, 
                               current_user: CurrentUser,
                               session: schemas.SessionCreate):
    if current_user.type != 'therapist':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Only therapists can create sessions")
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return crud.session.create_session_for_users(db=db, patient_id=patient.id, therapist_id=current_user.id, session=session)


@router.get('/active', response_model=schemas.Session)
def get_active_session(db: SessionDep, current_user: CurrentUser):
    """
    Return the user's active session where now is between start_date and end_date.
    Searches both patient and therapist roles.
    """
    now = datetime.utcnow()
    # First try as patient
    session = db.query(models.Session).filter(
        models.Session.patient_id == current_user.id,
        models.Session.start_date <= now,
        models.Session.end_date >= now,
    ).first()
    if session:
        return session

    # Then try as therapist
    session = db.query(models.Session).filter(
        models.Session.therapist_id == current_user.id,
        models.Session.start_date <= now,
        models.Session.end_date >= now,
    ).first()
    if session:
        return session

    # Not found
    raise HTTPException(status_code=404, detail="No active session")
