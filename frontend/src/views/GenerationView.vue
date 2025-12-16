<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, computed } from 'vue'
import { comfyService } from '../api/comfyService'
import { userService } from '../api/userService.js'
import { sessionsService } from '../api/sessionsService.js'
import { useRoute, useRouter } from 'vue-router'
import { showToast } from '../stores/toastStore.js'

import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Button } from "@/components/ui/button"
import { Loader2 } from "lucide-vue-next"
import { Spinner } from '@/components/ui/spinner'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Textarea } from '@/components/ui/textarea'
import { FolderOpen, Brush } from 'lucide-vue-next'

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

const showMultiSelectMode = ref(false)
const multiSelectMode = ref(false)            // si estamos en modo selección múltiple
const selectedImages = ref([])                // array de imágenes seleccionadas
const minMultiSelect = 2
const maxMultiSelect = 4

const showGallery = ref(false)

// Tab control for draw modal
const activeDrawTab = ref('upload')

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
          alert('La sesión ha finalizado.')
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
    activeDrawTab.value = 'draw' // Open 'draw' tab since image comes from canvas
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
    modalLoading.value = true
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
    modalLoading.value = false
  }
}

const createFromSketch = async(inputImage) => {
  try {
    modalLoading.value = true
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
    modalLoading.value = false
  }
}

// Open refine modal: generate initial image and allow regenerations with same seed
const openRefineModal = async () => {
  tempImageUrl.value = ''
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
    prompt.value.promptText = ''
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
  activeDrawTab.value = 'upload' // Reset to upload tab by default
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
  showMultiSelectMode.value = false
  selectedImages.value = []  
  if (!combinedGallery.value.length) {
    showToast('No hay imágenes en tu galería', { type: 'info' })
    return
  }
  showGallery.value = true
}

