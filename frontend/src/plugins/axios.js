import axios from 'axios'
import { ref } from 'vue'

export const sessionExpiredDialog = ref(false)

// Helper para saber la ruta actual
function getCurrentPath() {
  try {
    return window.location.pathname
  } catch {
    return ''
  }
}

axios.interceptors.response.use(
  (response) => response,
  (error) => {
    if (
      error.response && error.response.status === 401 &&
      getCurrentPath() !== '/'
    ) {
      sessionExpiredDialog.value = true
    }
    return Promise.reject(error)
  }
)

export default axios
