from fastapi import APIRouter
import requests
import json
import app.schemas as schemas
import time
import os
import shutil
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

router = APIRouter()

# Carpeta externa donde se generan las imágenes
CARPETA_ORIGEN = r"C:/Users/diana/AppData/Local/Programs/ComfyUI for developers/ComfyUI/output"

# Carpeta de destino dentro del proyecto
CARPETA_DESTINO = r"C:/Users/diana/TFG/VSC/TFG_ArtTerapiaApp/frontend/src/assets"

class ImagenHandler(FileSystemEventHandler):
    def __init__(self, prefijo):
        self.prefijo = prefijo
        self.archivo_encontrado = None

    def on_created(self, event):
        nombre = os.path.basename(event.src_path)
        if nombre.startswith(self.prefijo) and nombre.lower().endswith((".png", ".jpg", ".jpeg")):
            print(f"✅ Imagen detectada: {nombre}")
            origen = event.src_path
            destino = os.path.join(CARPETA_DESTINO, nombre)
            # Copiar la imagen
            time.sleep(1)
            shutil.copyfile(origen, destino)
            print(f"📂 Imagen copiada a: {destino}")
            self.archivo_encontrado = destino

def esperar_imagen(prefijo, timeout=60):
    handler = ImagenHandler(prefijo)
    observer = Observer()
    observer.schedule(handler, CARPETA_ORIGEN, recursive=False)
    observer.start()

    print(f"⏳ Esperando imagen con prefijo '{prefijo}' en {CARPETA_ORIGEN}...")

    start_time = time.time()
    while time.time() - start_time < timeout:
        if handler.archivo_encontrado:
            observer.stop()
            observer.join()
            return handler.archivo_encontrado
        time.sleep(0.5)

    observer.stop()
    observer.join()
    print("❌ Tiempo de espera agotado.")
    return None


@router.post("/generate-image")
def generate_image(prompt: schemas.Prompt):

    # Cargar workflow base
    with open("workflow.json", "r") as f:
        workflow = json.load(f)

    workflow["2"]["inputs"]["text"] = prompt.promptText

    url = "http://127.0.0.1:8188/prompt"
    payload = {"prompt": workflow}

    response = requests.post(url, json=payload)

    if response.status_code == 200:
        ruta_imagen = esperar_imagen("simple_test")
        return {"message": "Imagen generada correctamente", "file": "simple_test"}
    else:
        return {"error": "Error al generar la imagen", "status": response.status_code}
