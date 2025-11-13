from sqlalchemy.orm import Session
from fastapi import HTTPException
import app.models as models
import app.schemas as schemas
import app.services as services
from datetime import datetime


def create_session_for_users(db: Session, patient_id: int, therapist_id: int, session: schemas.SessionCreate):
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    therapist = db.query(models.Therapist).filter(models.Therapist.id == therapist_id).first()

    if not patient or not therapist:
        raise HTTPException(status_code=404, detail="Patient or Therapist not found")  
    
    # assign start/end directly from Pydantic model (they are Optional[datetime])
    db_session = models.Session(
        patient_id=patient.id,
        therapist_id=therapist.id,
        start_date=session.start_date,
        end_date=session.end_date,
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session


def end_session(db: Session, session_id: int):
    """
    Mark a session as ended by setting `ended_at` to now.
    """
    db_session = db.query(models.Session).filter(models.Session.id == session_id).first()
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
    if db_session.ended_at is not None:
        raise HTTPException(status_code=400, detail="Session already ended")
    db_session.ended_at = datetime.utcnow()
    db.commit()
    db.refresh(db_session)
    return db_session

