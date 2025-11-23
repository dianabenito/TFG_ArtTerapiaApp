import axios from 'axios'

const API_URL = 'http://127.0.0.1:8000' // tu backend FastAPI

export const comfyService = {

  async createImage(promptText, userId = 2) {
    const response = await axios.post(`${API_URL}/comfy/users/${userId}/images/`, promptText)
    return response.data
    },

  async uploadImage(file, userId = 2) {
    const form = new FormData()
    form.append('file', file)
    const response = await axios.post(`${API_URL}/comfy/users/${userId}/images/upload`, form, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return response.data
  },


}
