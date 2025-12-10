<script setup>
import { ref, onMounted, onBeforeUnmount, computed } from 'vue'
import { comfyService } from '../api/comfyService'
import { userService } from '../api/userService.js'
import { sessionsService } from '../api/sessionsService.js'

import { useRoute, useRouter } from 'vue-router'
import { showToast } from '../stores/toastStore.js'
const API_URL = 'http://127.0.0.1:8000'
const route = useRoute()
const router = useRouter()
const sessionId = Number(route.params.sessionId) // tomado de la ruta si está; será NaN si falta

const chatMessages = ref([])       
const newChatMessage = ref('')     
const role = 'patient'

const prompt = ref({ promptText: '', seed: null, inputImage: null })
const sketchPrompt = ref({ sketchImage: '' })
const imageUrl = ref('')
const tempImageUrl = ref('')
const seedLastImg = ref(null)
const uploadFile = ref(null)
const active_user = ref(null)
const isLoading = ref(false)
const sessionInfo = ref(null)
const inputImage = ref(null)
const isLoadingGallery = ref(true)
const galleryImages = ref({
  templates: [],
  generated: [],
  uploaded: []
})

const combinedGallery = computed(() => {
  const t = galleryImages.value.templates ?? []
  const g = galleryImages.value.generated ?? []
  const u = galleryImages.value.uploaded ?? []
  return [...t, ...g, ...u]
})

const multiSelectMode = ref(false)            // si estamos en modo selección múltiple
const selectedImages = ref([])                // array de imágenes seleccionadas
const minMultiSelect = 2
const maxMultiSelect = 4

const showGallery = ref(false)

// Refine modal state
const showRefineModal = ref(false)
const showImagesModal = ref(false)
const showDrawModal = ref(false)
const modalLoading = ref(false)

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
      if (obj.event === 'chat_message') {
        chatMessages.value.push({ sender: obj.sender, text: obj.text })
        return
      }
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
      sessionInfo.value = await sessionsService.getSession(sessionId)
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
  await loadGallery()
  // If navigated from Canvas with a drawn image, show it
  const drawn = route.query.image
  if (drawn) {
    // drawn images are saved under drawn_images
    showDrawModal.value = true 
    tempImageUrl.value = `${API_URL}/images/drawn_images/${drawn}`
    prompt.value.promptText = localStorage.getItem('prompt')
    localStorage.removeItem('prompt')
    await createFromSketch(tempImageUrl.value)
    // refresh gallery to include it (in case DB record exists)
    try { await loadGallery() } catch (e) { /* ignore */ }
    
    // Remove 'image' query param to avoid loop
    router.replace({ query: {} })
  }
})

onBeforeUnmount(() => ws?.close())

const sendChatMessage = () => {
  if (!newChatMessage.value || !ws || ws.readyState !== WebSocket.OPEN) return
  const msg = { event: 'chat_message', sender: role, text: newChatMessage.value }
  ws.send(JSON.stringify(msg))
  chatMessages.value.push(msg)  // reflejar mensaje localmente
  newChatMessage.value = ''
}

const generateImage = async (last_seed = null, inputImage = null) => {
  try {
    isLoading.value = true
    tempImageUrl.value = ''

    // Only accept numeric seeds; ignore click events or other objects
    if (typeof last_seed === 'number') {
      prompt.value.seed = last_seed
    } else {
      prompt.value.seed = null
    }

    console.log(inputImage)

    if(inputImage) {
      prompt.value.inputImage = inputImage
    } else {
      prompt.value.inputImage = null
    }

    // DESCOMENTAR ESTO PARA USAR USUARIO ACTIVO
    active_user.value = await userService.getCurrentUser()
    const response = await comfyService.createImage(prompt.value, active_user.value.id)
    

    if (response.file) {
      tempImageUrl.value = `${API_URL}/images/generated_images/${response.file}`
      console.log('Modal image URL:', prompt)
      seedLastImg.value = response.seed
      // Refresh gallery to include the newly generated image
      try {
        await loadGallery()
      } catch (e) {
        console.warn('No se pudo recargar la galería tras generar imagen:', e)
      }
    }
  } catch (e) {
    // show server-side validation errors if any
    const detail = e?.response?.data?.detail || e?.message || String(e)
    showToast('Error generando imagen: ' + detail, { type: 'error' })
    console.error('Error generating image:', e)
  } finally {
    isLoading.value = false
  }
}

