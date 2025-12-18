import axios from 'axios'
import { ref } from 'vue'

// Estado global reactivo para el diálogo de sesión expirada
export const sessionExpiredDialog = ref(false)

// Configurar interceptor de respuesta de Axios
axios.interceptors.response.use(
  // Si la respuesta es exitosa, simplemente la devolvemos
  (response) => response,
  
  // Si hay un error, verificamos si es 401 Unauthorized
  (error) => {
    if (error.response && error.response.status === 401) {
      // Token expirado o inválido
      sessionExpiredDialog.value = true
    }
    return Promise.reject(error)
  }
)

export default axios
