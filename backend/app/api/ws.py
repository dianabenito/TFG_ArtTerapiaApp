"""Router de API para comunicación WebSocket en tiempo real.

Proporciona endpoints WebSocket para:
- Comunicación bidireccional durante sesiones (chat, notificaciones de imágenes)
- Notificaciones en Home/Calendar (nuevas sesiones creadas)

Attributes:
    active_sessions (Dict[int, Dict[str, WebSocket]]): Conexiones activas por sesión.
        Estructura: {session_id: {"patient": WebSocket, "therapist": WebSocket}}
    home_ws_connections (Dict[int, WebSocket]): Conexiones Home activas por usuario.
        Estructura: {user_id: WebSocket}
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict
from app.security import decode_access_token
from app.database import SessionLocal
import app.models as models
import json
import asyncio

router = APIRouter()

active_sessions: Dict[int, Dict[str, WebSocket]] = {}
home_ws_connections: Dict[int, WebSocket] = {}


@router.websocket("/ws/{session_id}/{role}")
async def websocket_endpoint(websocket: WebSocket, session_id: int, role: str):
    """WebSocket bidireccional para comunicación en sesiones de terapia.
    
    Funcionalidades:
    - Chat en tiempo real entre paciente y terapeuta
    - Notificaciones de imágenes generadas
    - Notificaciones de estado de sesión
    - Finalización de sesión
    
    Args:
        websocket (WebSocket): Conexión WebSocket.
        session_id (int): ID de la sesión de terapia.
        role (str): Rol del usuario ("patient" o "therapist").
    
    Query Parameters:
        token (str): Token JWT para autenticación.
    
    Protocol:
        - Envío/recepción de JSON: {"event": str, "sender": str, "text": str, ...}
        - Texto plano se convierte automáticamente a mensaje de chat
    
    Note:
        La conexión se cierra si:
        - No se proporciona token
        - Token inválido
        - Usuario no autorizado para la sesión
        - Sesión ya finalizada (ended_at != None)
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

        # Si la sesión está finalizada, cerrar el WebSocket
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

@router.websocket("/ws/home")
async def websocket_home(websocket: WebSocket):
    """WebSocket para notificaciones en vista Home/Calendar.
    
    Permite notificar a pacientes cuando un terapeuta crea una sesión para ellos.
    
    Args:
        websocket (WebSocket): Conexión WebSocket.
    
    Query Parameters:
        token (str): Token JWT para autenticación.
    
    Protocol:
        - Server → Client: {"event": "new_session", "sessionId": int}
        - Client → Server: Heartbeat (cualquier texto para mantener conexión)
    
    Note:
        La conexión se cierra si no se proporciona token o es inválido.
    """
    
    # Obtener token del query param
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008)
        return

    # Decodificar JWT
    try:
        user_id = int(decode_access_token(token))
    except Exception:
        await websocket.close(code=1008)
        return

    # Aceptar conexión
    await websocket.accept()
    
    # Registrar conexión
    home_ws_connections[user_id] = websocket
    print(f"Usuario {user_id} conectado a Home WS")

    try:
        # Mantener conexión viva (heartbeat simple)
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        print(f"Usuario {user_id} desconectado de Home WS")
        home_ws_connections.pop(user_id, None)
    except Exception as e:
        print(f"Error en Home WS para usuario {user_id}: {e}")
        home_ws_connections.pop(user_id, None)


def notify_new_session_to_patient(patient_id: int, session_id: int):
    """Notifica a un paciente conectado sobre una nueva sesión creada.
    
    Envía notificación WebSocket al paciente si está conectado a /ws/home.
    Llamado automáticamente cuando un terapeuta crea una sesión.
    
    Args:
        patient_id (int): ID del paciente a notificar.
        session_id (int): ID de la nueva sesión creada.
    
    Note:
        Si el paciente no está conectado, la notificación se descarta silenciosamente.
        Utiliza asyncio.create_task para envío asíncrono sin bloquear.
    """
    if patient_id not in home_ws_connections:
        print(f"Paciente {patient_id} no está conectado a Home WS")
        return
    
    async def send_notification():
        try:
            websocket = home_ws_connections.get(patient_id)
            if websocket:
                await websocket.send_text(json.dumps({
                    "event": "new_session",
                    "sessionId": session_id
                }))
                print(f"✅ Notificación enviada al paciente {patient_id} para sesión {session_id}")
        except Exception as e:
            print(f"❌ Error notificando al paciente {patient_id}: {e}")
            home_ws_connections.pop(patient_id, None)
    
    # Crear una tarea en el event loop actual
    try:
        asyncio.create_task(send_notification())
    except RuntimeError as e:
        print(f"Error creando tarea async: {e}")
        # Fallback: intentar con asyncio.run() (menos ideal pero funciona)
        try:
            asyncio.run(send_notification())
        except Exception as e2:
            print(f"Error en fallback: {e2}")