const createFromSketch = async(inputImage) => {
  try {
    isLoading.value = true
    tempImageUrl.value = ''
    
    sketchPrompt.value.sketchText = prompt.value.promptText
    sketchPrompt.value.sketchImage = inputImage

    active_user.value = await userService.getCurrentUser()
    const response = await comfyService.convertirBoceto(sketchPrompt.value, active_user.value.id)
    console.log('Imagen generada:', response)

    if (response.file) {
      tempImageUrl.value = `${API_URL}/images/generated_images/${response.file}`
      console.log('Modal image URL:', prompt)
      seedLastImg.value = response.seed
      // Refresh gallery to include the newly generated image
      try {
        await loadGallery()
      } catch (e) {
        console.warn('No se pudo recargar la galería tras generar imagen:', e)
      }
    }
  } catch (e) {
    // show server-side validation errors if any
    const detail = e?.response?.data?.detail || e?.message || String(e)
    showToast('Error generando imagen: ' + detail, { type: 'error' })
    console.error('Error generating image:', e)
  } finally {
    isLoading.value = false
  }
}

// Open refine modal: generate initial image and allow regenerations with same seed
const openRefineModal = async () => {
  showRefineModal.value = true
  prompt.value.seed = null
  modalLoading.value = false
}

const modalRegenerate = async () => {
  if (!showRefineModal.value) return
  try {
    modalLoading.value = true
    // keep the same seed if present (pass the primitive value, not the ref)
    const seedToUse = prompt.value.seed ?? null

    active_user.value = await userService.getCurrentUser()
    const resp = await comfyService.createImage({ promptText: prompt.value.promptText, seed: seedToUse }, active_user.value.id)
    console.log('Modal regenerate:', resp)
    if (resp.file) {
      tempImageUrl.value = `${API_URL}/images/generated_images/${resp.file}`
      prompt.value.seed = resp.seed
      // Refresh gallery to include regenerated image
      try {
        await loadGallery()
      } catch (e) {
        console.warn('No se pudo recargar la galería tras regenerar en modal:', e)
      }
    }
  } catch (e) {
    showToast('Error regenerando imagen: ' + (e?.response?.data?.detail || e?.message || String(e)), { type: 'error' })
    console.error('Modal regenerate error:', e)
  } finally {
    modalLoading.value = false
  }
}

const modalTextConfirm = () => {
  // set main view to modal image and seed
  if (tempImageUrl.value) {
    imageUrl.value = tempImageUrl.value
    seedLastImg.value = prompt.value.seed
  }
  showRefineModal.value = false
}

const modalImagesConfirm = () => {
  // set main view to modal image and seed
  if (tempImageUrl.value && tempImageUrl.value !== '') {
    imageUrl.value = tempImageUrl.value
    seedLastImg.value = prompt.value.seed
  }
  showImagesModal.value = false
}

const modalDrawConfirm = () => {
  // set main view to modal image and seed
  if (tempImageUrl.value && tempImageUrl.value !== '') {
    imageUrl.value = tempImageUrl.value
    seedLastImg.value = prompt.value.seed
  }
  showDrawModal.value = false
}

const onFileChange = (ev) => {
  const f = ev.target.files && ev.target.files[0]
  if (f) uploadFile.value = f
}

const uploadUserImage = async () => {
  if (!uploadFile.value) return showToast('Selecciona una imagen primero', { type: 'warning' })
  try {
    isLoading.value = true
    active_user.value = await userService.getCurrentUser()
    const resp = await comfyService.uploadImage(uploadFile.value, active_user.value.id)
    console.log('Imagen subida:', resp)
    if (resp.file) {
      tempImageUrl.value = `${API_URL}/images/uploaded_images/${resp.file}`
      seedLastImg.value = resp.seed
      showToast('Imagen subida correctamente', { type: 'success' })
      uploadFile.value = null
      // Refresh gallery to show uploaded image
      try {
        await loadGallery()
      } catch (e) {
        console.warn('No se pudo recargar la galería tras subir imagen:', e)
      }
    }
  } catch (e) {
    showToast('Error subiendo imagen', { type: 'error' })
    console.error(e)
  } finally {
    isLoading.value = false
  }
}

