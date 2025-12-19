<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { sessionsService } from '../api/sessionsService'
import { userService } from '../api/userService'

import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import {
  Carousel,
  CarouselContent,
  CarouselItem,
  CarouselNext,
  CarouselPrevious,
} from '@/components/ui/carousel'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { ImageIcon, Info } from 'lucide-vue-next'
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

const route = useRoute()
const router = useRouter()
const sessionId = Number(route.params.sessionId)
const sessionInfo = ref(null) 
const images = ref([])
const isLoadingImages = ref(true)
const showDetails = ref(false)
const therapistUser = ref(null)
const role = 'patient'
const active_user = ref(null)
const another_user = ref(null)
const showUnauthorizedDialog = ref(false)

const API_URL = 'http://127.0.0.1:8000'

onMounted(async () => {
  // obtener info de sesión
  if (Number.isFinite(sessionId)) {
    try {
      sessionInfo.value = await sessionsService.getSession(sessionId)
      console.log('Sesión obtenida:', sessionInfo.value)
    } catch (err) {
      console.warn('No se pudo obtener la sesión:', err)
    }
  }

  // obtener usuario actual y validar pertenencia a la sesión
  let authorized = true
  try {
    active_user.value = await userService.getCurrentUser()
  } catch (e) {
    authorized = false
  }

  try {
    const patientId = sessionInfo.value?.patient_id ?? sessionInfo.value?.patient?.id
    const therapistId = sessionInfo.value?.therapist_id ?? sessionInfo.value?.therapist?.id
    authorized = authorized && !!active_user.value && (active_user.value.id === patientId || active_user.value.id === therapistId)
  } catch (e) {
    authorized = false
  }

  if (!authorized) {
    showUnauthorizedDialog.value = true
    isLoadingImages.value = false
    return
  }

  try {
    images.value = await sessionsService.getImagesForSession(sessionId)
    images.value = images.value.data ?? images.value.images ?? []
    console.log('Imágenes de la sesión:', images.value)
  } catch (err) {
    console.warn('No se pudieron obtener las imágenes:', err)
  } finally {
    isLoadingImages.value = false
  }
  
  try{
    if(active_user.value.type === 'therapist'){
      another_user.value = await userService.getUserById(sessionInfo.value.patient_id)
    } else if(active_user.value.type === 'patient'){
      another_user.value = await userService.getUserById(sessionInfo.value.therapist_id)
    }
  }
  catch(e){
    console.warn('No se pudo obtener el otro usuario de la sesión:', e)
  }
})

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

const formatLocalDate = (utcString) => {
  if (!utcString) return 'N/D';
  const ensureUTCString = (dateString) => {
    if (!dateString) return dateString
    if (typeof dateString === 'string' && !dateString.endsWith('Z') && !dateString.includes('+')) {
      return dateString + 'Z'
    }
    return dateString
  }
  const date = new Date(ensureUTCString(utcString))
  const day = String(date.getDate()).padStart(2, '0')
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const year = String(date.getFullYear()).slice(-2)
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  return `${day}/${month}/${year}, ${hours}:${minutes}`;
}

</script>
<template>
  <div>
    <!-- DIÁLOGO DE NO AUTORIZADO -->
    <AlertDialog
      :open="showUnauthorizedDialog"
      @update:open="(v) => { if (!v) router.push('/home') }"
    >
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Acceso no autorizado</AlertDialogTitle>
          <AlertDialogDescription>
            No formas parte de esta sesión. Serás redirigido al inicio.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogAction @click="router.push('/home')">
            Volver al inicio
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>

    <!-- DIÁLOGO DETALLES -->
    <Dialog :open="showDetails" @update:open="(v) => !v && (showDetails = false)">
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Detalles de la sesión</DialogTitle>
          <DialogDescription>
            Consulta la información detallada de la sesión actual.
          </DialogDescription>
        </DialogHeader>

        <dl class="grid grid-cols-2 gap-x-2 gap-y-1 text-sm">
          <dt class="font-semibold">
            {{ active_user?.type === 'therapist' ? 'Paciente' : 'Terapeuta' }}
          </dt>
          <dd>{{ another_user?.full_name ?? 'Cargando...' }}</dd>

          <dt class="font-semibold">Fecha</dt>
          <dd>{{ formatLocalDate(sessionInfo?.start_date).slice(0, 8) }}</dd>

          <dt class="font-semibold">Hora</dt>
          <dd>
            {{ formatLocalDate(sessionInfo?.start_date).slice(10, 16) }} –
            {{ formatLocalDate(sessionInfo?.end_date).slice(10, 16) }}
          </dd>
        </dl>
      </DialogContent>
    </Dialog>

    <!-- CONTENIDO -->
    <div class="bg-slate-300/30 min-h-[calc(100vh-4rem)] py-6">
      <!-- ESTE es el contenedor REAL -->
      <div class="relative mx-auto w-full max-w-4xl px-6 space-y-6">

        <!-- HEADER (sin padding propio) -->
        <div class="flex items-start justify-between gap-4">
          <div class="space-y-1">
            <h1 class="text-2xl font-semibold text-slate-900">
              Sesión {{ formatLocalDate(sessionInfo?.start_date).slice(0, 8) }}
            </h1>
            <p class="text-sm text-slate-600">
              {{ active_user?.type === 'therapist'
                ? 'Consulta las imágenes generadas por el paciente'
                : 'Consulta las imágenes que generaste'
              }}
              durante la sesión del día
              {{ formatLocalDate(sessionInfo?.start_date).slice(0, 8) }}
              en horario
              {{ formatLocalDate(sessionInfo?.start_date).slice(10, 16) }} –
              {{ formatLocalDate(sessionInfo?.end_date).slice(10, 16) }}.
            </p>
          </div>

          <Button
            variant="ghost"
            size="icon"
            class="!h-11 !w-11 rounded-xl shrink-0"
            @click="showDetails = true"
            aria-label="Información"
          >
            <Info class="!h-8 !w-8" />
          </Button>
        </div>

        <!-- IMÁGENES -->
        <div>
          <!-- LOADING -->
          <Card
            v-if="isLoadingImages"
            class="w-full p-8 flex items-center justify-center"
          >
            <span class="text-sm text-muted-foreground">
              Cargando imágenes...
            </span>
          </Card>

          <!-- EMPTY -->
          <Card
            v-else-if="!images || images.length === 0"
            class="w-full p-12 text-center"
          >
            <CardContent class="space-y-3">
              <ImageIcon class="h-12 w-12 mx-auto opacity-50" />
              <p class="text-sm text-slate-600">
                No hay imágenes registradas para esta sesión.
              </p>
            </CardContent>
          </Card>

          <!-- CAROUSEL -->
          <Carousel
            v-else
            class="w-full px-12"
          >
            <CarouselContent>
              <CarouselItem
                v-for="image in images"
                :key="image.id || image.fileName"
              >
                <Card class="w-full">
                  <!-- SOLO padding interno -->
                  <CardContent class="p-6">
                    <img
                      :src="getImageUrl(image.fileName)"
                      alt="Imagen de la sesión"
                      class="w-full aspect-square object-cover rounded-xl border shadow-sm"
                    />
                  </CardContent>
                </Card>
              </CarouselItem>
            </CarouselContent>

            <!-- Flechas 100% dentro del gris -->
            <CarouselPrevious class="absolute left-2 top-1/2 -translate-y-1/2" />
            <CarouselNext class="absolute right-2 top-1/2 -translate-y-1/2" />
          </Carousel>
        </div>

      </div>
    </div>
  </div>
</template>
