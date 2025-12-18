<template>
  <div class="mx-auto p-4 min-h-[calc(100vh-4rem)] space-y-4 bg-slate-300/30">
    <div class="flex flex-wrap items-center justify-between gap-3 px-6">
      <div class="space-y-1">
        <h1 class="text-2xl font-semibold text-slate-900">Calendario</h1>
        <p v-if="user?.type === 'therapist'" class="text-sm text-slate-600">Consulta tu agenda y gestiona tus sesiones.</p>
        <p v-if="user?.type === 'patient'" class="text-sm text-slate-600">Consulta las sesiones programadas en tu agenda.</p>
      </div>
    </div>

    <div class="rounded-2xl border border-slate-200 bg-white shadow-sm overflow-hidden mx-6">
      <FullCalendar
        :options="calendarOptions"
        @eventClick="handleEventClick"
        class="fc-shadcn"
      />
    </div>

    <Dialog :open="showModal"  @update:open="(val) => !val && closeModal()" >
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Detalles de la sesión</DialogTitle>
          <DialogDescription>
            Consulta la información detallada de la sesión seleccionada.
          </DialogDescription>
        </DialogHeader>
        <div v-if="selectedSession">
          <dl class="grid grid-cols-2 gap-x-1.5 gap-y-1 text-m">
            <template v-if="user?.type === 'therapist'">
              <dt class="font-semibold">Paciente</dt>
              <dd>{{ patient?.full_name ?? 'Cargando...' }}</dd>
            </template>
            <template v-else>
              <dt class="font-semibold">Terapeuta</dt>
              <dd>{{ therapist?.full_name ?? 'Cargando...' }}</dd>
            </template>

            <dt class="font-semibold">Fecha</dt>
            <dd>{{ formatLocalDate(selectedSession.start_date).slice(0,8) }}</dd>

            <dt class="font-semibold">Hora</dt>
            <dd>{{ formatLocalDate(selectedSession.start_date).slice(10,16) }} - {{ formatLocalDate(selectedSession.end_date).slice(10,16) }}</dd>
          </dl>

          <div class="mt-4 flex justify-end gap-2">
            <Button class="bg-cyan-600" v-if="isSessionActive(selectedSession)" @click="router.push(`/session/${selectedSession.id}/${user?.type}`)">
              Ir a sesión activa
            </Button>
            <Button v-if="user?.type==='therapist' && canModify(selectedSession)" variant="destructive" @click="eliminarSesion(selectedSession.id)">
              Cancelar sesión
            </Button>
            <Button v-if="user?.type==='therapist' && canModify(selectedSession)" variant="default" @click="actualizarSesion(selectedSession.id)">
              Actualizar sesión
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>

    <Dialog :open="showCreateModal" @update:open="(val) => !val && closeCreate()">
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Crear una nueva sesión</DialogTitle>
          <DialogDescription>
            Rellena los detalles para programar una nueva sesión.
          </DialogDescription>
        </DialogHeader>

        <form class="create-form" @submit.prevent="createSession">
          <div class="grid gap-4">
            <!-- Paciente -->
            <div class="grid gap-2">
              <Label for="patient">Paciente</Label>
              <Popover v-model:open="openCB">
                <PopoverTrigger as-child>
                  <Button
                    variant="outline"
                    role="combobox"
                    :aria-expanded="openCB"
                    class="w-full justify-between text-left font-normal"
                  >
                    {{
                      newSession.patientId
                        ? patients.find(patient => patient.id === newSession.patientId)?.full_name
                        : 'Selecciona paciente...'
                    }}
                    <ChevronsUpDownIcon class="ml-2 h-4 w-4 shrink-0 opacity-50" />
                  </Button>
                </PopoverTrigger>

                <PopoverContent class="w-full p-0">
                  <Command>
                    <CommandInput placeholder="Buscar paciente..." />
                    <CommandList>
                      <CommandEmpty>No se encontró el paciente.</CommandEmpty>
                      <CommandGroup>
                        <CommandItem
                          v-for="patient in patients"
                          :key="patient.id"
                          :value="patient.id"
                          @select="() => {
                            newSession.patientId = newSession.patientId === patient.id ? '' : patient.id
                            openCB = false
                          }"
                        >
                          <CheckIcon
                            :class="cn(
                              'h-4 w-4',
                              newSession.patientId === patient.id ? 'opacity-100' : 'opacity-0',
                            )"
                          />
                          {{ patient.full_name }}
                        </CommandItem>
                      </CommandGroup>
                    </CommandList>
                  </Command>
                </PopoverContent>
              </Popover>
            </div>

            <!-- Fecha -->
            <div class="grid gap-2">
              <Label for="date">Fecha</Label>
              <Popover v-slot="{ close }">
                <PopoverTrigger as-child>
                  <Button
                    variant="outline"
                    class="w-full justify-start text-left font-normal"
                  >
                    <CalendarIcon class="h-4 w-4" />
                    {{ newSession.date ? df.format(newSession.date.toDate(getLocalTimeZone())) : "Selecciona fecha" }}
                  </Button>
                </PopoverTrigger>
                <PopoverContent class="w-full p-0" align="start">
                  <Calendar
                    v-model="newSession.date"
                    :default-placeholder="defaultPlaceholder"
                    :min-value="today(getLocalTimeZone())"
                    layout="month-and-year"
                    initial-focus
                    @update:model-value="close"
                  />
                </PopoverContent>
              </Popover>
            </div>

            <!-- Hora inicio -->
            <div class="grid gap-2">
              <Label for="horaInicio">Hora de inicio</Label>
              <Input
                id="horaInicio"
                type="time"
                v-model="newSession.startTime"
                class="w-full"
              />
            </div>

            <!-- Hora fin -->
            <div class="grid gap-2">
              <Label for="horaFin">Hora de fin</Label>
              <Input
                id="horaFin"
                type="time"
                v-model="newSession.endTime"
                class="w-full"
              />
            </div>

            <Alert v-if="newSessionError" class="bg-red-100 text-red-800 border border-red-300">
              <AlertCircleIcon class="h-4 w-4" />
              <AlertTitle>Error al crear la sesión</AlertTitle>
              <AlertDescription class="text-red-800">
                {{ newSessionError }}
              </AlertDescription>
            </Alert>

            <!-- Botón de confirmación -->
            <div class="flex justify-end mt-4">
              <Button type="submit" variant="default">Confirmar</Button>
            </div>

          </div>
        </form>
      </DialogContent>
    </Dialog>

    <Dialog :open="showUpdateModal" @update:open="(val) => !val && closeUpdate()">
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Actualizar la fecha de la sesión</DialogTitle>
          <DialogDescription>
            Rellena los detalles para modificar la fecha y hora de la sesión programada.
          </DialogDescription>
        </DialogHeader>

        <form class="create-form" @submit.prevent="actualizarSesionConfirm(selectedSession.id)">
          <div class="grid gap-4">

            <!-- Fecha -->
            <div class="grid gap-2">
              <Label for="date">Fecha</Label>
              <Popover v-slot="{ close }">
                <PopoverTrigger as-child>
                  <Button
                    variant="outline"
                    class="w-full justify-start text-left font-normal"
                  >
                    <CalendarIcon class="h-4 w-4" />
                    {{ updateForm.date ? df.format(updateForm.date.toDate(getLocalTimeZone())) : "Selecciona fecha" }}
                  </Button>
                </PopoverTrigger>
                <PopoverContent class="w-full p-0" align="start">
                  <Calendar
                    v-model="updateForm.date"
                    :default-placeholder="defaultPlaceholder"
                    :min-value="today(getLocalTimeZone())"
                    layout="month-and-year"
                    initial-focus
                    @update:model-value="close"
                  />
                </PopoverContent>
              </Popover>
            </div>

            <!-- Hora inicio -->
            <div class="grid gap-2">
              <Label for="horaInicio">Hora de inicio</Label>
              <Input
                type="time"
                v-model="updateForm.startTime"
                class="w-full"
              />
            </div>

            <!-- Hora fin -->
            <div class="grid gap-2">
              <Label for="horaFin">Hora de fin</Label>
              <Input
                type="time"
                v-model="updateForm.endTime"
                class="w-full"
              />
            </div>

            <Alert v-if="updSessionError" class="bg-red-100 text-red-800 border border-red-300">
              <AlertCircleIcon class="h-4 w-4" />
              <AlertTitle>Error al actualizar la sesión</AlertTitle>
              <AlertDescription class="text-red-800">
                {{ updSessionError }}
              </AlertDescription>
            </Alert>

            <!-- Botón de confirmación -->
            <div class="flex justify-end mt-4">
              <Button type="submit" variant="default">Confirmar</Button>
            </div>
          </div>
        </form>
      </DialogContent>
    </Dialog>

    <AlertDialog :open="showOverlapDialog" @update:open="showOverlapDialog = $event">
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Sesión solapada</AlertDialogTitle>
          <AlertDialogDescription>
            La sesión que intentas actualizar coincide con otra ya agendada.
            ¿Deseas continuar igualmente?
          </AlertDialogDescription>
        </AlertDialogHeader>

        <AlertDialogFooter>
          <AlertDialogCancel @click="cancelOverlap">Cancelar</AlertDialogCancel>
          <AlertDialogAction @click="confirmOverlap">
            Continuar
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>

    <AlertDialog :open="showCancelDialog" @update:open="showCancelDialog = $event">
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Cancelar sesión</AlertDialogTitle>
          <AlertDialogDescription>
            Esta acción cancelará la sesión seleccionada. ¿Deseas continuar?
          </AlertDialogDescription>
        </AlertDialogHeader>

        <AlertDialogFooter>
          <AlertDialogCancel @click="cancelCancel">Mantener</AlertDialogCancel>
          <AlertDialogAction @click="confirmCancel" variant="destructive">
            Cancelar sesión
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import FullCalendar from "@fullcalendar/vue3";
import dayGridPlugin from "@fullcalendar/daygrid";
import { userService } from '../api/userService';
import { sessionsService } from '../api/sessionsService';
import { useRouter } from "vue-router";

