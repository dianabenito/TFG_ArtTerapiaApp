<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { userService } from '../api/userService.js'
import { sessionsService } from '../api/sessionsService.js'

const API_URL = 'http://127.0.0.1:8000'
const route = useRoute()
const router = useRouter()
const sessionId = Number(route.params.sessionId)
const role = 'therapist'

const message = ref('Esperando paciente...')
const latestImage = ref('')
const sessionInfo = ref(null)
const chatMessages = ref([])       // ← mensajes del chat
const newChatMessage = ref('')     // ← input del chat
let socket = null

const connectSocket = () => {
  const token = localStorage.getItem('token')
  if (!token) return

  if (!Number.isFinite(sessionId)) return

  socket = new WebSocket(`ws://127.0.0.1:8000/ws/${sessionId}/${role}?token=${token}`)

  socket.onopen = () => console.log('Conectado al WS como terapeuta')

  socket.onmessage = (event) => {
    const raw = event.data
    try {
      const obj = JSON.parse(raw)
      if (obj.event === 'submit_image' && obj.fileName) {
        const mount = obj.fileName.includes('generated') ? 'generated_images' : 'uploaded_images'
        latestImage.value = `${API_URL}/images/${mount}/${obj.fileName}`
        message.value = 'Nueva imagen enviada por el paciente:'
      } else if (obj.event === 'chat_message') {
        chatMessages.value.push({ sender: obj.sender, text: obj.text })
      }
    } catch (e) {
      const data = String(raw)
      if (data === 'user_is_generating') {
        message.value = 'El paciente está generando una imagen...'
      } else if (data === 'session_ended') {
        message.value = 'La sesión ha sido finalizada.'
        socket?.close()
      } else if (data.startsWith('new_image:')) {
        const filename = data.split(':')[1]
        latestImage.value = `${API_URL}/images/${filename}`
        message.value = 'Nueva imagen enviada por el paciente:'
      }
    }
  }

  socket.onclose = () => console.log('WS cerrado')
}

const sendChatMessage = () => {
  if (!newChatMessage.value || !socket || socket.readyState !== WebSocket.OPEN) return
  const msg = { event: 'chat_message', sender: role, text: newChatMessage.value }
  socket.send(JSON.stringify(msg))
  chatMessages.value.push(msg)   // reflejar localmente
  newChatMessage.value = ''
}

onMounted(async () => {
  if (!Number.isFinite(sessionId)) return
  try {
    sessionInfo.value = await sessionsService.getSession(sessionId)
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
  if (!Number.isFinite(sessionId)) return
  const ok = confirm('¿Confirmas que quieres finalizar la sesión? Esta acción la terminará para ambos participantes.')
  if (!ok) return

  try {
    await sessionsService.endSession(sessionId)
    socket?.close()
    alert('Sesión finalizada correctamente')
    router.push('/home')
  } catch (err) {
    console.error(err)
    alert('Error finalizando la sesión')
  }
}
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

    <!-- Chat -->
    <div v-if="!sessionInfo?.ended_at" class="chat-container" style="margin-top:1rem;">
      <div class="chat-messages" style="max-height:200px; overflow-y:auto; border:1px solid #ccc; padding:0.5rem; margin-bottom:0.5rem;">
        <div v-for="(msg, i) in chatMessages" :key="i" :style="{ textAlign: msg.sender === role ? 'right' : 'left' }">
          <strong>{{ msg.sender }}:</strong> {{ msg.text }}
        </div>
      </div>
      <input v-model="newChatMessage" @keyup.enter="sendChatMessage" placeholder="Escribe un mensaje..." style="width:70%" />
      <button @click="sendChatMessage" style="width:25%">Enviar</button>
    </div>

    <div v-if="!sessionInfo?.ended_at" style="margin-top: 1rem;">
      <button @click="confirmEnd">Finalizar sesión</button>
    </div>
  </div>
</template>
