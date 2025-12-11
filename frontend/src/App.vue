<template>
  <div class="min-h-screen bg-gray-50 text-gray-900 font-sans" id="app">
    <Toast />
    <router-view/>
  </div>
</template>

<script>
import Toast from './components/Toast.vue'

export default {
  components: { Toast },
  mounted () {
    document.title = 'App ArtTerapia'
  }
}

</script>
