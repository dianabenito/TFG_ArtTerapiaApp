<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, computed, watch, nextTick } from 'vue'
import ChatPanel from '@/components/ChatPanel.vue'
import { comfyService } from '../api/comfyService'
import { userService } from '../api/userService.js'
import { sessionsService } from '../api/sessionsService.js'
import { useRoute, useRouter } from 'vue-router'
import { toast } from 'vue-sonner'

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
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { Textarea } from '@/components/ui/textarea'
import GalleryDialog from '@/components/GalleryDialog.vue'
import RefineModal from '@/components/RefineModal.vue'
import ImagesModal from '@/components/ImagesModal.vue'
import DrawModal from '@/components/DrawModal.vue'
import DrawnGallery from '@/components/DrawnGallery.vue'
import MultiImageModal from '@/components/MultiImageModal.vue'
import { FolderOpen, Brush, Send, Type, ImageIcon, Layers, Loader2, Info, HelpCircle, PanelRightClose, MessageCircle } from 'lucide-vue-next'

import { useDateHelpers } from '@/lib/useDateHelpers'

const {
  ensureUTCString,
  formatLocalDate
} = useDateHelpers()

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const WS_URL = API_URL.replace(/^http/, 'ws')
const route = useRoute()
const router = useRouter()
const sessionId = Number(route.params.sessionId) // tomado de la ruta si está; será NaN si falta
const hasSession = Number.isFinite(sessionId)

const chatMessages = ref([])       
const newChatMessage = ref('')     
const chatMessagesContainer = ref<HTMLElement | null>(null)
const role = 'patient'

const prompt = ref({ promptText: '', seed: null, inputImage: null })
const sketchPrompt = ref({ sketchImage: '', sketchText: '' })
const imageUrl = ref('')
const tempImageUrl = ref('')
const seedLastImg = ref(null)
const uploadFile = ref(null)
const selectedGalleryImageName = ref('')
const selectedGallerySketchName = ref('')
const active_user = ref(null)          // usuario actual
const therapistUser = ref(null)        // terapeuta asociado a la sesión
const isLoading = ref(false)
const sessionInfo = ref(null)
const inputImage = ref(null)
const isLoadingGallery = ref(true)
const galleryImages = ref({
  templates: [],
  generated: [],
  uploaded: [],
  uploadedDraws: [],
  drawn : []
})

const combinedGallery = computed(() => {
  const t = galleryImages.value.templates ?? []
  const g = galleryImages.value.generated ?? []
  const u = galleryImages.value.uploaded ?? []
  const ud = galleryImages.value.uploadedDraws ?? []
  const d = galleryImages.value.drawn ?? []
  return [...t, ...g, ...u, ...ud, ...d]
})

const showMultiSelectMode = ref(false)
const multiSelectMode = ref(false)            // si estamos en modo selección múltiple
const selectedImages = ref([])                // array de imágenes seleccionadas
const minMultiSelect = 2
const maxMultiSelect = 4

const showGallery = ref(false)
const showdrawnGallery = ref(false)
const chatOpen = ref(false)
const showFinalView = ref(false)

const stateStorageKey = sessionId ? `gen_state_${sessionId}` : 'gen_state_default'
const instructionsSeenKey = sessionId ? `gen_instr_${sessionId}` : 'gen_instr_default'

// Tab control for draw modal
const activeDrawTab = ref('upload')

// Refine modal state
const showInstructions = ref(false)
const showRefineModal = ref(false)
const showImagesModal = ref(false)
const showDrawModal = ref(false)
const showMultiImageModal = ref(false)
const modalLoading = ref(false)
const showDetails = ref(false)
const showSessionEndedAlert = ref(false)
const showSessionAlreadyEndedAlert = ref(false)
const showAccessDeniedAlert = ref(false)
const activeSession = ref(null)