import { Button } from '@/components/ui/button'
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
import type { DateValue } from '@internationalized/date'
import { DateFormatter, getLocalTimeZone, today, parseDate } from '@internationalized/date'
import { CheckIcon, ChevronsUpDownIcon, CalendarIcon, AlertCircleIcon } from 'lucide-vue-next'
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from '@/components/ui/command'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover'
import { Calendar } from '@/components/ui/calendar'
import { cn } from '@/lib/utils'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { toast } from 'vue-sonner'


const showModal = ref(false)
const selectedSession = ref(null)
const router = useRouter()
const loading = ref(true)
const activeSession = ref(null)
const user = ref(null)
const patients = ref([])
const showCreateModal = ref(false)
const newSession = ref({ patientId: '', date: '', startTime: '', endTime: '' })
const updateForm = ref({ date: '', startTime: '', endTime: '' })
const sessionsList = ref([])
const showUpdateModal = ref(false)
const patient = ref(null)
const therapist = ref(null)
const openCB = ref(false)
const defaultPlaceholder = today(getLocalTimeZone())
const df = new DateFormatter('es-ES', {
  dateStyle: 'long',
})
const showOverlapDialog = ref(false)
const overlapAction = ref<null | (() => Promise<void>)>(null)
const showCancelDialog = ref(false)
const cancelAction = ref<null | (() => Promise<void>)>(null)
const newSessionError = ref('')
const updSessionError = ref('')

