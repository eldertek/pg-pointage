<template>
  <div>
    <h1 class="text-h4 mb-4">Anomalies</h1>
    
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
              v-model="filters.type"
              label="Type d'anomalie"
              :items="anomalyTypeOptions"
              variant="outlined"
              prepend-inner-icon="mdi-alert-circle"
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
              prepend-inner-icon="mdi-check-circle"
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
        :items="anomalies"
        :loading="loading"
        :items-per-page="10"
        class="elevation-1"
      >
        <template #type="{ item }">
          <v-chip
            :color="getTypeColor(item.raw.type)"
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
        <template #actions="{ item }">
          <v-btn
            v-if="item.raw.status === 'En attente'"
            icon
            variant="text"
            size="small"
            color="success"
            @click="resolveAnomaly(item.raw.id)"
          >
            <v-icon>mdi-check</v-icon>
          </v-btn>
          <v-btn
            v-if="item.raw.status === 'En attente'"
            icon
            variant="text"
            size="small"
            color="error"
            @click="ignoreAnomaly(item.raw.id)"
          >
            <v-icon>mdi-close</v-icon>
          </v-btn>
          <v-btn
            icon
            variant="text"
            size="small"
            color="primary"
          >
            <v-icon>mdi-eye</v-icon>
          </v-btn>
        </template>
      </v-data-table>
    </v-card>
  </div>
</template>

<script>
import { ref } from 'vue'

export default {
  name: 'AnomaliesView',
  setup() {
    const loading = ref(true)
    const headers = ref([
      { title: 'Date', align: 'start', key: 'date' },
      { title: 'Employé', align: 'start', key: 'employee' },
      { title: 'Site', align: 'start', key: 'site' },
      { title: 'Type', align: 'center', key: 'type' },
      { title: 'Description', align: 'start', key: 'description' },
      { title: 'Statut', align: 'center', key: 'status' },
      { title: 'Actions', align: 'end', key: 'actions', sortable: false }
    ])
    
    const filters = ref({
      employee: '',
      site: '',
      type: '',
      status: '',
      startDate: '',
      endDate: ''
    })
    
    const siteOptions = ref(['Centre Commercial', 'Hôpital Nord', 'Résidence Les Pins'])
    const anomalyTypeOptions = ref(['Retard', 'Départ anticipé', 'Arrivée manquante', 'Départ manquant', 'Heures insuffisantes'])
    const statusOptions = ref(['En attente', 'Résolu', 'Ignoré'])
    
    const anomalies = ref([])
    
    const getTypeColor = (type) => {
      if (type === 'Retard') return 'warning'
      if (type === 'Départ anticipé') return 'error'
      if (type === 'Arrivée manquante') return 'red'
      if (type === 'Départ manquant') return 'purple'
      if (type === 'Heures insuffisantes') return 'deep-orange'
      return 'grey'
    }
    
    const getStatusColor = (status) => {
      if (status === 'En attente') return 'warning'
      if (status === 'Résolu') return 'success'
      if (status === 'Ignoré') return 'grey'
      return 'grey'
    }
    
    const resolveAnomaly = (id) => {
      // Simulation d'API call
      console.log(`Résolution de l'anomalie ${id}`)
      
      // Pour la démo, on met à jour le statut localement
      const index = anomalies.value.findIndex(a => a.id === id)
      if (index !== -1) {
        anomalies.value[index].status = 'Résolu'
      }
    }
    
    const ignoreAnomaly = (id) => {
      // Simulation d'API call
      console.log(`Ignorer l'anomalie ${id}`)
      
      // Pour la démo, on met à jour le statut localement
      const index = anomalies.value.findIndex(a => a.id === id)
      if (index !== -1) {
        anomalies.value[index].status = 'Ignoré'
      }
    }
    
    const applyFilters = () => {
      loading.value = true
      
      // Simulation d'API call avec filtre
      setTimeout(() => {
        anomalies.value = [
          { 
            id: 1, 
            date: '11/03/2025', 
            employee: 'Jean Dupont', 
            site: 'Centre Commercial', 
            type: 'Retard', 
            description: 'Retard de 17 minutes',
            status: 'En attente'
          },
          { 
            id: 2, 
            date: '11/03/2025', 
            employee: 'Jean Dupont', 
            site: 'Centre Commercial', 
            type: 'Départ anticipé', 
            description: 'Départ anticipé de 15 minutes',
            status: 'En attente'
          },
          { 
            id: 3, 
            date: '10/03/2025', 
            employee: 'Pierre Lambert', 
            site: 'Résidence Les Pins', 
            type: 'Arrivée manquante', 
            description: 'Aucun pointage d\'arrivée enregistré',
            status: 'Résolu'
          },
          { 
            id: 4, 
            date: '09/03/2025', 
            employee: 'Marie Martin', 
            site: 'Hôpital Nord', 
            type: 'Départ manquant', 
            description: 'Aucun pointage de départ enregistré',
            status: 'Ignoré'
          },
          { 
            id: 5, 
            date: '08/03/2025', 
            employee: 'Sophie Petit', 
            site: 'Centre Commercial', 
            type: 'Heures insuffisantes', 
            description: 'Total: 5h30 (minimum requis: 6h)',
            status: 'Résolu'
          }
        ]
        loading.value = false
      }, 1000)
    }
    
    const resetFilters = () => {
      filters.value = {
        employee: '',
        site: '',
        type: '',
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
      anomalyTypeOptions,
      statusOptions,
      anomalies,
      getTypeColor,
      getStatusColor,
      resolveAnomaly,
      ignoreAnomaly,
      applyFilters,
      resetFilters
    }
  }
}
</script>

