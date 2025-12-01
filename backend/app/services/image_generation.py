from fileinput import filename
import random
from urllib.parse import urlparse
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
from pathlib import Path

# Carpeta externa donde se generan las imágenes
CARPETA_ORIGEN = r"C:/Users/diana/AppData/Local/Programs/ComfyUI for developers/ComfyUI/output"

# Obtener la ruta base del proyecto (backend/)
BASE_DIR = Path(__file__).parent.parent.parent
# Carpeta de destino dentro del proyecto
CARPETA_DESTINO_GEN = BASE_DIR.parent / "frontend" / "src" / "assets" / "images" / "generated_images"
CARPETA_DESTINO_UPL = BASE_DIR.parent / "frontend" / "src" / "assets" / "images" / "uploaded_images"
CARPETA_TEMPLATES = BASE_DIR.parent / "frontend" / "src" / "assets" / "images" / "template_images"

CARPETA_COMFY_INPUT = Path(r"C:/Users/diana/AppData/Local/Programs/ComfyUI for developers/ComfyUI/input")

# Ruta del workflow.json
WORKFLOW_TXT2IMG_PATH = BASE_DIR / "workflows" / "sdxl txt2img api workflow.json"
WORKFLOW_IMG2IMG_PATH = BASE_DIR / "workflows" / "sdxl img2img api workflow.json"
WORKFLOW_MULTIMG2_PATH = BASE_DIR / "workflows" / "sdxl twoimgs2img api workflow.json"
WORKFLOW_MULTIMG3_PATH = BASE_DIR / "workflows" / "sdxl threeimgs2img api workflow.json"
WORKFLOW_MULTIMG4_PATH = BASE_DIR / "workflows" / "sdxl fourimgs2img api workflow.json"

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


def generar_imagen(prompt_text: str, prompt_seed: Optional[int] = None, input_img: Optional[str] = None) -> dict:
    """
    Genera una imagen usando ComfyUI basándose en el prompt proporcionado.
    
    Args:
        prompt_text: Texto del prompt para generar la imagen
    
    Returns:
        Diccionario con la información de la imagen generada
    
    Raises:
        HTTPException: Si hay un error al generar la imagen
    """
    
    if(input_img):
        with open(WORKFLOW_IMG2IMG_PATH, "r") as f:
            workflow = json.load(f)
    else:
        with open(WORKFLOW_TXT2IMG_PATH, "r") as f:
            workflow = json.load(f)

    if(prompt_seed):
        seed = prompt_seed
    else:
        seed = random.randint(0, MAX_SQLITE_INT)

    if(input_img):
        filename = input_img.rpartition('/')[-1]
        print(f"Using input image: {filename}")

        origin_path = BASE_DIR.parent / "frontend" / "src" / "assets" / urlparse(input_img).path.lstrip("/")

        print(f"Copying from {origin_path} to {CARPETA_COMFY_INPUT}")
        destino_path = CARPETA_COMFY_INPUT / filename
        shutil.copy(origin_path, destino_path)
            
        workflow["10"]["inputs"]["image"] = filename

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

def obtener_imagenes_plantilla():
    try:
        files = [
            f for f in os.listdir(CARPETA_TEMPLATES)
            if os.path.isfile(os.path.join(CARPETA_TEMPLATES, f))
        ]
        return {"images": files}
    except Exception as e:
        return {"error": str(e)}
    

def generate_image_by_mult_images(images: list, count: int) -> dict:
    """
    Genera una imagen usando ComfyUI basándose en el prompt proporcionado.
    
    Args:
        prompt_text: Texto del prompt para generar la imagen
    
    Returns:
        Diccionario con la información de la imagen generada
    
    Raises:
        HTTPException: Si hay un error al generar la imagen
    """
    imgs_idx = []

    if (count == 2):
        with open(WORKFLOW_MULTIMG2_PATH, "r", encoding="utf-8") as f:
            workflow = json.load(f)
        imgs_idx  = [1, 2]

    elif (count == 3):
        with open(WORKFLOW_MULTIMG3_PATH, "r", encoding="utf-8") as f:
            workflow = json.load(f)
        imgs_idx  = [1, 2, 5]

    elif (count == 4):
        with open(WORKFLOW_MULTIMG4_PATH, "r", encoding="utf-8") as f:
            workflow = json.load(f)
        imgs_idx  = [1, 2, 28, 29]
    

    for i in range(count):
        filename = images[i].fileName
        print(f"Using input image: {filename}")
        
        file_name = urlparse(images[i].fileName).path.lstrip("/")

        if "generated" in file_name.lower():
            folder = BASE_DIR.parent / "frontend" / "src" / "assets" / "images" / "generated_images"
        elif "uploaded" in file_name.lower():
            folder = BASE_DIR.parent / "frontend" / "src" / "assets" / "images" / "uploaded_images"
        else:
            folder = BASE_DIR.parent / "frontend" / "src" / "assets" / "images" / "template_images"

        origin_path = folder / file_name

        print(f"Copying from {origin_path} to {CARPETA_COMFY_INPUT}")
        destino_path = CARPETA_COMFY_INPUT / filename
        shutil.copy(origin_path, destino_path)
        
        workflow[f"{imgs_idx[i]}"]["inputs"]["image"] = filename

    seed = random.randint(0, MAX_SQLITE_INT)

    workflow["16"]["inputs"]["seed"] = seed
    workflow["17"]["inputs"]["filename_prefix"] = "generated"

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

def obtener_imagenes_plantilla():
    try:
        files = [
            f for f in os.listdir(CARPETA_TEMPLATES)
            if os.path.isfile(os.path.join(CARPETA_TEMPLATES, f))
        ]
        return {"images": files}
    except Exception as e:
        return {"error": str(e)}