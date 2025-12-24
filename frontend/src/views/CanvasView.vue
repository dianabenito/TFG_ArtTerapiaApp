<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { comfyService } from '../api/comfyService'
import { userService } from '../api/userService'
import { sessionsService } from '../api/sessionsService'

import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Slider } from '@/components/ui/slider'
import { Brush, Eraser, Trash2, Wand2, Loader2, Undo2 } from 'lucide-vue-next'
import { toast } from 'vue-sonner'

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'


const route = useRoute()
const router = useRouter()

const canvas = ref<HTMLCanvasElement | null>(null)
const drawing = ref(false)
const ctx = ref<CanvasRenderingContext2D | null>(null)
const color = ref('#000000')
const size = ref([5])
const mode = ref<'draw' | 'erase'>('draw')
const savedImage = ref<string | null>(null)
const showConfirmModal = ref(false)
const promptText = ref('')
const modalLoading = ref(false)
const sessionId = ref<number | null>(null)
const history = ref<string[]>([])
const hasDrawn = ref(false)
const showAccessDeniedAlert = ref(false)
const showSessionEndedAlert = ref(false)
const showSessionAlreadyEndedAlert = ref(false)
let ws = null
let sessionEndTimeout = null

const handleKeyDown = (e: KeyboardEvent) => {
  // Ctrl+Z (Windows/Linux) o Cmd+Z (Mac) para deshacer
  if ((e.ctrlKey || e.metaKey) && e.key === 'z') {
    e.preventDefault()
    undo()
  }
}

const setupSessionEndWatcher = (sessionInfo) => {
  if (!sessionInfo?.end_date) return

  // Convertir a objeto Date en UTC correctamente
  let endDate = new Date(sessionInfo.end_date)
  if (typeof sessionInfo.end_date === 'string' && !sessionInfo.end_date.endsWith('Z') && !sessionInfo.end_date.includes('+')) {
    endDate = new Date(sessionInfo.end_date + 'Z')
  }
  const now = new Date()

  // Si la sesión ya está finalizada, muestra el aviso inmediatamente
  if (sessionInfo?.ended_at || endDate.getTime() <= now.getTime()) {
    showSessionAlreadyEndedAlert.value = true
    return
  }

  // Calcula el tiempo restante hasta el fin de la sesión
  const msUntilEnd = endDate.getTime() - now.getTime()

  if (msUntilEnd > 0) {
    sessionEndTimeout = setTimeout(() => {
      showSessionAlreadyEndedAlert.value = true
    }, msUntilEnd)
  }
}

const connectWs = (sessionId, role, sessionInfo) => {
  const token = localStorage.getItem('token')
  if (!token || !sessionId || sessionInfo?.ended_at) return
  ws = new WebSocket(`ws://192.168.1.37:8000/ws/${sessionId}/${role}?token=${token}`)
  ws.onmessage = (ev) => {
    try {
      const obj = JSON.parse(ev.data)
      if (obj.event === 'chat_message') {
        // ignore in canvas
        return
      }
    } catch (e) {
      const txt = String(ev.data)
      if (txt === 'session_ended') {
        showSessionEndedAlert.value = true
        ws?.close()
        return
      }
    }
  }
  ws.onclose = () => {}
}

onMounted(async () => {
  // usuario actual
  let currentUser = null
  try {
    currentUser = await userService.getCurrentUser()
  } catch (e) {
    console.warn('No se pudo obtener el usuario actual:', e)
  }

  // Si no hay usuario actual, redirigir al login (App.vue mostrará el alert global)
  if (!currentUser) {
    return
  }

  if (currentUser.type !== 'patient') {
    showAccessDeniedAlert.value = true
    return
  }

  // Comprobar que la sesión es la activa del paciente (si hay sessionId en la ruta)
  const sid = Number(route.params.sessionId)
  sessionId.value = Number.isFinite(sid) ? sid : null
  if (Number.isFinite(sid)) {
    try {
      const sessionInfo = await sessionsService.getSession(sid)
      if (currentUser.id !== sessionInfo?.patient_id) {
        showAccessDeniedAlert.value = true
        return
      }
      const activeSession = await sessionsService.getActiveSession()
      if (!activeSession || activeSession.id !== sid) {
        showAccessDeniedAlert.value = true
        return
      }
      // --- NUEVO: watcher y ws ---
      setupSessionEndWatcher(sessionInfo)
      connectWs(sid, 'patient', sessionInfo)
      // ---
    } catch (e) {
      showAccessDeniedAlert.value = true
      return
    }
  }
  if (canvas.value) {
    ctx.value = canvas.value.getContext('2d')
    
    if (ctx.value) {
      // Fondo blanco para poder guardar
      ctx.value.fillStyle = '#FFFFFF'
      ctx.value.fillRect(0, 0, canvas.value.width, canvas.value.height)
      // Guardar estado inicial
      saveToHistory()
    }
  }

  // Agregar listener para Ctrl+Z
  window.addEventListener('keydown', handleKeyDown)
  
})

