<template>
  <div id="app" class="font-sans text-gray-900">
    <Toast />

    <Header v-if="showHeader">
      <router-view />
    </Header>

    <div v-else>
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
const authPaths = ['/', '/signup']
const showHeader = computed(() => !authPaths.includes(route.path))

document.title = 'App ArtTerapia'
</script>

<style>
html, body {
  overscroll-behavior: none;
}
</style>
