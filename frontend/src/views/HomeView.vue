<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { userService } from '../api/userService'
import { sessionsService } from '../api/sessionsService'

import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Loader2 } from 'lucide-vue-next'
import CreateSessionModal from '@/components/CreateSessionModal.vue'

const router = useRouter()
const user = ref(null)
const loading = ref(true)
const errorMsg = ref('')
const activeSession = ref(null)
const nextSession = ref(null)
const anotherUserSession = ref(null)
const startTime = ref('')
const endTime =  ref('')
const nextStartTime = ref('')
const nextEndTime = ref('')
const nextDate = ref('')
const nextAnotherUserSession = ref(null)
const patients = ref([])
const showCreateModal = ref(false)
const sessionsList = ref([])

import { useDateHelpers } from '@/lib/useDateHelpers'

const {
  ensureUTCString,
  formatLocalDate
} = useDateHelpers()


onMounted(async () => {
  try {
    user.value = await userService.getCurrentUser()
  } catch (error) {
    console.error('Error al obtener el usuario:', error)
    errorMsg.value = error.response?.data?.detail || 'No autenticado'
  }

  // Cargar lista de pacientes si es terapeuta
  if (user.value?.type === 'therapist') {
    try {
      const allUsers = await userService.getUsers()
      patients.value = Array.isArray(allUsers) ? allUsers.filter(u => u.type === 'patient') : []
    } catch (e) {
      patients.value = []
    }
  }

  // obtener sesión activa (si existe)
  try {
    activeSession.value = await sessionsService.getActiveSession()
    if(user.value.type === 'patient' && activeSession.value){
      anotherUserSession.value = await userService.getUserById(activeSession.value.therapist_id)
    } else {
      anotherUserSession.value = await userService.getUserById(activeSession.value.patient_id)
    }
    startTime.value = formatLocalDate(activeSession.value.start_date).slice(10, 16)
    endTime.value = formatLocalDate(activeSession.value.end_date).slice(10, 16)
  } catch (e) {
    activeSession.value = null
    try{
    if(!activeSession.value){
      // No hay sesión activa, obtener la próxima sesión programada
      nextSession.value = await sessionsService.getNextSession()
      nextDate.value = formatLocalDate(nextSession.value.start_date).slice(0, 8)
      nextStartTime.value = formatLocalDate(nextSession.value.start_date).slice(10, 16)
      nextEndTime.value = formatLocalDate(nextSession.value.end_date).slice(10, 16)
      if(user.value.type === 'patient' && nextSession.value){
        nextAnotherUserSession.value = await userService.getUserById(nextSession.value.therapist_id)
      } else {
        nextAnotherUserSession.value = await userService.getUserById(nextSession.value.patient_id)
      }
    }
    } catch (error) {
      console.error('Error al obtener la próxima sesión:', error)
      nextSession.value = null
    }
  } finally {
    loading.value = false
  }

  // Cargar todas las sesiones para detección de solapamiento
  await loadSessions()
})


const loadSessions = async () => {
  try {
    const sessions = await sessionsService.getMySessions();
    const list = Array.isArray(sessions?.data) ? sessions.data : (Array.isArray(sessions) ? sessions : []);
    sessionsList.value = list
  } catch (e) {
    console.error('Error loading sessions:', e)
    sessionsList.value = []
  }
}

const handleSessionCreated = async () => {
  try {
    activeSession.value = await sessionsService.getActiveSession()
  } catch (e) {
    activeSession.value = null
  }
  try {
    nextSession.value = await sessionsService.getNextSession()
    if (nextSession.value) {
      nextDate.value = formatLocalDate(nextSession.value.start_date).slice(0, 8)
      nextStartTime.value = formatLocalDate(nextSession.value.start_date).slice(10, 16)
      nextEndTime.value = formatLocalDate(nextSession.value.end_date).slice(10, 16)
      if(user.value.type === 'patient' && nextSession.value){
        nextAnotherUserSession.value = await userService.getUserById(nextSession.value.therapist_id)
      } else {
        nextAnotherUserSession.value = await userService.getUserById(nextSession.value.patient_id)
      }
    }
  } catch (e) {
    nextSession.value = null
  }
  await loadSessions()
  showCreateModal.value = false
  // Forzar recarga completa de la página para refrescar Home
  window.location.reload()
}
</script>

