<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { userService } from '../api/userService'

const email = ref('')
const password = ref('')
const message = ref('')

const router = useRouter()

const login = async () => {
  try {
    const credentials = { email: email.value, password: password.value }
    const response = await userService.login(credentials)
    message.value = 'Inicio de sesión exitoso'
    router.push('/home')
  } catch (error) {
    message.value = error.response?.data?.detail || 'Error al iniciar sesión'
  }
}
</script>

<template>
  <div>
    <h1>Iniciar sesión</h1>
    <input v-model="email" type="email" placeholder="Email" />
    <input v-model="password" type="password" placeholder="Contraseña" />
    <button @click="login">Entrar</button>
    <p>{{ message }}</p>
  </div>
</template>
