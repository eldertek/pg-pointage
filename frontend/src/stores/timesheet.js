import { defineStore } from "pinia"
import { ref } from "vue"
import api from "@/services/api"

export const useTimesheetStore = defineStore("timesheet", () => {
  const timesheets = ref([])
  const loading = ref(false)
  const error = ref(null)

  // Fonction pour créer un nouveau pointage
  async function createTimesheet(data) {
    loading.value = true
    error.value = null

    try {
      const response = await api.post("/timesheets/create/", data)
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || "Erreur lors de la création du pointage"
      throw new Error(error.value)
    } finally {
      loading.value = false
    }
  }

  // Fonction pour récupérer les pointages récents
  async function fetchRecentTimesheets() {
    loading.value = true
    error.value = null

    try {
      const response = await api.get("/timesheets/", {
        params: {
          limit: 10,
          ordering: "-timestamp",
        },
      })
      // Récupérer les pointages depuis la réponse, en gérant différents schémas (tableau direct ou objet)
      const body = response.data
      const fetched = Array.isArray(body)
        ? body
        : body.results ?? body.data ?? []
      timesheets.value = fetched
      return fetched
    } catch (err) {
      error.value = "Erreur lors de la récupération des pointages"
      return []
    } finally {
      loading.value = false
    }
  }

  // Fonction pour récupérer l'historique des pointages
  async function fetchTimesheetHistory(params = {}) {
    loading.value = true
    error.value = null

    try {
      const response = await api.get("/timesheets/", { params })
      return response.data
    } catch (err) {
      error.value = "Erreur lors de la récupération de l'historique"
      return { results: [], count: 0 }
    } finally {
      loading.value = false
    }
  }

  // Fonction pour récupérer les statistiques de l'utilisateur
  async function fetchUserStats() {
    loading.value = true
    error.value = null

    try {
      const response = await api.get("/timesheets/reports/")
      return response.data
    } catch (err) {
      error.value = "Erreur lors de la récupération des statistiques"
      return {
        lateCount: 0,
        earlyDepartureCount: 0,
        totalHours: 0,
      }
    } finally {
      loading.value = false
    }
  }

  // Fonction pour signaler une anomalie
  async function reportAnomaly(data) {
    loading.value = true
    error.value = null

    try {
      const response = await api.post("/timesheets/anomalies/", data)
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || "Erreur lors du signalement de l'anomalie"
      throw new Error(error.value)
    } finally {
      loading.value = false
    }
  }

  return {
    timesheets,
    loading,
    error,
    createTimesheet,
    fetchRecentTimesheets,
    fetchTimesheetHistory,
    fetchUserStats,
    reportAnomaly,
  }
})

