# ComfyMind — Manual d'Instal·lació i Execució

Aquest manual explica com instal·lar i executar tots els serveis: ComfyUI, backend (FastAPI) i frontend (Vue), en Windows amb PowerShell.

## Prerequisits
- Windows 10/11 amb PowerShell
- Python 3.11+ i `pip`
- Node.js 18+ i `npm`
- Git
- Targeta gràfica NVIDIA amb CUDA (opcional, per acceleració; si no, es pot usar CPU)

## ComfyUI — Instal·lació i Execució

**Important:** ComfyUI s'ha d'instal·lar en una ubicació separada (no dins del projecte).

1. Obre PowerShell i posiciona't on vulguis instal·lar ComfyUI:
   ```powershell
   cd "C:\ruta\desitjada"
   ```

2. Clona el repositori oficial de ComfyUI:
   ```powershell
   git clone https://github.com/comfyanonymous/ComfyUI.git
   cd ComfyUI
   ```

3. Crea i activa l'entorn virtual de ComfyUI:
   ```powershell
   python -m venv .venv
   . .venv\Scripts\Activate.ps1
   ```

4. Instal·la les dependències:
   ```powershell
   pip install -r requirements.txt
   ```

5. **(Opcional) Si tens GPU NVIDIA amb CUDA i hi ha errors amb PyTorch**, reinstal·la amb el repositori CUDA 12.1:
   ```powershell
   pip uninstall torch torchvision torchaudio -y
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
   ```

6. **Executa ComfyUI** (en una finestra separada de PowerShell):
   ```powershell
   . .venv\Scripts\Activate.ps1
   python main.py --listen 0.0.0.0 --port 8188
   ```
   - Interfície disponible a: `http://127.0.0.1:8188`

---

## Preparació del projecte (un sol cop)

1. **Clona el repositori del projecte:**
   ```powershell
   git clone <URL_DEL_REPOSITORI>
   cd TFG_ArtTerapiaApp\ -\ copia
   ```

2. **Crea i activa l'entorn virtual de Python:**
   ```powershell
   python -m venv .venv
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
   . .venv\Scripts\Activate.ps1
   ```

3. **Instal·la les dependències del backend:**
   
   Opció A (recomanat) — des del fitxer `requirements.txt`:
   ```powershell
   pip install -r requirements.txt
   ```
   
   Opció B — instal·lació explícita:
   ```powershell
   pip install fastapi "uvicorn[standard]" SQLAlchemy "pydantic>=2.0" "passlib[bcrypt]" python-jose requests httpx aiofiles python-multipart email-validator watchdog bcrypt translate Pillow
   ```
   
   (Opcional, per a proves): 
   ```powershell
   pip install pytest pytest-asyncio anyio
   ```

4. **Instal·la les dependències del frontend:**
   ```powershell
   cd frontend
   npm install
   cd ..
   ```
   
   Això llegeix `package.json` i descarrega tots els paquets necessaris (`axios`, `vue-router`, `pinia`, `@fullcalendar/vue3`, `tailwindcss`, etc.).

## Configuració de variables d'entorn

El projecte té dos fitxers de configuració separats:

### Backend (carpeta root)
Copia el fitxer d'exemple:
```powershell
copy .env.example .env
```

Edita `.env` i ajusta les rutes segons la teva instal·lació de ComfyUI. Exemple:
```bash
SECRET_KEY=supersecretkey123456789
COMFY_UI_URL=http://localhost:8188
COMFY_OUTPUT_DIR=C:/Users/YOUR_USERNAME/AppData/Local/Programs/ComfyUI for developers/ComfyUI/output
COMFY_INPUT_DIR=C:/Users/YOUR_USERNAME/AppData/Local/Programs/ComfyUI for developers/ComfyUI/input
```

**Important:**
- **En producció:** genera una clau `SECRET_KEY` més segura.
- **COMFY_OUTPUT_DIR i COMFY_INPUT_DIR:** han de coincidir amb la ubicació real on tens instal·lat ComfyUI.

### Frontend (carpeta frontend)
Copia el fitxer d'exemple:
```powershell
copy .env.example .env
```

Edita `frontend/.env` si cal. Exemple:
```bash
VITE_API_URL=http://127.0.0.1:8000
```

Si no es configura, per defecte usa `http://localhost:8000`. Per accedir en xarxa local (WiFi), substitueix `127.0.0.1` o `localhost` per la IP local del ordinador.

## Execució

### 1) Iniciar ComfyUI (REQUERIT — primer pas)

**En una finestra NOVA de PowerShell**, assegura't que tens activat l'entorn virtual de ComfyUI i executa:

```powershell
cd "C:\ruta\a\ComfyUI"
. .venv\Scripts\Activate.ps1
python main.py --listen 0.0.0.0 --port 8188
```

✅ ComfyUI estará disponible a: `http://127.0.0.1:8188`

⚠️ **ComfyUI ha de estar en marxa SEMPRE antes de llançar el backend.**

### 2) Arrencar el backend

En una finestra diferent de PowerShell, a l'arrel del projecte:

**Opció A — Utilitzar l'script:**
```powershell
powershell -ExecutionPolicy Bypass -File .\start_backend.ps1
```

**Opció B — Execució manual:**
```powershell
. .venv\Scripts\Activate.ps1
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

✅ Backend disponible a: `http://localhost:8000`
✅ Documentació API: `http://localhost:8000/docs`
✅ Base de dades: `artTerapia_app.db` es crea automàticament a l'arrel.

### 3) Arrencar el frontend

En una altra finestra de PowerShell:

**Opció A — Utilitzar l'script:**
```powershell
powershell -ExecutionPolicy Bypass -File .\start_frontend.ps1
```

**Opció B — Execució manual:**
```powershell
cd frontend
npm run dev -- --host 0.0.0.0
```

✅ Frontend disponible a: `http://localhost:5173`

---

## Ordre d'arrencada correcta

1. ✅ **ComfyUI** (finestra 1)
2. ✅ **Backend** (finestra 2)
3. ✅ **Frontend** (finestra 3)

**No comencis el backend si ComfyUI no està en marxa.**

## Troubleshooting — Problemes comuns

| Problema | Solució |
|----------|---------|
| PowerShell bloqueja scripts | Usa `-ExecutionPolicy Bypass` o executa com a administrador |
| Port 8000 ja està ocupat | Canvia `--port 8001` a Uvicorn |
| Port 5173 ja està ocupat | Configura el port a Vite (`vite.config.js`) |
| Backend no pot connectar a ComfyUI | Assegura que ComfyUI está ejecutant-se a `http://localhost:8188` |
| Frontend no pot connectar al backend | Verifica que `.env` té la URL correcta (`VITE_API_URL=http://localhost:8000`) |
| Errors de PyTorch en GPU NVIDIA | Reinstal·la amb CUDA 12.1 (veure secció ComfyUI, pas 5) |
| Base de dades no es crea | La base de dades SQLite es crea automàticament a la primera execució del backend |

---

## Recursos addicionals

- **FastAPI Docs**: http://localhost:8000/docs
- **ComfyUI**: https://github.com/comfyanonymous/ComfyUI
- **Vue.js**: https://vuejs.org
- **Vite**: https://vitejs.dev
