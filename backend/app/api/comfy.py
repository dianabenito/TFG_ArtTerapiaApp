from fastapi import APIRouter
import requests
import json
import app.schemas as schemas

router = APIRouter()

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
        return {"message": "Imagen generada correctamente", "response": response.json()}
    else:
        return {"error": "Error al generar la imagen", "status": response.status_code}
