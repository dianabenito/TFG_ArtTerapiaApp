import { reactive } from 'vue'

const state = reactive({
  toasts: []
})

let idCounter = 1

export function showToast(message, { duration = 3000, type = 'info' } = {}) {
  const id = idCounter++
  state.toasts.push({ id, message, type })
  setTimeout(() => {
    const idx = state.toasts.findIndex(t => t.id === id)
    if (idx !== -1) state.toasts.splice(idx, 1)
  }, duration)
}

export function removeToast(id) {
  const idx = state.toasts.findIndex(t => t.id === id)
  if (idx !== -1) state.toasts.splice(idx, 1)
}

export default state
