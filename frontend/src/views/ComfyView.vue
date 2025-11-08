<script setup>
import { ref } from 'vue'
import { comfyService } from '../api/comfyService'

const API_URL = 'http://127.0.0.1:8000' // URL del backend
const prompt = ref({promptText: ''})
const result = ref(null)
const imageUrl = ref('')  // 🔹 nueva variable para la URL de la imagen
const isLoading = ref(false)

const generateImage = async () => {
  try {
    isLoading.value = true
    imageUrl.value = '' // Limpiar imagen anterior
    const response = await comfyService.createImage(prompt.value)
    if (response.file) {
      // Usar la URL del backend para servir la imagen
      // El backend monta /images que apunta a generated_images
      imageUrl.value = `${API_URL}/images/${response.file}`
      console.log('Image URL:', imageUrl.value) // Para debugging
    } else {
      console.error('No file path in response:', response)
    }
  } catch (err) {
    console.error('Error generating image:', err)
    alert('Error al generar la imagen: ' + (err.response?.data?.error || err.message))
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div>
    <h1>Generar imagen con ComfyUI</h1>
    <input v-model="prompt.promptText" type="text" placeholder="Describe tu imagen" />
    <button 
      @click="generateImage" 
      :disabled="isLoading"
      style="padding: 0.5rem 1rem;"
    >
      {{ isLoading ? 'Generando...' : 'Generar' }}
    </button>

    <div v-if="imageUrl">
      <h2>Imagen generada:</h2>
      <img :src="imageUrl" alt="Imagen generada" style="max-width: 100%; height: auto;" />
    </div>
  </div>
</template>