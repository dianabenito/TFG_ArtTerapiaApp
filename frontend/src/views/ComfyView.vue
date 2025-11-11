<script setup>
import { ref, onMounted } from 'vue'
import { comfyService } from '../api/comfyService'

const API_URL = 'http://127.0.0.1:8000'
const sessionId = 1 // sesión activa
const role = 'patient'

const prompt = ref({promptText: ''})
const imageUrl = ref('')
const isLoading = ref(false)

let ws

onMounted(() => {
  // connect using the server route: /ws/{session_id}/{role}
  ws = new WebSocket(`ws://127.0.0.1:8000/ws/${sessionId}/${role}`)
})

const generateImage = async () => {
  try {
    isLoading.value = true
    imageUrl.value = ''
    const response = await comfyService.createImage(prompt.value)
    if (response.file) {
      imageUrl.value = `${API_URL}/images/${response.file}`
    }
  } finally {
    isLoading.value = false
  }
}

// Enviar la imagen al terapeuta
const submitImage = () => {
  if (!imageUrl.value) return
  ws.send(JSON.stringify({
    event: 'submit_image',
    fileName: imageUrl.value.split('/').pop()
  }))
}
</script>

<template>
  <div>
    <h1>Generar imagen con ComfyUI</h1>
    <input v-model="prompt.promptText" type="text" placeholder="Describe tu imagen" />
    <button @click="generateImage" :disabled="isLoading">
      {{ isLoading ? 'Generando...' : 'Generar' }}
    </button>

    <div v-if="imageUrl">
      <h2>Imagen generada:</h2>
      <img :src="imageUrl" alt="Imagen generada" style="max-width: 100%; height: auto;" />
      <button @click="submitImage" style="margin-top:1rem;">Enviar al terapeuta</button>
    </div>
  </div>
</template>