const uploadAndTransformSketch = async () => {
  if (!uploadFile.value) return showToast('Selecciona una imagen primero', { type: 'warning' })
  try {
    isLoading.value = true
    active_user.value = await userService.getCurrentUser()
    const resp = await comfyService.uploadImage(uploadFile.value, active_user.value.id)
    console.log('Imagen subida:', resp)
    if (resp.file) {
      tempImageUrl.value = `${API_URL}/images/uploaded_images/${resp.file}`
      seedLastImg.value = resp.seed
      showToast('Imagen subida correctamente', { type: 'success' })
      uploadFile.value = null
      
      await createFromSketch(tempImageUrl.value)
      // Refresh gallery to show uploaded image
      try {
        await loadGallery()
      } catch (e) {
        console.warn('No se pudo recargar la galería tras subir imagen:', e)
      }
    }
  } catch (e) {
    showToast('Error subiendo imagen', { type: 'error' })
    console.error(e)
  } finally {
    isLoading.value = false
  }
}

const openSelectImagesModal = async () => {
  tempImageUrl.value = imageUrl.value
  showImagesModal.value = true
  modalLoading.value = false
}

const openDrawModal = async () => {
  tempImageUrl.value = ''
  showDrawModal.value = true
  modalLoading.value = false
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

const loadGallery = async () => {
  try {
    isLoadingGallery.value = true

    // 1. Cargar imágenes del usuario
    active_user.value = await userService.getCurrentUser()
    const resp = await comfyService.getImagesForUser(active_user.value.id)
    const userImages = resp.data ?? resp.images ?? []

    const generated = userImages.filter(img => img.fileName.startsWith("generated"))
    const uploaded = userImages.filter(img => img.fileName.startsWith("uploaded"))

    console.log("Imágenes del usuario:", generated, uploaded)

    // 2. Cargar imágenes de plantilla desde backend
    const tempResp = await comfyService.getTemplateImages()
    const templateNames = tempResp.images ?? []

    const templates = templateNames.map((file, i) => ({
      id: `template-${i}`,
      fileName: file,
      seed: null,
    }))

    console.log("Imágenes de plantilla:", templates)

    // 3. Unificar
    galleryImages.value = {
      templates,
      generated,
      uploaded
    }

    console.log("Galería unificada:", galleryImages.value)

  } catch (e) {
    console.error("Error cargando galería:", e)
    showToast("Error cargando galería", { type: "error" })
  } finally {
    isLoadingGallery.value = false
  }
}

// Función para obtener la URL correcta según el prefijo del archivo
const getImageUrl = (fileName) => {
  if (!fileName) return ''
  if (fileName.startsWith('uploaded')) {
    return `${API_URL}/images/uploaded_images/${fileName}`
  } else if (fileName.startsWith('generated')) {
    return `${API_URL}/images/generated_images/${fileName}`
  } else if (fileName.startsWith('drawn')) {
    return `${API_URL}/images/drawn_images/${fileName}`
  } else {
    return `${API_URL}/images/template_images/${fileName}`
  }
}

// Función para seleccionar imagen desde la galería
const selectImage = (img) => {
  tempImageUrl.value = getImageUrl(img.fileName)
  seedLastImg.value = img.seed
  showToast("Imagen seleccionada de la galería", { type: "success" })
  console.log('Imagen seleccionada:', tempImageUrl.value)
  showGallery.value = false
}

const openGalleryModal = () => {
  selectedImages.value = []  
  if (!combinedGallery.value.length) {
    showToast('No hay imágenes en tu galería', { type: 'info' })
    return
  }
  showGallery.value = true
}


const toggleMultiSelectMode = () => {
  multiSelectMode.value = !multiSelectMode.value
  selectedImages.value = []    // resetear selección al activar/desactivar
}

const toggleImageSelection = (img) => {
  const index = selectedImages.value.findIndex(i => i.fileName === img.fileName)
  if (index > -1) {
    // quitar de la selección
    selectedImages.value.splice(index, 1)
  } else if (selectedImages.value.length < maxMultiSelect) {
    // añadir a la selección
    selectedImages.value.push(img)
  } else {
    showToast(`Solo puedes seleccionar entre ${minMultiSelect} y ${maxMultiSelect} imágenes`, { type: 'warning' })
  }
}

const confirmMultiSelect = async () => {
  if (selectedImages.value.length < minMultiSelect) {
    showToast(`Selecciona al menos ${minMultiSelect} imágenes`, { type: 'warning' })
    return
  }

  // Aquí puedes enviar estas imágenes a tu flujo de Comfy
  console.log('Imágenes seleccionadas para flujo Comfy:', selectedImages.value)
  showGallery.value = false
  multiSelectMode.value = false

  try {
    isLoading.value = true
    tempImageUrl.value = ''

    // Preparar payload para el servicio
    const imagesPayload = {
      data: selectedImages.value.map(img => ({ fileName: img.fileName }))
    }

    active_user.value = await userService.getCurrentUser()
    const response = await comfyService.generateImageByMultiple(imagesPayload, selectedImages.value.length, active_user.value.id)
    console.log('Imagen generada por múltiples imágenes:', response)

    if (response.file) {
      tempImageUrl.value = `${API_URL}/images/generated_images/${response.file}`
      console.log('Imagen generada URL:', tempImageUrl.value)
      seedLastImg.value = response.seed
      // Refresh gallery to include the new image generated from multiple images
      try {
        await loadGallery()
      } catch (e) {
        console.warn('No se pudo recargar la galería tras generar imagen múltiple:', e)
      }
    }
  } catch (e) {
    showToast('Error generando imagen: ' + (e?.response?.data?.detail || e?.message || String(e)), { type: 'error' })
    console.error('Error generating image from multiple images:', e)
  } finally {
    isLoading.value = false
  }
}

const drawSketch = async () => {
  // Preserve sessionId if we're in a session context
  if (Number.isFinite(sessionId)) {
    router.push(`/session/${sessionId}/patient/canvas`)
  } else {
    router.push('/canvas/')
  }
}


</script>

<template>
  <div>
    <!-- Overlay de carga -->
    <div v-if="isLoadingGallery" class="loading-overlay">
      <p>Cargando galería...</p>
    </div>
    <div v-if="isLoading || modalLoading" class="loading-overlay">
      <p>Generando imagen...</p>
    </div>

    <h1>Genera tu obra de Arteterapia</h1>

    <div v-if="sessionInfo">
      <p><strong>Sesión ID:</strong> {{ sessionInfo.id }}</p>
      <p><strong>Estado:</strong> {{ sessionInfo.ended_at ? 'Finalizada' : 'Activa' }}</p>
    </div>

    <div v-if="imageUrl">
      <h2>Imagen generada:</h2>
      <img :src="imageUrl" alt="Imagen generada" class="main-image" />
    </div>

    <div style="margin-top: .5rem">
      <h2>Generar una nueva obra:</h2>
      <button @click="openRefineModal()" :disabled="isLoading">Generar a partir de texto</button>
      <button @click="openSelectImagesModal()" :disabled="isLoading">Generar a partir de imágenes</button>
      <button @click="openDrawModal()" :disabled="isLoading">Generar a partir de esbozo</button>
    </div>

    <!-- Refine Modal -->
    <div v-if="showRefineModal" class="modal-overlay" style="position:fixed;left:0;top:0;right:0;bottom:0;background:rgba(0,0,0,0.5);display:flex;align-items:center;justify-content:center;z-index:50;">
      <div class="modal" style="background:white;padding:1rem;max-width:760px;width:100%;border-radius:6px;">
        <button class="close-btn" @click="showRefineModal = false">Cerrar</button>
        <div>
          <label>Prompt:</label>
          <input v-model="prompt.promptText" type="text" style="width:100%;" />
        </div>
        <div style="margin-top:.5rem;">
          <button @click="modalRegenerate" :disabled="modalLoading || !prompt.promptText.trim()">Crear con texto</button>
          <button @click="modalTextConfirm" :disabled="modalLoading || !tempImageUrl" style="margin-left:.5rem;">Confirmar</button>
        </div>
        <div style="margin-top:.75rem;">
          <div v-if="modalLoading">Generando...</div>
          <div v-else-if="tempImageUrl">
            <img :src="tempImageUrl" alt="Modal preview" style="max-width:100%;height:auto;" />
          </div>
          <div v-else style="color:#666">Aún no hay imagen generada.</div>
        </div>
      </div>
    </div>

    <!-- Images Modal -->
    <div v-if="showImagesModal" class="modal-overlay" style="position:fixed;left:0;top:0;right:0;bottom:0;background:rgba(0,0,0,0.5);display:flex;align-items:center;justify-content:center;z-index:50;">
      <div class="modal" style="background:white;padding:1rem;max-width:760px;width:100%;border-radius:6px;">
        <button class="close-btn" @click="showImagesModal = false">Cerrar</button>
        <div style="margin-top:1rem;">
            <label for="fileInput">Subir imagen desde galería:</label>
            <input id="fileInput" type="file" accept="image/*" @change="onFileChange" />
            <button @click="uploadUserImage" :disabled="isLoadingGallery || !uploadFile" style="margin-left:0.5rem;">
                {{'Subir imagen' }}
            </button>
        </div>
        <div>
          <label>Prompt:</label>
          <input v-model="prompt.promptText" type="text" style="width:100%;" />
        </div>
        <div style="margin-top:.5rem;">
          <button v-if="tempImageUrl" @click="generateImage(null, tempImageUrl)" :disabled="isLoading || !prompt.promptText.trim()" style="margin-left:.5rem;">Crear añadiendo texto a la imagen</button>
            <div>
              Crear usando imágenes de la galería:
              <button @click="openGalleryModal" :disabled="isLoadingGallery">Ver galería</button>
            </div>
          <button @click="modalImagesConfirm" :disabled="modalLoading || !tempImageUrl" style="margin-left:.5rem;">Confirmar</button>
        </div>
        <div style="margin-top:.75rem;">
          <div v-if="modalLoading">Generando...</div>
          <div v-else-if="tempImageUrl">
            <img :src="tempImageUrl" alt="Modal preview" style="max-width:100%;height:auto;" />
          </div>
          <div v-else style="color:#666">Aún no hay imagen generada.</div>
        </div>
      </div>
    </div>

    <!-- Drawing Modal -->
    <div v-if="showDrawModal" class="modal-overlay" style="position:fixed;left:0;top:0;right:0;bottom:0;background:rgba(0,0,0,0.5);display:flex;align-items:center;justify-content:center;z-index:50;">
      <div class="modal" style="background:white;padding:1rem;max-width:760px;width:100%;border-radius:6px;">
        <button class="close-btn" @click="showDrawModal = false">Cerrar</button>
        <div style="margin-top:1rem;">
            <div>
              <label>Prompt:</label>
              <input v-model="prompt.promptText" type="text" style="width:100%;" />
            </div>
            <label for="fileInput">Subir esbozo desde galería:</label>
            <input id="fileInput" type="file" accept="image/*" @change="onFileChange" />
            <button @click="uploadAndTransformSketch" :disabled="isLoadingGallery || !uploadFile  || !prompt.promptText.trim()" style="margin-left:0.5rem;">
                {{'Subir y transformar esbozo' }}
            </button>
        </div>
        <div style="margin-top:.5rem;">
          <button @click="drawSketch">Dibujar boceto</button>
          <button @click="modalDrawConfirm" :disabled="modalLoading || !tempImageUrl" style="margin-left:.5rem;">Confirmar</button>
        </div>
        <div style="margin-top:.75rem;">
          <div v-if="modalLoading">Generando...</div>
          <div v-else-if="tempImageUrl">
            <img :src="tempImageUrl" alt="Modal preview" style="max-width:100%;height:auto;" />
          </div>
          <div v-else style="color:#666">Aún no hay imagen generada.</div>
        </div>
      </div>
    </div>

    <!-- Galería modal -->
    <div v-if="showGallery" class="gallery-modal">
      <button class="close-btn" @click="showGallery = false">Cerrar</button>
      <div style="margin-bottom: 10px;">
        <button @click="toggleMultiSelectMode">{{ multiSelectMode ? 'Cancelar selección múltiple' : 'Seleccionar varias imágenes' }}</button>
        <button v-if="multiSelectMode" @click="confirmMultiSelect" :disabled="selectedImages.length < minMultiSelect" style="margin-left:.5rem;">Confirmar selección ({{ selectedImages.length }})</button>
      </div>

      <!-- Templates -->
      <div v-if="galleryImages.templates?.length">
        <h3>Templates</h3>
        <div class="gallery-grid">
          <div v-for="img in galleryImages.templates" :key="img.id" class="img-item"
               @click="multiSelectMode ? toggleImageSelection(img) : selectImage(img)"
               :class="{ 'selected-multi': selectedImages.includes(img) }">
            <img :src="getImageUrl(img.fileName)" />
          </div>
        </div>
      </div>

      <!-- Generated -->
      <div v-if="galleryImages.generated?.length" style="margin-top: 1rem;">
        <h3>Generadas</h3>
        <div class="gallery-grid">
          <div v-for="img in galleryImages.generated" :key="img.id" class="img-item"
               @click="multiSelectMode ? toggleImageSelection(img) : selectImage(img)"
               :class="{ 'selected-multi': selectedImages.includes(img) }">
            <img :src="getImageUrl(img.fileName)" />
          </div>
        </div>
      </div>

      <!-- Uploaded -->
      <div v-if="galleryImages.uploaded?.length" style="margin-top: 1rem;">
        <h3>Subidas</h3>
        <div class="gallery-grid">
          <div v-for="img in galleryImages.uploaded" :key="img.id" class="img-item"
               @click="multiSelectMode ? toggleImageSelection(img) : selectImage(img)"
               :class="{ 'selected-multi': selectedImages.includes(img) }">
            <img :src="getImageUrl(img.fileName)" />
          </div>
        </div>
      </div>
    </div>
    <div class="chat-container" style="margin-top:1rem;">
      <div class="chat-messages" style="max-height:200px; overflow-y:auto; border:1px solid #ccc; padding:0.5rem; margin-bottom:0.5rem;">
        <div v-for="(msg, i) in chatMessages" :key="i" :style="{ textAlign: msg.sender === role ? 'right' : 'left' }">
          <strong>{{ msg.sender }}:</strong> {{ msg.text }}
        </div>
      </div>
      <input v-model="newChatMessage" @keyup.enter="sendChatMessage" placeholder="Escribe un mensaje..." style="width:70%" />
      <button @click="sendChatMessage" style="width:25%">Enviar</button>
    </div>

    <div>    
      <button @click="submitImage" style="margin-top:1rem">Enviar al terapeuta</button>
    </div>
    <div>
        <button @click="() => router.push('/home')">Volver al inicio</button>
    </div>
  </div>
</template>

<style scoped>
.loading-overlay {
  position: fixed;
  top: 0; left: 0;
  width: 100%; height: 100%;
  background: rgba(255,255,255,0.8);
  display: flex; justify-content: center; align-items: center;
  z-index: 999; font-size: 1.5em;
}

.gallery-modal {
  color: #000; /* negro */
  text-align: left;
  position: fixed;
  top: 10%; left: 10%;
  width: 80%; height: 80%;
  background: white; border-radius: 8px;
  overflow: auto; padding: 20px; z-index: 1000;
}

.close-btn { float: right; padding: 5px 10px; cursor: pointer; }

.gallery-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 10px; margin-top: 20px;
}

.img-item img { width: 100%; border-radius: 6px; cursor: pointer; }

.selected-multi {
  border: 3px solid #3b82f6; /* azul, por ejemplo */
  border-radius: 6px;
}

/* Main image display: consistent sizing regardless of resolution */
.main-image {
  max-width: 100%;
  max-height: 60vh;
  height: auto;
  object-fit: contain;
  display: block;
  margin: 1rem auto;
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