onBeforeUnmount(() => {
  // Remover listener al desmontar
  window.removeEventListener('keydown', handleKeyDown)
  if (sessionEndTimeout) clearTimeout(sessionEndTimeout)
  ws?.close()
})

const startDrawing = (e: MouseEvent) => {
  drawing.value = true
  hasDrawn.value = false
  if (ctx.value) {
    ctx.value.beginPath()
    ctx.value.moveTo(e.offsetX, e.offsetY)
  }
}

const draw = (e: MouseEvent) => {
  if (!drawing.value || !ctx.value) return

  hasDrawn.value = true
  ctx.value.lineWidth = size.value[0]
  ctx.value.lineCap = 'round'

  if (mode.value === 'draw') ctx.value.strokeStyle = color.value
  else if (mode.value === 'erase') ctx.value.strokeStyle = '#FFFFFF'

  ctx.value.lineTo(e.offsetX, e.offsetY)
  ctx.value.stroke()
}

const stopDrawing = () => {
  if (drawing.value && hasDrawn.value) {
    // Guardar estado después de cada trazo solo si realmente se dibujó
    saveToHistory()
  }
  drawing.value = false
  hasDrawn.value = false
  if (ctx.value) {
    ctx.value.closePath()
  }
}

const openConfirmModal = () => {
  showConfirmModal.value = true
}

const saveToHistory = () => {
  if (!canvas.value) return
  const dataUrl = canvas.value.toDataURL()
  history.value.push(dataUrl)
  // Limitar el historial a 50 estados para no consumir demasiada memoria
  if (history.value.length > 50) {
    history.value.shift()
  }
}

const undo = () => {
  if (history.value.length <= 1 || !canvas.value || !ctx.value) {
    toast.info('No hay más acciones para deshacer')
    return
  }
  
  // Eliminar el estado actual
  history.value.pop()
  
  // Restaurar el estado anterior
  const previousState = history.value[history.value.length - 1]
  if (!previousState) {
    toast.error('Error al deshacer')
    return
  }
  
  const img = new Image()
  img.onload = () => {
    if (ctx.value && canvas.value) {
      ctx.value.clearRect(0, 0, canvas.value.width, canvas.value.height)
      ctx.value.drawImage(img, 0, 0)
      toast.success('Acción deshecha')
    }
  }
  img.onerror = () => {
    toast.error('Error al restaurar el estado anterior')
  }
  img.src = previousState
}

const clearCanvas = () => {
  if (!canvas.value || !ctx.value) return
  ctx.value.fillStyle = '#FFFFFF'
  ctx.value.fillRect(0, 0, canvas.value.width, canvas.value.height)
  // Limpiar historial y guardar nuevo estado inicial
  history.value = []
  saveToHistory()
  toast.success('Lienzo limpiado')
}

const setErase = () => {
  mode.value = 'erase'
}

const setDraw = () => {
  mode.value = 'draw'
}

const saveImage = () => {
  if (!canvas.value) return
  savedImage.value = canvas.value.toDataURL('image/png')
}

const uploadSavedImage = async () => {
  if (!savedImage.value) {
    toast.warning('No hay dibujo guardado para subir.')
    return
  }
  
  // convert dataURL to blob
  const dataurl = savedImage.value
  const arr = dataurl.split(',')
  const mime = arr[0].match(/:(.*?);/)?.[1]
  const bstr = atob(arr[1])
  let n = bstr.length
  const u8arr = new Uint8Array(n)
  while (n--) {
    u8arr[n] = bstr.charCodeAt(n)
  }
  const blob = new Blob([u8arr], { type: mime })
  
  // create a file-like object
  const filename = `drawn_${Date.now()}.png`
  const file = new File([blob], filename, { type: mime })

  try {
    const active_user = await userService.getCurrentUser()
    const resp = await comfyService.uploadDrawnImage(file, active_user.id)
    const fname = resp.file
    
    // Preserve session context when navigating back
    if (sessionId.value) {
      router.push({ 
        path: `/session/${sessionId.value}/patient`, 
        query: { image: fname } 
      })
    } else {
      router.push({ path: '/generation/', query: { image: fname } })
    }
  } catch (e: any) {
    const detail = e?.response?.data?.detail || e?.message || String(e)
    console.error('Error uploading drawn image', e)
    toast.error('Error subiendo el dibujo: ' + detail)
  }
}

const modalConfirm = async () => {
  if (modalLoading.value) return
  modalLoading.value = true
  localStorage.setItem('prompt', promptText.value)
  saveImage()
  await uploadSavedImage()
  modalLoading.value = false
  showConfirmModal.value = false
}

</script>