let ws = null
let sessionEndTimeout = null

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
  ws = new WebSocket(`${WS_URL}/ws/${sessionId}/${role}?token=${token}`)

  ws.onopen = () => console.log('WS conectado como paciente')
  ws.onmessage = (ev) => {
    try {
      const obj = JSON.parse(ev.data)
      if (obj.event === 'chat_message') {
        chatMessages.value.push({ sender: obj.sender, text: obj.text })
        persistState()
        return
      }
    } catch (e) {
      // manejar mensaje plain text
      const txt = String(ev.data)
      if (txt === 'session_ended') {
        // actualizar estado local
        sessionInfo.value = { ...sessionInfo.value, ended_at: new Date().toISOString() }
        clearPersistedState()
        ws?.close()
        // mostrar alert y redirigir al paciente a Home
        showSessionEndedAlert.value = true
        return
      }
      console.log('WS message:', ev.data)
    }
  }
  ws.onclose = () => console.log('WS cerrado')
}

const clearPersistedState = () => {
  if (!hasSession) return
  try {
    localStorage.removeItem(stateStorageKey)
    localStorage.removeItem(instructionsSeenKey)
  } catch (e) {
    console.warn('No se pudo limpiar el estado local:', e)
  }
}

const persistState = () => {
  if (!hasSession) return
  try {
    const payload = {
      imageUrl: imageUrl.value,
      showFinalView: showFinalView.value,
      chatMessages: chatMessages.value,
    }
    localStorage.setItem(stateStorageKey, JSON.stringify(payload))
  } catch (e) {
    console.warn('No se pudo guardar el estado local:', e)
  }
}

const restoreState = () => {
  if (!hasSession) return
  try {
    const raw = localStorage.getItem(stateStorageKey)
    if (!raw) return
    const saved = JSON.parse(raw)
    if (saved?.imageUrl) imageUrl.value = saved.imageUrl
    if (typeof saved?.showFinalView === 'boolean') {
      showFinalView.value = saved.showFinalView
      chatOpen.value = saved.showFinalView || chatOpen.value
    }
    if (Array.isArray(saved?.chatMessages)) {
      chatMessages.value = saved.chatMessages
    }
  } catch (e) {
    console.warn('No se pudo restaurar el estado local:', e)
  }
}

const setupSessionEndWatcher = () => {
  if (!sessionInfo.value?.end_date) return

  // Convertir a objeto Date en UTC correctamente
  const endDate = new Date(ensureUTCString(sessionInfo.value.end_date))
  const now = new Date()

  // Si la sesión ya está finalizada, muestra el aviso inmediatamente
  if (sessionInfo.value?.ended_at || endDate.getTime() <= now.getTime()) {
    showSessionAlreadyEndedAlert.value = true
    return
  }

  // Calcula el tiempo restante hasta el fin de la sesión
  const msUntilEnd = endDate.getTime() - now.getTime()

  if (msUntilEnd > 0) {
    sessionEndTimeout = setTimeout(() => {
      showSessionAlreadyEndedAlert.value = true
      // Aquí puedes añadir lógica extra, como cerrar el websocket, redirigir, etc.
    }, msUntilEnd)
  }
}

