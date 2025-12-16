<script>
import { comfyService } from '../api/comfyService'
import { userService } from '../api/userService'

export default {
  name: "CanvasBView",

  data() {
    return {
      drawing: false,
      ctx: null,
      color: "#000000",
      size: 5,
      mode: "draw",
      savedImage: null,
      showConfirmModal: false,
      promptText: '',
      modalLoading: false,
      sessionId: null,
    };
  },

  mounted() {
    const canvas = this.$refs.canvas;
    this.ctx = canvas.getContext("2d");

    // Fondo blanco para poder guardar
    this.ctx.fillStyle = "#FFFFFF";
    this.ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Capture sessionId from route params if present
    this.sessionId = Number(this.$route.params.sessionId)
    if (!Number.isFinite(this.sessionId)) {
      this.sessionId = null
    }
  },

  methods: {
    startDrawing(e) {
      this.drawing = true;
      this.ctx.beginPath();
      this.ctx.moveTo(e.offsetX, e.offsetY);
    },

    draw(e) {
      if (!this.drawing) return;

      this.ctx.lineWidth = this.size;
      this.ctx.lineCap = "round";

      if (this.mode === "draw") this.ctx.strokeStyle = this.color;
      else if (this.mode === "erase") this.ctx.strokeStyle = "#FFFFFF";

      this.ctx.lineTo(e.offsetX, e.offsetY);
      this.ctx.stroke();
    },

    stopDrawing() {
      this.drawing = false;
      this.ctx.closePath();
    },

    openConfirmModal() {
      this.showConfirmModal = true;
    },



    clearCanvas() {
      const canvas = this.$refs.canvas;
      this.ctx.fillStyle = "#FFFFFF";
      this.ctx.fillRect(0, 0, canvas.width, canvas.height);
    },

    setErase() {
      this.mode = "erase";
    },

    setDraw() {
      this.mode = "draw";
    },

    saveImage() {
      const canvas = this.$refs.canvas;
      this.savedImage = canvas.toDataURL("image/png");
      // Aquí puedes enviarlo a tu backend si lo quieres almacenar
    },
    async uploadSavedImage() {
      if (!this.savedImage) {
        alert('No hay dibujo guardado para subir.')
        return
      }
      // convert dataURL to blob
      const dataurl = this.savedImage
      const arr = dataurl.split(',')
      const mime = arr[0].match(/:(.*?);/)[1]
      const bstr = atob(arr[1])
      let n = bstr.length
      const u8arr = new Uint8Array(n)
      while (n--) {
        u8arr[n] = bstr.charCodeAt(n)
      }
      const blob = new Blob([u8arr], { type: mime })
      // create a file-like object
      const filename = `drawn_${Date.now()}.png`
      const file = new File([blob], filename, { type: mime })

      try {
        const active_user = await userService.getCurrentUser()
        const resp = await comfyService.uploadDrawnImage(file, active_user.id)
        // after upload, navigate back to Generation view preserving sessionId
        const fname = resp.file
        
        // Preserve session context when navigating back
        if (this.sessionId) {
          this.$router.push({ 
            path: `/session/${this.sessionId}/patient`, 
            query: { image: fname } 
          })
        } else {
          this.$router.push({ path: '/generation/', query: { image: fname } })
        }
      } catch (e) {
        const detail = e?.response?.data?.detail || e?.message || String(e)
        console.error('Error uploading drawn image', e)
        alert('Error subiendo el dibujo: ' + detail)
      }
    },

    async modalConfirm() {
      if (this.modalLoading) return
      this.modalLoading = true
      localStorage.setItem('prompt', this.promptText)
      await this.saveImage()
      await this.uploadSavedImage()
      this.modalLoading = false
      this.showConfirmModal = false
    },
  },
};
</script>

<template>
  <div class="canvas-wrapper">
    <h2>Editor de dibujo</h2>
    
    <div v-if="sessionId" style="background: #e3f2fd; padding: 0.5rem; border-radius: 4px; margin-bottom: 1rem;">
      <strong>Sesión activa ID: {{ sessionId }}</strong>
    </div>

    <!-- Controles -->
    <div class="controls">
      <label>
        Color:
        <input type="color" v-model="color">
      </label>

      <label>
        Grosor:
        <input type="range" v-model="size" min="1" max="40" />
        {{ size }} px
      </label>

      <button @click="setErase">Borrar</button>
      <button @click="setDraw">Dibujar</button>
      <button @click="clearCanvas">Limpiar</button>
    </div>

    <!-- Lienzo -->
    <canvas
      ref="canvas"
      width="500"
      height="500"
      class="drawing-canvas"
      @mousedown="startDrawing"
      @mousemove="draw"
      @mouseup="stopDrawing"
      @mouseleave="stopDrawing"
    ></canvas>

    <button @click="openConfirmModal()">Transformar esbozo</button>
    
    <!-- Refine Modal -->
    <div v-if="showConfirmModal" class="modal-overlay" style="position:fixed;left:0;top:0;right:0;bottom:0;background:rgba(0,0,0,0.5);display:flex;align-items:center;justify-content:center;z-index:50;">
      <div class="modal" style="background:white;padding:1rem;max-width:760px;width:100%;border-radius:6px;">
        <div>
          <label>Prompt:</label>
          <input v-model="promptText" type="text" style="width:100%;" />
        </div>
          <button @click="modalConfirm" :disabled="!promptText || modalLoading" style="margin-left:.5rem;">Confirmar</button>
        </div>
    </div>

  </div>
</template>


<style scoped>
.canvas-wrapper {
  display: flex;
  flex-direction: column;
  gap: 15px;
  width: 100%;
  align-items: center;
}

.controls {
  display: flex;
  gap: 20px;
  align-items: center;
}

.drawing-canvas {
  border: 2px solid #555;
  border-radius: 8px;
  background: white;
  cursor: crosshair;
}

.saved-img img {
  border: 2px solid #333;
  margin-top: 10px;
  max-width: 500px;
}

/* Modal sizing: limit height and allow scrolling for large images */
.modal {
  max-height: 80vh;
  overflow: auto;
  color: #000; /* Texto negro por defecto en modal */
}

.modal div {
  color: #000; /* Asegura que todo el texto en divs sea negro */
}

.modal label {
  color: #000; /* Labels negros */
}

.modal input {
  color: #000; /* Input text negra */
}

.modal img {
  max-width: 100%;
  height: auto;
  max-height: 70vh;
  object-fit: contain;
  display: block;
  margin: 0 auto;
}
</style>
