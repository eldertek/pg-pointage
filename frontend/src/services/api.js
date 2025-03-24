import axios from "axios"
import { useAuthStore } from "@/stores/auth"

const api = axios.create({
  baseURL: "http://127.0.0.1:3000/api/v1",
  timeout: 10000,
  headers: {
    "Content-Type": "application/json",
    Accept: "application/json",
  },
})

// Intercepteur pour ajouter le token aux requêtes
api.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore()
    if (authStore.token) {
      console.log("Ajout du token à la requête:", {
        url: config.url,
        method: config.method,
        baseURL: config.baseURL,
        fullURL: config.baseURL + config.url,
        token: authStore.token.substring(0, 10) + '...'
      })
      config.headers.Authorization = `Bearer ${authStore.token}`
    }
    return config
  },
  (error) => {
    console.error("Erreur lors de la préparation de la requête:", error)
    return Promise.reject(error)
  }
)

// Intercepteur pour gérer les réponses et les erreurs
api.interceptors.response.use(
  (response) => {
    return response
  },
  async (error) => {
    const authStore = useAuthStore()
    const originalRequest = error.config

    // Si l'erreur est 401 (non autorisé) et qu'on n'a pas déjà essayé de rafraîchir le token
    if (error.response?.status === 401 && !originalRequest._retry && authStore.refreshToken) {
      console.log("Token expiré, tentative de rafraîchissement")
      originalRequest._retry = true

      try {
        const success = await authStore.refreshAccessToken()
        if (success) {
          console.log("Token rafraîchi, nouvelle tentative de la requête originale")
          // Mettre à jour le token dans la requête originale
          originalRequest.headers.Authorization = `Bearer ${authStore.token}`
          return api(originalRequest)
        }
      } catch (refreshError) {
        console.error("Échec du rafraîchissement du token:", refreshError)
      }
    }

    // Si on ne peut pas rafraîchir le token ou si c'est une autre erreur
    if (error.response?.status === 401) {
      console.log("Session expirée, déconnexion")
      await authStore.logout()
    }

    return Promise.reject(error)
  }
)

export default api

