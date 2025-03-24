<template>
  <div>
    <h1 class="text-h4 mb-4">Pointages</h1>
    
    <v-card class="mb-4">
      <v-card-title>Filtres</v-card-title>
      <v-card-text>
        <v-row>
          <v-col cols="12" md="3">
            <v-text-field
              v-model="filters.employee"
              label="Employé"
              variant="outlined"
              prepend-inner-icon="mdi-account-search"
              clearable
              @update:modelValue="applyFilters"
            ></v-text-field>
          </v-col>
          
          <v-col cols="12" md="3">
            <v-select
              v-model="filters.site"
              label="Site"
              :items="siteOptions"
              variant="outlined"
              prepend-inner-icon="mdi-map-marker"
              clearable
              @update:modelValue="applyFilters"
            ></v-select>
          </v-col>
          
          <v-col cols="12" md="3">
            <v-select
              v-model="filters.entryType"
              label="Type de pointage"
              :items="entryTypeOptions"
              variant="outlined"
              prepend-inner-icon="mdi-clock-time-four"
              clearable
              @update:modelValue="applyFilters"
            ></v-select>
          </v-col>
          
          <v-col cols="12" md="3">
            <v-select
              v-model="filters.status"
              label="Statut"
              :items="statusOptions"
              variant="outlined"
              prepend-inner-icon="mdi-alert-circle"
              clearable
              @update:modelValue="applyFilters"
            ></v-select>
          </v-col>
        </v-row>
        
        <v-row>
          <v-col cols="12" md="4">
            <v-text-field
              v-model="filters.startDate"
              label="Du"
              type="date"
              variant="outlined"
              prepend-inner-icon="mdi-calendar"
              clearable
              @update:modelValue="applyFilters"
            ></v-text-field>
          </v-col>
          
          <v-col cols="12" md="4">
            <v-text-field
              v-model="filters.endDate"
              label="Au"
              type="date"
              variant="outlined"
              prepend-inner-icon="mdi-calendar"
              clearable
              @update:modelValue="applyFilters"
            ></v-text-field>
          </v-col>
          
          <v-col cols="12" md="4" class="d-flex align-center">
            <v-btn color="primary" @click="applyFilters" class="mr-2">
              Appliquer
            </v-btn>
            <v-btn color="error" variant="outlined" @click="resetFilters">
              Réinitialiser
            </v-btn>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>
    
    <v-card>
      <v-data-table
        :headers="headers"
        :items="timesheets"
        :loading="loading"
        :items-per-page="10"
        class="elevation-1"
      >
        <template #type="{ item }">
          <v-chip
            :color="item.raw.type === 'Arrivée' ? 'success' : 'info'"
            size="small"
          >
            {{ item.raw.type }}
          </v-chip>
        </template>
        <template #status="{ item }">
          <v-chip
            :color="getStatusColor(item.raw.status)"
            size="small"
          >
            {{ item.raw.status }}
          </v-chip>
        </template>
      </v-data-table>
    </v-card>
  </div>
</template>

<script>
import { ref } from 'vue'

export default {
  name: 'TimesheetsView',
  setup() {
    const loading = ref(true)
    const headers = ref([
      { title: 'Date', align: 'start', key: 'date' },
      { title: 'Heure', align: 'start', key: 'time' },
      { title: 'Employé', align: 'start', key: 'employee' },
      { title: 'Site', align: 'start', key: 'site' },
      { title: 'Type', align: 'center', key: 'type' },
      { title: 'Statut', align: 'center', key: 'status' }
    ])
    
    const filters = ref({
      employee: '',
      site: '',
      entryType: '',
      status: '',
      startDate: '',
      endDate: ''
    })
    
    const siteOptions = ref(['Centre Commercial', 'Hôpital Nord', 'Résidence Les Pins'])
    const entryTypeOptions = ref(['Arrivée', 'Départ'])
    const statusOptions = ref(['Normal', 'Retard', 'Départ anticipé'])
    
    const timesheets = ref([])
    
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
        timesheets.value = [
          { date: '10/03/2025', time: '08:02', employee: 'Jean Dupont', site: 'Centre Commercial', type: 'Arrivée', status: 'Normal' },
          { date: '10/03/2025', time: '16:00', employee: 'Jean Dupont', site: 'Centre Commercial', type: 'Départ', status: 'Normal' },
          { date: '10/03/2025', time: '08:00', employee: 'Marie Martin', site: 'Hôpital Nord', type: 'Arrivée', status: 'Normal' },
          { date: '10/03/2025', time: '16:05', employee: 'Marie Martin', site: 'Hôpital Nord', type: 'Départ', status: 'Normal' },
          { date: '11/03/2025', time: '08:17', employee: 'Jean Dupont', site: 'Centre Commercial', type: 'Arrivée', status: 'Retard' },
          { date: '11/03/2025', time: '15:45', employee: 'Jean Dupont', site: 'Centre Commercial', type: 'Départ', status: 'Départ anticipé' },
          { date: '11/03/2025', time: '08:05', employee: 'Marie Martin', site: 'Hôpital Nord', type: 'Arrivée', status: 'Normal' },
          { date: '11/03/2025', time: '16:00', employee: 'Marie Martin', site: 'Hôpital Nord', type: 'Départ', status: 'Normal' },
          { date: '12/03/2025', time: '08:00', employee: 'Jean Dupont', site: 'Centre Commercial', type: 'Arrivée', status: 'Normal' },
          { date: '12/03/2025', time: '16:00', employee: 'Jean Dupont', site: 'Centre Commercial', type: 'Départ', status: 'Normal' }
        ]
        loading.value = false
      }, 1000)
    }
    
    const resetFilters = () => {
      filters.value = {
        employee: '',
        site: '',
        entryType: '',
        status: '',
        startDate: '',
        endDate: ''
      }
      applyFilters()
    }
    
    // Charger les données initiales
    applyFilters()
    
    return {
      loading,
      headers,
      filters,
      siteOptions,
      entryTypeOptions,
      statusOptions,
      timesheets,
      getStatusColor,
      applyFilters,
      resetFilters
    }
  }
}
</script>

