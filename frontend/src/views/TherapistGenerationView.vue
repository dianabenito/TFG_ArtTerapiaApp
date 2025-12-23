<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { userService } from '../api/userService.js'
import { sessionsService } from '../api/sessionsService.js'
import ChatPanel from '@/components/ChatPanel.vue'

import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { ImageIcon, Info } from 'lucide-vue-next'

const API_URL = 'http://127.0.0.1:8000'
const route = useRoute()
const router = useRouter()
const sessionId = Number(route.params.sessionId)
const role = 'therapist'

const chatMessages = ref([])
const latestImage = ref('')
const sessionInfo = ref(null)
const patientUser = ref(null)
const showDetails = ref(false)
const artworkConfirmed = ref(false)  // ← detecta si el paciente confirmó la obra
const showConfirmEndDialog = ref(false)
const showSuccessEndDialog = ref(false)
const showErrorEndDialog = ref(false)
const showSessionAlreadyEndedAlert = ref(false)

// Persistencia local por sesión para terapeuta
const stateStorageKey = Number.isFinite(sessionId) ? `tgen_state_${sessionId}` : 'tgen_state_default'

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
        // No confirmar la obra aún; solo actualizar la imagen
        persistState()
      } else if (obj.event === 'confirm_artwork') {
        artworkConfirmed.value = true
        persistState()
      } else if (obj.event === 'chat_message') {
        chatMessages.value.push({ sender: obj.sender, text: obj.text })
        persistState()
      }
    } catch (e) {
      const data = String(raw)
      if (data === 'session_ended') {
        clearPersistedState()
        socket?.close()
      } else if (data.startsWith('new_image:')) {
        const filename = data.split(':')[1]
        latestImage.value = `${API_URL}/images/${filename}`
        persistState()
      }
    }
  }

  socket.onclose = () => console.log('WS cerrado')
}

const sendChatMessage = (text: string) => {
  if (!text || !socket || socket.readyState !== WebSocket.OPEN) return
  const msg = { event: 'chat_message', sender: role, text }
  socket.send(JSON.stringify(msg))
  chatMessages.value.push(msg)
  persistState()
}

let sessionEndTimeout = null

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
  // Restaurar estado local si existe
  restoreState()
  if (!Number.isFinite(sessionId)) return
  try {
    sessionInfo.value = await sessionsService.getSession(sessionId)
    if (sessionInfo.value?.ended_at) {
      clearPersistedState()
      showSuccessEndDialog.value = true
      return
    }
    // obtener datos del paciente
    try {
      const patientId = sessionInfo.value?.patient_id ?? sessionInfo.value?.patient?.id
      if (patientId) {
        patientUser.value = await userService.getUserById(patientId)
      }
    } catch (e) {
      console.warn('No se pudo obtener datos del paciente:', e)
    }
  } catch (err) {
    console.warn('No se pudo obtener la sesión:', err)
  }
  connectSocket()
  setupSessionEndWatcher()
})

onBeforeUnmount(() => {
  if (sessionEndTimeout) clearTimeout(sessionEndTimeout)
  socket?.close()
})

const confirmEnd = async () => {
  if (!Number.isFinite(sessionId)) return
  showConfirmEndDialog.value = true
}

const executeEndSession = async () => {
  showConfirmEndDialog.value = false
  
  try {
    await sessionsService.endSession(sessionId)
    socket?.close()
    clearPersistedState()
    showSuccessEndDialog.value = true
  } catch (err) {
    console.error(err)
    showErrorEndDialog.value = true
  }
}

const ensureUTCString = (dateString) => {
  if (!dateString) return dateString
  if (typeof dateString === 'string' && !dateString.endsWith('Z') && !dateString.includes('+')) {
    return dateString + 'Z'
  }
  return dateString
}

const formatLocalDate = (utcString) => {
  if (!utcString) return 'N/D'
  const date = new Date(ensureUTCString(utcString))
  const day = String(date.getDate()).padStart(2, '0')
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const year = String(date.getFullYear()).slice(-2)
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  return `${day}/${month}/${year}, ${hours}:${minutes}`
}

// Helpers de persistencia local
const clearPersistedState = () => {
  try {
    localStorage.removeItem(stateStorageKey)
  } catch (e) {
    console.warn('No se pudo limpiar el estado local (terapeuta):', e)
  }
}

const persistState = () => {
  try {
    const payload = {
      latestImage: latestImage.value,
      chatMessages: chatMessages.value,
      artworkConfirmed: artworkConfirmed.value,
    }
    localStorage.setItem(stateStorageKey, JSON.stringify(payload))
  } catch (e) {
    console.warn('No se pudo guardar el estado local (terapeuta):', e)
  }
}

const restoreState = () => {
  try {
    const raw = localStorage.getItem(stateStorageKey)
    if (!raw) return
    const saved = JSON.parse(raw)
    if (typeof saved?.latestImage === 'string') latestImage.value = saved.latestImage
    if (Array.isArray(saved?.chatMessages)) chatMessages.value = saved.chatMessages
    if (typeof saved?.artworkConfirmed === 'boolean') artworkConfirmed.value = saved.artworkConfirmed
  } catch (e) {
    console.warn('No se pudo restaurar el estado local (terapeuta):', e)
  }
}

// Persistir cuando cambian piezas clave
watch(latestImage, persistState)
watch(chatMessages, persistState, { deep: true })
</script>

