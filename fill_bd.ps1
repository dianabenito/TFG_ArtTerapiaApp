
# Permitir ejecución de scripts solo para esta sesión
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process

# Activar entorno virtual
. .venv\Scripts\Activate.ps1

# Cambiar a la carpeta backend
cd backend

# Llenar la base de datos con datos de prueba
python fill_bd_testing.py

deactivate

cd ..
