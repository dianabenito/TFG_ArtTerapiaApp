from sqlalchemy.orm import Session
from fastapi import HTTPException
import app.models as models
import app.schemas as schemas
import app.services as services
from datetime import datetime


def finalize_expired_sessions(db: Session, user_id: int | None = None):
    """Auto-finalize sessions that passed their scheduled end_date without being ended.

    If user_id is provided, scope to sessions where the user is patient or therapist
    to minimize the update set for per-request calls.
    """
    query = db.query(models.Session).filter(
            models.Session.ended_at == None,
            models.Session.end_date != None,
            models.Session.end_date <= datetime.utcnow()
    )

    if user_id is not None:
        query = query.filter(
            (models.Session.patient_id == user_id) | (models.Session.therapist_id == user_id)
        )

    to_close = query.all()
    if not to_close:
        return 0

    for session in to_close:
        session.ended_at = session.end_date

    db.commit()
    return len(to_close)


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

def get_images_for_session(db: Session, session_id: int):
    """Retrieve all images for a given session."""
    db_session = db.query(models.Session).filter(models.Session.id == session_id).first()
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
    images = db.query(models.Image).filter(models.Image.session_id == session_id).all()
    return {
        "data": images,
        "count": len(images)
    }
