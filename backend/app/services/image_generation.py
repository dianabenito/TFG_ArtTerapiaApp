import random
import requests
import json
import time
import os
import shutil
from typing import Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pathlib import Path
from fastapi import HTTPException
import uuid

# Carpeta externa donde se generan las imágenes
CARPETA_ORIGEN = r"C:/Users/diana/AppData/Local/Programs/ComfyUI for developers/ComfyUI/output"

# Obtener la ruta base del proyecto (backend/)
BASE_DIR = Path(__file__).parent.parent.parent
# Carpeta de destino dentro del proyecto
CARPETA_DESTINO_GEN = BASE_DIR.parent / "frontend" / "src" / "assets" / "images" / "generated_images"
CARPETA_DESTINO_UPL = BASE_DIR.parent / "frontend" / "src" / "assets" / "images" / "uploaded_images"

# Ruta del workflow.json
WORKFLOW_PATH = BASE_DIR / "workflows" / "sdxl txt2img api workflow.json"

# URL de ComfyUI
COMFYUI_URL = "http://127.0.0.1:8188/prompt"

MAX_SQLITE_INT = 9223372036854775807

class ImagenHandler(FileSystemEventHandler):
    """Handler para detectar cuando se crea una nueva imagen en ComfyUI"""
    def __init__(self, prefijo):
        self.prefijo = prefijo
        self.archivo_encontrado = None

    def on_created(self, event):
        nombre = os.path.basename(event.src_path)
        if nombre.startswith(self.prefijo) and nombre.lower().endswith((".png", ".jpg", ".jpeg")):
            print(f"✅ Imagen detectada: {nombre}")
            origen = event.src_path

            # Esperar a que el archivo esté completamente escrito
            max_wait = 10  # segundos
            wait_time = 0.1
            elapsed = 0
            last_size = -1

            while elapsed < max_wait:
                current_size = os.path.getsize(origen)
                if current_size == last_size:
                    break  # el archivo dejó de crecer
                last_size = current_size
                time.sleep(wait_time)
                elapsed += wait_time

            # Asegurar que la carpeta de destino existe
            os.makedirs(str(CARPETA_DESTINO_GEN), exist_ok=True)
            destino = os.path.join(str(CARPETA_DESTINO_GEN), nombre)

            # Copiar la imagen
            shutil.copyfile(origen, destino)
            print(f"📂 Imagen copiada a: {destino}")
            self.archivo_encontrado = destino



def esperar_imagen(prefijo: str, timeout: int = 500) -> Optional[str]:
    """
    Espera a que se genere una imagen con el prefijo especificado.
    
    Args:
        prefijo: Prefijo del nombre de archivo a buscar
        timeout: Tiempo máximo de espera en segundos
    
    Returns:
        Ruta completa de la imagen generada o None si se agota el tiempo
    """
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


def generar_imagen(prompt_text: str) -> dict:
    """
    Genera una imagen usando ComfyUI basándose en el prompt proporcionado.
    
    Args:
        prompt_text: Texto del prompt para generar la imagen
    
    Returns:
        Diccionario con la información de la imagen generada
    
    Raises:
        HTTPException: Si hay un error al generar la imagen
    """
    # Cargar workflow base
    if not WORKFLOW_PATH.exists():
        raise HTTPException(
            status_code=500, 
            detail=f"Workflow file not found at {WORKFLOW_PATH}"
        )
    
    with open(WORKFLOW_PATH, "r") as f:
        workflow = json.load(f)

    seed = random.randint(0, MAX_SQLITE_INT)

    workflow["6"]["inputs"]["text"] = prompt_text
    workflow["3"]["inputs"]["seed"] = seed
    workflow["9"]["inputs"]["filename_prefix"] = "generated"

    # Enviar petición a ComfyUI
    payload = {"prompt": workflow}
    
    try:
        response = requests.post(COMFYUI_URL, json=payload, timeout=300)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=503,
            detail=f"Error al comunicarse con ComfyUI: {str(e)}"
        )

    # Esperar a que se genere la imagen
    ruta_imagen = esperar_imagen("generated")
    
    if ruta_imagen:
        nombre_archivo = os.path.basename(ruta_imagen)
        print(f"✅ Devolviendo ruta de imagen: assets/{nombre_archivo}")
        return {
            "message": "Imagen generada correctamente",
            "file": nombre_archivo,
            "fullPath": ruta_imagen,
            "seed": seed
        }
    else:
        raise HTTPException(
            status_code=408,
            detail="No se encontró la imagen generada. Tiempo de espera agotado."
        )


def publicar_imagen(upload_file):
    os.makedirs(str(CARPETA_DESTINO_UPL), exist_ok=True)

    # create unique filename to avoid collisions
    original_name = getattr(upload_file, 'filename', 'upload')
    ext = os.path.splitext(original_name)[1] or '.png'
    filename = f"uploaded_{uuid.uuid4().hex}{ext}"
    destino_path = CARPETA_DESTINO_UPL / filename

    # write file contents
    with open(destino_path, 'wb') as f:
        f.write(upload_file.file.read())

    return {"message": "Imagen subida correctamente", "file": filename, "fullPath": str(destino_path), "seed": None}