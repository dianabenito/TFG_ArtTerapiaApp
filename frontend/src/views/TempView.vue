<script setup>
import { ref, onMounted } from 'vue'
import { userService } from '../api/userService'
import UserCard from '../components/UserCard.vue'

const users = ref([])
const newUser = ref({email: '', password: '', type: '' })

onMounted(async () => {
  users.value = await userService.getUsers()
})

const addUser = async () => {
  try {
    const created = await userService.createUser(newUser.value)
    users.value.push(created) // Añadimos el nuevo usuario a la lista
    newUser.value = { email: '', password: '', type: '' } // Reseteamos el formulario
  } catch (err) {
    console.error('Error creando usuario:', err)
  }
}
</script>

<template>
  <div>
    <h1>Usuarios</h1>

    <!-- Formulario para crear usuario -->
    <form @submit.prevent="addUser" class="form">
      <input v-model="newUser.email" type="email" placeholder="Email" required />
      <input v-model="newUser.password" type="password" placeholder="Contraseña" required />
      <select v-model="newUser.type">
        <option value="patient">Paciente</option>
        <option value="therapist">Terapeuta</option>
      </select>
      <button type="submit">Crear usuario</button>
    </form>
  </div>
</template>

<style scoped>
.form {
  display: flex;
  flex-direction: column;
  max-width: 300px;
  margin-bottom: 1rem;
}
input {
  margin: 0.3rem 0;
  padding: 0.5rem;
}
button {
  background-color: #42b883;
  color: white;
  border: none;
  padding: 0.5rem;
  cursor: pointer;
  border-radius: 6px;
}
button:hover {
  background-color: #2f9d72;
}
.users-list {
  margin-top: 1rem;
}
</style>
