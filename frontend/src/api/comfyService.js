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

  async convertirBoceto(prompt, userId = 2) {
    try {
      // log payload for easier debugging
      console.debug('createImage payload:', prompt)
      const response = await axios.post(`${API_URL}/comfy/users/${userId}/sketch-images/`, prompt, {
        headers: { 'Content-Type': 'application/json' }
      })
      return response.data
    } catch (err) {
      // surface FastAPI validation error body in the client console
      console.error('createImage error response:', err?.response?.data || err)
      throw err
    }
  },

  async generateImageByMultiple(images, count, userId = 2) {
    try {
      console.log('generateImageByMultiple called with images:', images, 'and count:', count)
      // backend expects { data: [{ fileName: '...' }, ...], count: N }
      const payload = { data: (images?.data ?? images).map(i => ({ fileName: i.fileName || i })), count }
      console.debug('generateImageByMultiple payload:', payload)
      const response = await axios.post(`${API_URL}/comfy/users/${userId}/multiple-images/`, payload, {
        headers: { 'Content-Type': 'application/json' }
      })
      return response.data
    } catch (err) {
      console.error('generateImageByMultiple error response:', err?.response?.data || err)
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

  async getImagesForUser(userId = 2) {
    const response = await axios.get(`${API_URL}/comfy/users/${userId}/images`)
    return response.data
  },

  async getTemplateImages() {
    const response = await axios.get(`${API_URL}/comfy/template-images`)
    return response.data
  }
  
}