from sqlalchemy.orm import Session
from fastapi import HTTPException
import app.models as models
import app.schemas as schemas
import app.services as services


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

