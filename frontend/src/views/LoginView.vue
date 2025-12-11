<script setup lang="ts">
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { userService } from '../api/userService'

// Importar logo desde assets
import logoImg from '@/assets/utils/logo.png'
import loginBg from '@/assets/utils/fondo_login.jpg'

const email = ref('')
const password = ref('')
const message = ref('')

const bgStyle = computed(() => ({
  backgroundImage: `url(${loginBg})`,
  backgroundSize: 'cover',
  backgroundPosition: 'center',
}))

const router = useRouter()

const login = async () => {
  try {
    const credentials = { email: email.value, password: password.value }
    await userService.login(credentials)
    message.value = 'Inicio de sesión exitoso'
    router.push('/home')
  } catch (error) {
    message.value = error.response?.data?.detail || 'Error al iniciar sesión'
  }
}
</script>

<template>
  <div
    class="relative min-h-screen flex items-center justify-center overflow-hidden px-4"
    :style="bgStyle"
  >
    <div class="absolute inset-0 bg-white/60 backdrop-blur"></div>

    <div class="relative z-10 flex w-full max-w-md flex-col items-center">
      <!-- Logo pequeño / Header simple -->
      <div class="mb-6 text-center">
        <img :src="logoImg" alt="ArtTeràpia App" class="mx-auto h-16 w-16 mb-2" />
        <h1 class="text-2xl font-bold text-gray-900">ArtTeràpia App</h1>
      </div>

      <!-- Card de login -->
      <Card class="w-full text-gray-900 shadow-lg bg-white/95 backdrop-blur border border-white/70">
      <CardHeader>
        <CardTitle>Inicia sesión en tu cuenta</CardTitle>
        <CardDescription>
          Introduce tu correo electrónico para acceder
        </CardDescription>
      </CardHeader>

      <CardContent>
        <form>
          <div class="grid w-full items-center gap-4">
            <div class="flex flex-col space-y-1.5">
              <Label for="email">Correo electrónico</Label>
              <Input id="email" type="email" placeholder="ejemplo@correo.com" v-model="email"/>
            </div>
            <div class="flex flex-col space-y-1.5">
              <Label for="password">Contraseña</Label>
              <Input id="password" type="password" v-model="password"/>
              <div v-if="message" class="text-sm text-red-600 mt-1">
                {{ message }}
              </div>
            </div>
          </div>
        </form>
      </CardContent>

      <CardFooter class="flex flex-col gap-2">
        <Button class="w-full" @click="login">Iniciar sesión</Button>
        <Button variant="outline" class="w-full" @click="() => router.push('/')">
          Crear cuenta
        </Button>
      </CardFooter>
      </Card>
    </div>
  </div>
</template>
