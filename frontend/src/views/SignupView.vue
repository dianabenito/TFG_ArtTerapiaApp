<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { Eye, EyeOff } from 'lucide-vue-next'
import { userService } from '../api/userService'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card'
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import signupBg from '@/assets/utils/fondo_login.jpg'
import logoImg from '@/assets/utils/logo.png'
import { AlertCircleIcon} from 'lucide-vue-next'
import {
  Alert,
  AlertDescription,
  AlertTitle,
} from '@/components/ui/alert'


const router = useRouter()
const newUser = ref({ email: '', full_name: '', password: '', type: '' })
const confirmPassword = ref('')
const message = ref('')
const messageType = ref<'error' | 'success' | ''>('')
const isLoading = ref(false)
const errors = ref<Record<string, string>>({})
const showPassword = ref(false)
const showConfirmPassword = ref(false)
const passwordRequirements = ref({
  length: false,
  uppercase: false,
  number: false,
  special: false,
})

const bgStyle = computed(() => ({
  backgroundImage: `url(${signupBg})`,
  backgroundSize: 'cover',
  backgroundPosition: 'top center',
}))

const validateEmail = (emailStr: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(emailStr)
}

const updatePasswordRequirements = (password: string) => {
  passwordRequirements.value = {
    length: password.length >= 8,
    uppercase: /[A-Z]/.test(password),
    number: /\d/.test(password),
    special: /[!@#$%^&*(),.?":{}|<>]/.test(password),
  }
}

const validateForm = (): boolean => {
  errors.value = {}

  if (!newUser.value.email.trim()) {
    errors.value.email = 'El correo electrónico es requerido'
  } else if (!validateEmail(newUser.value.email)) {
    errors.value.email = 'Por favor, introduce un correo electrónico válido'
  }

  if (!newUser.value.full_name.trim()) {
    errors.value.full_name = 'El nombre completo es requerido'
  } else if (newUser.value.full_name.trim().length < 3) {
    errors.value.full_name = 'El nombre debe tener al menos 3 caracteres'
  }

  if (!newUser.value.password) {
    errors.value.password = 'La contraseña es requerida'
  } else if (newUser.value.password.length < 8) {
    errors.value.password = 'La contraseña debe tener al menos 8 caracteres'
  } else if (!/[A-Z]/.test(newUser.value.password)) {
    errors.value.password = 'La contraseña debe contener al menos una mayúscula'
  } else if (!/\d/.test(newUser.value.password)) {
    errors.value.password = 'La contraseña debe contener al menos un número'
  } else if (!/[!@#$%^&*(),.?":{}|<>]/.test(newUser.value.password)) {
    errors.value.password = 'La contraseña debe contener al menos un carácter especial'
  }

  if (!confirmPassword.value) {
    errors.value.confirmPassword = 'Por favor, confirma la contraseña'
  } else if (newUser.value.password !== confirmPassword.value) {
    errors.value.confirmPassword = 'Las contraseñas no coinciden'
  }

  if (!newUser.value.type) {
    errors.value.type = 'Selecciona un tipo de usuario'
  }

  return Object.keys(errors.value).length === 0
}

const addUser = async () => {
  message.value = ''
  messageType.value = ''

  if (!validateForm()) {
    message.value = 'Por favor, verifica los campos indicados'
    messageType.value = 'error'
    return
  }

  isLoading.value = true

  try {
    await userService.createUser({
      email: newUser.value.email,
      full_name: newUser.value.full_name,
      password: newUser.value.password,
      type: newUser.value.type,
    })
    router.push('/')
  } catch (err: any) {
    messageType.value = 'error'
    const detail = err?.response?.data?.detail
    message.value = typeof detail === 'string' && detail
      ? detail
      : 'Error al crear la cuenta. Intenta de nuevo.'
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
    <!-- overlay suave -->
    <div class="absolute inset-0 bg-white/60"></div>

    <div class="relative z-10 flex flex-col w-full max-w-md items-center">      <!-- Logo -->
      <div class="mb-6 text-center">
        <img :src="logoImg" alt="ComfyMind" class="mx-auto h-16 w-16 mb-2" />
        <h1 class="text-2xl font-bold text-gray-900">ComfyMind</h1>
      </div>

      <!-- Card de signup -->
      <Card class="w-full text-gray-900 shadow-lg bg-white/95 border border-white/70">
        <CardHeader>
          <CardTitle>Crear nueva cuenta</CardTitle>
          <CardDescription>
            Introduce los datos para registrarte
          </CardDescription>
        </CardHeader>

        <CardContent>
          <form @submit.prevent="addUser" class="space-y-4" @keydown.enter="addUser">
            <!-- Email field -->
            <div class="flex flex-col space-y-1.5">
              <Label for="email">Correo electrónico</Label>
              <Input
                id="email"
                type="email"
                placeholder="ejemplo@correo.com"
                v-model="newUser.email"
                :class="{ 'border-red-500': errors.email }"
                @input="() => { if (errors.email) delete errors.email }"
              />
              <span v-if="errors.email" class="text-xs text-red-600 mt-0.5">
                {{ errors.email }}
              </span>
            </div>

            <!-- Full Name field -->
            <div class="flex flex-col space-y-1.5">
              <Label for="full_name">Nombre completo</Label>
              <Input
                id="full_name"
                type="text"
                placeholder="Nombre completo"
                v-model="newUser.full_name"
                :class="{ 'border-red-500': errors.full_name }"
                @input="() => { if (errors.full_name) delete errors.full_name }"
              />
              <span v-if="errors.full_name" class="text-xs text-red-600 mt-0.5">
                {{ errors.full_name }}
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
                  v-model="newUser.password"
                  @input="(e) => updatePasswordRequirements((e.target).value)"
                  :class="{ 'border-red-500': errors.password }"
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
              <!-- Password requirements checker -->
              <div class="mt-2 space-y-1 text-xs">
                <div :class="passwordRequirements.length ? 'text-green-600' : 'text-gray-500'">
                  ✓ Al menos 8 caracteres
                </div>
                <div :class="passwordRequirements.uppercase ? 'text-green-600' : 'text-gray-500'">
                  ✓ Al menos una mayúscula
                </div>
                <div :class="passwordRequirements.number ? 'text-green-600' : 'text-gray-500'">
                  ✓ Al menos un número
                </div>
                <div :class="passwordRequirements.special ? 'text-green-600' : 'text-gray-500'">
                  ✓ Al menos un carácter especial (!@#$%...)
                </div>
              </div>
            </div>

            <!-- Confirm Password field -->
            <div class="flex flex-col space-y-1.5">
              <Label for="confirmPassword">Confirmar contraseña</Label>
              <div class="relative">
                <Input
                  id="confirmPassword"
                  :type="showConfirmPassword ? 'text' : 'password'"
                  placeholder="••••••••"
                  v-model="confirmPassword"
                  :class="{ 'border-red-500': errors.confirmPassword }"
                  @input="() => { if (errors.confirmPassword) delete errors.confirmPassword }"
                  class="pr-10"
                />
                <button
                  type="button"
                  @click="showConfirmPassword = !showConfirmPassword"
                  class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
                >
                  <Eye v-if="!showConfirmPassword" class="h-4 w-4" />
                  <EyeOff v-else class="h-4 w-4" />
                </button>
              </div>
              <span v-if="errors.confirmPassword" class="text-xs text-red-600 mt-0.5">
                {{ errors.confirmPassword }}
              </span>
            </div>

            <!-- User Type field -->
            <div class="flex flex-col space-y-1.5">
              <Label for="type">Tipo de usuario</Label>

                <Select id="type"
                  v-model="newUser.type"
                  :class="['border rounded p-2 text-sm', errors.type ? 'border-red-500' : 'border-gray-300']"
                  @change="() => { if (errors.type) delete errors.type }">
                  <SelectTrigger class="w-full">
                    <SelectValue placeholder="Selecciona un tipo de usuario" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectGroup>
                      <SelectLabel>Tipos de usuario</SelectLabel>
                      <SelectItem value="patient">
                        Paciente
                      </SelectItem>
                      <SelectItem value="therapist">
                        Terapeuta
                      </SelectItem>
                    </SelectGroup>
                  </SelectContent>
                </Select>
              <span v-if="errors.type" class="text-xs text-red-600 mt-0.5">
                {{ errors.type }}
              </span>
            </div>

            <!-- General message -->
            <div
              v-if="message"
            >
              <Alert class="bg-red-100 text-red-800 border border-red-300">
                <AlertCircleIcon />
                <AlertTitle>Error al crear la cuenta</AlertTitle>
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
            @click="addUser"
            type="submit"
            :disabled="isLoading"
          >
            {{ isLoading ? 'Creando cuenta...' : 'Crear cuenta' }}
          </Button>

          <p
            class="mt-2 text-center text-sm text-blue-600 hover:underline cursor-pointer"
            @click="router.push('/')"
          >
            ¿Ya tienes una cuenta? Inicia sesión
          </p>
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
