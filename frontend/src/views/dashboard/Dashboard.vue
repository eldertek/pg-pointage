<template>
  <div>
    <div class="d-flex justify-space-between align-center mb-4">
      <AppTitle :level="1">{{ $t('dashboard.title') }}</AppTitle>
      <v-btn
        color="primary"
        :loading="loading.stats || loading.anomalies"
        @click="refreshDashboard"
      >
        <v-icon class="me-2">mdi-refresh</v-icon>
        {{ $t('dashboard.refresh') }}
      </v-btn>
    </div>

    <v-row>
      <v-col cols="12" md="6" lg="3">
        <v-card class="mb-4" :loading="loading.stats">
          <v-card-text class="text-center">
            <div class="text-overline mb-2">{{ $t('sites.title') }}</div>
            <div class="text-h3 mb-2">{{ stats.sitesCount }}</div>
            <div class="text-caption">{{ $t('dashboard.total_des_sites_actifs') }}</div>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="6" lg="3">
        <v-card class="mb-4" :loading="loading.stats">
          <v-card-text class="text-center">
            <div class="text-overline mb-2">{{ $t('reports.reportTypes.EMPLOYEE') }}</div>
            <div class="text-h3 mb-2">{{ stats.employeesCount }}</div>
            <div class="text-caption">{{ $t('dashboard.total_des_employs_actifs') }}</div>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="6" lg="3">
        <v-card class="mb-4" :loading="loading.stats">
          <v-card-text class="text-center">
            <div class="text-overline mb-2">{{ $t('timesheets.title') }}</div>
            <div class="text-h3 mb-2">{{ stats.timesheetsCount }}</div>
            <div class="text-caption">{{ $t('dashboard.pointages_aujourdhui') }}</div>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="6" lg="3">
        <v-card class="mb-4" :loading="loading.stats">
          <v-card-text class="text-center">
            <div class="text-overline mb-2">{{ $t('anomalies.title') }}</div>
            <div class="text-h3 mb-2">{{ stats.anomaliesCount }}</div>
            <div class="text-caption">{{ $t('dashboard.anomalies_traiter') }}</div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12" lg="8">
        <v-card class="mb-4">
          <v-card-title>{{ $t('dashboard.recentActivity') }}</v-card-title>
          <v-card-text>
            <p class="text-center py-4">{{ $t('dashboard.graphique_dactivit_venir') }}</p>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" lg="4">
        <v-card class="mb-4" :loading="loading.anomalies">
          <v-card-title class="d-flex justify-space-between align-center">
            {{ $t('anomalies.title') }}
            <v-btn
              icon="mdi-refresh"
              size="small"
              :loading="loading.anomalies"
              @click="fetchRecentAnomalies"
            >
              <v-icon>mdi-refresh</v-icon>
            </v-btn>
          </v-card-title>

          <v-alert
            v-if="error.anomalies"
            type="error"
            class="ma-4"
          >
            {{ error.anomalies }}
          </v-alert>

          <v-card-text v-else-if="recentAnomalies.length === 0" class="text-center py-4">
            {{ $t('dashboard.aucune_anomalie_rcente') }}
          </v-card-text>

          <v-card-text v-else class="pb-0">
            <v-row dense>
              <v-col v-for="anomaly in recentAnomalies" :key="anomaly.id" cols="12">
                <v-card 
                  :color="anomaly.status === 'PENDING' ? 'error' : 'success'" 
                  class="anomaly-card mb-4" 
                  variant="outlined"
                  :ripple="false"
                >
                  <div class="d-flex align-center py-2 pl-4 pr-2 anomaly-header">
                    <v-avatar 
                      size="36" 
                      :color="anomaly.status === 'PENDING' ? 'error' : 'success'" 
                      class="mr-3 elevation-1"
                    >
                      <v-icon 
                        color="white" 
                        :title="t(`anomalies.anomalyTypes.${anomaly.anomaly_type}`)"
                      >
                        {{ getAnomalyIcon(anomaly.anomaly_type) }}
                      </v-icon>
                    </v-avatar>
                    
                    <div class="flex-grow-1">
                      <div class="text-subtitle-1 font-weight-medium text-truncate">
                        {{ t(`anomalies.anomalyTypes.${anomaly.anomaly_type}`) }}
                      </div>
                    </div>
                    
                    <v-chip
                      size="small"
                      :color="anomaly.status === 'PENDING' ? 'error' : 'success'"
                      label
                      class="px-2 ml-2 white--text"
                    >
                      {{ t(`anomalies.anomalyStatuses.${anomaly.status}`) }}
                    </v-chip>
                  </div>
                  
                  <v-card-text class="py-2 px-4 bg-surface">
                    <div class="d-flex flex-column">
                      <div class="d-flex align-center mb-1">
                        <v-icon size="small" color="black" class="me-2">mdi-account</v-icon>
                        <span class="text-body-2">{{ anomaly.employee_name }}</span>
                      </div>
                      
                      <div class="d-flex align-center mb-1">
                        <v-icon size="small" color="black" class="me-2">mdi-map-marker</v-icon>
                        <span class="text-body-2">{{ anomaly.site_name }}</span>
                      </div>
                      
                      <div class="d-flex align-center mb-1">
                        <v-icon size="small" color="black" class="me-2">mdi-clock-outline</v-icon>
                        <span class="text-caption">{{ formatDate(anomaly.created_at) }}</span>
                      </div>
                      
                      <div v-if="anomaly.description" class="d-flex align-center">
                        <v-icon size="small" color="black" class="me-2">mdi-information</v-icon>
                        <span class="text-caption text-grey-darken-1">{{ anomaly.translated_description || anomaly.description }}</span>
                      </div>
                    </div>
                  </v-card-text>
                </v-card>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <v-snackbar
      v-model="showStatsError"
      color="error"
      :timeout="3000"
    >
      {{ error.stats }}
    </v-snackbar>
  </div>
