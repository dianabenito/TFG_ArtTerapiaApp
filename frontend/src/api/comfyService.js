import axios from 'axios'

const API_URL = 'http://127.0.0.1:8000' // tu backend FastAPI

export const comfyService = {

  async createImage(promptText) {
    const response = await axios.post(`${API_URL}/comfy/generate-image`, promptText)
    return response.data
    },


}
