# Permitir ejecución de scripts solo para esta sesión
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process

# Activar entorno virtual
. .venv\Scripts\Activate.ps1

# Cambiar a la carpeta frontend
cd frontend

# Ejecutar el backend con Uvicorn
npm run dev -- --host 0.0.0.0