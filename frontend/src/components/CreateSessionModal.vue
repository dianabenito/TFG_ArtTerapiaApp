<template>
  <div style="display: contents">
  <Dialog :open="open" @update:open="(val) => !val && handleClose()">
    <DialogContent>
      <DialogHeader>
        <DialogTitle>Crear una nueva sesión</DialogTitle>
        <DialogDescription>
          Rellena los detalles para programar una nueva sesión.
        </DialogDescription>
      </DialogHeader>

      <form class="create-form" @submit.prevent="handleCreateSession">
        <div class="grid gap-4">
          <!-- Paciente -->
          <div class="grid gap-2">
            <Label for="patient">Paciente</Label>
            <Popover :open="openCB" @update:open="openCB = $event">
              <PopoverTrigger as-child>
                <Button
                  variant="outline"
                  role="combobox"
                  :aria-expanded="openCB"
                  class="w-full justify-between text-left font-normal"
                >
                  {{
                    formData.patientId != null
                      ? patients.find(patient => patient.id === formData.patientId)?.full_name
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
                          formData.patientId = patient.id
                          openCB = false
                        }"
                      >
                          <CheckIcon
                            :class="[ 'h-4 w-4', formData.patientId === patient.id ? 'opacity-100' : 'opacity-0' ]"
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
                  {{ formData.date ? formData.date.toString() : "Selecciona fecha" }}
                </Button>
              </PopoverTrigger>
              <PopoverContent class="w-full p-0" align="start">
                <Calendar
                  v-model="formData.date"
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
              v-model="formData.startTime"
              class="w-full"
            />
          </div>

          <!-- Hora fin -->
          <div class="grid gap-2">
            <Label for="horaFin">Hora de fin</Label>
            <Input
              id="horaFin"
              type="time"
              v-model="formData.endTime"
              class="w-full"
            />
          </div>

          <Alert v-if="errorMessage" class="bg-red-100 text-red-800 border border-red-300">
            <AlertCircleIcon class="h-4 w-4" />
            <AlertTitle>Error al crear la sesión</AlertTitle>
            <AlertDescription class="text-red-800">
              {{ errorMessage }}
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
          La sesión que intentas crear coincide con otra ya agendada.
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
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { sessionsService } from '../api/sessionsService'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { getLocalTimeZone, today } from '@internationalized/date'
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
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { toast } from 'vue-sonner'

import { useDateHelpers } from '@/lib/useDateHelpers'

const {
  ensureUTCString,
  localToUTC
} = useDateHelpers()

interface Props {
  open: boolean
  patients: Array<{ id: number; full_name: string }>
  existingSessions: Array<{ id: number; start_date: string; end_date: string }>
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'update:open', value: boolean): void
  (e: 'session-created'): void
}>()

const formData = ref<{ patientId: number | null; date: any; startTime: string; endTime: string }>({ patientId: null, date: null, startTime: '', endTime: '' })
const openCB = ref(false)
const defaultPlaceholder = today(getLocalTimeZone())
// no DateFormatter needed; we show YYYY-MM-DD from DateValue.toString()
const showOverlapDialog = ref(false)
const overlapAction = ref<null | (() => Promise<void>)>(null)
const errorMessage = ref('')

// Resetear formulario cuando se cierra el modal
watch(() => props.open, (newVal) => {
  if (!newVal) {
    resetForm()
  }
})

const handleCreateSession = async () => {
  try {
    errorMessage.value = ''
    if (formData.value.patientId == null || !formData.value.date || !formData.value.startTime || !formData.value.endTime) {
      errorMessage.value = 'Completa todos los campos'
      return
    }

    if (formData.value.startTime >= formData.value.endTime) {
      errorMessage.value = 'La hora de inicio debe ser anterior a la hora de fin'
      return
    }

    const startDateTime = localToUTC(formData.value.date, formData.value.startTime);
    const endDateTime = localToUTC(formData.value.date, formData.value.endTime);
    const newStart = new Date(startDateTime);
    const newEnd = new Date(endDateTime);
    const session_data = {
      start_date: startDateTime,
      end_date: endDateTime,
    }
    
    const overlap = props.existingSessions.find(s => {
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

const doCreateSession = async (session_data: { start_date: string; end_date: string }) => {
  try {
    console.log('Creando sesión para paciente:', formData.value.patientId, session_data)
    await sessionsService.createSession(formData.value.patientId as number, session_data)
    console.log('Sesión creada exitosamente')
    toast.success('Sesión creada correctamente')
    emit('session-created')
    handleClose()
  } catch (error) {
    console.error('Error al crear sesión:', error)
    errorMessage.value = error?.response?.data?.detail || 'Error al crear sesión'
  }
}

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

const resetForm = () => {
  formData.value = { patientId: null, date: null, startTime: '', endTime: '' }
  errorMessage.value = ''
}

const handleClose = () => {
  emit('update:open', false)
}
</script>
