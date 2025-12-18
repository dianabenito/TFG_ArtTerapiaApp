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

    <!-- AlertDialog global para sesión expirada -->
    <AlertDialog :open="sessionExpiredDialog" @update:open="(val) => sessionExpiredDialog = val">
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Sesión expirada</AlertDialogTitle>
          <AlertDialogDescription>
            Tu sesión ha expirado. Por favor, inicia sesión nuevamente para continuar.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <div class="flex justify-end">
          <AlertDialogAction @click="handleSessionExpired">
            Iniciar sesión
          </AlertDialogAction>
        </div>
      </AlertDialogContent>
    </AlertDialog>
  </div>
</template>


<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Toaster } from '@/components/ui/sonner'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { sessionExpiredDialog } from '@/plugins/axios'
import { userService } from '@/api/userService'

import Header from './components/Header.vue'

const route = useRoute()
const router = useRouter()
const authPaths = ['/', '/signup']
const showHeader = computed(() => !authPaths.includes(route.path))

const handleSessionExpired = () => {
  sessionExpiredDialog.value = false
  userService.logout()
  router.push('/')
}

document.title = 'ArteTerapia App'
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

