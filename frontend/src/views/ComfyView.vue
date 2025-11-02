<script setup>
import { ref, onMounted } from 'vue'
import { comfyService } from '../api/comfyService'

const prompt = ref({promptText: ''})
const result = ref(null)

const generateImage = async () => {
  try {
    result.value = await comfyService.createImage(prompt.value)
  } catch (err) {
    console.error('Error generating image:', err)
  } 
}
</script>

<template>
  <div>
    <h1>Generar imagen con ComfyUI</h1>
    <input v-model="prompt.promptText" type="email" placeholder="Describe tu imagen" />
    <button @click="generateImage">Generar</button>
    <pre>{{ result }}</pre>
  </div>
</template>