<template>
  <div class="bg-slate-300/30 min-h-[calc(100vh-4rem)]">
    <div class="max-w-7xl mx-auto px-6 py-4 space-y-4">
      <!-- HEADER -->
      <div class="space-y-1">
        <h1 class="text-2xl font-semibold text-slate-900">Editor de dibujo</h1>
        <p class="text-sm text-slate-600">Dibuja tu boceto y conviértelo en una obra de arte</p>
      </div>

      <!-- MAIN CONTENT -->
      <div class="grid grid-cols-1 lg:grid-cols-[auto_1fr] gap-6">
        <!-- CONTROLS PANEL -->
        <Card class="h-fit">
          <CardContent class="p-6 space-y-6 w-64">
            <!-- SIZE SLIDER -->
            <div class="space-y-3">
              <div class="flex justify-between items-center">
                <Label class="text-sm font-semibold">Grosor</Label>
                <span class="text-sm text-muted-foreground">{{ size[0] }} px</span>
              </div>
              <Slider v-model="size" :min="1" :max="40" :step="1" />
            </div>

            <!-- MODE BUTTONS -->
            <div class="space-y-2">
              <Label class="text-sm font-semibold">Herramienta</Label>
              <div class="grid grid-cols-2 gap-2">
                <Button 
                  @click="setDraw" 
                  :variant="mode === 'draw' ? 'default' : 'outline'"
                  class="w-full"
                >
                  <Brush class="h-4 w-4 mr-2" />
                  Dibujar
                </Button>
                <Button 
                  @click="setErase" 
                  :variant="mode === 'erase' ? 'default' : 'outline'"
                  class="w-full"
                >
                  <Eraser class="h-4 w-4 mr-2" />
                  Borrar
                </Button>
              </div>
            </div>

            <!-- ACTION BUTTONS -->
            <div class="pt-4 border-t space-y-2">
              <Button 
                @click="undo" 
                variant="outline" 
                class="w-full"
                :disabled="history.length <= 1"
              >
                <Undo2 class="h-4 w-4 mr-2" />
                Deshacer
              </Button>
              
              <Button 
                @click="clearCanvas" 
                variant="outline" 
                class="w-full"
              >
                <Trash2 class="h-4 w-4 mr-2" />
                Limpiar lienzo
              </Button>
              
              <Button 
                @click="openConfirmModal" 
                class="w-full bg-green-600 hover:bg-green-700"
              >
                <Wand2 class="h-4 w-4 mr-2" />
                Transformar boceto
              </Button>
            </div>
          </CardContent>
        </Card>

        <!-- CANVAS -->
        <Card class="flex items-center justify-center">
          <CardContent class="p-6">
            <canvas
              ref="canvas"
              width="600"
              height="600"
              class="border-2 border-slate-300 rounded-lg bg-white cursor-crosshair shadow-md"
              @mousedown="startDrawing"
              @mousemove="draw"
              @mouseup="stopDrawing"
              @mouseleave="stopDrawing"
            ></canvas>
          </CardContent>
        </Card>
      </div>
    </div>

    <!-- CONFIRM MODAL -->
    <Dialog :open="showConfirmModal" @update:open="(v) => showConfirmModal = v">
      <DialogContent class="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Transformar tu boceto</DialogTitle>
          <DialogDescription>
            Describe cómo quieres transformar tu boceto en una obra de arte
          </DialogDescription>
        </DialogHeader>

        <div class="space-y-4 mt-4">
          <div class="space-y-2">
            <Label for="promptText">Descripción de la obra</Label>
            <Textarea 
              id="promptText"
              v-model="promptText" 
              placeholder="Describe cómo quieres que se transforme tu boceto..."
              class="min-h-[120px]"
              :disabled="modalLoading"
            />
          </div>

          <div class="flex justify-end gap-3 pt-4">
            <Button 
              variant="outline" 
              @click="showConfirmModal = false"
              :disabled="modalLoading"
            >
              Cancelar
            </Button>
            <Button 
              @click="modalConfirm" 
              :disabled="!promptText || modalLoading"
              class="bg-green-600 hover:bg-green-700"
            >
              <Loader2 v-if="modalLoading" class="h-4 w-4 mr-2 animate-spin" />
              <Wand2 v-else class="h-4 w-4 mr-2" />
              Confirmar transformación
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>

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

    <AlertDialog :open="showSessionAlreadyEndedAlert" @update:open="(val) => showSessionAlreadyEndedAlert = val">
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Sesión finalizada</AlertDialogTitle>
          <AlertDialogDescription>
            La sesión ha finalizado.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <div class="flex justify-end gap-3">
          <AlertDialogAction @click="router.push('/home')">
            Volver al inicio
          </AlertDialogAction>
        </div>
      </AlertDialogContent>
    </AlertDialog>

  </div>
</template>
