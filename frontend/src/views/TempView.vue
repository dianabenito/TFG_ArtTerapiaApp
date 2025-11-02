<script setup>
import { ref, onMounted } from 'vue'
import { userService } from '../api/userService'
import UserCard from '../components/UserCard.vue'

const users = ref([])

onMounted(async () => {
  users.value = await userService.getUsers()
  console.log(users.value)  // Para ver los datos que vienen
})
</script>

<template>
  <div>
    <h1>Usuarios</h1>
    <div>
      <!-- Iteramos y llamamos al componente UserCard -->
      <UserCard
        v-for="user in users"
        :key="user.id"
        :user="user"
      />
    </div>
  </div>
</template>
