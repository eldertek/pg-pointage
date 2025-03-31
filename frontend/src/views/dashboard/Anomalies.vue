<template>
  <div>
    <div class="d-flex justify-space-between align-center mb-4" v-if="!isDetailView">
      <Title :level="1">Anomalies</Title>
      <v-btn 
        color="warning" 
        prepend-icon="mdi-magnify-scan" 
        :loading="scanning"
        @click="scanForAnomalies"
      >
        Scanner les anomalies
      </v-btn>
    </div>
    
    <v-card class="mb-4" v-if="!isDetailView">
      <v-card-title>Filtres</v-card-title>
      <v-card-text>
        <v-row>
          <v-col cols="12" :md="currentSiteId ? 4 : 3">
            <v-autocomplete
              v-model="filters.employee"
              :loading="searchingEmployees"
              :items="employeeOptions"
              :search-input.sync="employeeSearch"
              label="Employé"
              item-title="text"
              item-value="value"
              variant="outlined"
              prepend-inner-icon="mdi-account-search"
              clearable
              @update:search="searchEmployees"
              @update:modelValue="applyFilters"
            >
              <template v-slot:no-data>
                <v-list-item>
                  <v-list-item-title>
                    Commencez à taper pour rechercher un employé
                  </v-list-item-title>
                </v-list-item>
              </template>
            </v-autocomplete>
          </v-col>
          
          <v-col cols="12" :md="currentSiteId ? 4 : 3" v-if="!currentSiteId">
            <v-select
              v-model="filters.site"
              label="Site"
              :items="siteOptions"
              item-title="text"
              item-value="value"
              variant="outlined"
              prepend-inner-icon="mdi-map-marker"
              clearable
              @update:modelValue="applyFilters"
            ></v-select>
          </v-col>
          
          <v-col cols="12" :md="currentSiteId ? 4 : 3">
            <v-select
              v-model="filters.type"
              label="Type d'anomalie"
              :items="anomalyTypeOptions"
              item-title="text"
              item-value="value"
              variant="outlined"
              prepend-inner-icon="mdi-alert-circle"
              clearable
              @update:modelValue="applyFilters"
            ></v-select>
          </v-col>
          
          <v-col cols="12" :md="currentSiteId ? 4 : 3">
            <v-select
              v-model="filters.status"
              label="Statut"
              :items="statusOptions"
              item-title="text"
              item-value="value"
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
            <v-btn 
              color="error" 
              variant="outlined" 
              @click="resetFilters"
              prepend-icon="mdi-refresh"
              class="px-4"
            >
              Réinitialiser les filtres
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
        :no-data-text="'Aucune anomalie trouvée'"
        :loading-text="'Chargement des anomalies...'"
        :items-per-page-text="'Lignes par page'"
        :page-text="'{0}-{1} sur {2}'"
        :items-per-page-options="[
          { title: '5', value: 5 },
          { title: '10', value: 10 },
          { title: '15', value: 15 },
          { title: 'Tout', value: -1 }
        ]"
        class="elevation-1"
      >
        <template #type="{ item }">
          <v-chip
            :color="getTypeColor(item.raw.anomaly_type_display)"
            size="small"
          >
            {{ item.raw.anomaly_type_display }}
          </v-chip>
        </template>
        <template #status="{ item }">
          <v-chip
            :color="getStatusColor(item.raw.status_display)"
            size="small"
          >
            {{ item.raw.status_display }}
          </v-chip>
        </template>
        <template #actions="{ item }">
          <v-btn
            v-if="item.raw.status === 'PENDING'"
            icon
            variant="text"
            size="small"
            color="success"
            @click="resolveAnomaly(item.raw.id)"
          >
            <v-icon>mdi-check</v-icon>
          </v-btn>
          <v-btn
            v-if="item.raw.status === 'PENDING'"
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

    <!-- Dialog de confirmation -->
    <v-dialog v-model="showDeleteDialog" max-width="400" persistent>
      <v-card>
        <!-- Dialog content -->
      </v-card>
    </v-dialog>
  </div>
