<template>
  <div class="history-container">
    <h1 class="text-h5 mb-4">Historique des pointages</h1>
    
    <v-card class="mb-4">
      <v-card-title>Filtres</v-card-title>
      <v-card-text>
        <v-select
          v-model="filters.site"
          label="Site"
          :items="siteOptions"
          variant="outlined"
          clearable
          class="mb-2"
        ></v-select>
        
        <v-select
          v-model="filters.type"
          label="Type"
          :items="typeOptions"
          variant="outlined"
          clearable
          class="mb-2"
        ></v-select>
        
        <v-select
          v-model="filters.status"
          label="Statut"
          :items="statusOptions"
          variant="outlined"
          clearable
          class="mb-2"
        ></v-select>
        
        <div class="d-flex">
          <v-text-field
            v-model="filters.startDate"
            label="Du"
            type="date"
            variant="outlined"
            class="mr-2"
          ></v-text-field>
          
          <v-text-field
            v-model="filters.endDate"
            label="Au"
            type="date"
            variant="outlined"
          ></v-text-field>
        </div>
        
        <div class="d-flex justify-space-between mt-2">
          <v-btn
            color="primary"
            @click="applyFilters"
          >
            Appliquer
          </v-btn>
          
          <v-btn
            color="error"
            variant="text"
            @click="resetFilters"
          >
            Réinitialiser
          </v-btn>
        </div>
      </v-card-text>
    </v-card>
    
    <div v-if="loading" class="text-center my-4">
      <v-progress-circular indeterminate color="primary" size="64"></v-progress-circular>
    </div>
    
    <template v-else>
      <div v-if="timesheets.length === 0" class="text-center my-4">
        <p class="text-subtitle-1">Aucun pointage trouvé</p>
      </div>
      
      <template v-else>
        <v-timeline density="compact" align="start">
          <v-timeline-item
            v-for="(timesheet, index) in timesheets"
            :key="index"
            :dot-color="getTimesheetColor(timesheet)"
            size="small"
          >
            <div class="d-flex justify-space-between align-center">
              <div>
                <div class="text-subtitle-2">{{ timesheet.site }}</div>
                <div class="text-caption">{{ formatDate(timesheet.date, timesheet.time) }}</div>
              </div>
              <v-chip
                :color="getTimesheetColor(timesheet)"
                size="small"
                class="ml-2"
              >
                {{ timesheet.type }}
              </v-chip>
            </div>
            <div v-if="timesheet.status !== 'Normal'" class="mt-1">
              <v-chip
                size="x-small"
                :color="getStatusColor(timesheet.status)"
                variant="outlined"
                class="mt-1"
              >
                {{ timesheet.statusDetail }}
              </v-chip>
            </div>
          </v-timeline-item>
        </v-timeline>
        
        <div class="text-center mt-4">
          <v-btn
            v-if="hasMoreTimesheets"
            color="primary"
            variant="outlined"
            @click="loadMoreTimesheets"
            :loading="loadingMore"
          >
            Charger plus
          </v-btn>
        </div>
      </template>
    </template>
  </div>
</template>

<script>
import { ref } from 'vue'
import { format } from 'date-fns'
import { fr } from 'date-fns/locale'

export default {
  name: 'HistoryView',
  setup() {
    const loading = ref(true)
    const loadingMore = ref(false)
    const hasMoreTimesheets = ref(true)
    
    const filters = ref({
      site: '',
      type: '',
      status: '',
      startDate: '',
      endDate: ''
    })
    
    const siteOptions = ref(['Centre Commercial', 'Hôpital Nord', 'Résidence Les Pins'])
    const typeOptions = ref(['Arrivée', 'Départ'])
    const statusOptions = ref(['Normal', 'Retard', 'Départ anticipé'])
    
    const timesheets = ref([])
    
    const formatDate = (date, time) => {
      const dateObj = new Date(`${date}T${time}`)
      return format(dateObj, 'EEEE d MMMM yyyy à HH:mm', { locale: fr })
    }
    
    const getTimesheetColor = (timesheet) => {
      if (timesheet.status === 'Retard') return 'warning'
      if (timesheet.status === 'Départ anticipé') return 'error'
      return timesheet.type === 'Arrivée' ? 'success' : 'info'
    }
    
    const getStatusColor = (status) => {
      if (status === 'Normal') return 'success'
      if (status === 'Retard') return 'warning'
      if (status === 'Départ anticipé') return 'error'
      return 'grey'
    }
    
    const applyFilters = () => {
      loading.value = true
      
      // Simulation d'API call avec filtre
      setTimeout(() => {
        timesheets.value = generateMockTimesheets()
        loading.value = false
        hasMoreTimesheets.value = true
      }, 1000)
    }
    
    const resetFilters = () => {
      filters.value = {
        site: '',
        type: '',
        status: '',
        startDate: '',
        endDate: ''
      }
      applyFilters()
    }
    
    const loadMoreTimesheets = () => {
      loadingMore.value = true
      
      // Simulation d'API call pour charger plus de données
      setTimeout(() => {
        const moreTimesheets = generateMockTimesheets(5)
        timesheets.value = [...timesheets.value, ...moreTimesheets]
        loadingMore.value = false
        
        // Simulation de fin des données
        if (timesheets.value.length > 20) {
          hasMoreTimesheets.value = false
        }
      }, 1000)
    }
    
    const generateMockTimesheets = (count = 10) => {
      const result = []
      const sites = ['Centre Commercial', 'Hôpital Nord', 'Résidence Les Pins']
      const types = ['Arrivée', 'Départ']
      const statuses = ['Normal', 'Retard', 'Départ anticipé']
      
      for (let i = 0; i < count; i++) {
        const status = statuses[Math.floor(Math.random() * statuses.length)]
        const type = types[Math.floor(Math.random() * types.length)]
        
        let statusDetail = ''
        if (status === 'Retard') {
          statusDetail = `Retard de ${Math.floor(Math.random() * 30) + 1} minutes`
        } else if (status === 'Départ anticipé') {
          statusDetail = `Départ anticipé de ${Math.floor(Math.random() * 30) + 1} minutes`
        }
        
        result.push({
          site: sites[Math.floor(Math.random() * sites.length)],
          date: `2025-03-${String(Math.floor(Math.random() * 15) + 1).padStart(2, '0')}`,
          time: `${String(Math.floor(Math.random() * 12) + 8).padStart(2, '0')}:${String(Math.floor(Math.random() * 60)).padStart(2, '0')}`,
          type,
          status,
          statusDetail
        })
      }
      
      // Trier par date et heure, du plus récent au plus ancien
      return result.sort((a, b) => {
        const dateA = new Date(`${a.date}T${a.time}`)
        const dateB = new Date(`${b.date}T${b.time}`)
        return dateB - dateA
      })
    }
    
    // Charger les données initiales
    applyFilters()
    
    return {
      loading,
      loadingMore,
      hasMoreTimesheets,
      filters,
      siteOptions,
      typeOptions,
      statusOptions,
      timesheets,
      formatDate,
      getTimesheetColor,
      getStatusColor,
      applyFilters,
      resetFilters,
      loadMoreTimesheets
    }
  }
}
</script>

<style scoped>
.history-container {
  padding: 16px;
}
</style>

