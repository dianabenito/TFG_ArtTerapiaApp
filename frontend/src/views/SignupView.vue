<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { userService } from '../api/userService'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card'
import signupBg from '@/assets/utils/fondo_login.jpg'
import logoImg from '@/assets/utils/logo.png'

const users = ref([])
const router = useRouter()
const newUser = ref({email: '', full_name: '', password: '', type: '' })

onMounted(async () => {
  users.value = await userService.getUsers()
})

const bgStyle = computed(() => ({
  backgroundImage: `url(${signupBg})`,
  backgroundSize: 'cover',
  backgroundPosition: 'center',
}))

const addUser = async () => {
  try {
    const created = await userService.createUser(newUser.value)
    users.value.push(created) 
    newUser.value = { email: '', full_name: '', password: '', type: '' }
  } catch (err) {
    console.error('Error creando usuario:', err)
  }
}
</script>

<template>
  <div class="relative min-h-screen flex items-center justify-center overflow-hidden px-4" :style="bgStyle">
    <!-- overlay suave -->
    <div class="absolute inset-0 bg-white/60 backdrop-blur"></div>

    <div class="relative z-10 flex w-full max-w-md flex-col items-center">
      <!-- Logo -->
      <div class="mb-6 text-center">
        <img :src="logoImg" alt="ArtTeràpia App" class="mx-auto h-16 w-16 mb-2" />
        <h1 class="text-2xl font-bold text-gray-900">ArtTeràpia App</h1>
      </div>

      <!-- Card de signup -->
      <Card class="w-full text-gray-900 shadow-lg bg-white/95 backdrop-blur border border-white/70">
        <CardHeader>
          <CardTitle>Crear nueva cuenta</CardTitle>
          <CardDescription>
            Introduce los datos para registrarte
          </CardDescription>
        </CardHeader>

        <CardContent>
          <form @submit.prevent="addUser" class="grid gap-4">
            <div class="flex flex-col space-y-1.5">
              <Label for="email">Email</Label>
              <Input id="email" type="email" placeholder="ejemplo@correo.com" v-model="newUser.email" required />
            </div>
            <div class="flex flex-col space-y-1.5">
              <Label for="full_name">Nombre completo</Label>
              <Input id="full_name" type="text" placeholder="Nombre completo" v-model="newUser.full_name" required />
            </div>
            <div class="flex flex-col space-y-1.5">
              <Label for="password">Contraseña</Label>
              <Input id="password" type="password" placeholder="Contraseña" v-model="newUser.password" required />
            </div>
            <div class="flex flex-col space-y-1.5">
              <Label for="type">Tipo de usuario</Label>
              <select id="type" v-model="newUser.type" class="border rounded p-2">
                <option value="patient">Paciente</option>
                <option value="therapist">Terapeuta</option>
              </select>
            </div>
          </form>
        </CardContent>

        <CardFooter class="flex flex-col gap-2">
          <Button class="w-full" @click="addUser" type="submit">Crear cuenta</Button>

          <!-- Mensaje para redirigir a login -->
          <p
            class="mt-2 text-center text-sm text-blue-600 hover:underline cursor-pointer"
            @click="router.push('/login')"
          >
            ¿Ya tienes una cuenta? Inicia sesión
          </p>
        </CardFooter>

      </Card>
    </div>
  </div>
</template>
