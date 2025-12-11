<script setup lang="ts">
import { Button } from '@/components/ui/button'
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
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
  <div class="min-h-screen flex items-center justify-center bg-gray-50">
    <Card class="w-full max-w-sm text-gray-900 shadow-lg">
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
        <Button class="w-full" @click="login">
          Iniciar sesión
        </Button>
        <Button variant="outline" class="w-full" @click="() => router.push('/')">
          Crear cuenta
        </Button>
      </CardFooter>
    </Card>
  </div>
</template>