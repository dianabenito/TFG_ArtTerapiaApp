/**
 * @fileoverview Servicio de gestión de usuarios.
 * Proporciona funciones para autenticación, registro y gestión de usuarios.
 * @module userService
 */

import axios from '@/plugins/axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const userService = {
  /**
   * Obtiene lista de todos los usuarios.
   * @async
   * @returns {Promise<Array<Object>>} Lista de usuarios.
   */
  async getUsers() {
    const response = await axios.get(`${API_URL}/users/users/`)
    return response.data
  },

  /**
   * Obtiene un usuario por su ID.
   * @async
   * @param {number} userId - ID del usuario a obtener.
   * @returns {Promise<Object>} Datos del usuario.
   */
  async getUserById(userId) {
    const token = localStorage.getItem('token')
    const response = await axios.get(`${API_URL}/users/users/${userId}`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    return response.data
  },

  /**
   * Crea un nuevo usuario (registro).
   * @async
   * @param {Object} userData - Datos del usuario a crear.
   * @param {string} userData.email - Email del usuario.
   * @param {string} userData.password - Contraseña.
   * @param {string} userData.full_name - Nombre completo.
   * @param {('patient'|'therapist')} userData.type - Tipo de usuario.
   * @returns {Promise<Object>} Usuario creado.
   */
  async createUser(userData) {
    const response = await axios.post(`${API_URL}/users/users/`, userData)
    return response.data
  },

  /**
   * Realiza login de usuario y almacena el token JWT.
   * @async
   * @param {Object} credentials - Credenciales de login.
   * @param {string} credentials.email - Email del usuario.
   * @param {string} credentials.password - Contraseña.
   * @returns {Promise<Object>} Token de acceso.
   * @returns {string} return.access_token - Token JWT.
   * @returns {string} return.token_type - Tipo de token (bearer).
   */
  async login(credentials) {
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

  /**
   * Obtiene el usuario actual autenticado desde el token.
   * @async
   * @returns {Promise<Object>} Usuario actual.
   */
  async getCurrentUser() {
    const token = localStorage.getItem('token')
    const response = await axios.get(`${API_URL}/users/users/me`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    return response.data
  },

  /**
   * Cierra sesión eliminando el token del almacenamiento local.
   * @async
   */
  async logout() {
    localStorage.removeItem('token')
  },

}


