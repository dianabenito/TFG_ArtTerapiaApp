import axios from 'axios'

const API_URL = 'http://127.0.0.1:8000' // tu backend FastAPI

export const comfyService = {

  async createImage(promptText, userId = 1) {
    const response = await axios.post(`${API_URL}/comfy/users/${userId}/images/`, promptText)
    return response.data
    },


}
