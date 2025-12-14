<template>
  <div id="app" class="font-sans text-gray-900">
    <Header v-if="showHeader">
      <router-view />
    </Header>

    <div v-else>
      <router-view />
    </div>

    <Toaster 
    position="top-right"
    rich-colors
    />
  </div>
</template>


<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { Toaster } from '@/components/ui/sonner'

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
/*
html, body {
  margin: 0;
  min-height: 100%;
  overscroll-behavior: none;
}


body {
  background: linear-gradient(
    to bottom,
    #d1d5db,
    #e5e7eb,
    #f3f4f6
  );
  background-attachment: fixed;
}

body::before {
  content: "";
  position: absolute;
  inset: 0;
  z-index: -1;

  background: linear-gradient(
    to bottom,
    #d1d5db,
    #e5e7eb,
    #f3f4f6
  );
}

#app {
  min-height: 100%;
  display: flex;
  flex-direction: column;
}
*/
</style>

