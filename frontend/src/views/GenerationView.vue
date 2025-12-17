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
import { FolderOpen, Brush, Send, PenTool, ImageIcon, Layers, Loader2, Info, HelpCircle, PanelRightClose, MessageCircle } from 'lucide-vue-next'

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
const active_user = ref(null)          // usuario actual
const therapistUser = ref(null)        // terapeuta asociado a la sesión
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
const chatOpen = ref(false)


// Tab control for draw modal
const activeDrawTab = ref('upload')

// Refine modal state
const showInstructions = ref(false)
const showRefineModal = ref(false)
const showImagesModal = ref(false)
const showDrawModal = ref(false)
const modalLoading = ref(false)
const showDetails = ref(false)

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

  // usuario actual
  try {
    active_user.value = await userService.getCurrentUser()
  } catch (e) {
    console.warn('No se pudo obtener el usuario actual:', e)
  }

  // terapeuta asociado (para vista paciente)
  try {
    const therapistId = sessionInfo.value?.therapist_id ?? sessionInfo.value?.therapist?.id
    if (role === 'patient' && therapistId) {
      therapistUser.value = await userService.getUserById(therapistId)
    }
  } catch (e) {
    console.warn('No se pudo obtener el terapeuta de la sesión:', e)
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
  showInstructions.value = true
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
  chatOpen.value = false
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
  submitImage()
}

const modalImagesConfirm = () => {
  // set main view to modal image and seed
  if (tempImageUrl.value && tempImageUrl.value !== '') {
    imageUrl.value = tempImageUrl.value
    seedLastImg.value = prompt.value.seed
  }
  showImagesModal.value = false
  submitImage()
}

const modalDrawConfirm = () => {
  // set main view to modal image and seed
  if (tempImageUrl.value && tempImageUrl.value !== '') {
    imageUrl.value = tempImageUrl.value
    seedLastImg.value = prompt.value.seed
  }
  showDrawModal.value = false
  submitImage()
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
  chatOpen.value = false
  tempImageUrl.value = imageUrl.value
  showImagesModal.value = true
  modalLoading.value = false
}

