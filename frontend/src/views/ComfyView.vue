<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { comfyService } from '../api/comfyService'
import { userService } from '../api/userService.js'

import { useRoute, useRouter } from 'vue-router'
import { showToast } from '../stores/toastStore.js'
const API_URL = 'http://127.0.0.1:8000'
const route = useRoute()
const router = useRouter()
const sessionId = Number(route.params.sessionId) // tomado de la ruta si está; será NaN si falta
const role = 'patient'

const prompt = ref({ promptText: '' })
const imageUrl = ref('')
const seedLastImg = ref(null)
const uploadFile = ref(null)
const active_user = ref(null)
const isLoading = ref(false)
const sessionInfo = ref(null)

let ws = null

const connectWs = () => {
  const token = localStorage.getItem('token')
  if (!token) {
    console.warn('No token found; websocket will not connect')
    return
  }

  if (!Number.isFinite(sessionId)) {
    console.warn('sessionId no válido en la ruta; websocket no se conectará')
    return
  }

  // no conectar si sesión ya finalizada
  if (sessionInfo.value?.ended_at) {
    console.warn('La sesión ya está finalizada; no se conectará al websocket')
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
      // manejar mensaje plain text
      const txt = String(ev.data)
      if (txt === 'session_ended') {
        // actualizar estado local
        sessionInfo.value = { ...sessionInfo.value, ended_at: new Date().toISOString() }
        ws?.close()
        // redirigir al paciente a Home
        try {
          alert('La sesión ha sido finalizada por el terapeuta.')
          router.push('/home')
        } catch (e) {
          console.warn('No se pudo redirigir tras finalización de sesión:', e)
        }
        return
      }
      console.log('WS message:', ev.data)
    }
  }
  ws.onclose = () => console.log('WS cerrado')
}

onMounted(async () => {
  // obtener info de sesión
  if (Number.isFinite(sessionId)) {
    try {
      sessionInfo.value = await userService.getSession(sessionId)
      // si la sesión ya está finalizada, mostrar alerta y redirigir al home
      if (sessionInfo.value?.ended_at) {
        try {
          alert('La sesión ha sido finalizada por el terapeuta.')
          router.push('/home')
          return
        } catch (e) {
          console.warn('No se pudo redirigir tras detectar sesión finalizada:', e)
        }
      }
    } catch (err) {
      console.warn('No se pudo obtener la sesión:', err)
    }
  }

  connectWs()
})

onBeforeUnmount(() => ws?.close())

const generateImage = async () => {
  try {
    isLoading.value = true
    imageUrl.value = ''

    // DESCOMENTAR ESTO PARA USAR USUARIO ACTIVO
    // active_user.value = await userService.getCurrentUser()
    // const response = await comfyService.createImage(prompt.value, active_user.value.id)
    
    // Y COMENTAR ESTA
    const response = await comfyService.createImage(prompt.value, 2)
    console.log('Imagen generada:', response)

    if (response.file) {
      imageUrl.value = `${API_URL}/images/generated_images/${response.file}`
      seedLastImg.value = response.seed
    }
  } finally {
    isLoading.value = false
  }
}

const onFileChange = (ev) => {
  const f = ev.target.files && ev.target.files[0]
  if (f) uploadFile.value = f
}

const uploadUserImage = async () => {
  if (!uploadFile.value) return showToast('Selecciona una imagen primero', { type: 'warning' })
  try {
    isLoading.value = true
    const resp = await comfyService.uploadImage(uploadFile.value, 2)
    console.log('Imagen subida:', resp)
    if (resp.file) {
      imageUrl.value = `${API_URL}/images/uploaded_images/${resp.file}`
      seedLastImg.value = resp.seed
      showToast('Imagen subida correctamente', { type: 'success' })
      uploadFile.value = null
    }
  } catch (e) {
    showToast('Error subiendo imagen', { type: 'error' })
    console.error(e)
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
  // mostrar confirmación de envío al usuario
  try {
    showToast('Imagen enviada correctamente', { type: 'success', duration: 2200 })
  } catch (e) {
    console.warn('No se pudo mostrar toast tras enviar la imagen:', e)
  }
}
</script>

<template>
  <div>
    <h1>Generar imagen con ComfyUI</h1>

    <div v-if="sessionInfo">
      <p><strong>Sesión ID:</strong> {{ sessionInfo.id }}</p>
      <p><strong>Estado:</strong> {{ sessionInfo.ended_at ? 'Finalizada' : 'Activa' }}</p>
    </div>
    <input v-model="prompt.promptText" type="text" placeholder="Describe tu imagen" />
    <button @click="generateImage" :disabled="isLoading">
      {{ isLoading ? 'Generando...' : 'Generar' }}
    </button>

    <!-- Upload from gallery -->
    <div style="margin-top:1rem;">
      <label for="fileInput">Subir imagen desde galería:</label>
      <input id="fileInput" type="file" accept="image/*" @change="onFileChange" />
      <button @click="uploadUserImage" :disabled="isLoading || !uploadFile" style="margin-left:0.5rem;">
        {{'Subir imagen' }}
      </button>
      <div v-if="uploadFile" style="margin-top:.5rem; font-size:.9rem; color:#444;">Seleccionado: {{ uploadFile.name || uploadFile.filename }}</div>
    </div>

    <div v-if="imageUrl">
      <h2>Imagen generada:</h2>
      <img :src="imageUrl" alt="Imagen generada" style="max-width: 100%; height: auto;" />
      <button @click="submitImage" style="margin-top:1rem;">Enviar al terapeuta</button>
      <div v-if="imageUrl && seedLastImg">Seed: {{ seedLastImg }}</div>
    </div>
  </div>
</template>