const confirmOverlap = async () => {
  if (overlapAction.value) {
    await overlapAction.value()
  }
  overlapAction.value = null
  showOverlapDialog.value = false
}

const cancelOverlap = () => {
  overlapAction.value = null
  showOverlapDialog.value = false
}

const confirmCancel = async () => {
  if (cancelAction.value) {
    await cancelAction.value()
  }
  cancelAction.value = null
  showCancelDialog.value = false
}

const cancelCancel = () => {
  cancelAction.value = null
  showCancelDialog.value = false
}


const calendarOptions = ref({
  plugins: [dayGridPlugin],
  initialView: 'dayGridMonth',
  locale: 'es',
  events: [],
  headerToolbar: {
    left: '',
    center: '',
    right: ''
  },
    titleFormat: { // aquí personalizas el título del mes
    year: 'numeric',
    month: 'long'
  },
  buttonText: {
    today: 'Hoy',
    month: 'Mes',
    week: 'Semana',
    day: 'Día'
  },
  eventTimeFormat: {
    hour: '2-digit',
    minute: '2-digit',
    meridiem: false,
    hour12: false
  },
  eventClick: null,
  firstDay: 1,
  height: 'auto',
    customButtons: {
    customCreateButton: {
      text: 'Crear nueva sesión',
      click: () => {
        showCreateModal.value = true;
      }
    }
  },
})