const openGalleryModalMultiselect = () => {
  showMultiSelectMode.value = true
  multiSelectMode.value = true
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
  showMultiSelectMode.value = false

  try {
    modalLoading.value = true
    imageUrl.value = ''

    // Preparar payload para el servicio
    const imagesPayload = {
      data: selectedImages.value.map(img => ({ fileName: img.fileName }))
    }

    active_user.value = await userService.getCurrentUser()
    const response = await comfyService.generateImageByMultiple(imagesPayload, selectedImages.value.length, active_user.value.id)
    console.log('Imagen generada por múltiples imágenes:', response)

    if (response.file) {
      imageUrl.value = `${API_URL}/images/generated_images/${response.file}`
      console.log('Imagen generada URL:', imageUrl.value)
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
    modalLoading.value = false
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
      <Card  class="w-full max-w-md p-6 flex items-center justify-center">
        <Spinner class="size-8"/>
        <span>Cargando galería...</span>
      </Card>
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
      <Button @click="openRefineModal()" :disabled="isLoading">Generar a partir de texto</Button>
      <Button @click="openSelectImagesModal()" :disabled="isLoading">Generar a partir de imágenes</Button>
      <Button @click="openDrawModal()" :disabled="isLoading">Generar a partir de esbozo</Button>
      <Button @click="openGalleryModalMultiselect()" :disabled="isLoading">Mezclar varias imagenes</Button>
    </div>


    

    <Dialog
      :open="showRefineModal"
      @update:open="(val) => !val && (showRefineModal = false)"
    >
      <DialogContent class="w-full max-w-5xl sm:max-w-5xl">
        <!-- HEADER -->
        <DialogHeader>
          <DialogTitle>Generar obra a partir de un prompt de texto</DialogTitle>
          <DialogDescription>
            Describe la obra que quieres crear y genera una imagen basada en tu descripción.
          </DialogDescription>
        </DialogHeader>

        <!-- LAYOUT DOS COLUMNAS -->
        <div class="grid grid-cols-1 md:grid-cols-[1fr_auto_1fr] gap-6 mt-4">
          <!-- COLUMNA IZQUIERDA · PROMPT -->
          <div class="flex flex-col gap-4">
            <div class="grid gap-2">
              <Label for="promptText">
                Descripción de la obra
              </Label>
              <Textarea
                id="promptText"
                v-model="prompt.promptText"
                placeholder="Describe el contenido que quieres ver en tu obra."
                class="min-h-[200px]"
                :disabled="modalLoading"
              />
            </div>

            <div class="flex justify-end">
              <Button 
                variant="default"
                class="px-4 py-2"
                @click="modalRegenerate"
                :disabled="modalLoading || !prompt.promptText.trim()"
              >
                Generar imagen
              </Button>
            </div>
          </div>

          <!-- DIVISOR -->
          <div class="hidden md:flex items-stretch">
            <div class="w-px bg-border" />
          </div>

          <!-- COLUMNA DERECHA · PREVISUALIZACIÓN -->
          <Card class="h-full">
            <CardContent
              class="flex flex-col items-center justify-center h-full gap-4 py-6 text-center"
            >
              <!-- LOADING -->
              <div
                v-if="modalLoading"
                class="flex flex-col items-center gap-3 text-muted-foreground"
              >
                <Loader2 class="h-6 w-6 animate-spin" />
                <span class="text-sm">Generando imagen...</span>
              </div>

              <!-- IMAGEN GENERADA -->
              <div
                v-else-if="tempImageUrl"
                class="flex flex-col items-center gap-4 w-full"
              >
                <img
                  :src="tempImageUrl"
                  alt="Previsualización de la obra"
                  class="max-h-[360px] rounded-lg border object-contain"
                />

              </div>

              <!-- ESTADO VACÍO -->
              <div
                v-else
                class="flex flex-col items-center gap-2 text-muted-foreground"
              >
                <ImageIcon class="h-8 w-8 opacity-50" />
                <span class="text-sm">
                  Aún no hay ninguna imagen generada
                </span>
              </div>
            </CardContent>
          </Card>
        </div>
        <div class="flex justify-center mt-3">
          <Button 
              :disabled="modalLoading || !tempImageUrl"
            class="bg-green-600 hover:bg-green-700 text-white px-8 py-5 rounded-lg font-bold text-lg shadow-lg"          
            @click="modalTextConfirm"
          >
            Confirmar imagen
        </Button>
        </div>
      </DialogContent>
    </Dialog>



    <Dialog
      :open="showImagesModal"
      @update:open="(val) => !val && (showImagesModal = false)"
    >
      <DialogContent class="w-full max-w-5xl sm:max-w-5xl">
        <!-- HEADER -->
        <DialogHeader>
          <DialogTitle>Generar obra a partir de una imagen de entrada y un prompt de texto</DialogTitle>
          <DialogDescription>
            Sube una imagen desde tu biblioteca o selecciona una imagen existente de la galería, y añade una descripción para transformar la imagen en una nueva obra.
          </DialogDescription>
        </DialogHeader>

        <!-- LAYOUT DOS COLUMNAS -->
        <div class="grid grid-cols-1 md:grid-cols-[1fr_auto_1fr] gap-6 mt-4">
          <!-- COLUMNA IZQUIERDA · PROMPT -->
          <div class="flex flex-col gap-4">
            <Tabs default-value="upload">
              <TabsList class="mx-auto mb-3">
                <TabsTrigger value="upload">
                  Subir imagen
                </TabsTrigger>
                <TabsTrigger value="gallery">
                  Escoger de la galería
                </TabsTrigger>
              </TabsList>
              <TabsContent value="upload">
                <div class="grid gap-2 mb-3">
              
                  <!-- Label + Input -->
                  <Label for="fileInput">
                    Paso 1: Sube una imagen de la biblioteca de archivos de tu ordenador:
                  </Label>
                                
                  <div class="flex items-center gap-3">
                    <!-- Botón seleccionar archivo -->
                    <div class="relative shrink-0">
                      <input
                        id="fileInput"
                        type="file"
                        accept="image/*"
                        @change="onFileChange"
                        class="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                      />
                      <Button variant="outline">
                        <FolderOpen class="h-4 w-4" />
                        <span>Seleccionar archivo</span>
                      </Button>
                    </div>

                    <!-- Nombre del archivo -->
                    <span class="text-sm text-muted-foreground truncate max-w-xs">
                      {{ uploadFile ? uploadFile.name : 'Ningún archivo seleccionado' }}
                    </span>
                  </div>

                </div>

                <Button
                  @click="uploadUserImage"
                  :disabled="isLoadingGallery || !uploadFile"
                  variant="default"
                >
                  Subir imagen
                </Button>


                <div class="h-px bg-border my-4" v-if="tempImageUrl"/>

            
                <div class="grid gap-2" v-if="tempImageUrl">
                  <Label for="promptText">
                    Paso 2: Describe la obra que quieres crear a partir de la imagen subida:
                  </Label>
                  <Textarea
                    id="promptText"
                    v-model="prompt.promptText"
                    placeholder="Describe el contenido del texto que quieres añadir a tu imagen de partida."
                    class="min-h-[200px]"
                    :disabled="modalLoading"
                  />
                </div>

                <div class="flex justify-start mt-3">
                  <Button 
                    v-if="tempImageUrl"
                    variant="default"
                    class="px-4 py-2"
                    @click="generateImage(null, tempImageUrl)"
                    :disabled="modalLoading || !prompt.promptText.trim()"
                  >
                    Convertir la imagen con texto
                  </Button>
                </div>
              </TabsContent>
              <TabsContent value="gallery">
                <div class="grid gap-2">
                  <!-- Label + Input -->
                  <Label>
                    Paso 1: Escoge una imagen de la galería de imágenes:
                  </Label>
                  <Button 
                    variant="default"
                    class="px-4 py-2 w-fit mt-1"
                    @click="openGalleryModal"
                    :disabled="isLoadingGallery"
                  >
                    Ver galería
                  </Button>
                </div>

                <div class="h-px bg-border my-4" v-if="tempImageUrl"/>
            
                <div class="grid gap-2" v-if="tempImageUrl">
                  <Label for="promptText" class="leading-normal">
                    Paso 2: Describe la obra que quieres crear a partir de la imagen seleccionada:
                  </Label>
                  <Textarea
                    id="promptText"
                    v-model="prompt.promptText"
                    placeholder="Describe el contenido del texto que quieres añadir a tu imagen de partida."
                    class="min-h-[200px]"
                    :disabled="modalLoading"
                  />
                </div>

                <div class="flex justify-start mt-3">
                  <Button 
                    v-if="tempImageUrl"
                    variant="default"
                    class="px-4 py-2"
                    @click="generateImage(null, tempImageUrl)"
                    :disabled="modalLoading || !prompt.promptText.trim()"
                  >
                    Convertir la imagen con texto
                  </Button>
                </div>
              </TabsContent>
            </Tabs>
          </div>

          <!-- DIVISOR -->
          <div class="hidden md:flex items-stretch">
            <div class="w-px bg-border" />
          </div>

          <!-- COLUMNA DERECHA · PREVISUALIZACIÓN -->
          <Card class="h-full">
            <CardContent
              class="flex flex-col items-center justify-center h-full gap-4 py-6 text-center"
            >
              <!-- LOADING -->
              <div
                v-if="modalLoading"
                class="flex flex-col items-center gap-3 text-muted-foreground"
              >
                <Loader2 class="h-6 w-6 animate-spin" />
                <span class="text-sm">Generando imagen...</span>
              </div>

              <!-- IMAGEN GENERADA -->
              <div
                v-else-if="tempImageUrl"
                class="flex flex-col items-center gap-4 w-full"
              >
                <img
                  :src="tempImageUrl"
                  alt="Previsualización de la obra"
                  class="max-h-[360px] rounded-lg border object-contain"
                />

              </div>

              <!-- ESTADO VACÍO -->
              <div
                v-else
                class="flex flex-col items-center gap-2 text-muted-foreground"
              >
                <ImageIcon class="h-8 w-8 opacity-50" />
                <span class="text-sm">
                  Aún no hay ninguna imagen generada
                </span>
              </div>
            </CardContent>
          </Card>
        </div>
        <div class="flex justify-center mt-3">
          <Button
            :disabled="modalLoading || !tempImageUrl"
            class="bg-green-600 hover:bg-green-700 text-white px-8 py-5 rounded-lg font-bold text-lg shadow-lg"          
            @click="modalImagesConfirm"
          >
            Confirmar imagen
        </Button>
        </div>
      </DialogContent>
    </Dialog>


        <Dialog
      :open="showDrawModal"
      @update:open="(val) => !val && (showDrawModal = false)"
    >
      <DialogContent class="w-full max-w-5xl sm:max-w-5xl">
        <!-- HEADER -->
        <DialogHeader>
          <DialogTitle>Generar obra a partir de un esbozo</DialogTitle>
          <DialogDescription>
            Sube un esbozo desde tu biblioteca o dibujalo en el editor, y añade una descripción para transformar el esbozo en una nueva obra.
          </DialogDescription>
        </DialogHeader>

        <!-- LAYOUT DOS COLUMNAS -->
        <div class="grid grid-cols-1 md:grid-cols-[1fr_auto_1fr] gap-6 mt-4">
          <!-- COLUMNA IZQUIERDA · PROMPT -->
          <div class="flex flex-col gap-4">
            <Tabs v-model="activeDrawTab">
              <TabsList class="mx-auto mb-3">
                <TabsTrigger value="upload">
                  Subir boceto
                </TabsTrigger>
                <TabsTrigger value="draw">
                  Dibujar boceto
                </TabsTrigger>
              </TabsList>
              <TabsContent value="upload">
                <div class="grid gap-2 mb-3">
              
                  <!-- Label + Input -->
                  <Label for="fileInput">
                    Paso 1: Sube un boceto desde la biblioteca de archivos de tu ordenador:
                  </Label>
                                
                  <div class="flex items-center gap-3">
                    <!-- Botón seleccionar archivo -->
                    <div class="relative shrink-0">
                      <input
                        id="fileInput"
                        type="file"
                        accept="image/*"
                        @change="onFileChange"
                        class="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                      />
                      <Button variant="outline">
                        <FolderOpen class="h-4 w-4" />
                        <span>Seleccionar archivo</span>
                      </Button>
                    </div>

                    <!-- Nombre del archivo -->
                    <span class="text-sm text-muted-foreground truncate max-w-xs">
                      {{ uploadFile ? uploadFile.name : 'Ningún archivo seleccionado' }}
                    </span>
                  </div>

                </div>

                <div class="h-px bg-border my-4"/>

            
                <div class="grid gap-2">
                  <Label for="promptText">
                    Paso 2: Describe la obra que quieres crear a partir del boceto subido:
                  </Label>
                  <Textarea
                    id="promptText"
                    v-model="prompt.promptText"
                    placeholder="Describe tu boceto en detalle para reconvertirlo en una obra final."
                    class="min-h-[200px]"
                    :disabled="modalLoading"
                  />
                </div>

                <Button class="mt-3"
                  @click="uploadAndTransformSketch"
                  :disabled="isLoadingGallery || !uploadFile || !prompt.promptText.trim()"
                  variant="default"
                >
                  Transformar boceto
                </Button>

              </TabsContent>
              <TabsContent value="draw">
                <div class="grid gap-2">
                  <Label for="promptText">
                    Diseña un nuevo boceto en el editor:
                  </Label>
                </div>
                <div class="flex justify-start mt-3">
                  <Button 
                    variant="default"
                    class="px-4 py-2"
                    @click="drawSketch">
                    <Brush class="h-4 w-4" />
                    Ir a dibujar boceto
                  </Button>
                </div>
              </TabsContent>
            </Tabs>
          </div>

          <!-- DIVISOR -->
          <div class="hidden md:flex items-stretch">
            <div class="w-px bg-border" />
          </div>

          <!-- COLUMNA DERECHA · PREVISUALIZACIÓN -->
          <Card class="h-full">
            <CardContent
              class="flex flex-col items-center justify-center h-full gap-4 py-6 text-center"
            >
              <!-- LOADING -->
              <div
                v-if="modalLoading"
                class="flex flex-col items-center gap-3 text-muted-foreground"
              >
                <Loader2 class="h-6 w-6 animate-spin" />
                <span class="text-sm">Generando imagen...</span>
              </div>

              <!-- IMAGEN GENERADA -->
              <div
                v-else-if="tempImageUrl"
                class="flex flex-col items-center gap-4 w-full"
              >
                <img
                  :src="tempImageUrl"
                  alt="Previsualización de la obra"
                  class="max-h-[360px] rounded-lg border object-contain"
                />

              </div>

              <!-- ESTADO VACÍO -->
              <div
                v-else
                class="flex flex-col items-center gap-2 text-muted-foreground"
              >
                <ImageIcon class="h-8 w-8 opacity-50" />
                <span class="text-sm">
                  Aún no hay ninguna imagen generada
                </span>
              </div>
            </CardContent>
          </Card>
        </div>
        <div class="flex justify-center mt-3">
          <Button
            :disabled="modalLoading || !tempImageUrl"
            class="bg-green-600 hover:bg-green-700 text-white px-8 py-5 rounded-lg font-bold text-lg shadow-lg"          
            @click="modalDrawConfirm"
          >
            Confirmar imagen
        </Button>
        </div>
      </DialogContent>
    </Dialog>

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

    <!-- Galería modal en Dialog -->
    <Dialog
      :open="showGallery"
      @update:open="(val) => !val && (showGallery = false)"
    >
      <DialogContent class="max-w-5xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{{ showMultiSelectMode ? 'Selecciona imágenes para combinar' : 'Selecciona una imagen' }}</DialogTitle>
          <DialogDescription>{{ showMultiSelectMode ? 'Selecciona de 2 a 4 imagenes que se mezclaran para crear una nueva obra.' : 'Selecciona una imagen como punto de partida para tu obra.' }}</DialogDescription>
        </DialogHeader>

        <div class="flex items-center gap-3 mb-2">
          <Button
            v-if="showMultiSelectMode && multiSelectMode"
            size="sm"
            :disabled="selectedImages.length < minMultiSelect"
            @click="confirmMultiSelect"
          >
            Confirmar selección ({{ selectedImages.length }})
          </Button>
        </div>

        <div class="space-y-4">
          <div v-if="galleryImages.templates?.length">
            <h3>Templates</h3>
            <div class="gallery-grid">
              <div
                v-for="img in galleryImages.templates"
                :key="img.id"
                class="img-item"
                @click="multiSelectMode ? toggleImageSelection(img) : selectImage(img)"
                :class="{ 'selected-multi': selectedImages.includes(img) }"
              >
                <img :src="getImageUrl(img.fileName)" />
              </div>
            </div>
          </div>

          <div v-if="galleryImages.generated?.length">
            <h3>Generadas</h3>
            <div class="gallery-grid">
              <div
                v-for="img in galleryImages.generated"
                :key="img.id"
                class="img-item"
                @click="multiSelectMode ? toggleImageSelection(img) : selectImage(img)"
                :class="{ 'selected-multi': selectedImages.includes(img) }"
              >
                <img :src="getImageUrl(img.fileName)" />
              </div>
            </div>
          </div>

          <div v-if="galleryImages.uploaded?.length">
            <h3>Subidas</h3>
            <div class="gallery-grid">
              <div
                v-for="img in galleryImages.uploaded"
                :key="img.id"
                class="img-item"
                @click="multiSelectMode ? toggleImageSelection(img) : selectImage(img)"
                :class="{ 'selected-multi': selectedImages.includes(img) }"
              >
                <img :src="getImageUrl(img.fileName)" />
              </div>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
    
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

.gallery-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 10px; margin-top: 20px;
}

.img-item img { 
  width: 100%; 
  aspect-ratio: 1 / 1;
  object-fit: cover;
  border-radius: 6px; 
  cursor: pointer; 
}

.img-item {
  cursor: pointer;
}

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