onMounted(async () => {
  if (hasSession) restoreState()

  // usuario actual
  let currentUser = null
  try {
    currentUser = await userService.getCurrentUser()
    active_user.value = currentUser
  } catch (e) {
    console.warn('No se pudo obtener el usuario actual:', e)
  }

  
  // Si no hay usuario actual, redirigir al login (App.vue mostrará el alert global)
  if (!currentUser) {
    return
  }

  // comprobar que el usuario actual es el paciente de la sesión
  if (currentUser.type !== 'patient') {
    showAccessDeniedAlert.value = true
    return
  }


  // obtener info de sesión
  if (Number.isFinite(sessionId)) {
    try {
      sessionInfo.value = await sessionsService.getSession(sessionId)
      // si la sesión ya está finalizada, mostrar alerta y redirigir al home
      if (sessionInfo.value?.ended_at) {
        showSessionAlreadyEndedAlert.value = true
        return
      }
    } catch (err) {
      console.warn('No se pudo obtener la sesión:', err)
    }
    
    // comprobar que el usuario actual es el paciente de la sesión
    if (currentUser.id !== sessionInfo.value?.patient_id) {
      showAccessDeniedAlert.value = true
      return
    }

    activeSession.value = await sessionsService.getActiveSession()
    if(!activeSession.value || activeSession.value.id !== sessionId) {
      showAccessDeniedAlert.value = true
      return
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

  // mostrar instrucciones solo la primera vez en esta sesión
  if (hasSession) {
    const alreadySeenInstructions = localStorage.getItem(instructionsSeenKey)
    if (!alreadySeenInstructions) {
      showInstructions.value = true
      localStorage.setItem(instructionsSeenKey, '1')
    }
  }

  setupSessionEndWatcher()
})

// Función helper para scroll automático al final del chat
const scrollChatToBottom = async () => {
  if (!chatMessagesContainer.value) return
    await nextTick()
    setTimeout(() => {
      chatMessagesContainer.value?.scrollTo({
        top: chatMessagesContainer.value.scrollHeight,
        behavior: 'smooth'
      })
    }, 100)
}

// persist local state when key pieces change (solo con sessionId)
watch(imageUrl, persistState)
watch(showFinalView, persistState)
watch(chatMessages, () => {
  persistState()
  // Auto-scroll al final cuando llegan nuevos mensajes
  scrollChatToBottom()
}, { deep: true })

// Auto-scroll cuando se abre el chat
watch(chatOpen, async (newVal) => {
  if (newVal) {
    scrollChatToBottom()
  }
})

onBeforeUnmount(() => {
  if (sessionEndTimeout) clearTimeout(sessionEndTimeout)
  ws?.close()
})

const sendChatMessage = () => {
  if (!newChatMessage.value || !ws || ws.readyState !== WebSocket.OPEN) return
  const msg = { event: 'chat_message', sender: role, text: newChatMessage.value }
  ws.send(JSON.stringify(msg))
  chatMessages.value.push(msg)  // reflejar mensaje localmente
  newChatMessage.value = ''
  persistState()
}

const sendChatFromChild = (text: string) => {
  if (!text) return
  newChatMessage.value = text
  sendChatMessage()
}

// Handlers para bloquear cierre de modales mientras se genera imagen
const handleRefineModalClose = (val: boolean) => {
  if (!val && !modalLoading.value) {
    showRefineModal.value = false
  }
}

const handleImagesModalClose = (val: boolean) => {
  if (!val && !modalLoading.value) {
    showImagesModal.value = false
  }
}

const handleDrawModalClose = (val: boolean) => {
  if (!val && !modalLoading.value) {
    showDrawModal.value = false
  }
}

const handleMultiImageModalClose = (val: boolean) => {
  if (!val && !modalLoading.value) {
    showMultiImageModal.value = false
    selectedImages.value = []
  }
}

const generateImage = async (last_seed = null, inputImage = null) => {
  try {
    modalLoading.value = true
    tempImageUrl.value = ''

    // Only accept numeric seeds; ignore click events or other objects
    prompt.value.seed = null

    if(inputImage) {
      prompt.value.inputImage = inputImage
    } else {
      prompt.value.inputImage = null
    }

    // DESCOMENTAR ESTO PARA USAR USUARIO ACTIVO
    active_user.value = await userService.getCurrentUser()
    const response = await comfyService.createImage(prompt.value, active_user.value.id, Number.isFinite(sessionId) ? sessionId : null)
    

    if (response.file) {
      tempImageUrl.value = `${API_URL}/images/generated_images/${response.file}`
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
    toast.error('Error generando imagen: ' + detail)
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
    const response = Number.isFinite(sessionId) 
      ? await comfyService.convertirBoceto(sketchPrompt.value, active_user.value.id, sessionId)
      : await comfyService.convertirBoceto(sketchPrompt.value, active_user.value.id)

    if (response.file) {
      tempImageUrl.value = `${API_URL}/images/generated_images/${response.file}`
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
    toast.error('Error generando imagen: ' + detail)
    console.error('Error generating image:', e)
  } finally {
    modalLoading.value = false
  }
}

// Open refine modal: generate initial image and allow regenerations with same seed
const openRefineModal = async () => {
  prompt.value.promptText = ''
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
    const seedToUse = null

    active_user.value = await userService.getCurrentUser()
    const resp = await comfyService.createImage({ promptText: prompt.value.promptText, seed: seedToUse }, active_user.value.id, Number.isFinite(sessionId) ? sessionId : null)
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
    toast.error('Error regenerando imagen: ' + (e?.response?.data?.detail || e?.message || String(e)))
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
  persistState()
}

const modalImagesConfirm = () => {
  // set main view to modal image and seed
  if (tempImageUrl.value && tempImageUrl.value !== '') {
    imageUrl.value = tempImageUrl.value
    seedLastImg.value = prompt.value.seed
  }
  showImagesModal.value = false
  submitImage()
  persistState()
}

const modalDrawConfirm = () => {
  // set main view to modal image and seed
  if (tempImageUrl.value && tempImageUrl.value !== '') {
    imageUrl.value = tempImageUrl.value
    seedLastImg.value = prompt.value.seed
  }
  showDrawModal.value = false
  submitImage()
  persistState()
}

const onFileChange = (arg: any) => {
  let f: File | null = null
  if (arg && typeof arg === 'object' && 'target' in arg) {
    const ev = arg as Event & { target: HTMLInputElement }
    f = ev.target?.files?.[0] || null
  } else {
    f = arg as File
  }
  if (f) uploadFile.value = f
}

const uploadUserImage = async () => {
  if (!uploadFile.value) return toast.warning('Selecciona una imagen primero')
  try {
    isLoading.value = true
    active_user.value = await userService.getCurrentUser()
    const resp = await comfyService.uploadImage(uploadFile.value, active_user.value.id)
    if (resp.file) {
      // tempImageUrl.value = `${API_URL}/images/uploaded_images/${resp.file}`
      seedLastImg.value = resp.seed
      toast.success('Imagen subida correctamente')
      uploadFile.value = null
      // Refresh gallery to show uploaded image
      try {
        await loadGallery()
      } catch (e) {
        console.warn('No se pudo recargar la galería tras subir imagen:', e)
      }
    }
  } catch (e) {
    toast.error('Error subiendo imagen')
    console.error(e)
  } finally {
    isLoading.value = false
  }
}

const uploadUserImageandAddText = async () => {
  if (!uploadFile.value) return toast.warning('Selecciona una imagen primero')
  try {
    isLoading.value = true
    active_user.value = await userService.getCurrentUser()
    const resp = await comfyService.uploadImage(uploadFile.value, active_user.value.id)
    if (resp.file) {
      tempImageUrl.value = `${API_URL}/images/uploaded_images/${resp.file}`
      seedLastImg.value = resp.seed
      toast.success('Imagen subida correctamente')
      uploadFile.value = null

      await generateImage(null, tempImageUrl.value)
      // Refresh gallery to show uploaded image
      try {
        await loadGallery()
      } catch (e) {
        console.warn('No se pudo recargar la galería tras subir imagen:', e)
      }
    }
  } catch (e) {
    toast.error('Error subiendo imagen')
    console.error(e)
  } finally {
    isLoading.value = false
    prompt.value.promptText = ''
  }
}

const uploadAndTransformSketch = async () => {
  if (!uploadFile.value) return toast.warning('Selecciona una imagen primero')
  try {
    isLoading.value = true
    active_user.value = await userService.getCurrentUser()
    const resp = await comfyService.uploadImage(uploadFile.value, active_user.value.id, true)
    if (resp.file) {
      tempImageUrl.value = `${API_URL}/images/uploaded_images/${resp.file}`
      seedLastImg.value = resp.seed
      toast.success('Imagen subida correctamente')
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
    toast.error('Error subiendo imagen: ' + (e?.response?.data?.detail || e?.message || String(e)))
    console.error(e)
  } finally {
    isLoading.value = false
    prompt.value.promptText = ''
  }
}

const openSelectImagesModal = async () => {
  prompt.value.promptText = ''
  chatOpen.value = false
  tempImageUrl.value = ''
  selectedGalleryImageName.value = ''
  showImagesModal.value = true
  modalLoading.value = false
}

const convertGalleryImage = async () => {
  if (!selectedGalleryImageName.value) return
  tempImageUrl.value = getImageUrl(selectedGalleryImageName.value)
  await generateImage(null, tempImageUrl.value)
}

const selectGalleryImageDirectly = () => {
  if (!selectedGalleryImageName.value) return
  tempImageUrl.value = getImageUrl(selectedGalleryImageName.value)
}

const openDrawModal = async () => {
  prompt.value.promptText = ''
  chatOpen.value = false
  tempImageUrl.value = ''
  showDrawModal.value = true
  selectedGallerySketchName.value = ''
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
    toast.success('Imagen enviada correctamente')
  } catch (e) {
    console.warn('No se pudo mostrar toast tras enviar la imagen:', e)
  }
}

const confirmFinalArtwork = () => {
  if (!ws || ws.readyState !== WebSocket.OPEN) return
  ws.send(JSON.stringify({
    event: 'confirm_artwork',
    fileName: imageUrl.value.split('/').pop()
  }))
  showFinalView.value = true
  chatOpen.value = true
  persistState()
}

const loadGallery = async () => {
  try {
    isLoadingGallery.value = true

    // 1. Cargar imágenes del usuario
    active_user.value = await userService.getCurrentUser()
    const resp = await comfyService.getImagesForUser(active_user.value.id)
    const userImages = resp.data ?? resp.images ?? []

    const generated = userImages.filter(img => img.fileName.startsWith("generated"))
    const uploaded = userImages.filter(img => img.fileName.startsWith("uploaded_image"))
    const uploadedDraws = userImages.filter(img => img.fileName.startsWith("uploaded_drawn"))
    const drawn = userImages.filter(img => img.fileName.startsWith("drawn"))

    // 2. Cargar imágenes de plantilla desde backend
    const tempResp = await comfyService.getTemplateImages()
    const templateNames = tempResp.images ?? []

    const templates = templateNames.map((file, i) => ({
      id: `template-${i}`,
      fileName: file,
      seed: null,
    }))

    // 3. Unificar
    galleryImages.value = {
      templates,
      generated,
      uploaded,
      uploadedDraws,
      drawn
    }

  } catch (e) {
    console.error("Error cargando galería:", e)
    toast.error('Error cargando galería: ' + (e?.response?.data?.detail || e?.message || String(e)))
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
  selectedGalleryImageName.value = img.fileName
  seedLastImg.value = img.seed
  toast.success("Imagen seleccionada de la galería")
  showGallery.value = false
}

const selectDrawnImage = (img) => {
  selectedGallerySketchName.value = img.fileName
  seedLastImg.value = img.seed
  toast.success("Imagen dibujada seleccionada de la galería")
  showdrawnGallery.value = false
}

const openGalleryModal = () => {
  showMultiSelectMode.value = false
  selectedImages.value = []  
  if (!combinedGallery.value.length) {
    toast.info('No hay imágenes en tu galería')
    return
  }
  showGallery.value = true
}

const openDrawnGalleryModal = () => {
  showMultiSelectMode.value = false
  selectedImages.value = []  
  if (!galleryImages.value.drawn.length) {
    toast.info('No hay imágenes dibujadas en tu galería')
    return
  }
  showdrawnGallery.value = true
}


const openGalleryModalMultiselect = () => {
  chatOpen.value = false
  selectedImages.value = []
  tempImageUrl.value = ''
  if (!combinedGallery.value.length) {
    toast.info('No hay imágenes en tu galería')
    return
  }
  showMultiImageModal.value = true
  modalLoading.value = false
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
    toast.warning(`Solo puedes seleccionar entre ${minMultiSelect} y ${maxMultiSelect} imágenes`)
  }
}

const generateMultiImage = async () => {
  if (selectedImages.value.length < minMultiSelect) {
    toast.warning(`Selecciona al menos ${minMultiSelect} imágenes`)
    return
  }

  try {
    modalLoading.value = true
    tempImageUrl.value = ''

    const imagesPayload = {
      data: selectedImages.value.map(img => ({ fileName: img.fileName }))
    }

    active_user.value = await userService.getCurrentUser()
    const response = await comfyService.generateImageByMultiple(imagesPayload, selectedImages.value.length, active_user.value.id, Number.isFinite(sessionId) ? sessionId : null)

    if (response.file) {
      tempImageUrl.value = `${API_URL}/images/generated_images/${response.file}`
      seedLastImg.value = response.seed
      try {
        await loadGallery()
      } catch (e) {
        console.warn('No se pudo recargar la galería tras generar imagen múltiple:', e)
      }
    }
  } catch (e) {
    toast.error('Error generando imagen: ' + (e?.response?.data?.detail || e?.message || String(e)))
    console.error('Error generating image from multiple images:', e)
  } finally {
    modalLoading.value = false
  }
}

const modalMultiImageConfirm = () => {
  if (tempImageUrl.value && tempImageUrl.value !== '') {
    imageUrl.value = tempImageUrl.value
    seedLastImg.value = seedLastImg.value
  }
  showMultiImageModal.value = false
  selectedImages.value = []
  submitImage()
  persistState()
}

const confirmMultiSelect = async () => {
  if (selectedImages.value.length < minMultiSelect) {
    toast.warning(`Selecciona al menos ${minMultiSelect} imágenes`)
    return
  }

  // Aquí puedes enviar estas imágenes a tu flujo de Comfy
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
    const response = await comfyService.generateImageByMultiple(imagesPayload, selectedImages.value.length, active_user.value.id, Number.isFinite(sessionId) ? sessionId : null)

    if (response.file) {
      imageUrl.value = `${API_URL}/images/generated_images/${response.file}`
      seedLastImg.value = response.seed
      // Refresh gallery to include the new image generated from multiple images
      try {
        await loadGallery()
      } catch (e) {
        console.warn('No se pudo recargar la galería tras generar imagen múltiple:', e)
      }
    }
  } catch (e) {
    toast.error('Error generando imagen: ' + (e?.response?.data?.detail || e?.message || String(e)))
    console.error('Error generating image from multiple images:', e)
  } finally {
    modalLoading.value = false
    submitImage()
    persistState()
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

// Handler para conversión de boceto seleccionado de la galería
const convertDrawnSketch = async () => {
  const imageUrl = ref('')
  if (!selectedGallerySketchName.value) return
  if (selectedGallerySketchName.value.startsWith('uploaded')) {
    imageUrl.value = `${API_URL}/images/uploaded_images/${selectedGallerySketchName.value}`
  } else {
    imageUrl.value = `${API_URL}/images/drawn_images/${selectedGallerySketchName.value}`
  }
  await createFromSketch(imageUrl.value)
}

</script>

<template>
  <div class="flex flex-col">
    <Dialog :open="showDetails"  @update:open="(val) => !val && (showDetails = false)" >
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Detalles de la sesión</DialogTitle>
          <DialogDescription>
            Consulta la información detallada de la sesión actual.
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

    <AlertDialog :open="showSessionAlreadyEndedAlert" @update:open="(val) => showSessionAlreadyEndedAlert = val">
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Sesión finalizada</AlertDialogTitle>
          <AlertDialogDescription>
            La sesión ha finalizado.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <div class="flex justify-end gap-3">
          <AlertDialogAction @click="() => { clearPersistedState(); router.push('/home'); }">
            Volver al inicio
          </AlertDialogAction>
        </div>
      </AlertDialogContent>
    </AlertDialog>

    <AlertDialog :open="showSessionEndedAlert" @update:open="(val) => showSessionEndedAlert = val">
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Sesión finalizada</AlertDialogTitle>
          <AlertDialogDescription>
            La sesión ha sido finalizada por el terapeuta.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <div class="flex justify-end gap-3">
          <AlertDialogAction @click="router.push('/home')">
            Volver al inicio
          </AlertDialogAction>
        </div>
      </AlertDialogContent>
    </AlertDialog>

    <AlertDialog :open="showAccessDeniedAlert" @update:open="(val) => showAccessDeniedAlert = val">
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Acceso denegado</AlertDialogTitle>
          <AlertDialogDescription>
            No tienes acceso a este contenido.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <div class="flex justify-end gap-3">
          <AlertDialogAction @click="() => { router.push('/home'); }">
            Volver al inicio
          </AlertDialogAction>
        </div>
      </AlertDialogContent>
    </AlertDialog>



    <Dialog
      :open="showInstructions"
      @update:open="(val) => !val && (showInstructions = false)"
    >
      <DialogContent class="max-w-3xl sm:max-w-3xl overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Instrucciones para tu sesión de arteterapia</DialogTitle>
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
      v-if="!showFinalView"
      class="transition-all duration-300 bg-slate-300/30"
      :class="chatOpen ? 'mr-80' : 'mr-0'"
    >
      <div class="max-w-7xl mx-auto px-6 py-4 space-y-4">

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
          <div class="space-y-1">
            <h1 class="text-2xl font-semibold text-slate-900">
              Genera tu obra de arteterapia
            </h1>
            <p class="text-sm text-slate-600">
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
          <CardContent class="flex items-center justify-center h-full p-2">
            <div v-if="imageUrl" class="flex flex-col items-center gap-4">
              <img
                :src="imageUrl"
                class="max-h-[360px] rounded-xl border shadow-md object-contain"
              />
              <span class="text-sm text-muted-foreground mt-2 block">
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
              <Type class="h-8 w-8" />
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
                Dibuja o sube un boceto inicial para convertirlo en una obra 
              </p>
            </CardContent>
          </Card>

          <Card class="hover:shadow-lg transition cursor-pointer" @click="openGalleryModalMultiselect">
            <CardContent class="p-6 flex flex-col items-center text-center gap-3">
              <Layers class="h-8 w-8" />
              <h3 class="font-semibold">Mezcla de imágenes</h3>
              <p class="text-sm text-muted-foreground">
                Combina varias imágenes para crear una nueva obra
              </p>
            </CardContent>
          </Card>

        </div>

        <div class="flex justify-center">
          <Button v-if="sessionId"
            size="lg"
            class="bg-green-600 hover:bg-green-700 text-white px-10 py-5 text-lg font-bold rounded-full shadow-lg shadow-green-600/30"
            @click="confirmFinalArtwork"
            :disabled="!imageUrl"
          >
            Confirmar la obra creada
          </Button>
        </div>

      </div>
    </div>

    <!-- VISTA FINAL · IMAGEN + CHAT -->
    <div v-else class="bg-slate-300/30 min-h-[calc(100vh-4rem)]">
      <div class="max-w-7xl mx-auto px-6 py-4 space-y-4">
        <!-- HEADER -->
        <div class="flex items-start justify-between gap-6">
          <div class="space-y-1">
            <h2 class="text-2xl font-semibold text-slate-900">Tu obra de la sesión</h2>
            <p class="text-sm text-slate-600">Has completado tu obra, este es tu espacio 
              para comentarla con el terapeuta.</p>
          </div>

          <Button
            variant="ghost"
            size="icon"
            class="!h-11 !w-11 rounded-xl p-2.5"
            @click="showDetails = true"
            aria-label="Información"
          >
            <Info class="!h-8 !w-8" />
          </Button>
        </div>

        <div class="grid gap-6 lg:grid-cols-[1.3fr_1fr] items-start">
          <Card class="min-h-[600px] max-h-[600px] min-w-[420px] flex flex-col">
            <CardContent class="flex items-center justify-center p-6">
              <div v-if="imageUrl" class="w-full min-w-[420px]">
                <img
                  :src="imageUrl"
                  class="w-full max-h-[70vh] rounded-xl border shadow-md object-contain bg-white"
                />
              </div>
              <div v-else class="text-center text-muted-foreground space-y-2">
                <ImageIcon class="h-12 w-12 mx-auto opacity-50" />
                <p class="text-sm">No hay imagen final disponible.</p>
              </div>
            </CardContent>
          </Card>

          <ChatPanel
            :messages="chatMessages"
            :role="role"
            :activeUser="active_user"
            :therapistUser="therapistUser"
            @send="(text) => sendChatFromChild(text)"
          />
        </div>
      </div>
    </div>


    <RefineModal
      :open="showRefineModal"
      :loading="modalLoading"
      :tempImageUrl="tempImageUrl"
      v-model:promptText="prompt.promptText"
      @update:open="handleRefineModalClose"
      @generate="modalRegenerate"
      @confirm="modalTextConfirm"
    />

    <ImagesModal
      :open="showImagesModal"
      :loading="modalLoading"
      :tempImageUrl="tempImageUrl"
      :selectedGalleryImageName="selectedGalleryImageName"
      :isLoadingGallery="isLoadingGallery"
      :uploadFileName="uploadFile ? uploadFile.name : null"
      v-model:promptText="prompt.promptText"
      @update:open="handleImagesModalClose"
      @fileChange="onFileChange"
      @uploadImage="uploadUserImageandAddText"
      @openGallery="openGalleryModal"
      @convert="convertGalleryImage"
      @selectGalleryImage="selectGalleryImageDirectly"
      @confirm="modalImagesConfirm"
    />

    <DrawModal
      :open="showDrawModal"
      :loading="modalLoading"
      :tempImageUrl="tempImageUrl"
      :activeTab="activeDrawTab"
      :isLoadingGallery="isLoadingGallery"
      :uploadFileName="uploadFile ? uploadFile.name : null"
      v-model:promptText="prompt.promptText"
      :selectedGallerySketchName="selectedGallerySketchName"
      @update:open="handleDrawModalClose"
      @update:activeTab="(v) => (activeDrawTab = v)"
      @fileChange="onFileChange"
      @uploadAndTransform="uploadAndTransformSketch"
      @openDrawnGallery="openDrawnGalleryModal"
      @drawSketch="drawSketch"
      @convertDrawnSketch="convertDrawnSketch"
      @confirm="modalDrawConfirm"


    />


    <MultiImageModal
      :open="showMultiImageModal"
      :loading="modalLoading"
      :tempImageUrl="tempImageUrl"
      :templates="galleryImages.templates"
      :generated="galleryImages.generated"
      :uploaded="galleryImages.uploaded"
      :selectedImages="selectedImages"
      :minMultiSelect="minMultiSelect"
      :maxMultiSelect="maxMultiSelect"
      :getImageUrl="getImageUrl"
      @update:open="handleMultiImageModalClose"
      @toggle="toggleImageSelection"
      @generate="generateMultiImage"
      @confirm="modalMultiImageConfirm"
      :isLoadingGallery="isLoadingGallery"
      :uploadFileName="uploadFile ? uploadFile.name : null"
      @fileChange="onFileChange"
      @uploadImage="uploadUserImage"
    />

  
    <!-- Galería modal en Dialog -->
    <GalleryDialog
      :open="showGallery"
      :templates="galleryImages.templates"
      :generated="galleryImages.generated"
      :uploaded="galleryImages.uploaded"
      :multiSelectMode="!!(showMultiSelectMode && multiSelectMode)"
      :selectedImages="selectedImages"
      :minMultiSelect="minMultiSelect"
      :getImageUrl="getImageUrl"
      @update:open="(v) => !v && (showGallery = false)"
      @toggle="toggleImageSelection"
      @confirm="confirmMultiSelect"
      @selectSingle="selectImage"
    />

    <!-- Galería modal en Dialog -->
    <DrawnGallery
      :open="showdrawnGallery"
      :uploadedDraws="galleryImages.uploadedDraws"
      :drawn="galleryImages.drawn"
      :multiSelectMode="false"
      :selectedImages="selectedImages"
      :minMultiSelect="minMultiSelect"
      :getImageUrl="getImageUrl"
      @update:open="(v) => !v && (showdrawnGallery = false)"
      @toggle="toggleImageSelection"
      @confirm="confirmMultiSelect"
      @selectSingle="selectDrawnImage"
    />
  

    <template v-if="!showFinalView && hasSession">
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
        class="fixed right-0 z-[60] w-80 flex flex-col border-l shadow-lg transition-all duration-300 rounded-t-xl"
        style="top: 4rem; height: calc(100% - 4rem); background-color: rgb(245, 250, 255);"
      >
      <!-- HEADER -->
        <div class="flex items-center justify-between px-4 py-3 border-b rounded-t-xl" style="background-color: rgba(96, 165, 250, 0.6);">
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
        <div ref="chatMessagesContainer" class="flex-1 overflow-y-auto px-4 py-3 space-y-2">
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
              {{ msg.sender === "patient" ? (active_user?.full_name ?? 'Tú') : (therapistUser?.full_name ?? 'Terapeuta') }}
            </div>
            <div>
              {{ msg.text }}
            </div>
          </div>
        </div>

        <!-- FOOTER -->
        <div class="p-3 border-t" style="background-color: rgba(96, 165, 250, 0.25);">
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
    </template>


  </div>
</template>