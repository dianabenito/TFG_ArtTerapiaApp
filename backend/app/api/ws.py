from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict
from app.security import decode_access_token
from app.database import SessionLocal
import app.models as models

router = APIRouter()

# Diccionario que mantiene las conexiones activas por sesión
active_sessions: Dict[int, Dict[str, WebSocket]] = {}


@router.websocket("/ws/{session_id}/{role}")
async def websocket_endpoint(websocket: WebSocket, session_id: int, role: str):
    """
    WebSocket para comunicación paciente-terapeuta.
    Autentica al usuario mediante token JWT pasado por query param `?token=...`.
    Sólo permite la conexión si el token identifica al paciente/terapeuta de la sesión.
    """
    # Obtener token desde query params (más fiable para websockets en este setup)
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008)
        return

    # Decodificar token y obtener user id
    try:
        user_id = decode_access_token(token)
        user_id = int(user_id)
    except Exception:
        await websocket.close(code=1008)
        return

    # Cargar sesión y usuario desde DB y verificar permisos
    db = SessionLocal()
    try:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            await websocket.close(code=1008)
            return

        session = db.query(models.Session).filter(models.Session.id == session_id).first()
        if not session:
            await websocket.close(code=1008)
            return

        # Verificar que el usuario coincide con el role y pertenece a la sesión
        if role == "patient":
            if user.id != session.patient_id:
                await websocket.close(code=1008)
                return
        elif role == "therapist":
            if user.id != session.therapist_id:
                await websocket.close(code=1008)
                return
        else:
            await websocket.close(code=1003)
            return
    finally:
        db.close()

    # Si todo OK, aceptar la conexión
    await websocket.accept()

    if session_id not in active_sessions:
        active_sessions[session_id] = {}

    active_sessions[session_id][role] = websocket
    print(f"🟢 {role} conectado en sesión {session_id} (user {user_id})")

    try:
        while True:
            data = await websocket.receive_text()
            other_role = "therapist" if role == "patient" else "patient"
            if other_role in active_sessions.get(session_id, {}):
                try:
                    await active_sessions[session_id][other_role].send_text(data)
                except Exception:
                    # si no se puede enviar, eliminar la conexión y continuar
                    del active_sessions[session_id][other_role]
    except WebSocketDisconnect:
        print(f"🔴 {role} desconectado de la sesión {session_id}")
        if session_id in active_sessions and role in active_sessions[session_id]:
            del active_sessions[session_id][role]
        if session_id in active_sessions and not active_sessions[session_id]:
            del active_sessions[session_id]
