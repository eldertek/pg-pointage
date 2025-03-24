<template>
  <div>
    <h1 class="text-h4 mb-4">Tableau de bord</h1>
    
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
              :subtitle="new Date(anomaly.created_at).toLocaleString()"
            >
              <template v-slot:prepend>
                <v-icon
                  :color="anomaly.status === 'resolved' ? 'success' : 'error'"
                  class="me-2"
                >
                  {{ anomaly.status === 'resolved' ? 'mdi-check-circle' : 'mdi-alert-circle' }}
                </v-icon>
              </template>
              
              <v-list-item-title>{{ anomaly.type }}</v-list-item-title>
              <v-list-item-subtitle>{{ anomaly.employee }} - {{ anomaly.site }}</v-list-item-subtitle>
            </v-list-item>
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
import api from '@/services/api'

interface Stats {
  sitesCount: number
  employeesCount: number
  timesheetsCount: number
  anomaliesCount: number
}

interface Anomaly {
  id: number
  type: string
  employee: string
  site: string
  created_at: string
  status: string
}

export default {
  name: 'DashboardView',
  setup() {
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
        const response = await api.get('/dashboard/stats')
        console.log('Dashboard stats received:', response.data)
        stats.value = response.data
      } catch (err) {
        console.error('Error fetching dashboard stats:', err)
        error.value.stats = 'Erreur lors du chargement des statistiques'
      } finally {
        loading.value.stats = false
      }
    }

    const fetchRecentAnomalies = async () => {
      try {
        loading.value.anomalies = true
        console.log('Fetching recent anomalies...')
        const response = await api.get('/dashboard/anomalies/recent')
        console.log('Recent anomalies received:', response.data)
        recentAnomalies.value = response.data
      } catch (err) {
        console.error('Error fetching recent anomalies:', err)
        error.value.anomalies = 'Erreur lors du chargement des anomalies'
      } finally {
        loading.value.anomalies = false
      }
    }

    // Refresh data every 5 minutes
    const startAutoRefresh = () => {
      const refreshInterval = 5 * 60 * 1000 // 5 minutes
      setInterval(() => {
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

