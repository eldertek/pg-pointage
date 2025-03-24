import axios from "axios"
import { useAuthStore } from "@/stores/auth"

const api = axios.create({
  baseURL: "/api/v1",
  timeout: 10000,
  headers: {
    "Content-Type": "application/json",
    Accept: "application/json",
  },
})

// Intercepteur pour ajouter le token aux requêtes
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("token")
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
      console.log("Ajout du token à la requête:", {
        url: config.url,
        method: config.method,
        baseURL: config.baseURL,
        fullURL: config.baseURL + config.url,
        token: token.substring(0, 10) + "..."
      })
    }
    return config
  },
  (error) => {
    console.error("Erreur dans l'intercepteur de requête:", error)
    return Promise.reject(error)
  }
)

// Intercepteur pour gérer les réponses
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    if (error.response) {
      console.error("Erreur de réponse:", {
        status: error.response.status,
        data: error.response.data,
        headers: error.response.headers
      })
    }
    return Promise.reject(error)
  }
)

export default api

