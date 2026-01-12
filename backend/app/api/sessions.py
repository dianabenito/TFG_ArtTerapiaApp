from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
import app.schemas as schemas
from sqlalchemy.orm import Session
from app.dependencies import SessionDep, CurrentUser
import app.crud as crud
import app.models as models
from datetime import datetime
from sqlalchemy import and_, exists
from sqlalchemy.orm import aliased

router = APIRouter()


@router.post("/session/{patient_id}/{therapist_id}", response_model=schemas.Session)
def create_session(db: SessionDep, patient_id: int, therapist_id: int, session: schemas.SessionCreate, current_user: CurrentUser):
    return crud.session.create_session_for_users(db=db, patient_id=patient_id, therapist_id=therapist_id, session=session)

@router.post("/session/{patient_id}", response_model=schemas.Session)
def create_session_for_patient(patient_id: int, 
                               db: SessionDep, 
                               current_user: CurrentUser,
                               session: schemas.SessionCreate):
    if current_user.type != 'therapist':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Solo los terapeutas pueden crear sesiones")
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    if session.start_date >= session.end_date:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="La fecha de inicio debe ser anterior a la fecha de fin")
    return crud.session.create_session_for_users(db=db, patient_id=patient.id, therapist_id=current_user.id, session=session)

@router.put("/session/{session_id}", response_model=schemas.Session)
def update_session(session_id: int, session: schemas.SessionUpdate, db: SessionDep, current_user: CurrentUser):
    return crud.session.update_session(db, session_id, session, current_user.id)

@router.get('/my-sessions', response_model=schemas.SessionsOut)
async def get_sessions_active_user(db: SessionDep, current_user: CurrentUser):
    crud.session.finalize_expired_sessions(db, current_user.id)
    sessions = db.query(models.Session).filter(
        (models.Session.patient_id == current_user.id) | (models.Session.therapist_id == current_user.id)
    ).all()
    return {"data": sessions, "count": len(sessions)}


@router.get('/active', response_model=schemas.Session)
def get_active_session(db: SessionDep, current_user: CurrentUser):
    """
    Return the user's active session where now is between start_date and end_date.
    Searches both patient and therapist roles.
    """
    now = datetime.utcnow()
    crud.session.finalize_expired_sessions(db, current_user.id)
    # First try as patient

    S2 = aliased(models.Session)
    session = db.query(models.Session).filter(
        models.Session.patient_id == current_user.id,
        models.Session.start_date <= now,
        models.Session.end_date >= now,
        models.Session.ended_at == None,
        ~exists().where(and_(
            S2.therapist_id == models.Session.therapist_id,
            S2.start_date <= now,
            S2.end_date >= now,
            S2.ended_at == None,
            S2.start_date < models.Session.start_date
        ))
    ).order_by(models.Session.start_date.asc()).first()
    if session:
        return session

    # Then try as therapist
    session = db.query(models.Session).filter(
        models.Session.therapist_id == current_user.id,
        models.Session.start_date <= now,
        models.Session.end_date >= now,
        models.Session.ended_at == None,
    ).order_by(models.Session.start_date.asc()).first()
    if session:
        return session

    # Not found
    raise HTTPException(status_code=404, detail="No hay sesión activa")


@router.get('/next', response_model=schemas.Session)
def get_next_session(db: SessionDep, current_user: CurrentUser):
    """
    Devuelve la sesión inmediata para el usuario logueado (paciente o terapeuta).
    - Si hay una sesión activa (start <= now <= end y no finalizada), se devuelve esa.
    - Si no hay activa, se devuelve la próxima agendada futura para este usuario.
    - Si no existe ninguna, se responde 404 con mensaje claro.
    """
    now = datetime.utcnow()
    crud.session.finalize_expired_sessions(db, current_user.id)

    base_query = db.query(models.Session).filter(
        ((models.Session.patient_id == current_user.id) | (models.Session.therapist_id == current_user.id)),
        models.Session.ended_at == None,
    )

    # Primero, la activa
    active = base_query.filter(
        models.Session.start_date <= now,
        models.Session.end_date >= now,
    ).first()
    if active:
        return active

    # Luego, la próxima futura ordenada por fecha de inicio
    upcoming = base_query.filter(models.Session.start_date > now).order_by(models.Session.start_date.asc()).first()
    if upcoming:
        return upcoming

    raise HTTPException(status_code=404, detail="No tienes ninguna sesión programada")


@router.get('/session/{session_id}', response_model=schemas.Session)
def get_session_by_id(session_id: int, db: SessionDep, current_user: CurrentUser):
    """
    Return a session by id. Allows participants (patient or therapist) to view session info.
    This returns the session even if it has been finalized (ended_at set).
    """
    crud.session.finalize_expired_sessions(db, current_user.id)
    session = db.query(models.Session).filter(models.Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")

    # Only patient or therapist may view the session
    if current_user.id not in (session.patient_id, session.therapist_id):
        raise HTTPException(status_code=403, detail="No tienes permiso para ver esta sesión")

    return session


@router.post('/end/{session_id}', response_model=schemas.Session)
async def end_session_by_id(session_id: int, db: SessionDep, current_user: CurrentUser):
    """
    Finalize a session (unambiguous path). Only the therapist of the session may perform this action.
    This sets `ended_at` to now and attempts to notify/close active websockets for that session.
    """
    session = db.query(models.Session).filter(models.Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    if current_user.type != 'therapist' or current_user.id != session.therapist_id:
        raise HTTPException(status_code=403, detail="Solo el terapeuta de esta sesión puede finalizarla")

    updated = crud.session.end_session(db, session_id)

    # Try to notify/close any active websockets for this session (best-effort)
    try:
        import app.api.ws as ws_module
        conns = ws_module.active_sessions.get(session_id, {})
        for role, ws in list(conns.items()):
            try:
                await ws.send_text('session_ended')
            except Exception:
                pass
            try:
                await ws.close(code=1000)
            except Exception:
                pass
    except Exception:
        pass

    return updated

@router.delete('/session/{session_id}')
async def delete_session_by_id(session_id: int, db: SessionDep, current_user: CurrentUser):
    """
    Delete a session by id. Only the therapist of the session may perform this action.
    """
    return crud.session.delete_session(db, session_id, current_user.id, current_user.type)



@router.get('/sessions/{session_id}/images', response_model=schemas.ImagesOut)
async def get_images_for_session(db: SessionDep, session_id: int, current_user: CurrentUser):
    """Endpoint para que el usuario suba una imagen desde su galería."""
    return crud.session.get_images_for_session(db=db, session_id=session_id)