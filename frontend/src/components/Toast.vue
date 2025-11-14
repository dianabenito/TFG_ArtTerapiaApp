<template>
  <div class="toast-container">
    <div v-for="t in toasts" :key="t.id" :class="['toast', t.type]">
      <div class="toast-message">{{ t.message }}</div>
      <button class="toast-close" @click="remove(t.id)">×</button>
    </div>
  </div>
</template>

<script setup>
import state, { removeToast } from '../stores/toastStore.js'
const toasts = state.toasts
const remove = removeToast
</script>

<style scoped>
.toast-container {
  position: fixed;
  top: 1rem;
  right: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  z-index: 10000;
}
.toast {
  min-width: 220px;
  padding: 0.6rem 0.8rem;
  border-radius: 6px;
  box-shadow: 0 6px 18px rgba(0,0,0,0.12);
  color: #fff;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.toast.info { background: #2b8aef; }
.toast.success { background: #2ba84a; }
.toast.error { background: #e05b5b; }
.toast-close {
  background: transparent;
  border: none;
  color: rgba(255,255,255,0.9);
  font-size: 1.1rem;
  line-height: 1;
  cursor: pointer;
}
.toast-message { margin-right: 0.5rem; }
</style>
