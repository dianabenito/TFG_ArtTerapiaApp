/**
 * @fileoverview Servicio de generación de imágenes con ComfyUI.
 * Proporciona funciones para generar, subir y gestionar imágenes usando
 * workflows de Stable Diffusion XL a través de ComfyUI.
 * @module comfyService
 */

import axios from '@/plugins/axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const comfyService = {

  /**
   * Genera una imagen desde texto (txt2img workflow).
   * @async
   * @param {Object} prompt - Parámetros de generación.
   * @param {string} prompt.prompt_text - Texto descriptivo de la imagen.
   * @param {number} [prompt.seed] - Semilla para reproducibilidad.
   * @param {number} userId - ID del usuario propietario.
   * @param {number|null} [sessionId=null] - ID de sesión opcional.
   * @returns {Promise<Object>} Imagen generada con metadata.
   */
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
      console.error('createImage error response:', err?.response?.data || err)
      throw err
    }
  },

  /**
   * Convierte un boceto o imagen en imagen realista (img2img/sketch2img workflow).
   * @async
   * @param {Object} prompt - Parámetros de conversión.
   * @param {string} prompt.image - Nombre del archivo de imagen base.
   * @param {string} [prompt.prompt_text] - Texto descriptivo opcional.
   * @param {number} [prompt.denoise] - Intensidad de transformación (0.0-1.0).
   * @param {number} userId - ID del usuario propietario.
   * @param {number|null} [sessionId=null] - ID de sesión opcional.
   * @returns {Promise<Object>} Imagen convertida con metadata.
   */
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
      console.error('convertirBoceto error response:', err?.response?.data || err)
      throw err
    }
  },

  /**
   * Genera una imagen combinando múltiples imágenes (2, 3 o 4).
   * @async
   * @param {Array<Object>|Object} images - Lista de imágenes o objeto con propiedad data.
   * @param {number} count - Número de imágenes a combinar (2, 3 o 4).
   * @param {number} userId - ID del usuario propietario.
   * @param {number|null} [sessionId=null] - ID de sesión opcional.
   * @returns {Promise<Object>} Imagen combinada con metadata.
   */
  async generateImageByMultiple(images, count, userId, sessionId = null) {
    try {
      const token = localStorage.getItem('token')
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

  /**
   * Sube una imagen desde el cliente al servidor.
   * @async
   * @param {File} file - Archivo de imagen a subir.
   * @param {number} userId - ID del usuario propietario.
   * @param {boolean} [isDrawnImage=false] - Si es un dibujo creado en canvas.
   * @returns {Promise<Object>} Información de la imagen subida.
   */
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

  /**
   * Sube un dibujo creado en canvas.
   * @async
   * @param {File} file - Archivo del dibujo.
   * @param {number} userId - ID del usuario propietario.
   * @returns {Promise<Object>} Información del dibujo guardado.
   */
  async uploadDrawnImage(file, userId) {
    const token = localStorage.getItem('token')
    const form = new FormData()
    form.append('file', file)
    const response = await axios.post(`${API_URL}/comfy/users/${userId}/images/drawn`, form, {
      headers: { 'Content-Type': 'multipart/form-data', Authorization: `Bearer ${token}` }
    })
    return response.data
  },

  /**
   * Obtiene todas las imágenes de un usuario.
   * @async
   * @param {number} userId - ID del usuario.
   * @returns {Promise<Object>} Lista de imágenes del usuario.
   */
  async getImagesForUser(userId) {
    const token = localStorage.getItem('token')
    const response = await axios.get(`${API_URL}/comfy/users/${userId}/images`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    return response.data
  },

  /**
   * Obtiene lista de imágenes plantilla disponibles.
   * @async
   * @returns {Promise<Array<string>>} Nombres de archivos de imágenes plantilla.
   */
  async getTemplateImages() {
    const response = await axios.get(`${API_URL}/comfy/template-images`)
    return response.data
  },

  /**
   * Asocia una imagen existente a una sesión sin duplicar el archivo.
   * @async
   * @param {string} imageFileName - Nombre del archivo de imagen.
   * @param {number} userId - ID del usuario propietario.
   * @param {number} sessionId - ID de la sesión.
   * @returns {Promise<Object>} Información de la imagen vinculada.
   */
  async linkImageToSession(imageFileName, userId, sessionId) {
    try {
      const token = localStorage.getItem('token')
      const url = `${API_URL}/comfy/users/${userId}/session-images/link?image_file_name=${encodeURIComponent(imageFileName)}&session_id=${sessionId}`
      const response = await axios.post(url, {}, {
        headers: { Authorization: `Bearer ${token}` }
      })
      return response.data
    } catch (err) {
      console.error('linkImageToSession error response:', err?.response?.data || err)
      throw err
    }
  }
  
}