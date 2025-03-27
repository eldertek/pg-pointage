<template>
  <div>
    <Title level="1" class="mb-4">Tableau de bord</Title>
    
    <v-row>
      <v-col cols="12" md="6" lg="3">
        <v-card class="mb-4" :loading="loading.stats">
          <v-card-text class="text-center">
            <div class="text-overline mb-2">Sites</div>
            <div class="text-h3 mb-2">{{ stats.sitesCount }}</div>
            <div class="text-caption">Total des sites actifs</div>
          </v-card-text>
        </v-card>
      </v-col>
      
      <v-col cols="12" md="6" lg="3">
        <v-card class="mb-4" :loading="loading.stats">
          <v-card-text class="text-center">
            <div class="text-overline mb-2">Employés</div>
            <div class="text-h3 mb-2">{{ stats.employeesCount }}</div>
            <div class="text-caption">Total des employés actifs</div>
          </v-card-text>
        </v-card>
      </v-col>
      
      <v-col cols="12" md="6" lg="3">
        <v-card class="mb-4" :loading="loading.stats">
          <v-card-text class="text-center">
            <div class="text-overline mb-2">Pointages</div>
            <div class="text-h3 mb-2">{{ stats.timesheetsCount }}</div>
            <div class="text-caption">Pointages aujourd'hui</div>
          </v-card-text>
        </v-card>
      </v-col>
      
      <v-col cols="12" md="6" lg="3">
        <v-card class="mb-4" :loading="loading.stats">
          <v-card-text class="text-center">
            <div class="text-overline mb-2">Anomalies</div>
            <div class="text-h3 mb-2">{{ stats.anomaliesCount }}</div>
            <div class="text-caption">Anomalies à traiter</div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
    
    <v-row>
      <v-col cols="12" lg="8">
        <v-card class="mb-4">
          <v-card-title>Activité récente</v-card-title>
          <v-card-text>
            <p class="text-center py-4">Graphique d'activité à venir</p>
          </v-card-text>
        </v-card>
      </v-col>
      
      <v-col cols="12" lg="4">
        <v-card class="mb-4" :loading="loading.anomalies">
          <v-card-title class="d-flex justify-space-between align-center">
            Dernières anomalies
            <v-btn
              icon="mdi-refresh"
              size="small"
              @click="fetchRecentAnomalies"
              :loading="loading.anomalies"
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
            Aucune anomalie récente
          </v-card-text>

          <v-list v-else>
            <v-list-item
              v-for="anomaly in recentAnomalies"
              :key="anomaly.id"
              class="py-2"
            >
              <template v-slot:prepend>
                <v-icon
                  :color="anomaly.status === 'PENDING' ? 'error' : 'success'"
                  class="me-2"
                  :title="anomaly.status_display"
                >
                  {{ anomaly.status === 'PENDING' ? 'mdi-alert-circle' : 'mdi-check-circle' }}
                </v-icon>
              </template>
              
              <v-list-item-title class="font-weight-medium">
                {{ anomaly.anomaly_type_display }}
                <v-chip
                  size="x-small"
                  :color="anomaly.status === 'PENDING' ? 'error' : 'success'"
                  class="ml-2"
                >
                  {{ anomaly.status_display }}
                </v-chip>
              </v-list-item-title>
              
              <v-list-item-subtitle class="mt-1">
                <v-icon size="small" class="me-1">mdi-account</v-icon>
                {{ anomaly.employee_name }}
              </v-list-item-subtitle>
              
              <v-list-item-subtitle>
                <v-icon size="small" class="me-1">mdi-map-marker</v-icon>
                {{ anomaly.site_name }}
              </v-list-item-subtitle>
              
              <v-list-item-subtitle class="text-caption mt-1">
                <v-icon size="small" class="me-1">mdi-clock-outline</v-icon>
                {{ new Date(anomaly.created_at).toLocaleString('fr-FR', {
                  dateStyle: 'medium',
                  timeStyle: 'medium'
                }) }}
              </v-list-item-subtitle>

              <v-list-item-subtitle v-if="anomaly.description" class="text-caption mt-1 text-grey">
                <v-icon size="small" class="me-1">mdi-information</v-icon>
                {{ anomaly.description }}
              </v-list-item-subtitle>
            </v-list-item>
            
            <v-divider v-if="recentAnomalies.length > 1" class="my-2"></v-divider>
          </v-list>
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
import { Title } from '@/components/typography'

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
    Title
  },
  setup() {
    const toast = useToast() as ToastInterface
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

    const fetchDashboardStats = async () => {
      try {
        loading.value.stats = true
        console.log('Fetching dashboard stats...')
        
        // Récupérer le nombre de sites
        const sitesResponse = await sitesApi.getAllSites()
        console.log('Sites response:', sitesResponse.data)
        stats.value.sitesCount = sitesResponse.data?.count || sitesResponse.data?.results?.length || 0
        
        // Récupérer le nombre d'employés
        const employeesResponse = await usersApi.searchUsers('')  // Recherche vide pour obtenir tous les utilisateurs
        console.log('Employees response:', employeesResponse.data)
        stats.value.employeesCount = employeesResponse.data?.count || employeesResponse.data?.results?.length || 0
        
        // Récupérer le nombre de pointages du jour
        const today = new Date().toISOString().split('T')[0]
        const timesheetsResponse = await timesheetsApi.getTimesheets({
          start_date: today,
          end_date: today
        })
        console.log('Timesheets response:', timesheetsResponse.data)
        stats.value.timesheetsCount = timesheetsResponse.data?.count || timesheetsResponse.data?.results?.length || 0
        
        // Récupérer le nombre d'anomalies en attente
        const anomaliesResponse = await timesheetsApi.getAnomalies({
          status: 'PENDING'
        })
        console.log('Anomalies response:', anomaliesResponse.data)
        stats.value.anomaliesCount = anomaliesResponse.data?.count || anomaliesResponse.data?.results?.length || 0
        
        console.log('Updated stats:', stats.value)
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
        recentAnomalies.value = response.data?.results || []
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
      fetchRecentAnomalies
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
</style>