<template>
  <div class="flex flex-col">
    <!-- DIÁLOGO DE CONFIRMACIÓN PARA FINALIZAR SESIÓN -->
    <AlertDialog :open="showConfirmEndDialog" @update:open="(val) => showConfirmEndDialog = val">
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>¿Finalizar sesión?</AlertDialogTitle>
          <AlertDialogDescription>
            Esta acción terminará la sesión para ambos participantes y no se puede deshacer.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Cancelar</AlertDialogCancel>
          <AlertDialogAction @click="executeEndSession">Finalizar</AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>

    <!-- DIÁLOGO DE ÉXITO -->
    <AlertDialog :open="showSuccessEndDialog" @update:open="(val) => showSuccessEndDialog = val">
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Sesión finalizada</AlertDialogTitle>
          <AlertDialogDescription>
            La sesión ha sido finalizada correctamente.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <div class="flex justify-end">
          <AlertDialogAction @click="router.push('/home')">
            Volver al inicio
          </AlertDialogAction>
        </div>
      </AlertDialogContent>
    </AlertDialog>

    <!-- DIÁLOGO DE ERROR -->
    <AlertDialog :open="showErrorEndDialog" @update:open="(val) => showErrorEndDialog = val">
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Error</AlertDialogTitle>
          <AlertDialogDescription>
            Ha ocurrido un error al finalizar la sesión. Por favor, inténtalo de nuevo.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <div class="flex justify-end">
          <AlertDialogAction @click="showErrorEndDialog = false">
            Cerrar
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
          <AlertDialogAction @click="() => { clearPersistedState(); router.push('/home'); }">
            Volver al inicio
          </AlertDialogAction>
        </div>
      </AlertDialogContent>
    </AlertDialog>

    <!-- DIÁLOGO DE DETALLES DE SESIÓN -->
    <Dialog :open="showDetails" @update:open="(val) => !val && (showDetails = false)">
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Detalles de la sesión</DialogTitle>
          <DialogDescription>Consulta la información detallada de la sesión actual.</DialogDescription>
        </DialogHeader>
        <dl v-if="sessionInfo" class="grid grid-cols-2 gap-x-1.5 gap-y-1 text-m">
          <dt class="font-semibold">Paciente</dt>
          <dd>{{ patientUser?.full_name ?? 'Cargando...' }}</dd>

          <dt class="font-semibold">Fecha</dt>
          <dd>{{ formatLocalDate(sessionInfo.start_date).slice(0, 8) }}</dd>

          <dt class="font-semibold">Hora</dt>
          <dd>{{ formatLocalDate(sessionInfo.start_date).slice(10, 16) }} - {{ formatLocalDate(sessionInfo.end_date).slice(10, 16) }}</dd>

        </dl>
      </DialogContent>
    </Dialog>

    <!-- CONTENIDO PRINCIPAL -->
    <div v-if="sessionInfo && !sessionInfo.ended_at" class="bg-slate-300/30 min-h-[calc(100vh-4rem)]">
      <div class="max-w-7xl mx-auto px-6 py-4 space-y-4">
        <!-- HEADER -->
        <div class="flex items-start justify-between gap-3">
          <div class="space-y-1">
            <h1 class="text-2xl font-semibold text-slate-900">
              {{ artworkConfirmed ? 'El paciente ha completado su obra' : 'Se está generando la obra' }}
            </h1>
            <p class="text-sm text-slate-600">
              {{ artworkConfirmed ? 'El paciente ha finalizado su obra.' : 'El paciente está trabajando en su obra.' }}
            </p>
          </div>

          <!-- BOTÓN DE INFORMACIÓN -->
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

        <!-- LAYOUT IMAGEN + CHAT -->
        <div class="grid gap-6 lg:grid-cols-[1.3fr_1fr] items-start">
          <!-- IMAGEN -->
          <Card class="min-h-[600px] max-h-[600px] flex flex-col min-w-[420px]">
            <CardContent class="flex items-center justify-center p-6">
              <div v-if="latestImage" class="w-full min-w-[420px]">
                <img
                  :src="latestImage"
                  class="w-full max-h-[70vh] rounded-xl border shadow-md object-contain bg-white"
                />
              </div>
              <div v-else class="text-center text-muted-foreground space-y-2">
                <ImageIcon class="h-12 w-12 mx-auto opacity-50" />
                <p class="text-sm">Esperando imagen del paciente...</p>
              </div>
            </CardContent>
          </Card>

          <!-- CHAT -->
          <ChatPanel
            class="h-full"
            :messages="chatMessages"
            :role="role"
            :otherUser="patientUser"
            title="Chat con paciente"
            selfTone="blue"
            otherTone="gray"
            otherLabel="Paciente"
            @send="(text) => sendChatMessage(text)"
          />
        </div>

        <!-- BOTÓN FINALIZAR SESIÓN -->
        <div class="flex justify-center pt-2">
          <Button
            size="lg"
            variant="destructive"
            class="px-10 py-5 text-lg font-bold rounded-full shadow-lg"
            @click="confirmEnd"
          >
            Finalizar sesión
          </Button>
        </div>
      </div>
    </div>

    <!-- SESIÓN FINALIZADA -->
    <div v-else class="min-h-[calc(100vh-4rem)]">
      <AlertDialog :open="true" @update:open="(v) => { if (!v) router.push('/home') }">
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Sesión finalizada</AlertDialogTitle>
            <AlertDialogDescription>
              La sesión ha sido cerrada. Puedes volver al inicio.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <div class="flex justify-end">
            <AlertDialogAction @click="router.push('/home')">
              Volver al inicio
            </AlertDialogAction>
          </div>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  </div>
</template>