</template>

<script>
import { ref, watch, computed } from 'vue'
import { timesheetsApi, sitesApi, usersApi } from '@/services/api'
import { useToast } from 'vue-toastification'
import { useSitesStore } from '@/stores/sites'
import { Title } from '@/components/typography'

export default {
  name: 'AnomaliesView',
  components: {
    Title
  },
  props: {
    isDetailView: {
      type: Boolean,
      default: false
    },
    siteId: {
      type: Number,
      default: null
    }
  },
  setup(props) {
    const toast = useToast()
    const sitesStore = useSitesStore()
    const loading = ref(true)
    const scanning = ref(false)
    
    // Computed pour le site courant - priorité au siteId passé en prop
    const currentSiteId = computed(() => props.siteId || sitesStore.getCurrentSiteId)
    
    const error = ref(null)
    const searchingEmployees = ref(false)
    const employeeSearch = ref('')
    const employeeOptions = ref([])
    
    const headers = ref([
      { title: 'Date', align: 'start', key: 'date' },
      { title: 'Employé', align: 'start', key: 'employee_name' },
      { title: 'Site', align: 'start', key: 'site_name' },
      { title: 'Type', align: 'center', key: 'anomaly_type_display' },
      { title: 'Description', align: 'start', key: 'description' },
      { title: 'Statut', align: 'center', key: 'status_display' },
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
    
    const siteOptions = ref([])
    const anomalyTypeOptions = ref([
      { text: 'Retard', value: 'LATE' },
      { text: 'Départ anticipé', value: 'EARLY_DEPARTURE' },
      { text: 'Arrivée manquante', value: 'MISSING_ARRIVAL' },
      { text: 'Départ manquant', value: 'MISSING_DEPARTURE' },
      { text: 'Heures insuffisantes', value: 'INSUFFICIENT_HOURS' },
      { text: 'Pointages consécutifs', value: 'CONSECUTIVE_SAME_TYPE' }
    ])
    const statusOptions = ref([
      { text: 'En attente', value: 'PENDING' },
      { text: 'Résolu', value: 'RESOLVED' },
      { text: 'Ignoré', value: 'IGNORED' }
    ])
    
    const anomalies = ref([])
    
    // Charger les sites
    const loadSites = async () => {
      try {
        const response = await sitesApi.getAllSites()
        if (response.data?.results) {
          siteOptions.value = response.data.results.map(site => ({
            text: site.name,
            value: site.id
          }))
        } else {
          console.error('Format de réponse inattendu pour les sites:', response.data)
          siteOptions.value = []
        }
      } catch (error) {
        console.error('Erreur lors du chargement des sites:', error)
        siteOptions.value = []
      }
    }
    
    const getTypeColor = (type) => {
      if (type === 'Retard') return 'warning'
      if (type === 'Départ anticipé') return 'error'
      if (type === 'Arrivée manquante') return 'red'
      if (type === 'Départ manquant') return 'purple'
      if (type === 'Heures insuffisantes') return 'deep-orange'
      if (type === 'Pointages consécutifs') return 'orange'
      return 'grey'
    }
    
    const getStatusColor = (status) => {
      if (status === 'En attente') return 'warning'
      if (status === 'Résolu') return 'success'
      if (status === 'Ignoré') return 'grey'
      return 'grey'
    }
    
    const resolveAnomaly = async (id) => {
      try {
        loading.value = true
        await timesheetsApi.updateAnomaly(id, {
          status: 'RESOLVED'
        })
        await applyFilters()
      } catch (error) {
        console.error('Erreur lors de la résolution de l\'anomalie:', error)
      } finally {
        loading.value = false
      }
    }
    
    const ignoreAnomaly = async (id) => {
      try {
        loading.value = true
        await timesheetsApi.updateAnomaly(id, {
          status: 'IGNORED'
        })
        await applyFilters()
      } catch (error) {
        console.error('Erreur lors de l\'ignorance de l\'anomalie:', error)
      } finally {
        loading.value = false
      }
    }
    
    const buildQueryParams = () => {
      const params = {}
      
      if (filters.value.employee) {
        params.employee = filters.value.employee
      }
      // Utiliser le site actif en priorité
      if (currentSiteId.value) {
        params.site = currentSiteId.value
      } else if (filters.value.site) {
        params.site = filters.value.site
      }
      if (filters.value.type) {
        params.anomaly_type = filters.value.type
      }
      if (filters.value.status) {
        params.status = filters.value.status
      }
      if (filters.value.startDate) {
        params.start_date = filters.value.startDate
      }
      if (filters.value.endDate) {
        params.end_date = filters.value.endDate
      }
      
      return params
    }
    
    const applyFilters = async () => {
      loading.value = true
      error.value = null
      try {
        const params = buildQueryParams()
        const response = await timesheetsApi.getAnomalies(params)
        if (response.data?.results) {
          anomalies.value = response.data.results
        } else if (Array.isArray(response.data)) {
          anomalies.value = response.data
        } else {
          console.error('Format de réponse inattendu pour les anomalies:', response.data)
          anomalies.value = []
          error.value = 'Format de données incorrect'
        }
      } catch (error) {
        console.error('Erreur lors du chargement des anomalies:', error)
        anomalies.value = []
        error.value = 'Erreur lors du chargement des données'
      } finally {
        loading.value = false
      }
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
    
    const scanForAnomalies = async () => {
      try {
        scanning.value = true
        const params = buildQueryParams()
        const response = await timesheetsApi.scanAnomalies(params)
        
        // Afficher une notification de succès
        if (response.data?.anomalies_count !== undefined) {
          const count = response.data.anomalies_count
          const message = count > 0 
            ? `${count} anomalie${count > 1 ? 's' : ''} détectée${count > 1 ? 's' : ''} et créée${count > 1 ? 's' : ''}.`
            : 'Aucune nouvelle anomalie détectée.'
          
          toast.success(message)
        }
        
        // Recharger les anomalies après le scan
        await applyFilters()
      } catch (error) {
        console.error('Erreur lors du scan des anomalies:', error)
        
        // Afficher une notification d'erreur
        toast.error(
          error.response?.data?.error || 'Une erreur est survenue lors du scan des anomalies.'
        )
      } finally {
        scanning.value = false
      }
    }
    
    // Recherche d'employés
    const searchEmployees = async (query) => {
      if (!query || query.length < 2) {
        employeeOptions.value = []
        return
      }

      try {
        searchingEmployees.value = true
        const response = await usersApi.searchUsers(query)
        if (response.data?.results) {
          employeeOptions.value = response.data.results.map(user => ({
            text: `${user.first_name} ${user.last_name}`,
            value: user.id
          }))
        }
      } catch (error) {
        console.error('Erreur lors de la recherche des employés:', error)
        employeeOptions.value = []
      } finally {
        searchingEmployees.value = false
      }
    }
    
    // Watch for changes in current site
    watch(() => currentSiteId.value, (newSiteId) => {
      if (newSiteId) {
        filters.value.site = newSiteId
        applyFilters()
      }
    })
    
    // Charger les données initiales
    const init = async () => {
      if (currentSiteId.value) {
        filters.value.site = currentSiteId.value
      }
      await loadSites()
      await applyFilters()
    }
    
    // Ajout de la variable manquante
    const showDeleteDialog = ref(false)
    
    init()
    
    return {
      loading,
      scanning,
      error,
      searchingEmployees,
      employeeSearch,
      employeeOptions,
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
      resetFilters,
      scanForAnomalies,
      searchEmployees,
      showDeleteDialog,
      currentSiteId
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

:deep(.v-btn[color="warning"]) {
  background-color: #F78C48 !important;
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

:deep(.v-btn--icon[color="warning"]) {
  color: #F78C48 !important;
}

/* Correction des overlays et underlays */
:deep(.v-btn__overlay),
:deep(.v-btn__underlay) {
  opacity: 0 !important;
}
</style>

