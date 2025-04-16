<template>
  <div class="history-container">
    <Title :level="1" class="mb-4">Historique des enregistrements</Title>

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
        <p class="text-subtitle-1">Aucun enregistrement trouvé</p>
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
                <div class="text-subtitle-2">{{ timesheet.site_name }}</div>
                <div class="text-caption">{{ formatDate(timesheet.timestamp.split('T')[0], timesheet.timestamp.split('T')[1]) }}</div>
              </div>
              <v-chip
                :color="getTimesheetColor(timesheet)"
                size="small"
                class="ml-2"
              >
                {{ timesheet.entry_type === 'ARRIVAL' ? 'Arrivée' : 'Départ' }}
              </v-chip>
            </div>
            <div v-if="timesheet.is_late || timesheet.is_early_departure" class="mt-1">
              <v-chip
                size="x-small"
                :color="getTimesheetColor(timesheet)"
                variant="outlined"
                class="mt-1"
              >
                {{ timesheet.is_late ? `Retard de ${timesheet.late_minutes} minutes` :
                   timesheet.is_early_departure ? `Départ anticipé de ${timesheet.early_departure_minutes} minutes` : '' }}
              </v-chip>
            </div>
          </v-timeline-item>
        </v-timeline>

        <!-- Le bouton "Charger plus" est supprimé car la pagination est désactivée sur le backend -->
        <!-- Tous les résultats sont déjà chargés en une seule requête -->
      </template>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { format } from 'date-fns'
import { fr } from 'date-fns/locale'
import { timesheetsApi, sitesApi } from '@/services/api'
import { Title } from '@/components/typography'

interface Timesheet {
  id: number;
  entry_type: 'ARRIVAL' | 'DEPARTURE';
  timestamp: string;
  site_name: string;
  is_late: boolean;
  is_early_departure: boolean;
  late_minutes?: number;
  early_departure_minutes?: number;
}

interface TimesheetParams {
  // Paramètres de pagination (optionnels car la pagination est désactivée sur le backend)
  page?: number;
  page_size?: number;

  // Paramètres de filtrage
  site?: string;
  entry_type?: string; // 'ARRIVAL' ou 'DEPARTURE'
  start_date?: string; // Format YYYY-MM-DD
  end_date?: string; // Format YYYY-MM-DD
  is_late?: boolean;
  is_early_departure?: boolean;
}

const loading = ref(true)
// Ces variables ne sont plus utilisées car la pagination est désactivée sur le backend
// const loadingMore = ref(false)
// const hasMoreTimesheets = ref(false)
// const currentPage = ref(1)
// const perPage = ref(10)

const filters = ref({
  site: '',
  type: '',
  status: '',
  startDate: '',
  endDate: ''
})

const siteOptions = ref<string[]>([])
const typeOptions = ref(['Arrivée', 'Départ'])
const statusOptions = ref(['Normal', 'Retard', 'Départ anticipé'])

const timesheets = ref<Timesheet[]>([])

const formatDate = (date: string, time: string): string => {
  const dateObj = new Date(`${date}T${time}`)
  return format(dateObj, 'EEEE d MMMM yyyy à HH:mm', { locale: fr })
}

const getTimesheetColor = (timesheet: Timesheet): string => {
  if (timesheet.is_late) return 'warning'
  if (timesheet.is_early_departure) return 'error'
  return timesheet.entry_type === 'ARRIVAL' ? 'success' : 'info'
}

// Fonction non utilisée, commentée pour éviter les avertissements du linter
// const getStatusColor = (status: string): string => {
//   if (status === 'Normal') return 'success'
//   if (status === 'Retard') return 'warning'
//   if (status === 'Départ anticipé') return 'error'
//   return 'grey'
// }

const loadSites = async () => {
  try {
    const response = await sitesApi.getAllSites()
    siteOptions.value = response.data.results.map(site => site.name)
  } catch (error) {
    console.error('Erreur lors de la récupération des sites:', error)
  }
}

const fetchTimesheets = async () => {
  try {
    // Nous n'avons pas besoin de paramètres de pagination car la pagination est désactivée sur le backend
    const params: TimesheetParams = {}

    console.log('Historique - Début de la récupération des pointages')

    // Ajouter les filtres seulement s'ils sont définis
    if (filters.value.site) {
      params.site = filters.value.site
    }

    if (filters.value.type) {
      params.entry_type = filters.value.type === 'Arrivée' ? 'ARRIVAL' : 'DEPARTURE' // Changed from entryType to entry_type
    }

    if (filters.value.startDate) {
      params.start_date = filters.value.startDate // Changed from startDate to start_date
    }

    if (filters.value.endDate) {
      params.end_date = filters.value.endDate // Changed from endDate to end_date
    }

    if (filters.value.status === 'Retard') {
      params.is_late = true // Changed from isLate to is_late
    } else if (filters.value.status === 'Départ anticipé') {
      params.is_early_departure = true // Changed from isEarlyDeparture to is_early_departure
    }

    console.log('Historique - Paramètres de la requête:', params)
    const response = await timesheetsApi.getTimesheets(params)
    console.log('Historique - Réponse API complète:', response)
    console.log('Historique - Données reçues:', response.data)

    // Déterminer si la réponse est un tableau ou un objet avec results
    const results = Array.isArray(response.data) ? response.data : (response.data.results || [])
    console.log('Historique - Nombre de résultats:', results.length)

    // Affecter directement les résultats (pas de pagination)
    timesheets.value = results
    console.log('Historique - Timesheets après affectation:', timesheets.value.length)

    // La vue backend TimesheetListView a pagination_class = None, donc il n'y a pas de pagination
    // Nous recevons toujours tous les résultats en une seule requête
    console.log('Historique - Pagination désactivée sur le backend, tous les résultats sont déjà chargés')
  } catch (error) {
    console.error('Erreur lors de la récupération des enregistrements:', error)
  } finally {
    loading.value = false
  }
}

const applyFilters = () => {
  loading.value = true
  fetchTimesheets()
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

// Cette fonction n'est plus utilisée car la pagination est désactivée sur le backend
// Tous les résultats sont déjà chargés en une seule requête
// const loadMoreTimesheets = () => {
//   console.log('Fonction loadMoreTimesheets non utilisée - pagination désactivée')
//   // Code conservé pour référence
//   // loadingMore.value = true
//   // currentPage.value++
//   // fetchTimesheets()
// }

// Charger les données initiales
onMounted(async () => {
  await loadSites()
  fetchTimesheets()
})
</script>

<style scoped>
.history-container {
  padding: 16px;
}
</style>

