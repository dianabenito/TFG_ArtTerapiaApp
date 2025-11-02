import axios from 'axios'

const API_URL = 'http://127.0.0.1:8000' // tu backend FastAPI

export const userService = {
  async getUsers() {
    const response = await axios.get(`${API_URL}/users/users/`)
    return response.data
  },

  async createUser(userData) {
    const response = await axios.post(`${API_URL}/users/users/`, userData)
    return response.data
  },

}
