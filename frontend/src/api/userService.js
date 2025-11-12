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

  async login(credentials) {
    // credentials = { email, password }
    const response = await axios.post(`${API_URL}/users/login`, credentials)
    const token = response.data.access_token
    if (token) {
      localStorage.setItem('token', token)
      localStorage.setItem('userType', response.data.user_type)
    }
    return response.data
  },

}


