<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { userService } from '../api/userService'

const router = useRouter()
const user = ref(null)
const loading = ref(true)
const errorMsg = ref('')

onMounted(async () => {
  try {
    user.value = await userService.getCurrentUser()
    console.log('Usuario actual:', user.value)
  } catch (error) {
    console.error('Error al obtener el usuario:', error)
    errorMsg.value = error.response?.data?.detail || 'No autenticado'
    // if unauthorized, redirect to login (optional)
    // router.push('/login')
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
    </div>
  </div>
</template>
