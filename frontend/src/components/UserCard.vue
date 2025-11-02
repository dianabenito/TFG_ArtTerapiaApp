<template>
  <div class="user-card">
    <h3>{{ user.id }}</h3>
    <p>{{ user.email }}</p>
  </div>
</template>

<script setup>
defineProps({
  user: Object
})
</script>

<style scoped>
.user-card {
  border: 1px solid #ccc;
  padding: 1rem;
  margin: 0.5rem 0;
}
</style>
