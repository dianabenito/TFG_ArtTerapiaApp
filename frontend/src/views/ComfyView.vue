<script setup>
import { ref, onMounted, onBeforeUnmount, computed } from 'vue'
import { comfyService } from '../api/comfyService'
import { userService } from '../api/userService.js'

import { useRoute, useRouter } from 'vue-router'
import { showToast } from '../stores/toastStore.js'
const API_URL = 'http://127.0.0.1:8000'
const route = useRoute()
const router = useRouter()
const sessionId = Number(route.params.sessionId) // tomado de la ruta si está; será NaN si falta
const role = 'patient'

const prompt = ref({ promptText: '', seed: null, inputImage: null })
const imageUrl = ref('')
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


const showGallery = ref(false)

// Refine modal state
const showRefineModal = ref(false)
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
  await loadGallery()
})

onBeforeUnmount(() => ws?.close())

const generateImage = async (last_seed = null, inputImage = null) => {
  try {
    isLoading.value = true
    imageUrl.value = ''

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
    // active_user.value = await userService.getCurrentUser()
    // const response = await comfyService.createImage(prompt.value, active_user.value.id)
    
    // Y COMENTAR ESTA
    const response = await comfyService.createImage(prompt.value, 2)
    console.log('Imagen generada:', response)

    if (response.file) {
      imageUrl.value = `${API_URL}/images/generated_images/${response.file}`
      console.log('Modal image URL:', prompt)
      seedLastImg.value = response.seed
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
  // generate initial image to obtain a seed
  try {
    modalLoading.value = true
    const resp = await comfyService.createImage({ promptText: prompt.value.promptText, seed: null }, 2)
    console.log('Modal initial generation:', resp)
    if (resp.file) {
      imageUrl.value = `${API_URL}/images/generated_images/${resp.file}`
      console.log('Modal image URL:', prompt)
      prompt.value.seed = resp.seed
    }
  } catch (e) {
    showToast('Error generando imagen en el modal: ' + (e?.response?.data?.detail || e?.message || String(e)), { type: 'error' })
    console.error('Modal generation error:', e)
  } finally {
    modalLoading.value = false
  }
}

const modalRegenerate = async () => {
  if (!showRefineModal.value) return
  try {
    modalLoading.value = true
    // keep the same seed if present (pass the primitive value, not the ref)
    const seedToUse = prompt.value.seed ?? null
    const resp = await comfyService.createImage({ promptText: prompt.value.promptText, seed: seedToUse }, 2)
    console.log('Modal regenerate:', resp)
    if (resp.file) {
      imageUrl.value = `${API_URL}/images/generated_images/${resp.file}`
      prompt.value.seed = resp.seed
    }
  } catch (e) {
    showToast('Error regenerando imagen: ' + (e?.response?.data?.detail || e?.message || String(e)), { type: 'error' })
    console.error('Modal regenerate error:', e)
  } finally {
    modalLoading.value = false
  }
}

const modalConfirm = () => {
  // set main view to modal image and seed
  if (imageUrl.value) {
    imageUrl.value = imageUrl.value
    seedLastImg.value = prompt.value.seed
  }
  showRefineModal.value = false
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

const loadGallery = async () => {
  try {
    isLoadingGallery.value = true

    // 1. Cargar imágenes del usuario
    const resp = await comfyService.getImagesForUser()
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
  } else {
    return `${API_URL}/images/template_images/${fileName}`
  }
}

// Función para seleccionar imagen desde la galería
const selectImage = (img) => {
  imageUrl.value = getImageUrl(img.fileName)
  seedLastImg.value = img.seed
  showToast("Imagen seleccionada de la galería", { type: "success" })
  console.log('Imagen seleccionada:', imageUrl.value)
  showGallery.value = false
}

const openGalleryModal = () => {
  if (!combinedGallery.value.length) {
    showToast('No hay imágenes en tu galería', { type: 'info' })
    return
  }
  showGallery.value = true
}

</script>

<template>
  <div>
    <!-- Overlay de carga -->
    <div v-if="isLoading" class="loading-overlay">
      <p>Cargando galería...</p>
    </div>

    <h1>Generar imagen con ComfyUI</h1>

    <div v-if="sessionInfo">
      <p><strong>Sesión ID:</strong> {{ sessionInfo.id }}</p>
      <p><strong>Estado:</strong> {{ sessionInfo.ended_at ? 'Finalizada' : 'Activa' }}</p>
    </div>
    <input v-model="prompt.promptText" type="text" placeholder="Describe tu imagen" />
    <div style="margin-top: .5rem">
      <button @click="openRefineModal()" :disabled="isLoading">Crear con texto</button>
      <button v-if="imageUrl" @click="generateImage(null, imageUrl)" :disabled="isLoading" style="margin-left:.5rem;">Crear a partir de imagen</button>
    </div>

    <!-- Upload from gallery -->
    <div style="margin-top:1rem;">
      <label for="fileInput">Subir imagen desde galería:</label>
      <input id="fileInput" type="file" accept="image/*" @change="onFileChange" />
      <button @click="uploadUserImage" :disabled="isLoadingGallery || !uploadFile" style="margin-left:0.5rem;">
        {{'Subir imagen' }}
      </button>
      <div v-if="uploadFile" style="margin-top:.5rem; font-size:.9rem; color:#444;">Seleccionado: {{ uploadFile.name || uploadFile.filename }}</div>
    </div>

        <!-- Botón para abrir la galería -->
    <div>
      <button @click="openGalleryModal" :disabled="isLoadingGallery">Ver galería</button>
    </div>

  <!-- Galería modal -->
  <div v-if="showGallery" class="gallery-modal">
    <button class="close-btn" @click="showGallery = false">Cerrar</button>

    <!-- Templates -->
    <div v-if="galleryImages.templates?.length">
      <h3>Templates</h3>
      <div class="gallery-grid">
        <div
          v-for="img in galleryImages.templates"
          :key="img.id"
          class="img-item"
          @click="selectImage(img)"
        >
          <img :src="getImageUrl(img.fileName)" />
        </div>
      </div>
    </div>

    <!-- Generated -->
    <div v-if="galleryImages.generated?.length" style="margin-top: 1rem;">
      <h3>Generadas</h3>
      <div class="gallery-grid">
        <div
          v-for="img in galleryImages.generated"
          :key="img.id"
          class="img-item"
          @click="selectImage(img)"
        >
          <img :src="getImageUrl(img.fileName)" />
        </div>
      </div>
    </div>

    <!-- Uploaded -->
    <div v-if="galleryImages.uploaded?.length" style="margin-top: 1rem;">
      <h3>Subidas</h3>
      <div class="gallery-grid">
        <div
          v-for="img in galleryImages.uploaded"
          :key="img.id"
          class="img-item"
          @click="selectImage(img)"
        >
          <img :src="getImageUrl(img.fileName)" />
        </div>
      </div>
    </div>
  </div>




    <!-- Refine Modal -->
    <div v-if="showRefineModal" class="modal-overlay" style="position:fixed;left:0;top:0;right:0;bottom:0;background:rgba(0,0,0,0.5);display:flex;align-items:center;justify-content:center;z-index:50;">
      <div class="modal" style="background:white;padding:1rem;max-width:760px;width:100%;border-radius:6px;">
        <h3>Perfeccionar imagen (seed: {{ prompt.seed }})</h3>
        <div>
          <label>Prompt:</label>
          <input v-model="prompt.promptText" type="text" style="width:100%;" />
        </div>
        <div style="margin-top:.5rem;">
          <button @click="modalRegenerate" :disabled="modalLoading">Regenerar (mantener seed)</button>
          <button @click="modalConfirm" :disabled="modalLoading || !imageUrl" style="margin-left:.5rem;">Confirmar</button>
        </div>
        <div style="margin-top:.75rem;">
          <div v-if="modalLoading">Generando...</div>
          <div v-else-if="imageUrl">
            <img :src="imageUrl" alt="Modal preview" style="max-width:100%;height:auto;" />
          </div>
          <div v-else style="color:#666">Aún no hay imagen generada.</div>
        </div>
      </div>
    </div>

    <div v-if="imageUrl">
      <h2>Imagen generada:</h2>
      <img :src="imageUrl" alt="Imagen generada" style="max-width: 100%; height: auto;" />
      <button @click="submitImage" style="margin-top:1rem;">Enviar al terapeuta</button>
      <div v-if="imageUrl && seedLastImg">Seed: {{ seedLastImg }}</div>
    </div>

  </div>
</template>

<style>
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
</style>