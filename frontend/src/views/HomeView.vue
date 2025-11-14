<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { userService } from '../api/userService'

const router = useRouter()
const user = ref(null)
const loading = ref(true)
const errorMsg = ref('')
const activeSession = ref(null)

onMounted(async () => {
  try {
    user.value = await userService.getCurrentUser()
    console.log('Usuario actual:', user.value)
  } catch (error) {
    console.error('Error al obtener el usuario:', error)
    errorMsg.value = error.response?.data?.detail || 'No autenticado'
  }

  // obtener sesión activa (si existe)
  try {
    activeSession.value = await userService.getActiveSession()
    console.log('Active session:', activeSession.value)
  } catch (e) {
    activeSession.value = null
  } finally {
    loading.value = false
  }
})

const logout = () => {
  userService.logout()
  router.push('/login')
}
</script>

<template>
  <div>
    <div v-if="loading">Cargando usuario...</div>

    <div v-else>
      <div v-if="user">
        <p><strong>Email:</strong> {{ user.email }}</p>
        <p><strong>Tipo de usuario:</strong> {{ user.type }}</p>
      </div>

      <div v-else class="muted">
        <p>No has iniciado sesión.</p>
        <p>{{ errorMsg }}</p>
        <router-link to="/login">Ir a iniciar sesión</router-link>
      </div>

      <div>
        <button @click="logout">Cerrar sesión</button>
      </div>

      <div v-if="activeSession" style="margin-top:1rem">
        <p class="muted">Tienes una sesión activa (ID: {{ activeSession.id }})</p>
        <button v-if="user && user.type === 'patient' && !activeSession.ended_at" @click="() => router.push(`/session/${activeSession.id}/patient`)">Ir a mi sesión (Paciente)</button>
        <button v-else-if="user && user.type === 'therapist' && !activeSession.ended_at" @click="() => router.push(`/session/${activeSession.id}/therapist`)">Ir a mi sesión (Terapeuta)</button>
        <p v-else-if="activeSession.ended_at">La sesión está finalizada.</p>
      </div>
    </div>
  </div>
</template>
