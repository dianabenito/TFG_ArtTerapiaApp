<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'

import { useRoute } from 'vue-router'
const API_URL = 'http://127.0.0.1:8000'
const route = useRoute()
const sessionId = Number(route.params.sessionId) // será NaN si no hay sessionId en la ruta
const role = 'therapist'

const message = ref('Esperando paciente...')
const latestImage = ref('')
let socket = null

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

  socket = new WebSocket(`ws://127.0.0.1:8000/ws/${sessionId}/${role}?token=${token}`)

  socket.onopen = () => console.log('Conectado al WS como terapeuta')

  socket.onmessage = (event) => {
    const raw = event.data
    console.log('Mensaje recibido:', raw)

    // intentar parsear como JSON (caso en que el cliente envía {event, fileName})
    try {
      const obj = JSON.parse(raw)
      if (obj && obj.event === 'submit_image' && obj.fileName) {
        latestImage.value = `${API_URL}/images/${obj.fileName}`
        message.value = 'Nueva imagen enviada por el paciente:'
        return
      }
    } catch (e) {
      // no es JSON, seguir con formatos legacy
    }

    const data = String(raw)
    if (data === 'user_is_generating') {
      message.value = 'El paciente está generando una imagen...'
    } else if (data.startsWith('new_image:')) {
      const filename = data.split(':')[1]
      latestImage.value = `${API_URL}/images/${filename}`
      message.value = 'Nueva imagen enviada por el paciente:'
    }
  }

  socket.onclose = () => console.log('WS cerrado')
})

onBeforeUnmount(() => socket?.close())
</script>

<template>
  <div>
    <h1>Vista del Terapeuta</h1>
    <p>{{ message }}</p>

    <div v-if="latestImage">
      <img :src="latestImage" alt="Imagen del paciente" style="max-width: 100%;" />
    </div>
  </div>
</template>
