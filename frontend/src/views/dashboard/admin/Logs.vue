<template>
  <div>
    <div class="d-flex justify-space-between align-center mb-4">
      <h1 class="text-h4">Logs Système</h1>
      <v-btn color="primary" prepend-icon="mdi-refresh" @click="fetchLogs" :loading="loading">
        Rafraîchir
      </v-btn>
    </div>

    <v-card>
      <v-card-title>
        <v-row align="center">
          <v-col cols="12" sm="4">
            <v-text-field
              v-model="search"
              prepend-inner-icon="mdi-magnify"
              label="Rechercher"
              single-line
              hide-details
              variant="outlined"
              density="compact"
            ></v-text-field>
          </v-col>
          <v-col cols="12" sm="4">
            <v-select
              v-model="selectedLevel"
              :items="logLevels"
              label="Niveau"
              hide-details
              variant="outlined"
              density="compact"
              clearable
            ></v-select>
          </v-col>
          <v-col cols="12" sm="4">
            <v-menu
              ref="menu"
              v-model="menu"
              :close-on-content-click="false"
              transition="scale-transition"
              offset-y
            >
              <template v-slot:activator="{ props }">
                <v-text-field
                  v-model="dateRange"
                  label="Période"
                  prepend-inner-icon="mdi-calendar"
                  readonly
                  v-bind="props"
                  hide-details
                  variant="outlined"
                  density="compact"
                ></v-text-field>
              </template>
              <v-date-picker
                v-model="dates"
                range
                @update:model-value="menu = false"
              ></v-date-picker>
            </v-menu>
          </v-col>
        </v-row>
      </v-card-title>

      <v-data-table
        :headers="headers"
        :items="filteredLogs"
        :search="search"
        :loading="loading"
      >
        <template #[`item.level`]="{ item }">
          <v-chip
            :color="getLevelColor(item.raw.level)"
            size="small"
          >
            {{ item.raw.level }}
          </v-chip>
        </template>

        <template #[`item.timestamp`]="{ item }">
          {{ formatDate(item.raw.timestamp) }}
        </template>

        <template #[`item.actions`]="{ item }">
          <v-btn
            icon
            variant="text"
            size="small"
            color="primary"
            @click="showLogDetails(item.raw)"
          >
            <v-icon>mdi-information</v-icon>
          </v-btn>
        </template>
      </v-data-table>
    </v-card>

    <!-- Dialog pour les détails du log -->
    <v-dialog v-model="showDetailsDialog" max-width="800px">
      <v-card>
        <v-card-title class="text-h5">
          Détails du Log
          <v-chip
            :color="getLevelColor(selectedLog?.level)"
            class="ml-4"
          >
            {{ selectedLog?.level }}
          </v-chip>
        </v-card-title>
        <v-card-text>
          <v-list>
            <v-list-item>
              <v-list-item-title>Timestamp</v-list-item-title>
              <v-list-item-subtitle>{{ formatDate(selectedLog?.timestamp) }}</v-list-item-subtitle>
            </v-list-item>
            <v-list-item>
              <v-list-item-title>Service</v-list-item-title>
              <v-list-item-subtitle>{{ selectedLog?.service }}</v-list-item-subtitle>
            </v-list-item>
            <v-list-item>
              <v-list-item-title>Message</v-list-item-title>
              <v-list-item-subtitle>{{ selectedLog?.message }}</v-list-item-subtitle>
            </v-list-item>
            <v-list-item v-if="selectedLog?.details">
              <v-list-item-title>Détails</v-list-item-title>
              <v-list-item-subtitle>
                <pre>{{ JSON.stringify(selectedLog?.details, null, 2) }}</pre>
              </v-list-item-subtitle>
            </v-list-item>
          </v-list>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="primary" variant="text" @click="showDetailsDialog = false">Fermer</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import api from '@/services/api'

export default {
  name: 'AdminLogsView',
  setup() {
    const loading = ref(false)
    const search = ref('')
    const selectedLevel = ref(null)
    const dates = ref([])
    const menu = ref(false)
    const showDetailsDialog = ref(false)
    const selectedLog = ref(null)
    
    const headers = ref([
      { title: 'Date', align: 'start', key: 'timestamp' },
      { title: 'Niveau', key: 'level', align: 'center' },
      { title: 'Service', key: 'service' },
      { title: 'Message', key: 'message' },
      { title: 'Actions', key: 'actions', align: 'end', sortable: false }
    ])

    const logs = ref([])
    const logLevels = ['INFO', 'WARNING', 'ERROR', 'CRITICAL']

    const dateRange = computed(() => {
      return dates.value.length === 2
        ? `${formatDate(dates.value[0])} - ${formatDate(dates.value[1])}`
        : ''
    })

    const filteredLogs = computed(() => {
      let filtered = [...logs.value]
      
      if (selectedLevel.value) {
        filtered = filtered.filter(log => log.level === selectedLevel.value)
      }
      
      if (dates.value.length === 2) {
        const startDate = new Date(dates.value[0])
        const endDate = new Date(dates.value[1])
        filtered = filtered.filter(log => {
          const logDate = new Date(log.timestamp)
          return logDate >= startDate && logDate <= endDate
        })
      }
      
      return filtered
    })

    const getLevelColor = (level) => {
      switch (level) {
        case 'INFO':
          return 'info'
        case 'WARNING':
          return 'warning'
        case 'ERROR':
          return 'error'
        case 'CRITICAL':
          return 'deep-purple'
        default:
          return 'grey'
      }
    }

    const formatDate = (date) => {
      if (!date) return ''
      return new Date(date).toLocaleString()
    }

    const fetchLogs = async () => {
      loading.value = true
      try {
        const response = await api.get('/api/v1/admin/logs/')
        logs.value = response.data
      } catch (error) {
        console.error('Erreur lors du chargement des logs:', error)
      } finally {
        loading.value = false
      }
    }

    const showLogDetails = (log) => {
      selectedLog.value = log
      showDetailsDialog.value = true
    }

    // Rafraîchir les logs toutes les minutes
    setInterval(fetchLogs, 60000)

    // Charger les logs au montage
    fetchLogs()

    return {
      loading,
      search,
      selectedLevel,
      dates,
      menu,
      showDetailsDialog,
      selectedLog,
      headers,
      logs,
      logLevels,
      dateRange,
      filteredLogs,
      getLevelColor,
      formatDate,
      fetchLogs,
      showLogDetails
    }
  }
}
</script>

<style scoped>
pre {
  background-color: #f5f5f5;
  padding: 1rem;
  border-radius: 4px;
  overflow-x: auto;
}
</style> 