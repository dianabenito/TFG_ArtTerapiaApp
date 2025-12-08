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
    // Backend expects OAuth2 form-encoded fields: username & password
    const params = new URLSearchParams()
    params.append('username', credentials.email)
    params.append('password', credentials.password)
    const response = await axios.post(`${API_URL}/users/login/`, params, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    })
    const token = response.data.access_token
    if (token) {
      localStorage.setItem('token', token)
    }
    return response.data
  },

  async getCurrentUser() {
    const token = localStorage.getItem('token')
    const response = await axios.get(`${API_URL}/users/users/me`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    return response.data
  },

  async logout() {
    localStorage.removeItem('token')
  },

}


