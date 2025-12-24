import axios from '@/plugins/axios'

const API_URL = 'http://192.168.1.37:8000' // tu backend FastAPI

export const comfyService = {

  async createImage(prompt, userId, sessionId = null) {
    try {
      const token = localStorage.getItem('token')
      const url = sessionId 
        ? `${API_URL}/comfy/users/${userId}/images/?session_id=${sessionId}`
        : `${API_URL}/comfy/users/${userId}/images/`
      const response = await axios.post(url, prompt, {
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` }
      })
      return response.data
    } catch (err) {
      // surface FastAPI validation error body in the client console
      console.error('createImage error response:', err?.response?.data || err)
      throw err
    }
  },

  async convertirBoceto(prompt, userId, sessionId = null) {
    try {
      const token = localStorage.getItem('token')
      const url = sessionId 
        ? `${API_URL}/comfy/users/${userId}/sketch-images/?session_id=${sessionId}`
        : `${API_URL}/comfy/users/${userId}/sketch-images/`
      const response = await axios.post(url, prompt, {
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` }
      })
      return response.data
    } catch (err) {
      // surface FastAPI validation error body in the client console
      console.error('convertirBoceto error response:', err?.response?.data || err)
      throw err
    }
  },

  async generateImageByMultiple(images, count, userId, sessionId = null) {
    try {
      const token = localStorage.getItem('token')
      // backend expects { data: [{ fileName: '...' }, ...], count: N }
      const payload = { data: (images?.data ?? images).map(i => ({ fileName: i.fileName || i })), count }
      const url = sessionId 
        ? `${API_URL}/comfy/users/${userId}/multiple-images/?session_id=${sessionId}`
        : `${API_URL}/comfy/users/${userId}/multiple-images/`
      const response = await axios.post(url, payload, {
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` }
      })
      return response.data
    } catch (err) {
      console.error('generateImageByMultiple error response:', err?.response?.data || err)
      throw err
    }
  },


  async uploadImage(file, userId, isDrawnImage = false) {
    const token = localStorage.getItem('token')
    const form = new FormData()
    form.append('file', file)
    const url = `${API_URL}/comfy/users/${userId}/images/upload${isDrawnImage ? '?isDrawn=true' : ''}`
    const response = await axios.post(url, form, {
      headers: { 'Content-Type': 'multipart/form-data', Authorization: `Bearer ${token}` }
    })
    return response.data
  },


  async uploadDrawnImage(file, userId) {
    const token = localStorage.getItem('token')
    const form = new FormData()
    form.append('file', file)
    const response = await axios.post(`${API_URL}/comfy/users/${userId}/images/drawn`, form, {
      headers: { 'Content-Type': 'multipart/form-data', Authorization: `Bearer ${token}` }
    })
    return response.data
  },


  async getImagesForUser(userId) {
    const token = localStorage.getItem('token')
    const response = await axios.get(`${API_URL}/comfy/users/${userId}/images`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    return response.data
  },

  async getTemplateImages() {
    // Las imágenes de plantilla pueden seguir siendo públicas si así lo deseas
    const response = await axios.get(`${API_URL}/comfy/template-images`)
    return response.data
  }
  
}