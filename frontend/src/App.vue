<template>
  <div class="min-h-screen bg-gray-50 text-gray-900 font-sans" id="app">
    <Toast />

    <Header v-if="showHeader">
      <router-view />
    </Header>

    <div v-else class="min-h-screen">
      <router-view />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

import Toast from './components/Toast.vue'
import Header from './components/Header.vue'

const route = useRoute()
const authPaths = ['/login', '/']
const showHeader = computed(() => !authPaths.includes(route.path))

document.title = 'App ArtTerapia'
</script>
