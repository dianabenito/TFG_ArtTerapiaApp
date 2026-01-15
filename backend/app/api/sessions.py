"""Router de API para gestión de sesiones de terapia.

Endpoints para crear, actualizar, consultar y finalizar sesiones entre terapeutas y pacientes.
Incluye gestión de sesiones activas, próximas y finalizadas.
"""

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
from app.api.ws import notify_new_session_to_patient

router = APIRouter()


@router.post("/session/{patient_id}/{therapist_id}", response_model=schemas.Session)
def create_session(db: SessionDep, patient_id: int, therapist_id: int, session: schemas.SessionCreate, current_user: CurrentUser):
    """Crea una sesión entre un paciente y un terapeuta (endpoint genérico).
    
    Args:
        db (Session): Sesión de base de datos.
        patient_id (int): ID del paciente.
        therapist_id (int): ID del terapeuta.
        session (schemas.SessionCreate): Datos de la sesión (fechas).
        current_user (CurrentUser): Usuario autenticado.
    
    Returns:
        schemas.Session: Sesión creada.
    """
    return crud.session.create_session_for_users(db=db, patient_id=patient_id, therapist_id=therapist_id, session=session)

@router.post("/session/{patient_id}", response_model=schemas.Session)
def create_session_for_patient(patient_id: int, 
                               db: SessionDep, 
                               current_user: CurrentUser,
                               session: schemas.SessionCreate):
    """Crea una sesión para un paciente (solo terapeutas).
    
    Args:
        patient_id (int): ID del paciente.
        db (Session): Sesión de base de datos.
        current_user (CurrentUser): Usuario autenticado (debe ser terapeuta).
        session (schemas.SessionCreate): Datos de la sesión.
    
    Returns:
        schemas.Session: Sesión creada.
    
    Raises:
        HTTPException: 403 si el usuario no es terapeuta.
        HTTPException: 404 si el paciente no existe.
        HTTPException: 400 si las fechas son inválidas.
    
    Note:
        Envía notificación WebSocket al paciente si está conectado.
    """
    if current_user.type != 'therapist':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Solo los terapeutas pueden crear sesiones")
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    if session.start_date >= session.end_date:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="La fecha de inicio debe ser anterior a la fecha de fin")
    
    new_session = crud.session.create_session_for_users(db=db, patient_id=patient.id, therapist_id=current_user.id, session=session)
    
    notify_new_session_to_patient(patient_id, new_session.id)
    
    return new_session

@router.put("/session/{session_id}", response_model=schemas.Session)
def update_session(session_id: int, session: schemas.SessionUpdate, db: SessionDep, current_user: CurrentUser):
    """Actualiza una sesión existente.
    
    Args:
        session_id (int): ID de la sesión a actualizar.
        session (schemas.SessionUpdate): Nuevos datos de la sesión.
        db (Session): Sesión de base de datos.
        current_user (CurrentUser): Usuario autenticado.
    
    Returns:
        schemas.Session: Sesión actualizada.
    """
    return crud.session.update_session(db, session_id, session, current_user.id)

@router.get('/my-sessions', response_model=schemas.SessionsOut)
async def get_sessions_active_user(db: SessionDep, current_user: CurrentUser):
    """Obtiene todas las sesiones del usuario actual (como paciente o terapeuta).
    
    Args:
        db (Session): Sesión de base de datos.
        current_user (CurrentUser): Usuario autenticado.
    
    Returns:
        schemas.SessionsOut: Lista de sesiones del usuario con contador.
    
    Note:
        Finaliza automáticamente sesiones expiradas antes de retornar.
    """
    crud.session.finalize_expired_sessions(db, current_user.id)
    sessions = db.query(models.Session).filter(
        (models.Session.patient_id == current_user.id) | (models.Session.therapist_id == current_user.id)
    ).all()
    return {"data": sessions, "count": len(sessions)}


