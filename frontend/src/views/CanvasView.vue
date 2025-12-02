<script>
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
    };
  },

  mounted() {
    const canvas = this.$refs.canvas;
    this.ctx = canvas.getContext("2d");

    // Fondo blanco para poder guardar
    this.ctx.fillStyle = "#FFFFFF";
    this.ctx.fillRect(0, 0, canvas.width, canvas.height);
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
  },
};
</script>

<template>
  <div class="canvas-wrapper">
    <h2>Editor de dibujo</h2>

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
      <button @click="saveImage">Guardar imagen</button>
    </div>

    <!-- Lienzo -->
    <canvas
      ref="canvas"
      width="800"
      height="500"
      class="drawing-canvas"
      @mousedown="startDrawing"
      @mousemove="draw"
      @mouseup="stopDrawing"
      @mouseleave="stopDrawing"
    ></canvas>

    <!-- Resultado guardado -->
    <div v-if="savedImage" class="saved-img">
      <h3>Imagen guardada:</h3>
      <img :src="savedImage" alt="drawing result">
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
  max-width: 800px;
}
</style>
