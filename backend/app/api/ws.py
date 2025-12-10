from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict
from app.security import decode_access_token
from app.database import SessionLocal
import app.models as models
import json

router = APIRouter()

# Diccionario que mantiene conexiones activas por sesión
active_sessions: Dict[int, Dict[str, WebSocket]] = {}


@router.websocket("/ws/{session_id}/{role}")
async def websocket_endpoint(websocket: WebSocket, session_id: int, role: str):
    """
    WebSocket seguro y bidireccional para paciente y terapeuta.
    Permite:
      - envío de imágenes
      - notificaciones de estado
      - finalización de sesión
      - **chat en tiempo real**
    """

    # 1. Obtener token del query param
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008)
        return

    # 2. Decodificar JWT
    try:
        user_id = int(decode_access_token(token))
    except Exception:
        await websocket.close(code=1008)
        return

    # 3. Verificar sesión y rol en la base de datos
    db = SessionLocal()
    try:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        session = db.query(models.Session).filter(models.Session.id == session_id).first()

        if not user or not session:
            await websocket.close(code=1008)
            return

        if getattr(session, "ended_at", None) is not None:
            await websocket.close(code=1008)
            return

        # Verificar rol
        if role == "patient" and user.id != session.patient_id:
            await websocket.close(code=1008)
            return
        if role == "therapist" and user.id != session.therapist_id:
            await websocket.close(code=1008)
            return

    finally:
        db.close()

    # 4. Aceptar conexión
    await websocket.accept()

    # Registrar socket
    if session_id not in active_sessions:
        active_sessions[session_id] = {}
    active_sessions[session_id][role] = websocket

    print(f"{role} conectado en sesión {session_id} (user {user_id})")

    # Informar

    try:
        while True:
            data = await websocket.receive_text()
            other_role = "therapist" if role == "patient" else "patient"
            
            try:
                obj = json.loads(data)
            except json.JSONDecodeError:
                # Texto plano → convertir a mensaje de chat
                obj = {"event": "chat_message", "sender": role, "text": data}

            # Si el otro está conectado, enviar mensaje
            if other_role in active_sessions.get(session_id, {}):
                try:
                    await active_sessions[session_id][other_role].send_text(json.dumps(obj))
                except Exception:
                    del active_sessions[session_id][other_role]
                    
    except WebSocketDisconnect:
        print(f"{role} desconectado de la sesión {session_id}")
        if session_id in active_sessions and role in active_sessions[session_id]:
            del active_sessions[session_id][role]
        if session_id in active_sessions and not active_sessions[session_id]:
            del active_sessions[session_id]
