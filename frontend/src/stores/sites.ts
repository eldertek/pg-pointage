import { defineStore } from 'pinia'
import { sitesApi } from '@/services/api'
import type { Site } from '@/services/api'

interface SitesState {
  currentSite: Site | null
  loading: boolean
  error: string | null
}

export const useSitesStore = defineStore('sites', {
  state: (): SitesState => ({
    currentSite: null,
    loading: false,
    error: null
  }),

  getters: {
    getCurrentSite: (state) => state.currentSite,
    getCurrentSiteId: (state) => state.currentSite?.id || null,
    isLoading: (state) => state.loading
  },

  actions: {
    async setCurrentSite(siteId: number) {
      try {
        this.loading = true
        const response = await sitesApi.getSite(siteId)
        this.currentSite = response.data
      } catch (error) {
        console.error('Erreur lors du chargement du site:', error)
        this.error = 'Erreur lors du chargement du site'
        throw error
      } finally {
        this.loading = false
      }
    },

    clearCurrentSite() {
      this.currentSite = null
    }
  }
}) 