import axios from 'axios'

const API_URL = 'http://127.0.0.1:8000' // tu backend FastAPI

export const sessionsService = {
  async getActiveSession() {
    const token = localStorage.getItem('token')
    const response = await axios.get(`${API_URL}/sessions/active`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    return response.data
  },

  async endSession(sessionId) {
    const token = localStorage.getItem('token')
    const response = await axios.post(`${API_URL}/sessions/end/${sessionId}`, null, {
      headers: { Authorization: `Bearer ${token}` }
    })
    return response.data
  },

  async getSession(sessionId) {
    const token = localStorage.getItem('token')
    const response = await axios.get(`${API_URL}/sessions/session/${sessionId}`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    return response.data
  },

  async getMySessions() {
    const token = localStorage.getItem('token')
    // Backend exposes GET /sessions/my-sessions
    const response = await axios.get(`${API_URL}/sessions/my-sessions`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    // API returns { data: [...], count: n }
    const payload = response.data
    if (Array.isArray(payload)) return payload
    if (payload && Array.isArray(payload.data)) return payload.data
    return []
  },

  async createSession(patientId, sessionData) {
    const token = localStorage.getItem('token')
    const response = await axios.post(
      `${API_URL}/sessions/session/${patientId}`,
      sessionData,
      { headers: { Authorization: `Bearer ${token}` } }
    )
    return response.data
  },

  async deleteSession(sessionId) {
    const token = localStorage.getItem('token')
    const response = await axios.delete(`${API_URL}/sessions/session/${sessionId}`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    return response.data
  },

  async updateSession(sessionId, sessionData) {
    const token = localStorage.getItem('token')
    const response = await axios.put(
      `${API_URL}/sessions/session/${sessionId}`,
      sessionData,
      { headers: { Authorization: `Bearer ${token}` } }
    )
    return response.data
  }

}