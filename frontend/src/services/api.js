import axios from "axios"
import { useAuthStore } from "@/stores/auth"

const api = axios.create({
  baseURL: process.env.VUE_APP_API_URL || "http://localhost:8000/api/v1",
  headers: {
    "Content-Type": "application/json",
    Accept: "application/json",
  },
})

// Intercepteur pour ajouter le token d'authentification
api.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore()
    if (authStore.token) {
      config.headers.Authorization = `Bearer ${authStore.token}`
    }
    return config
  },
  (error) => Promise.reject(error),
)

// Intercepteur pour gérer les erreurs 401 (token expiré)
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    const authStore = useAuthStore()

    // Si l'erreur est 401 et que nous n'avons pas déjà essayé de rafraîchir le token
    if (error.response.status === 401 && !originalRequest._retry && authStore.refreshToken) {
      originalRequest._retry = true

      try {
        // Essayer de rafraîchir le token
        const refreshed = await authStore.refreshAccessToken()

        if (refreshed) {
          // Mettre à jour le token dans la requête originale
          originalRequest.headers.Authorization = `Bearer ${authStore.token}`
          // Réessayer la requête originale
          return api(originalRequest)
        }
      } catch (refreshError) {
        // Si le rafraîchissement échoue, déconnecter l'utilisateur
        authStore.logout()
        return Promise.reject(refreshError)
      }
    }

    return Promise.reject(error)
  },
)

export default api

