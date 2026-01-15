"""Script simple para poblar la base de datos con usuarios y sesiones de prueba.

Ejecución (desde la carpeta `backend`):
    python seed.py

El script es idempotente respecto a emails: no volverá a crear usuarios si ya existen.
"""
from datetime import datetime, timedelta
from app.database import SessionLocal, engine
import app.models as models
from app.security import hash_password


def ensure_tables():
    models.Base.metadata.create_all(bind=engine)


def get_or_create_user(db, model_cls, email, plain_password, full_name):
    user = db.query(model_cls).filter(model_cls.email == email).first()
    if user:
        return user
    hashed = hash_password(plain_password)
    user = model_cls(email=email, full_name=full_name, hashed_password=hashed)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_session(db, patient_id, therapist_id, start_dt, end_dt):
    # Check if similar session exists (same patient/therapist and overlapping dates)
    existing = db.query(models.Session).filter(
        models.Session.patient_id == patient_id,
        models.Session.therapist_id == therapist_id,
        models.Session.start_date == start_dt,
        models.Session.end_date == end_dt,
    ).first()
    if existing:
        return existing

    s = models.Session(patient_id=patient_id, therapist_id=therapist_id, start_date=start_dt, end_date=end_dt)
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


def main():
    ensure_tables()
    db = SessionLocal()
    try:
        p1 = get_or_create_user(db, models.Patient, 'patient1@example.com', 'P@ssword1', 'Paciente Uno')
        p2 = get_or_create_user(db, models.Patient, 'patient2@example.com', 'P@ssword2', 'Paciente Dos')
        p3 = get_or_create_user(db, models.Patient, 'patient3@example.com', 'P@ssword3', 'Paciente Tres')
        t1 = get_or_create_user(db, models.Therapist, 'therapist1@example.com', 'T@ssword1', 'Terapeuta Uno')
        t2 = get_or_create_user(db, models.Therapist, 'therapist2@example.com', 'T@ssword2', 'Terapeuta Dos')
        t3 = get_or_create_user(db, models.Therapist, 'therapist3@example.com', 'T@ssword3', 'Terapeuta Tres')
        t4 = get_or_create_user(db, models.Therapist, 'therapist4@example.com', 'T@ssword4', 'Terapeuta Cuatro')

        now = datetime.utcnow()
        active_start = now - timedelta(minutes=10)
        active_end = now + timedelta(hours=1)

        future_start = now + timedelta(days=1)
        future_end = future_start + timedelta(hours=2)

        s1 = create_session(db, p1.id, t1.id, active_start, active_end)
        s2 = create_session(db, p2.id, t2.id, future_start, future_end)
        s3 = create_session(db, p3.id, t3.id, active_start, active_end)

    finally:
        db.close()


if __name__ == '__main__':
    main()
