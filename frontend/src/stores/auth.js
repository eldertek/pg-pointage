import { defineStore } from "pinia"
import { ref, computed } from "vue"
import api from "@/services/api"
import router from "@/router"

export const useAuthStore = defineStore("auth", () => {
  const user = ref(null)
  const token = ref(localStorage.getItem("token") || null)
  const refreshToken = ref(localStorage.getItem("refreshToken") || null)
  const loading = ref(false)
  const error = ref(null)

  const isAuthenticated = computed(() => !!token.value)
  const userRole = computed(() => user.value?.role || null)
  const isEmployee = computed(() => userRole.value === "EMPLOYEE")
  const isManager = computed(() => userRole.value === "MANAGER")
  const isSuperAdmin = computed(() => userRole.value === "SUPER_ADMIN")

  async function login(credentials) {
    loading.value = true
    error.value = null

    try {
      const response = await api.post("/users/login/", credentials)
      token.value = response.data.access
      refreshToken.value = response.data.refresh
      localStorage.setItem("token", token.value)
      localStorage.setItem("refreshToken", refreshToken.value)

      await fetchUserProfile()

      // Rediriger vers le dashboard approprié en fonction du rôle
      if (isEmployee.value) {
        router.push("/mobile")
      } else {
        router.push("/dashboard")
      }

      return true
    } catch (err) {
      error.value = err.response?.data?.detail || "Une erreur est survenue lors de la connexion"
      return false
    } finally {
      loading.value = false
    }
  }

  async function logout() {
    try {
      await api.post("/users/logout/", { refresh: refreshToken.value })
    } catch (err) {
      console.error("Erreur lors de la déconnexion:", err)
    } finally {
      user.value = null
      token.value = null
      refreshToken.value = null
      localStorage.removeItem("token")
      localStorage.removeItem("refreshToken")
      router.push("/login")
    }
  }

  async function fetchUserProfile() {
    loading.value = true
    error.value = null

    try {
      const response = await api.get("/users/profile/")
      user.value = response.data
      return user.value
    } catch (err) {
      error.value = "Erreur lors de la récupération du profil utilisateur"
      return null
    } finally {
      loading.value = false
    }
  }

  async function refreshAccessToken() {
    try {
      const response = await api.post("/users/token/refresh/", {
        refresh: refreshToken.value,
      })
      token.value = response.data.access
      localStorage.setItem("token", token.value)
      return true
    } catch (err) {
      logout()
      return false
    }
  }

  return {
    user,
    token,
    refreshToken,
    loading,
    error,
    isAuthenticated,
    userRole,
    isEmployee,
    isManager,
    isSuperAdmin,
    login,
    logout,
    fetchUserProfile,
    refreshAccessToken,
  }
})

