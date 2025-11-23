import axios from 'axios'

const API_URL = 'http://127.0.0.1:8000' // tu backend FastAPI

export const comfyService = {

  async createImage(prompt, userId = 2) {
    try {
      // log payload for easier debugging
      console.debug('createImage payload:', prompt)
      const response = await axios.post(`${API_URL}/comfy/users/${userId}/images/`, prompt, {
        headers: { 'Content-Type': 'application/json' }
      })
      return response.data
    } catch (err) {
      // surface FastAPI validation error body in the client console
      console.error('createImage error response:', err?.response?.data || err)
      throw err
    }
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
