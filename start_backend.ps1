# Ejecutar después de iniciar ComfyUI con python main.py --listen 0.0.0.0 --port 8188
# en C:\Users\diana\AppData\Local\Programs\ComfyUI for developers\ComfyUI

# Permitir ejecución de scripts solo para esta sesión
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process

# Activar entorno virtual
. .venv\Scripts\Activate.ps1

# Cambiar a la carpeta backend
cd backend

# Ejecutar el backend con Uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
