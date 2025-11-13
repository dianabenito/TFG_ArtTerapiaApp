<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { userService } from '../api/userService.js'

const API_URL = 'http://127.0.0.1:8000'
const route = useRoute()
const router = useRouter()
const sessionId = Number(route.params.sessionId) // será NaN si no hay sessionId en la ruta
const role = 'therapist'

const message = ref('Esperando paciente...')
const latestImage = ref('')
const sessionInfo = ref(null)
let socket = null

const connectSocket = () => {
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
    } else if (data === 'session_ended') {
      message.value = 'La sesión ha sido finalizada.'
      // cerrar socket local si sigue abierto
      socket?.close()
    } else if (data.startsWith('new_image:')) {
      const filename = data.split(':')[1]
      latestImage.value = `${API_URL}/images/${filename}`
      message.value = 'Nueva imagen enviada por el paciente:'
    }
  }

  socket.onclose = () => console.log('WS cerrado')
}

// On mount: fetch session info first, then connect the websocket if session not ended
onMounted(async () => {
  if (!Number.isFinite(sessionId)) return
  try {
    sessionInfo.value = await userService.getSession(sessionId)
    if (sessionInfo.value?.ended_at) {
      message.value = 'La sesión está finalizada.'
      return
    }
  } catch (err) {
    console.warn('No se pudo obtener la sesión:', err)
  }
  connectSocket()
})

onBeforeUnmount(() => socket?.close())

const confirmEnd = async () => {
  if (!Number.isFinite(sessionId)) {
    alert('Session ID inválido')
    return
  }
  const ok = confirm('¿Confirmas que quieres finalizar la sesión? Esta acción la terminará para ambos participantes.')
  if (!ok) return

  try {
    await userService.endSession(sessionId)
    // cerrar websocket y redirigir
    socket?.close()
    alert('Sesión finalizada correctamente')
    router.push('/home')
  } catch (err) {
    console.error(err)
    alert('Error finalizando la sesión')
  }
}

// (fetch moved into single onMounted above)
</script>

<template>
  <div>
    <h1>Vista del Terapeuta</h1>

    <div v-if="sessionInfo">
      <p><strong>Sesión ID:</strong> {{ sessionInfo.id }}</p>
      <p><strong>Estado:</strong> {{ sessionInfo.ended_at ? 'Finalizada' : 'Activa' }}</p>
    </div>

    <p>{{ message }}</p>

    <div v-if="latestImage">
      <img :src="latestImage" alt="Imagen del paciente" style="max-width: 100%;" />
    </div>

    <div v-if="!sessionInfo?.ended_at" style="margin-top: 1rem;">
      <button @click="confirmEnd">Finalizar sesión</button>
    </div>
  </div>
</template>
