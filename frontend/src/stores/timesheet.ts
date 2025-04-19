import { defineStore } from "pinia"
import { ref } from "vue"
import type { Ref } from "vue"
import api from "@/services/api"

export interface Timesheet {
  id: number
  employee?: number
  employee_name?: string
  site?: number
  site_name?: string
  timestamp: string
  entry_type: string
  latitude: number | null
  longitude: number | null
  is_late: boolean
  late_minutes: number | null
  is_early_departure: boolean
  early_departure_minutes: number | null
  correction_note?: string | null
  created_at: string
  updated_at: string
  schedule_details?: any | null
}

export interface TimesheetCreateParams {
  site_id: string
  latitude?: number
  longitude?: number
  scan_type: string
  entry_type?: string
  timestamp?: string
}

export interface UserStats {
  lateCount: number
  earlyDepartureCount: number
  totalHours: number
}

export const useTimesheetStore = defineStore("timesheet", () => {
  const timesheets: Ref<Timesheet[]> = ref([])
  const loading: Ref<boolean> = ref(false)
  const error: Ref<string | null> = ref(null)

  async function createTimesheet(
    data: TimesheetCreateParams
  ): Promise<any> {
    loading.value = true
    error.value = null
    try {
      const response = await api.post("/timesheets/create/", data)
      return response.data
    } catch (err: any) {
      const detail = err.response?.data?.detail
      error.value = typeof detail === "string"
        ? detail
        : "Erreur lors de la création du pointage"
      throw new Error(error.value)
    } finally {
      loading.value = false
    }
  }

  async function fetchRecentTimesheets(): Promise<Timesheet[]> {
    loading.value = true
    error.value = null
    try {
      const response = await api.get("/timesheets/", {
        params: { limit: 10, ordering: "-timestamp" }
      })
      const body = response.data
      const fetched: Timesheet[] = Array.isArray(body)
        ? body
        : (body.results ?? body.data) as Timesheet[]
      timesheets.value = fetched
      return fetched
    } catch (_err: any) {
      error.value = "Erreur lors de la récupération des pointages"
      return []
    } finally {
      loading.value = false
    }
  }

  async function fetchTimesheetHistory(
    params: Record<string, any> = {}
  ): Promise<{ results: Timesheet[]; count: number }> {
    loading.value = true
    error.value = null
    try {
      const response = await api.get("/timesheets/", { params })
      return response.data
    } catch (_err: any) {
      error.value = "Erreur lors de la récupération de l'historique"
      return { results: [], count: 0 }
    } finally {
      loading.value = false
    }
  }

  async function fetchUserStats(): Promise<UserStats> {
    loading.value = true
    error.value = null
    try {
      const response = await api.get("/timesheets/reports/")
      return response.data
    } catch (_err: any) {
      error.value = "Erreur lors de la récupération des statistiques"
      return { lateCount: 0, earlyDepartureCount: 0, totalHours: 0 }
    } finally {
      loading.value = false
    }
  }

  async function reportAnomaly(data: any): Promise<any> {
    loading.value = true
    error.value = null
    try {
      const response = await api.post("/timesheets/anomalies/", data)
      return response.data
    } catch (err: any) {
      const detail = err.response?.data?.detail
      error.value = typeof detail === "string"
        ? detail
        : "Erreur lors du signalement de l'anomalie"
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
    reportAnomaly
  }
}) 