<template>
  <div class="flex justify-center mt-10 px-4">
    <!-- LOADING -->
    <Card v-if="loading" class="w-full max-w-md p-6 flex items-center justify-center">
      <Loader2 class="animate-spin mr-2" />
      <span>Cargando usuario...</span>
    </Card>

    <!-- SIN CARGA -->
    <Card
      v-else
      class="w-full max-w-md transition-all duration-300 min-w-[400px]"
      :class="{
        'shadow-lg': activeSession,
        'shadow-sm': !activeSession
      }"
    >

      <!-- HEADER -->
      <CardHeader :class="!activeSession ? 'opacity-60' : ''">
        <CardTitle class="text-xl font-bold flex items-center gap-2">
          {{ activeSession ? "Accede a la sesión activa" : "No hay sesión activa" }}
        </CardTitle>

        <CardDescription>
          <span v-if="activeSession">
            Tienes una sesión activa en este momento. Accede a esta para comunicarte con tu 
            {{ user.type === 'patient' ? "terapeuta" : "paciente" }}.
          </span>
          <span v-else>
            No tienes ninguna sesión en curso.
          </span>
        </CardDescription>
      </CardHeader>

      <!-- CONTENT -->
      <CardContent :class="!activeSession ? 'opacity-60' : ''">
        <div v-if="activeSession" class="space-y-1">
          <p class="text-gray-700 font-medium text-lg">
            Datos de la sesión:
          </p>

          <p class="text-gray-500 text-sm">
            <span class="font-bold">{{ user.type === 'patient' ? "Terapeuta" : "Paciente" }}:</span> {{ anotherUserSession.full_name }}
          </p>
          <p class="text-gray-500 text-sm">
            <span class="font-bold">Horario de la sesión:</span> {{ startTime }} - {{ endTime }}
          </p>
        </div>

        <div v-else class="text-gray-600 italic">
          <div v-if="nextSession">
            Tu próxima sesión está programada para el {{ nextDate }} de {{ nextStartTime }} a {{ nextEndTime }}
            con el {{ user.type === 'patient' ? "terapeuta" : "paciente" }} {{ nextAnotherUserSession.full_name }}.
          </div>
          <div v-else>
            En este momento no tienes ninguna sesión programada.
          </div>
        </div>
      </CardContent>

      <!-- FOOTER -->
      <CardFooter class="flex justify-end">

        <!-- BOTÓN SI HAY SESIÓN ACTIVA -->
        <Button
          v-if="activeSession && !activeSession.ended_at && user"
          @click="() =>
            router.push(
              user.type === 'patient'
                ? `/session/${activeSession.id}/patient`
                : `/session/${activeSession.id}/therapist`
            )"
          class="w-full bg-cyan-600"
        >
          Acceder a la sesión
        </Button>

        <!-- NO HAY SESIÓN - PACIENTE -->
        <Button
          v-else-if="user?.type === 'patient'"
          class="w-full bg-emerald-600 text-white hover:bg-emerald-700 shadow-sm hover:shadow-md"
          @click="() =>
            router.push('/generation')"
        >
          Acceder a la generación libre
        </Button>

        <!-- NO HAY SESIÓN - TERAPEUTA -->
        <Button
          v-else-if="user?.type === 'therapist'"
          class="w-full bg-emerald-600 text-white hover:bg-emerald-700 shadow-sm hover:shadow-md"
          @click="showCreateModal = true"
        >
          Añadir una nueva sesión
        </Button>
      </CardFooter>
    </Card>

    <CreateSessionModal
      :open="showCreateModal"
      @update:open="showCreateModal = $event"
      :patients="patients"
      :existing-sessions="sessionsList"
      @session-created="handleSessionCreated"
    />
  </div>
</template>

