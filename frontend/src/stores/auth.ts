import { defineStore } from "pinia"
import api from "@/services/api"
import router from "@/router"
import { nextTick } from "vue"

interface Credentials {
  email: string;
  password: string;
}

interface UserData {
  email?: string;
  first_name?: string;
  last_name?: string;
  [key: string]: any;
}

interface ApiError {
  response?: {
    status?: number;
    statusText?: string;
    data?: any;
    headers?: any;
    detail?: string;
  };
  message?: string;
}

interface User {
  id: number;
  role: string;
  first_name: string;
  last_name: string;
  organization?: any;
}

interface AuthState {
  user: User | null;
  token: string | null;
  refreshToken: string | null;
  loading: boolean;
  error: string | null;
}

export const useAuthStore = defineStore("auth", {
  state: (): AuthState => ({
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
    setTokens(token: string, refreshToken: string) {
      if (!token || !refreshToken || typeof token !== 'string' || typeof refreshToken !== 'string') {
        console.error("Tentative de définir des tokens invalides:", { token, refreshToken })
        return
      }
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

    async login(credentials: Credentials) {
      // Réinitialiser l'état avant la nouvelle connexion
      this.resetStore()
      
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
        
        console.log("Profil chargé, rôle:", this.user?.role)
        
        // Attendre un tick pour s'assurer que le state est à jour
        await nextTick()
        
        // Redirection basée sur le rôle
        if (this.user?.role === "EMPLOYEE") {
          console.log("Redirection vers le tableau de bord mobile")
          await router.push("/mobile")
        } else if (this.user?.role) {
          console.log("Redirection vers le tableau de bord")
          await router.push("/dashboard")
        } else {
          console.error("Rôle non défini après connexion")
          throw new Error("Rôle non défini après connexion")
        }
      } catch (error: unknown) {
        const apiError = error as ApiError;
        console.error("Erreur de connexion:", apiError);
        console.error("Détails de l'erreur:", {
          status: apiError.response?.status,
          statusText: apiError.response?.statusText,
          data: apiError.response?.data,
          headers: apiError.response?.headers
        });
        this.error = apiError.response?.data?.detail || "Erreur lors de la connexion";
        throw error;
      } finally {
        this.loading = false
      }
    },

    async logout() {
      console.log("Déconnexion en cours...")
      try {
        const refreshToken = this.refreshToken
        if (refreshToken && typeof refreshToken === 'string' && refreshToken.length > 0) {
          try {
            console.log("Envoi du refresh token pour déconnexion:", { 
              tokenLength: refreshToken.length,
              tokenStart: refreshToken.substring(0, 10) + '...'
            })
            
            try {
              await api.post("/users/logout/", { refresh: refreshToken })
              console.log("Déconnexion réussie côté serveur")
            } catch (error: unknown) {
              const apiError = error as ApiError;
              console.warn(
                "Erreur lors de la déconnexion côté serveur:", 
                apiError.response?.data?.error || apiError.message
              );
            }
          } catch (error) {
            console.error("Erreur inattendue lors de la déconnexion:", error)
          }
        }
        
        // Nettoyage complet de la session
        this.resetStore()
        
        // Réinitialiser les en-têtes de l'API
        delete api.defaults.headers.common["Authorization"]
        
        // Forcer le rechargement de la page pour nettoyer tout état résiduel
        window.location.href = '/login'
        
      } catch (error) {
        console.error("Erreur lors de la déconnexion:", error)
        // S'assurer que l'état local est nettoyé même en cas d'erreur
        this.resetStore()
        throw error
      }
    },

    // Nouvelle fonction pour réinitialiser complètement le store
    resetStore() {
      // Réinitialiser l'état du store
      this.user = null
      this.token = null
      this.refreshToken = null
      this.loading = false
      this.error = null
      
      // Nettoyer le localStorage
      localStorage.clear()
      
      // Nettoyer les cookies de session
      document.cookie.split(";").forEach(function(c) { 
        document.cookie = c.replace(/^ +/, "").replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/")
      })

      // Nettoyer les en-têtes de l'API
      delete api.defaults.headers.common["Authorization"]
      
      // Réinitialiser l'état de Pinia
      this.$reset()
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

    async forgotPassword(email: string) {
      try {
        await api.post("/users/reset-password/", { email })
      } catch (error) {
        console.error("Erreur lors de la demande de réinitialisation:", error)
        throw error
      }
    },

    async resetPassword(token: string, password: string) {
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

    async updateProfile(userData: UserData) {
      try {
        const response = await api.patch("/users/profile/", userData)
        this.user = response.data
      } catch (error) {
        console.error("Erreur lors de la mise à jour du profil:", error)
        throw error
      }
    },

    updateUser(userData: Partial<User>) {
      if (this.user) {
        this.user = {
          ...this.user,
          ...userData
        } as User;
      }
    }
  }
})