onMounted(async () => {
  try {
    user.value = await userService.getCurrentUser()
    if (user.value && user.value.type === 'therapist') {
      calendarOptions.value.headerToolbar.left = 'prev,next today';
      calendarOptions.value.headerToolbar.center = 'title';
      calendarOptions.value.headerToolbar.right = 'customCreateButton';
    } else {
      calendarOptions.value.headerToolbar.left = 'title';
      calendarOptions.value.headerToolbar.right = 'prev,next today';
    }
  } catch (e) {
    user.value = null
  }

  try {
    const allUsers = await userService.getUsers()
    patients.value = Array.isArray(allUsers) ? allUsers.filter(u => u.type === 'patient') : []
  } catch (e) {
    patients.value = []
  }
  await loadSessions()
  try {
    activeSession.value = await sessionsService.getActiveSession()
    console.log('Active session:', activeSession.value)
  } catch (e) {
    activeSession.value = null
  }
  // Rebuild events once we know the active session, so green class applies
  await loadSessions()
  loading.value = false
});

async function handleEventClick(info) {
  selectedSession.value = info.event.extendedProps?.session || null
  
  // Load patient or therapist for this specific session
  if (selectedSession.value) {
    if (user.value?.type === 'therapist') {
      try {
        patient.value = await userService.getUserById(selectedSession.value.patient_id)
      } catch (e) {
        console.error('Error loading patient:', e)
        patient.value = null
      }
    } else {
      try {
        therapist.value = await userService.getUserById(selectedSession.value.therapist_id)
      } catch (e) {
        console.error('Error loading therapist:', e)
        therapist.value = null
      }
    }
  }
  
  showModal.value = true
}

const closeModal = () => {
  showModal.value = false
  selectedSession.value = null
}

const isSessionActive = (session) => {
  if (!session || !activeSession.value) return false
  return session.id === activeSession.value.id
}

const eliminarSesion = async (sessionId) => {
  cancelAction.value = async () => await doDeleteSession(sessionId)
  showCancelDialog.value = true
}

const doDeleteSession = async (sessionId) => {
  try {
    await sessionsService.deleteSession(sessionId)
    toast.success('Sesión cancelada correctamente')
    await loadSessions()
    closeModal()
  } catch (e) {
    console.error('Error cancelando sesión:', e)
    toast.error('No se pudo cancelar la sesión')
  }
}

const actualizarSesion = (sessionId) => {
  const session = sessionsList.value.find(s => s.id === sessionId)
  if (!session) {
    toast.error('Sesión no encontrada')
    return
  }
  selectedSession.value = { ...session }
  
  const start = utcToLocalInput(session.start_date);
  const end = utcToLocalInput(session.end_date);

  updateForm.value = {
    date: parseDate(start.date),
    startTime: start.time,
    endTime: end.time
  }


  showUpdateModal.value = true
  showModal.value = false
}

const actualizarSesionConfirm = async (sessionId) => {
  try {
    if (updateForm.value.startTime >= updateForm.value.endTime) {
      updSessionError.value = 'La hora de inicio debe ser anterior a la hora de fin'
      return
    }

    const startDateTime = localToUTC(updateForm.value.date, updateForm.value.startTime)
    const endDateTime = localToUTC(updateForm.value.date, updateForm.value.endTime)
    const newStart = new Date(startDateTime)
    const newEnd = new Date(endDateTime)
    
    const overlap = sessionsList.value.find(s => {
      if (!s.start_date || !s.end_date) return false
      if (s.id === sessionId) return false // Excluir la sesión que se está modificando
      const sStart = new Date(ensureUTCString(s.start_date))
      const sEnd = new Date(ensureUTCString(s.end_date))
      return newStart < sEnd && newEnd > sStart
    })

    if (overlap) {
      overlapAction.value = async () => await doUpdateSession(sessionId)
      showOverlapDialog.value = true
      return
    }

    await doUpdateSession(sessionId)

  } catch (e) {
    console.error('Error actualizando sesión:', e)
    toast.error('No se pudo actualizar la sesión')
  }
}

const doUpdateSession = async (sessionId) => {
  const startDateTime = localToUTC(updateForm.value.date, updateForm.value.startTime)
  const endDateTime = localToUTC(updateForm.value.date, updateForm.value.endTime)
  const session_data = {
    start_date: startDateTime,
    end_date: endDateTime
  }
  
  await sessionsService.updateSession(sessionId, session_data)
  try {
    activeSession.value = await sessionsService.getActiveSession()
  } catch (e) {
    activeSession.value = null
  }
  await loadSessions()
  closeUpdate()
  closeModal()
  toast.success('Sesión actualizada correctamente')
}