@router.get('/active', response_model=schemas.Session)
def get_active_session(db: SessionDep, current_user: CurrentUser):
    """Obtiene la sesión activa del usuario actual.
    
    Una sesión es activa si: now entre start_date y end_date, y ended_at es None.
    
    Args:
        db (Session): Sesión de base de datos.
        current_user (CurrentUser): Usuario autenticado.
    
    Returns:
        schemas.Session: Sesión activa del usuario.
    
    Raises:
        HTTPException: 404 si no hay sesión activa.
    
    Note:
        Busca primero como paciente, luego como terapeuta.
        Si el terapeuta tiene múltiples sesiones activas, devuelve la más antigua.
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
    """Obtiene la próxima sesión del usuario (activa o futura).
    
    Lógica:
    1. Si hay sesión activa (start <= now <= end, no finalizada): retorna esa.
    2. Si no hay activa: retorna la próxima sesión futura ordenada por start_date.
    3. Si no hay ninguna: error 404.
    
    Args:
        db (Session): Sesión de base de datos.
        current_user (CurrentUser): Usuario autenticado.
    
    Returns:
        schemas.Session: Próxima sesión (activa o futura).
    
    Raises:
        HTTPException: 404 si no hay sesiones programadas.
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
    """Obtiene información de una sesión por ID.
    
    Args:
        session_id (int): ID de la sesión.
        db (Session): Sesión de base de datos.
        current_user (CurrentUser): Usuario autenticado.
    
    Returns:
        schemas.Session: Información de la sesión.
    
    Raises:
        HTTPException: 404 si la sesión no existe.
        HTTPException: 403 si el usuario no es participante (paciente o terapeuta).
    
    Note:
        Retorna la sesión incluso si ha sido finalizada (ended_at establecido).
    """
    crud.session.finalize_expired_sessions(db, current_user.id)
    session = db.query(models.Session).filter(models.Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")

    if current_user.id not in (session.patient_id, session.therapist_id):
        raise HTTPException(status_code=403, detail="No tienes permiso para ver esta sesión")

    return session


@router.post('/end/{session_id}', response_model=schemas.Session)
async def end_session_by_id(session_id: int, db: SessionDep, current_user: CurrentUser):
    """Finaliza una sesión (solo terapeuta).
    
    Establece ended_at al momento actual y notifica a clientes WebSocket conectados.
    
    Args:
        session_id (int): ID de la sesión a finalizar.
        db (Session): Sesión de base de datos.
        current_user (CurrentUser): Usuario autenticado (debe ser terapeuta de la sesión).
    
    Returns:
        schemas.Session: Sesión finalizada.
    
    Raises:
        HTTPException: 404 si la sesión no existe.
        HTTPException: 403 si el usuario no es el terapeuta de la sesión.
    
    Note:
        Intenta cerrar conexiones WebSocket activas para esta sesión.
    """
    session = db.query(models.Session).filter(models.Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    if current_user.type != 'therapist' or current_user.id != session.therapist_id:
        raise HTTPException(status_code=403, detail="Solo el terapeuta de esta sesión puede finalizarla")

    updated = crud.session.end_session(db, session_id)

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
    """Elimina una sesión (solo terapeuta).
    
    Args:
        session_id (int): ID de la sesión a eliminar.
        db (Session): Sesión de base de datos.
        current_user (CurrentUser): Usuario autenticado (debe ser terapeuta).
    
    Returns:
        dict: Mensaje de confirmación de eliminación.
    
    Raises:
        HTTPException: 403 si el usuario no es terapeuta.
        HTTPException: 404 si la sesión no existe.
    """
    return crud.session.delete_session(db, session_id, current_user.id, current_user.type)



@router.get('/sessions/{session_id}/images', response_model=schemas.ImagesOut)
async def get_images_for_session(db: SessionDep, session_id: int, current_user: CurrentUser):
    """Obtiene todas las imágenes generadas durante una sesión.
    
    Args:
        db (Session): Sesión de base de datos.
        session_id (int): ID de la sesión.
        current_user (CurrentUser): Usuario autenticado.
    
    Returns:
        schemas.ImagesOut: Lista de imágenes de la sesión.
    """
    return crud.session.get_images_for_session(db=db, session_id=session_id)