</template>

<script lang="ts">
import { ref, onMounted, computed } from 'vue'
import type { ToastInterface } from 'vue-toastification'
import { useToast } from 'vue-toastification'
import { timesheetsApi, sitesApi, usersApi } from '@/services/api'
import { AppTitle } from '@/components/typography'
import { useI18n } from 'vue-i18n'

interface Stats {
  sitesCount: number
  employeesCount: number
  timesheetsCount: number
  anomaliesCount: number
}

interface Anomaly {
  id: number
  employee_name: string
  site_name: string
  anomaly_type_display: string
  status_display: string
  date: string
  anomaly_type: string
  description: string
  translated_description: string
  status: string
  minutes: number
  correction_date: string | null
  correction_note: string
  created_at: string
  updated_at: string
  employee: number
  site: number
  timesheet: number | null
  corrected_by: number | null
}

export default {
  name: 'DashboardView',
  components: {
    AppTitle
  },
  setup() {
    const toast = useToast() as ToastInterface
    const { t, locale } = useI18n()
    const stats = ref<Stats>({
      sitesCount: 0,
      employeesCount: 0,
      timesheetsCount: 0,
      anomaliesCount: 0
    })

    const recentAnomalies = ref<Anomaly[]>([])
    const loading = ref({
      stats: true,
      anomalies: true
    })
    const error = ref({
      stats: null as string | null,
      anomalies: null as string | null
    })

    const showStatsError = computed({
      get: () => !!error.value.stats,
      set: (value) => {
        if (!value) {
          error.value.stats = null
        }
      }
    })

    const formatDate = (dateString: string) => {
      if (!dateString) return ''
      const date = new Date(dateString)
      if (isNaN(date.getTime())) return dateString
      return date.toLocaleString(locale.value, {
        dateStyle: 'medium',
        timeStyle: 'medium'
      })
    }

    const fetchDashboardStats = async () => {
      try {
        loading.value.stats = true
        console.log('Fetching dashboard stats...')

        // Récupérer le nombre de sites
        const sitesResponse = await sitesApi.getAllSites()
        console.log('Sites response:', sitesResponse.data)
        stats.value.sitesCount = sitesResponse.data?.count || sitesResponse.data?.results?.length || 0

        // Récupérer le nombre d'employés
        const employeesResponse = await usersApi.getAllUsers()  // Utilise la bonne méthode pour obtenir tous les utilisateurs
        console.log('Employees response:', employeesResponse.data)
        stats.value.employeesCount = employeesResponse.data?.count || employeesResponse.data?.results?.length || 0

        // Récupérer le nombre de pointages du jour
        const today = new Date().toISOString().split('T')[0]
        const timesheetsResponse = await timesheetsApi.getTimesheets({
          start_date: today,
          end_date: today
        })
        console.log('Timesheets response:', timesheetsResponse.data)

        // Vérifier si la réponse est un tableau ou un objet avec count/results
        if (Array.isArray(timesheetsResponse.data)) {
          stats.value.timesheetsCount = timesheetsResponse.data.length
        } else {
          stats.value.timesheetsCount = timesheetsResponse.data?.count || timesheetsResponse.data?.results?.length || 0
        }

        // Récupérer le nombre d'anomalies en attente
        const anomaliesResponse = await timesheetsApi.getAnomalies({
          status: 'PENDING'
        })
        console.log('Anomalies response:', anomaliesResponse.data)

        // Vérifier si la réponse est un tableau ou un objet avec count/results
        if (Array.isArray(anomaliesResponse.data)) {
          stats.value.anomaliesCount = anomaliesResponse.data.length
        } else {
          stats.value.anomaliesCount = anomaliesResponse.data?.count || anomaliesResponse.data?.results?.length || 0
        }

        console.log('Updated stats:', stats.value)
        console.log('Timesheets count:', stats.value.timesheetsCount)
        console.log('Anomalies count:', stats.value.anomaliesCount)
      } catch (err) {
        console.error('Error fetching dashboard stats:', err)
        error.value.stats = 'Erreur lors du chargement des statistiques'
        toast.error('Erreur lors du chargement des statistiques')
      } finally {
        loading.value.stats = false
      }
    }

    const fetchRecentAnomalies = async () => {
      try {
        loading.value.anomalies = true
        console.log('Fetching recent anomalies...')
        const response = await timesheetsApi.getAnomalies({
          status: 'PENDING',
          limit: 5,
          ordering: '-created_at'
        })
        console.log('Recent anomalies received:', response.data)

        // Vérifier si la réponse est un tableau ou un objet avec results
        if (Array.isArray(response.data)) {
          // Si c'est un tableau, prendre les 5 premiers éléments
          recentAnomalies.value = response.data.slice(0, 5)
        } else {
          recentAnomalies.value = response.data?.results || []
        }
      } catch (err) {
        console.error('Error fetching recent anomalies:', err)
        error.value.anomalies = 'Erreur lors du chargement des anomalies'
        toast.error('Erreur lors du chargement des anomalies récentes')
      } finally {
        loading.value.anomalies = false
      }
    }

    // Refresh data every 5 minutes
    const startAutoRefresh = () => {
      const refreshInterval = 5 * 60 * 1000 // 5 minutes
      setInterval(() => {
        console.log('Auto-refreshing dashboard data...')
        fetchDashboardStats()
        fetchRecentAnomalies()
      }, refreshInterval)
    }

    const refreshDashboard = () => {
      console.log('Manually refreshing dashboard...')
      fetchDashboardStats()
      fetchRecentAnomalies()
    }

    // Function to retrieve the correct icon based on anomaly type
    const getAnomalyIcon = (type: string): string => {
      switch (type) {
        case 'LATE_ARRIVAL': return 'mdi-clock-alert'
        case 'EARLY_DEPARTURE': return 'mdi-exit-to-app'
        case 'MISSED_CHECK_IN': return 'mdi-login-variant'
        case 'MISSED_CHECK_OUT': return 'mdi-logout-variant'
        case 'UNPLANNED_DAY': return 'mdi-calendar-question'
        case 'SITE_INACTIVE': return 'mdi-domain-off'
        case 'SCHEDULE_INACTIVE': return 'mdi-calendar-remove'
        case 'CONSECUTIVE_SCANS': return 'mdi-scan-helper'
        case 'FREQUENCY_INSUFFICIENT': return 'mdi-timer-alert'
        default: return 'mdi-alert-circle'
      }
    }

    onMounted(() => {
      console.log('Dashboard component mounted')
      fetchDashboardStats()
      fetchRecentAnomalies()
      startAutoRefresh()
    })

    return {
      stats,
      recentAnomalies,
      loading,
      error,
      showStatsError,
      fetchRecentAnomalies,
      refreshDashboard,
      t,
      formatDate,
      getAnomalyIcon
    }
  }
}
</script>