const canModify = (session) => {
  if (!session) return false;
  if (isSessionActive(session)) return false;
  if (!session.start_date) return false;
  return new Date(ensureUTCString(session.start_date)) > new Date();
}

const createSession = async () => {
  try {
    newSessionError.value = ''
    if (!newSession.value.patientId || !newSession.value.date || !newSession.value.startTime || !newSession.value.endTime) {
      newSessionError.value = 'Completa todos los campos'
      return
    }

    if (newSession.value.startTime >= newSession.value.endTime) {
      newSessionError.value = 'La hora de inicio debe ser anterior a la hora de fin'
      return
    }

    const startDateTime = localToUTC(newSession.value.date, newSession.value.startTime);
    const endDateTime = localToUTC(newSession.value.date, newSession.value.endTime);
    const newStart = new Date(startDateTime);
    const newEnd = new Date(endDateTime);
    const session_data = {
      start_date: startDateTime,
      end_date: endDateTime,
    }
    
    const overlap = sessionsList.value.find(s => {
      if (!s.start_date || !s.end_date) return false
      const sStart = new Date(ensureUTCString(s.start_date))
      const sEnd = new Date(ensureUTCString(s.end_date))
      return newStart < sEnd && newEnd > sStart
    })

    if (overlap) {
      overlapAction.value = async () => await doCreateSession(session_data)
      showOverlapDialog.value = true
      return
    }

    await doCreateSession(session_data)
  } catch (e) {
    console.error('Error creando sesión:', e)
    toast.error('No se pudo crear la sesión')
  }
}

const doCreateSession = async (session_data) => {
  const created = await sessionsService.createSession(newSession.value.patientId, session_data)
  console.log('Sesión creada:', created)
  try {
    activeSession.value = await sessionsService.getActiveSession()
  } catch (e) {
    activeSession.value = null
  }
  await loadSessions()
  closeCreate()
  toast.success('Sesión creada correctamente')
}

const loadSessions = async () => {
  const sessions = await sessionsService.getMySessions();
  const list = Array.isArray(sessions?.data) ? sessions.data : (Array.isArray(sessions) ? sessions : []);
  sessionsList.value = list

  console.log('Sesiones cargadas:', list);

  // Build event titles: for therapists show patient name + time, for patients show "Sesión"
  const eventTitles = await Promise.all(
    list.map(async (s) => {
      if (user.value?.type === 'therapist') {
        try {
          const patientData = await userService.getUserById(s.patient_id)
          return patientData.full_name
        } catch (e) {
          console.error('Error getting patient:', e)
          return "Sesión"
        }
      }
      else{
        try {
          const therapistData = await userService.getUserById(s.therapist_id)
          return therapistData.full_name
        } catch (e) {
          console.error('Error getting therapist:', e)
          return "Sesión"
        }
      }
    })
  )

  calendarOptions.value = {
    ...calendarOptions.value,
    events: list.map((s, idx) => ({
      title: eventTitles[idx],
      start: dateToLocalString(new Date(ensureUTCString(s.start_date))),
      end: dateToLocalString(new Date(ensureUTCString(s.end_date))),
      displayEventTime: true,
      extendedProps: { session: s },
      classNames: isSessionActive(s) ? ['active-event'] : (s.ended_at ? [] : ['pending-event']),
    })),
    eventClick: handleEventClick,
  };
}

const closeCreate = () => {
  showCreateModal.value = false
  newSession.value = { patientId: '', date: '', startTime: '', endTime: '' }
  newSessionError.value = ''
}

const closeUpdate = () => {
  showUpdateModal.value = false
  selectedSession.value = null
}

// Helper: Asegura que un string UTC tenga 'Z' al final para interpretación correcta
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

const localToUTC = (dateInput, timeStr) => {
  // Si es un DateValue, convertir a string YYYY-MM-DD
  const dateStr = dateInput?.toString ? dateInput.toString() : dateInput;
  const date = new Date(`${dateStr}T${timeStr}:00`);
  return date.toISOString();
}

