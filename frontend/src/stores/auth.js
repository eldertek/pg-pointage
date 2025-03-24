import { defineStore } from "pinia"
import api from "@/services/api"
import router from "@/router"

export const useAuthStore = defineStore("auth", {
  state: () => ({
    user: null,
    token: localStorage.getItem("token"),
    refreshToken: localStorage.getItem("refreshToken"),
    loading: false,
    error: null
  }),

  getters: {
    isAuthenticated: (state) => !!state.token,
    userRole: (state) => state.user?.role || null,
    isSuperAdmin: (state) => state.user?.role === "SUPER_ADMIN",
    isManager: (state) => state.user?.role === "MANAGER",
    isEmployee: (state) => state.user?.role === "EMPLOYEE",
    userOrganization: (state) => state.user?.organization || null,
    userName: (state) => state.user ? `${state.user.first_name} ${state.user.last_name}` : null
  },

  actions: {
    setTokens(token, refreshToken) {
      this.token = token
      this.refreshToken = refreshToken
      localStorage.setItem("token", token)
      localStorage.setItem("refreshToken", refreshToken)
      api.defaults.headers.common["Authorization"] = `Bearer ${token}`
    },

    clearTokens() {
      this.token = null
      this.refreshToken = null
      localStorage.removeItem("token")
      localStorage.removeItem("refreshToken")
      delete api.defaults.headers.common["Authorization"]
    },

    async login(credentials) {
      this.loading = true
      this.error = null
      try {
        console.log("Tentative de connexion avec les données:", { 
          email: credentials.email,
          password: '***'
        })
        console.log("Headers de la requête:", api.defaults.headers)
        const response = await api.post("/users/login/", credentials)
        console.log("Réponse de connexion reçue:", response.data)
        
        this.setTokens(response.data.access, response.data.refresh)
        await this.fetchUserProfile()
        
        // Redirection basée sur le rôle
        if (this.isSuperAdmin) {
          console.log("Redirection vers le tableau de bord des organisations")
          router.push("/dashboard/organizations")
        } else if (this.isManager) {
          console.log("Redirection vers le tableau de bord des sites")
          router.push("/dashboard/sites")
        } else {
          console.log("Redirection vers le tableau de bord")
          router.push("/dashboard")
        }
      } catch (error) {
        console.error("Erreur de connexion:", error)
        console.error("Détails de l'erreur:", {
          status: error.response?.status,
          statusText: error.response?.statusText,
          data: error.response?.data,
          headers: error.response?.headers
        })
        this.error = error.response?.data?.detail || "Erreur lors de la connexion"
        throw error
      } finally {
        this.loading = false
      }
    },

    async logout() {
      console.log("Déconnexion en cours...")
      try {
        if (this.refreshToken) {
          await api.post("/users/logout/", { refresh: this.refreshToken })
          console.log("Déconnexion réussie côté serveur")
        }
      } catch (error) {
        console.error("Erreur lors de la déconnexion:", error)
      } finally {
        this.user = null
        this.clearTokens()
        console.log("Session locale nettoyée")
        router.push("/login")
      }
    },

    async refreshAccessToken() {
      console.log("Rafraîchissement du token...")
      try {
        const response = await api.post("/users/token/refresh/", {
          refresh: this.refreshToken
        })
        this.setTokens(response.data.access, response.data.refresh)
        return response.data.access
      } catch (error) {
        console.error("Erreur lors du rafraîchissement du token:", error)
        this.logout()
        throw error
      }
    },

    async fetchUserProfile() {
      console.log("Récupération du profil utilisateur...")
      try {
        const response = await api.get("/users/profile/")
        console.log("Profil utilisateur reçu:", response.data)
        this.user = response.data
      } catch (error) {
        console.error("Erreur lors de la récupération du profil:", error)
        throw error
      }
    },

    async initAuth() {
      console.log("Initialisation de l'authentification...")
      if (this.token) {
        try {
          console.log("Token trouvé, récupération du profil...")
          await this.fetchUserProfile()
          console.log("Profil récupéré avec succès:", this.user)
          return true
        } catch (error) {
          console.error("Erreur lors de l'initialisation de l'auth:", error)
          await this.logout()
          return false
        }
      }
      return false
    },

    async forgotPassword(email) {
      try {
        await api.post("/users/reset-password/", { email })
      } catch (error) {
        console.error("Erreur lors de la demande de réinitialisation:", error)
        throw error
      }
    },

    async resetPassword(token, password) {
      try {
        await api.post("/users/reset-password/confirm/", {
          token,
          password
        })
      } catch (error) {
        console.error("Erreur lors de la réinitialisation du mot de passe:", error)
        throw error
      }
    },

    async updateProfile(userData) {
      try {
        const response = await api.patch("/users/profile/", userData)
        this.user = response.data
      } catch (error) {
        console.error("Erreur lors de la mise à jour du profil:", error)
        throw error
      }
    }
  }
})