<style scoped>
/* Styles des boutons d'action */
:deep(.v-btn--icon) {
  background-color: transparent !important;
  opacity: 1 !important;
}

:deep(.v-btn--icon .v-icon) {
  color: inherit !important;
  opacity: 1 !important;
}

/* Style des boutons colorés */
:deep(.v-btn[color="primary"]) {
  background-color: #00346E !important;
  color: white !important;
}

:deep(.v-btn[color="error"]) {
  background-color: #F78C48 !important;
  color: white !important;
}

:deep(.v-btn[color="success"]) {
  background-color: #00346E !important;
  color: white !important;
}

/* Style des boutons icônes colorés */
:deep(.v-btn--icon[color="primary"]) {
  color: #00346E !important;
}

:deep(.v-btn--icon[color="error"]) {
  color: #F78C48 !important;
}

:deep(.v-btn--icon[color="success"]) {
  color: #00346E !important;
}

/* Correction des overlays et underlays */
:deep(.v-btn__overlay),
:deep(.v-btn__underlay) {
  opacity: 0 !important;
}

/* Ensure all v-icon elements are visible inside this component */
:deep(.v-icon) {
  opacity: 1 !important;
}

/* Styles pour les cartes d'anomalies */
.anomaly-card {
  border-width: 1px;
  transition: all 0.2s ease;
  overflow: hidden;
}

.anomaly-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1) !important;
}

.anomaly-header {
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  background-color: rgba(255, 255, 255, 0.9);
}

:deep(.v-avatar) {
  border: 2px solid white;
}

:deep(.v-chip.white--text) {
  color: white !important;
}

:deep(.bg-surface) {
  background-color: #fafafa !important;
}

/* Force les icônes de la liste à être noires */
:deep(.anomaly-card .v-card-text .v-icon) {
  color: #000000 !important;
  opacity: 1 !important;
}
</style>

