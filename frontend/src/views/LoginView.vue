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
import { Eye, EyeOff } from 'lucide-vue-next'
import { userService } from '../api/userService'

import { AlertCircleIcon} from 'lucide-vue-next'
import {
  Alert,
  AlertDescription,
  AlertTitle,
} from '@/components/ui/alert'

// Importar logo desde assets
import logoImg from '@/assets/utils/logo.png'
import loginBg from '@/assets/utils/fondo_login.jpg'

const email = ref('')
const password = ref('')
const message = ref('')
const messageType = ref<'error' | 'success' | ''>('')
const isLoading = ref(false)
const showPassword = ref(false)
const errors = ref<Record<string, string>>({})

const bgStyle = computed(() => ({
  backgroundImage: `url(${loginBg})`,
  backgroundSize: 'cover',
  backgroundPosition: 'center',
}))

const router = useRouter()

const validateEmail = (emailStr: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(emailStr)
}

const validateForm = (): boolean => {
  errors.value = {}

  if (!email.value.trim()) {
    errors.value.email = 'El correo electrónico es requerido'
  } else if (!validateEmail(email.value)) {
    errors.value.email = 'Por favor, introduce un correo electrónico válido'
  }

  if (!password.value) {
    errors.value.password = 'La contraseña es requerida'
  } else if (password.value.length < 8) {
    errors.value.password = 'La contraseña debe tener al menos 8 caracteres'
  }

  return Object.keys(errors.value).length === 0
}

const login = async () => {
  message.value = ''
  messageType.value = ''

  if (!validateForm()) {
    message.value = 'Por favor, verifica los campos indicados'
    messageType.value = 'error'
    return
  }

  isLoading.value = true

  try {
    const credentials = { email: email.value, password: password.value }
    await userService.login(credentials)
    router.push('/home')
  } catch (error: any) {
    messageType.value = 'error'
    const detail = error?.response?.data?.detail
    message.value = typeof detail === 'string' && detail
      ? detail
      : 'Error al iniciar sesión. Intenta de nuevo.'
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div
    class="relative flex flex-col items-center px-4 py-16 min-h-screen w-full"
    :style="bgStyle"
  >
    <div class="absolute inset-0 bg-white/60"></div>

    <div class="relative z-10 flex flex-col w-full max-w-md items-center">
      <!-- Logo pequeño / Header simple -->
      <div class="mb-6 text-center">
        <img :src="logoImg" alt="ArtTeràpia App" class="mx-auto h-16 w-16 mb-2" />
        <h1 class="text-2xl font-bold text-gray-900">ArtTeràpia App</h1>
      </div>

      <!-- Card de login -->
      <Card class="w-full text-gray-900 shadow-lg bg-white/95 border border-white/70">
      <CardHeader>
        <CardTitle>Inicia sesión en tu cuenta</CardTitle>
        <CardDescription>
          Introduce tu correo electrónico para acceder
        </CardDescription>
      </CardHeader>

      <CardContent>
        <form @submit.prevent="login" @keyup.enter="login" class="space-y-4">
          <!-- Email field -->
          <div class="flex flex-col space-y-1.5">
            <Label for="email">Correo electrónico</Label>
            <Input
              id="email"
              type="email"
              placeholder="ejemplo@correo.com"
              v-model="email"
              :class="{ 'border-red-500': errors.email }"
              @input="() => { if (errors.email) delete errors.email }"
            />
            <span v-if="errors.email" class="text-xs text-red-600 mt-0.5">
              {{ errors.email }}
            </span>
          </div>

          <!-- Password field -->
          <div class="flex flex-col space-y-1.5">
            <Label for="password">Contraseña</Label>
            <div class="relative">
              <Input
                id="password"
                :type="showPassword ? 'text' : 'password'"
                placeholder="••••••••"
                v-model="password"
                :class="{ 'border-red-500': errors.password }"
                @input="() => { if (errors.password) delete errors.password }"
                class="pr-10"
              />
              <button
                type="button"
                @click="showPassword = !showPassword"
                class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
              >
                <Eye v-if="!showPassword" class="h-4 w-4" />
                <EyeOff v-else class="h-4 w-4" />
              </button>
            </div>
            <span v-if="errors.password" class="text-xs text-red-600 mt-0.5">
              {{ errors.password }}
            </span>
          </div>

          <!-- General message -->
          <div
            v-if="message"
          >
            <Alert class="bg-red-100 text-red-800 border border-red-300">
              <AlertCircleIcon />
              <AlertTitle>Error al iniciar sesión</AlertTitle>
              <AlertDescription class="text-red-800">
                {{ message }}
              </AlertDescription>
            </Alert>
          </div>
        </form>
      </CardContent>

      <CardFooter class="flex flex-col gap-2">
        <Button
          class="w-full"
          @click="login"
          :disabled="isLoading"
        >
          {{ isLoading ? 'Iniciando sesión...' : 'Iniciar sesión' }}
        </Button>
        <Button
          variant="outline"
          class="w-full"
          @click="() => router.push('/signup')"
          :disabled="isLoading"
        >
          Crear cuenta
        </Button>
      </CardFooter>
      </Card>
    </div>
  </div>
</template>

<style scoped>
/* Ocultar el icono nativo de mostrar/ocultar contraseña del navegador */
input[type="password"]::-ms-reveal,
input[type="password"]::-ms-clear {
  display: none;
}

input[type="password"]::-webkit-credentials-auto-fill-button {
  display: none !important;
}
</style>
