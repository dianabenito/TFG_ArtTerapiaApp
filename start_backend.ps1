# Permitir ejecución de scripts solo para esta sesión
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process

# Activar entorno virtual
. .venv\Scripts\Activate.ps1

# Cambiar a la carpeta backend
cd backend

# Ejecutar el backend con Uvicorn
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