// Convierte un UTC Date a string "YYYY-MM-DDTHH:mm:ss" (hora local, sin Z)
// para que FullCalendar lo muestre sin desfase
const dateToLocalString = (utcDate) => {
  const year = utcDate.getFullYear();
  const month = String(utcDate.getMonth() + 1).padStart(2, '0');
  const day = String(utcDate.getDate()).padStart(2, '0');
  const hours = String(utcDate.getHours()).padStart(2, '0');
  const minutes = String(utcDate.getMinutes()).padStart(2, '0');
  const seconds = String(utcDate.getSeconds()).padStart(2, '0');
  return `${year}-${month}-${day}T${hours}:${minutes}:${seconds}`;
}

const utcToLocalInput = (utcString) => {
  const date = new Date(ensureUTCString(utcString));

  const dateStr = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Europe/Madrid'
  }).format(date);

  const timeStr = new Intl.DateTimeFormat('es-ES', {
    timeZone: 'Europe/Madrid',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false
  }).format(date);

  return { date: dateStr, time: timeStr };
};

</script>

<style>
.fc-shadcn {
  --fc-border-color: #e2e8f0;
  --fc-button-bg-color: #059669;
  --fc-button-border-color: #059669;
  --fc-button-text-color: #f8fafc;
  --fc-button-hover-bg-color: #047857;
  --fc-button-hover-border-color: #047857;
  --fc-today-bg-color: #f1f5f9;
  --fc-neutral-bg-color: #ffffff;
  --fc-page-bg-color: #ffffff;
  --fc-list-event-dot-width: 8px;
  --fc-event-bg-color: #0ea5e9;
  --fc-event-border-color: #0ea5e9;
  --fc-event-text-color: #f8fafc;
}

.fc-shadcn .fc-toolbar {
  padding-top: 0.75rem;
  padding-right: 1rem;
  padding-left: 1rem;
  gap: 0.65rem;
}

.fc-shadcn .fc-toolbar-title {
  padding-top: 0.5rem;
  font-size: 1.25rem;
  font-weight: 700;
  color: #0f172a;
}

.fc-toolbar-title::first-letter {
  text-transform: uppercase; /* solo la primera letra en mayúscula */
}

.fc-shadcn .fc-button {
  border-radius: 0.75rem;
  font-weight: 600;
  padding: 0.5rem 0.9rem;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06);
  transition: all 0.18s ease;
}

.fc-shadcn .fc-button:focus,
.fc-shadcn .fc-button:focus-visible,
.fc-shadcn .fc-button:active {
  outline: none;
  box-shadow: none;
}

.fc-shadcn .fc-toolbar-chunk {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.fc-shadcn .fc-daygrid-event {
  border-radius: 0.6rem;
  padding: 0.25rem 0.5rem;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.12);
  font-weight: 600;
  font-size: 0.9rem;
  border: none;
}

.fc-shadcn .fc-daygrid-event:hover {
  filter: brightness(0.97);
}

.fc-shadcn .pending-event {
  background-color: #6366f1;
  border-color: #6366f1;
}

.fc-shadcn .active-event {
  background-color: #48d421;
  border-color: #48d421;
}

.fc-shadcn .fc-daygrid-day-number {
  color: #0f172a;
  font-weight: 600;
}


.fc-shadcn .fc-daygrid-day.fc-day-today .fc-daygrid-day-frame {
  background-color: #fffcd5 !important;
  border: 1px solid #899141;
  border-radius: 0.5rem;
}

/* Número del día ligeramente más destacado */
.fc-shadcn .fc-daygrid-day.fc-day-today .fc-daygrid-day-number {
  font-weight: 700; /* un poquito más pesado */
}

.fc-shadcn .fc-col-header-cell-cushion,
.fc-shadcn .fc-daygrid-day-number {
  padding: 0.5rem;
}

.fc-shadcn .fc-col-header-cell-cushion {
  font-size: 0.85rem;
  color: #475569;
  text-transform: capitalize;
}

.fc-shadcn .fc-daygrid-day-frame {
  padding: 0.4rem;
  border-radius: 0.75rem;
}

.fc-shadcn .fc-daygrid-day.fc-day-sat,
.fc-shadcn .fc-daygrid-day.fc-day-sun {
  background-color: #f8fafc;
}

.fc-shadcn .fc-scrollgrid-sync-table {
  border-radius: 0.75rem;
}

.fc-theme-standard td,
.fc-theme-standard th {
  border-color: #e2e8f0;
}


</style>