const openDrawModal = async () => {
  chatOpen.value = false
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
  chatOpen.value = false
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
    submitImage()
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

const ensureUTCString = (dateString) => {
  if (!dateString) return dateString;
  if (typeof dateString === 'string' && !dateString.endsWith('Z') && !dateString.includes('+')) {
    return dateString + 'Z';
  }
  return dateString;
}

const formatLocalDate = (utcString) => {
  if (!utcString) return 'N/D';
  return new Date(ensureUTCString(utcString)).toLocaleString('es-ES', {
    timeZone: 'Europe/Madrid',
    dateStyle: 'short',
    timeStyle: 'short'
  });
}

</script>

<template>

  <div class="flex flex-col">

    <Dialog :open="showDetails"  @update:open="(val) => !val && (showDetails = false)" >
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Detalles de la sesión</DialogTitle>
          <DialogDescription>
            Consulta la información detallada de la sesión seleccionada.
          </DialogDescription>
        </DialogHeader>
          <dl class="grid grid-cols-2 gap-x-1.5 gap-y-1 text-m">
            <dt class="font-semibold">Terapeuta</dt>
            <dd>{{ therapistUser?.full_name ?? 'Cargando...' }}</dd>


            <dt class="font-semibold">Fecha</dt>
            <dd>{{ formatLocalDate(sessionInfo.start_date).slice(0,8) }}</dd>

            <dt class="font-semibold">Hora</dt>
            <dd>{{ formatLocalDate(sessionInfo.start_date).slice(10,16) }} - {{ formatLocalDate(sessionInfo.end_date).slice(10,16) }}</dd>

          </dl>

      </DialogContent>
    </Dialog>

    <Dialog
      :open="showInstructions"
      @update:open="(val) => !val && (showInstructions = false)"
    >
      <DialogContent class="max-w-3xl sm:max-w-3xl overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Instrucciones para tu sesión de Arteterapia</DialogTitle>
          <DialogDescription class="leading-relaxed mt-2">
            En esta aplicación de generación de imágenes asistida por IA, podréis explorar diversos métodos innovadores 
            de creación artística como parte de vuestra sesión de arteterapia. A continuación, se detallan algunas indicaciones 
            que os ayudarán a aprovechar al máximo esta experiencia creativa:
          </DialogDescription>
        </DialogHeader>
        <div class="mt-2 space-y-6 text-sm leading-relaxed">

          <!-- LISTA DE INSTRUCCIONES -->
          <ul class="list-disc pl-5 space-y-3">
            <li>
              Crea un espacio y un tiempo seguros, de intimidad y sin interrupciones.
              Evita móviles, otras pantallas u otras personas en la sala.
            </li>

            <li>
              Disfruta del proceso creativo sin juzgarte.
              No hay obras buenas o malas, bonitas o feas; todas las creaciones son válidas.
            </li>

            <li>
              No te preocupes por el resultado final.
              Lo importante es el proceso y lo que te aporta a nivel personal.
            </li>

            <li>
              Si necesitas inspiración, puedes tomar como referencia un objeto de tu entorno
              o utilizar las imágenes de plantilla disponibles en la galería.
            </li>

            <li>
              Si te bloqueas, no sabes cómo continuar o te surgen dudas,
              puedes comunicarte con el terapeuta a través del chat.
            </li>

            <li>
              Durante la sesión, el terapeuta podrá observar tu proceso creativo
              a partir de las obras que vayas generando con los distintos métodos disponibles.
            </li>

            <li>
              Cuando sientas que tu obra está completa, envíala al terapeuta para continuar
              a la siguiente fase de la sesión y compartir impresiones sobre la experiencia.
            </li>
          </ul>

          <!-- CIERRE -->
          <div class="pt-4 border-t text-muted-foreground">
            <p>
              Recordad que esta herramienta está pensada como un apoyo al proceso terapéutico.
              No existe una forma correcta de crear: confiad en vuestro ritmo y en vuestra intuición.
            </p>
          </div>
        </div>


      </DialogContent>
    </Dialog>


    <!-- CONTENIDO PRINCIPAL -->
    <div
      class="transition-all duration-300 bg-muted/30"
      :class="chatOpen ? 'mr-80' : 'mr-0'"
    >
      <div class="max-w-7xl mx-auto px-6 py-8 space-y-10">

        <!-- OVERLAY DE CARGA -->
        <div
          v-if="isLoadingGallery"
          class="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
        >
          <Card class="p-6 flex items-center gap-3">
            <Spinner class="size-8" />
            <span>Cargando galería...</span>
          </Card>
        </div>

        <!-- HEADER -->
        <div class="flex items-start justify-between gap-6">
          <!-- TEXTO IZQUIERDA -->
          <div>
            <h1 class="text-xl font-semibold">
              Genera tu obra de Arteterapia
            </h1>
            <p class="text-sm text-muted-foreground mt-1">
              Explora distintas formas de creación a partir de texto, imágenes o bocetos.
            </p>
          </div>

          <!-- BOTONES DERECHA -->
          <div class="flex items-center gap-2">
            <Button
              variant="ghost"
              size="icon"
              class="!h-11 !w-11 rounded-xl p-2.5"
              @click="showDetails = true"
              aria-label="Información"
            >
              <Info class="!h-8 !w-8" />
            </Button>

            <Button
              variant="ghost"
              size="icon"
              class="!h-11 !w-11 rounded-xl p-2.5"
              @click="showInstructions = true"
              aria-label="Ayuda"
            >
              <HelpCircle class="!h-8 !w-8" />
            </Button>
          </div>
        </div>


        <Card
          class="transition-all duration-300"
          :class="imageUrl ? 'min-h-[420px]' : 'min-h-[220px]'"
        >
          <CardContent class="flex items-center justify-center h-full p-6">
            <div v-if="imageUrl" class="flex flex-col items-center gap-4">
              <img
                :src="imageUrl"
                class="max-h-[360px] rounded-xl border shadow-md object-contain"
              />
              <span class="text-sm text-muted-foreground">
                Esta es tu obra actual. Puedes modificarla o crear una nueva usando las opciones a continuación, o confirmarla cuando estés satisfecho.
              </span>
            </div>

                          <!-- LOADING -->
              <div
                v-else-if="modalLoading"
                class="flex flex-col items-center gap-3 text-muted-foreground"
              >
                <Loader2 class="h-6 w-6 animate-spin" />
                <span class="text-sm">Generando imagen...</span>
              </div>

            <div
              v-else
              class="text-center text-muted-foreground space-y-3"
            >
              <ImageIcon class="h-12 w-12 mx-auto opacity-50" />
              <p class="text-sm">
                Aún no has generado ninguna obra.<br />
                Empieza seleccionando una opción abajo.
              </p>
            </div>
          </CardContent>
        </Card>

        <!-- ACCIONES PRINCIPALES -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">

          <Card class="hover:shadow-lg transition cursor-pointer" @click="openRefineModal">
            <CardContent class="p-6 flex flex-col items-center text-center gap-3">
              <PenTool class="h-8 w-8" />
              <h3 class="font-semibold">Desde texto</h3>
              <p class="text-sm text-muted-foreground">
                Describe una idea y conviértela en una obra visual
              </p>
            </CardContent>
          </Card>

          <Card class="hover:shadow-lg transition cursor-pointer" @click="openSelectImagesModal">
            <CardContent class="p-6 flex flex-col items-center text-center gap-3">
              <ImageIcon class="h-8 w-8" />
              <h3 class="font-semibold">Desde imagen</h3>
              <p class="text-sm text-muted-foreground">
                Parte de una imagen existente y transfórmala
              </p>
            </CardContent>
          </Card>

          <Card class="hover:shadow-lg transition cursor-pointer" @click="openDrawModal">
            <CardContent class="p-6 flex flex-col items-center text-center gap-3">
              <Brush class="h-8 w-8" />
              <h3 class="font-semibold">Desde boceto</h3>
              <p class="text-sm text-muted-foreground">
                Dibuja o sube un boceto inicial
              </p>
            </CardContent>
          </Card>

          <Card class="hover:shadow-lg transition cursor-pointer" @click="openGalleryModalMultiselect">
            <CardContent class="p-6 flex flex-col items-center text-center gap-3">
              <Layers class="h-8 w-8" />
              <h3 class="font-semibold">Mezclar imágenes</h3>
              <p class="text-sm text-muted-foreground">
                Combina varias imágenes en una sola obra
              </p>
            </CardContent>
          </Card>

        </div>

        <div class="flex justify-center">
          <Button
            size="lg"
            class="bg-green-600 hover:bg-green-700 text-white px-10 py-5 text-lg font-bold rounded-full shadow-lg shadow-green-600/30"
            @click="submitImage"
            :disabled="!imageUrl"
          >
            Enviar al terapeuta
          </Button>
        </div>

      </div>
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
            <div class="grid grid-cols-[repeat(auto-fill,minmax(120px,1fr))] gap-[10px] mt-5">
              <div
                v-for="img in galleryImages.templates"
                :key="img.id"
                class="img-item"
                @click="multiSelectMode ? toggleImageSelection(img) : selectImage(img)"
                :class="{ 'selected-multi': selectedImages.includes(img) }"
              >
                <img
                  :src="getImageUrl(img.fileName)"
                  class="w-full aspect-square object-cover rounded-lg border"
                />
              </div>
            </div>
          </div>

          <div v-if="galleryImages.generated?.length">
            <h3>Generadas</h3>
            <div class="grid grid-cols-[repeat(auto-fill,minmax(120px,1fr))] gap-[10px] mt-5">
              <div
                v-for="img in galleryImages.generated"
                :key="img.id"
                class="img-item"
                @click="multiSelectMode ? toggleImageSelection(img) : selectImage(img)"
                :class="{ 'selected-multi': selectedImages.includes(img) }"
              >
                <img
                  :src="getImageUrl(img.fileName)"
                  class="w-full aspect-square object-cover rounded-lg border"
                />
              </div>
            </div>
          </div>

          <div v-if="galleryImages.uploaded?.length">
            <h3>Subidas</h3>
            <div class="grid grid-cols-[repeat(auto-fill,minmax(120px,1fr))] gap-[10px] mt-5">
              <div
                v-for="img in galleryImages.uploaded"
                :key="img.id"
                class="img-item"
                @click="multiSelectMode ? toggleImageSelection(img) : selectImage(img)"
                :class="{ 'selected-multi': selectedImages.includes(img) }"
              >
                <img
                  :src="getImageUrl(img.fileName)"
                  class="w-full aspect-square object-cover rounded-lg border"
                />
              </div>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  

    <!-- BOTÓN PARA ABRIR/CERRAR CHAT -->
    <div 
      class="fixed z-[60] transition-all duration-300"
      :class="chatOpen ? 'bottom-6 right-[21rem]' : 'bottom-6 right-6'"
    >
      <Button v-if="chatOpen === false"
        class="rounded-full w-16 h-16 flex items-center justify-center p-4 shadow-lg"
        @click="chatOpen = true"
      >
      <MessageCircle class="h-8 w-8" />
      </Button>
    </div>

    <div
      v-show="chatOpen"
      class="fixed right-0 z-[60] w-80 flex flex-col border-l shadow-lg transition-all duration-300"
      style="top: 4rem; height: calc(100% - 4rem); background-color: rgb(245, 250, 255);"
    >
      <!-- HEADER -->
      <div class="flex items-center justify-between px-4 py-3 border-b" style="background-color: rgba(96, 165, 250, 0.4);">
        <div class="flex items-center gap-2">
          <h2 class="text-sm font-semibold text-black">
            Chat con el terapeuta
          </h2>
        </div>

        <Button
          variant="ghost"
          size="icon"
          class="text-black hover:bg-blue-100"
          @click="chatOpen = false"
          aria-label="Cerrar chat"
        >
          <PanelRightClose class="h-4 w-4" />
        </Button>
      </div>

      <!-- MENSAJES -->
      <div class="flex-1 overflow-y-auto px-4 py-3 space-y-2">
        <div
          v-for="(msg, i) in chatMessages"
          :key="i"
          :class="[
            'max-w-[75%] px-3 py-2 rounded-xl text-sm shadow-sm break-words',
            msg.sender === role
              ? 'ml-auto bg-green-100 text-green-900 rounded-tr-sm'
              : 'mr-auto bg-gray-100 text-gray-900 rounded-tl-sm'
          ]"
        >
          <div class="text-xs font-semibold opacity-80 mb-0.5">
            {{ msg.sender === "patient" ? active_user.full_name: therapistUser.full_name }}
          </div>
          <div>
            {{ msg.text }}
          </div>
        </div>
      </div>

      <!-- FOOTER -->
      <div class="p-3 border-t" style="background-color: rgba(96, 165, 250, 0.3);">
        <div class="flex gap-2">
          <Input
            v-model="newChatMessage"
            placeholder="Escribe un mensaje…"
            @keyup.enter="sendChatMessage"
            class="flex-1 bg-white text-gray-900"
          />
          <Button
            size="icon"
            class="bg-blue-600 text-white hover:bg-blue-500"
            @click="sendChatMessage"
            aria-label="Enviar mensaje"
          >
            <Send class="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>


  </div>
</template>