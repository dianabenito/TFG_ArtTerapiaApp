<script setup>
import { ref } from 'vue'
import { comfyService } from '../api/comfyService'

const prompt = ref({promptText: ''})
const result = ref(null)
const imageUrl = ref('')  // 🔹 nueva variable para la URL de la imagen

const generateImage = async () => {
  try {
    const response = await comfyService.createImage(prompt.value)
    if (response.file) {
      // La ruta ya viene como assets/nombre_archivo.png
      imageUrl.value = `http://127.0.0.1:8000/${response.file}`
      console.log('Image URL:', imageUrl.value) // Para debugging
    } else {
      console.error('No file path in response:', response)
    }
  } catch (err) {
    console.error('Error generating image:', err)
  } 
}
</script>

<template>
  <div>
    <h1>Generar imagen con ComfyUI</h1>
    <input v-model="prompt.promptText" type="text" placeholder="Describe tu imagen" />
    <button @click="generateImage">Generar</button>

    <div v-if="imageUrl">
      <h2>Imagen generada:</h2>
      <img :src="imageUrl" alt="Imagen generada" style="max-width: 100%; height: auto;" />
    </div>
  </div>
</template>