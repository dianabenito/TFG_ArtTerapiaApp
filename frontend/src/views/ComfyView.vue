<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { comfyService } from '../api/comfyService'

import { useRoute } from 'vue-router'
const API_URL = 'http://127.0.0.1:8000'
const route = useRoute()
const sessionId = Number(route.params.sessionId) // tomado de la ruta si está; será NaN si falta
const role = 'patient'

const prompt = ref({ promptText: '' })
const imageUrl = ref('')
const isLoading = ref(false)

let ws = null

onMounted(() => {
  const token = localStorage.getItem('token')
  if (!token) {
    console.warn('No token found; websocket will not connect')
    return
  }

  if (!Number.isFinite(sessionId)) {
    console.warn('sessionId no válido en la ruta; websocket no se conectará')
    return
  }

  // incluir token en query param para que el servidor lo valide
  ws = new WebSocket(`ws://127.0.0.1:8000/ws/${sessionId}/${role}?token=${token}`)

  ws.onopen = () => console.log('WS conectado como paciente')
  ws.onmessage = (ev) => {
    try {
      const obj = JSON.parse(ev.data)
      console.log('WS message (obj):', obj)
    } catch (e) {
      console.log('WS message:', ev.data)
    }
  }
  ws.onclose = () => console.log('WS cerrado')
})

onBeforeUnmount(() => ws?.close())

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
  if (!ws || ws.readyState !== WebSocket.OPEN) {
    console.warn('WebSocket no está abierto')
    return
  }
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
