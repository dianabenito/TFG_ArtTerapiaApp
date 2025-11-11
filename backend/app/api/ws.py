from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict

router = APIRouter()

# 🔹 Diccionario que mantiene las conexiones activas por sesión
active_sessions: Dict[int, Dict[str, WebSocket]] = {}

@router.websocket("/ws/{session_id}/{role}")
async def websocket_endpoint(websocket: WebSocket, session_id: int, role: str):
    """
    WebSocket para comunicación paciente-terapeuta.
    - session_id: ID de la sesión compartida.
    - role: 'patient' o 'therapist'
    """
    await websocket.accept()

    if session_id not in active_sessions:
        active_sessions[session_id] = {}

    active_sessions[session_id][role] = websocket
    print(f"🟢 {role} conectado en sesión {session_id}")

    try:
        while True:
            data = await websocket.receive_text()
            other_role = "therapist" if role == "patient" else "patient"
            if other_role in active_sessions[session_id]:
                await active_sessions[session_id][other_role].send_text(data)
    except WebSocketDisconnect:
        print(f"🔴 {role} desconectado de la sesión {session_id}")
        del active_sessions[session_id][role]
        if not active_sessions[session_id]:
            del active_sessions[session_id]
