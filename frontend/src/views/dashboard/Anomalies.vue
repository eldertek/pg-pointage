<template>
  <div>
    <div v-if="!isDetailView" class="d-flex justify-space-between align-center mb-4">
      <PageTitle :level="1">Anomalies</PageTitle>
      <div class="d-flex align-center gap-2">
        <v-btn
          color="warning"
          prepend-icon="mdi-magnify-scan"
          :loading="scanning"
          @click="scanForAnomalies"
        >
          {{ $t('dashboard.scanner_les_anomalies') }}
        </v-btn>
      </div>
    </div>

    <v-card v-if="!isDetailView" class="mb-4">
      <v-card-title>{{ $t('reports.filters') }}</v-card-title>
      <v-card-text>
        <DashboardFilters @reset="resetFilters">
          <v-col cols="12" :md="currentSiteId ? 4 : 3">
            <v-autocomplete
              v-model="filters.employee"
              v-model:search-input="employeeSearch"
              :loading="searchingEmployees"
              :items="employeeOptions"
              :label="$t('users.roles.EMPLOYEE')"
              item-:title="$t('mobile.text')"
              item-value="value"
              variant="outlined"
              prepend-inner-icon="mdi-account-search"
              clearable
              @update:search="searchEmployees"
              @update:model-value="applyFilters"
            >
              <template #no-data>
                <v-list-item>
                  <v-list-item-title>
                    {{ $t('dashboard.commencez_taper_pour_rechercher_un_employ') }}
                  </v-list-item-title>
                </v-list-item>
              </template>
            </v-autocomplete>
          </v-col>

          <v-col v-if="!currentSiteId" cols="12" :md="currentSiteId ? 4 : 3">
            <v-select
              v-model="filters.site"
              :label="$t('timesheets.site')"
              :items="siteOptions"
              item-:title="$t('mobile.text')"
              item-value="value"
              variant="outlined"
              prepend-inner-icon="mdi-map-marker"
              clearable
              @update:model-value="applyFilters"
            ></v-select>
          </v-col>

          <v-col cols="12" :md="currentSiteId ? 4 : 3">
            <v-select
              v-model="filters.type"
              :label="$t('anomalies.type')"
              :items="anomalyTypeOptions"
              item-:title="$t('mobile.text')"
              item-value="value"
              variant="outlined"
              prepend-inner-icon="mdi-alert-circle"
              clearable
              @update:model-value="applyFilters"
            ></v-select>
          </v-col>

          <v-col cols="12" :md="currentSiteId ? 4 : 3">
            <v-select
              v-model="filters.status"
              :label="$t('timesheets.status')"
              :items="statusOptions"
              item-:title="$t('mobile.text')"
              item-value="value"
              variant="outlined"
              prepend-inner-icon="mdi-check-circle"
              clearable
              @update:model-value="applyFilters"
            ></v-select>
          </v-col>

          <v-col cols="12" md="4">
            <v-text-field
              v-model="filters.startDate"
              :label="$t('reports.fromDate')"
              type="date"
              variant="outlined"
              prepend-inner-icon="mdi-calendar"
              clearable
              @update:model-value="applyFilters"
            ></v-text-field>
          </v-col>

          <v-col cols="12" md="4">
            <v-text-field
              v-model="filters.endDate"
              :label="$t('reports.toDate')"
              type="date"
              variant="outlined"
              prepend-inner-icon="mdi-calendar"
              clearable
              @update:model-value="applyFilters"
            ></v-text-field>
          </v-col>
        </DashboardFilters>
      </v-card-text>
    </v-card>

    <v-card>
      <v-data-table
        v-model:page="page"
        :headers="headers"
        :items="anomalies"
        :loading="loading"
        :items-per-page="itemsPerPage"
        :items-length="anomalies.length"
        :no-data-text="$t('dashboard.aucune_anomalie_trouve')"
        :loading-text="$t('dashboard.chargement_des_anomalies')"
        class="elevation-1"
        :items-per-page-options="[
          { title: '5', value: 5 },
          { title: '10', value: 10 },
          { title: '15', value: 15 },
          { title: $t('common.all'), value: -1 }
        ]"
        :page-text="$t('dashboard.01_sur_2')"
        :items-per-page-text="$t('dashboard.lignes_par_page')"
        @click:row="handleRowClick"
      >
        <template #item.formatted_date="{ item }">
          {{ formatDate(item.created_at) }}
        </template>
        <template #item.anomaly_type_display="{ item }">
          <v-chip
            :color="getTypeColor(item.anomaly_type_display)"
            size="small"
          >
            {{ item.anomaly_type_display }}
          </v-chip>
        </template>

        <template #item.actions="{ item }">
          <v-btn
            icon
            variant="text"
            size="small"
            color="primary"
            @click.stop="showAnomalyDetails(item)"
          >
            <v-icon>mdi-eye</v-icon>
            <v-tooltip activator="parent">{{ $t('common.viewDetails') }}</v-tooltip>
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

    <!-- Dialog pour afficher les détails d'une anomalie -->
    <v-dialog v-model="showDetailsDialog" max-width="700" persistent>
      <v-card v-if="selectedAnomaly" class="form-dialog">
        <div class="form-dialog-header">
          <div class="form-dialog-title">
            <span class="text-h4">
              <v-chip
                :color="getTypeColor(selectedAnomaly.anomaly_type_display)"
                class="mr-2"
              >
                {{ selectedAnomaly.anomaly_type_display }}
              </v-chip>
              {{ $t('anomalies.details', 'Détails de l\'anomalie') }}
            </span>
          </div>
          <v-btn
            icon
            variant="text"
            size="small"
            color="grey"
            class="close-button"
            @click="showDetailsDialog = false"
          >
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </div>
        <v-divider></v-divider>

        <v-card-text>
          <v-row>
            <v-col cols="12" md="6">
              <p><strong>{{ $t('common.date') }}:</strong> {{ selectedAnomaly.formatted_date || formatDate(selectedAnomaly.created_at) }}</p>
              <p><strong>{{ $t('common.employee') }}:</strong> {{ selectedAnomaly.employee_name }}</p>
              <p><strong>{{ $t('common.site') }}:</strong> {{ selectedAnomaly.site_name }}</p>
            </v-col>

            <v-col cols="12" md="6">
              <p><strong>{{ $t('anomalies.description') }}:</strong></p>
              <p>{{ selectedAnomaly.translated_description || selectedAnomaly.description || $t('anomalies.noDescription', 'Aucune description disponible') }}</p>
            </v-col>
          </v-row>

          <v-divider class="my-4"></v-divider>

          <!-- Planning associé -->
          <div v-if="selectedAnomaly.schedule_details">
            <h3 class="text-h6 mb-3">{{ $t('dashboard.planning_associ') }}</h3>
            <v-card variant="outlined" class="mb-4 pa-3">
              <p><strong>{{ $t('common.name') }}:</strong> {{ selectedAnomaly.schedule_details.name }}</p>
              <p><strong>{{ $t('common.type') }}:</strong> {{ selectedAnomaly.schedule_details.schedule_type_display }}</p>

              <div v-if="selectedAnomaly.schedule_details.schedule_type === 'FIXED'">
                <p v-if="selectedAnomaly.schedule_details.start_time_1">
                  <strong>{{ $t('plannings.dayTypes.AM') }}:</strong>
                  {{ formatTime(selectedAnomaly.schedule_details.start_time_1) }} -
                  {{ formatTime(selectedAnomaly.schedule_details.end_time_1) }}
                </p>
                <p v-if="selectedAnomaly.schedule_details.start_time_2">
                  <strong>{{ $t('plannings.dayTypes.PM') }}:</strong>
                  {{ formatTime(selectedAnomaly.schedule_details.start_time_2) }} -
                  {{ formatTime(selectedAnomaly.schedule_details.end_time_2) }}
                </p>
              </div>

              <div v-if="selectedAnomaly.schedule_details.schedule_type === 'FREQUENCY'">
                <p>
                  <strong>{{ $t('plannings.duration') }}:</strong>
                  {{ selectedAnomaly.schedule_details.frequency_duration }} {{ $t('dashboard.min') }}
                </p>
                <p>
                  <strong>{{ $t('dashboard.marge_de_tolrance', 'Tolérance') }}:</strong>
                  {{ selectedAnomaly.schedule_details.tolerance_percentage || 10 }}%
                </p>
              </div>
            </v-card>
          </div>

          <!-- Pointages concernés -->
          <div v-if="relatedTimesheets.length > 0">
            <h3 class="text-h6 mb-3">{{ $t('dashboard.pointages_concerns') }}</h3>
            <v-table density="compact">
              <thead>
                <tr>
                  <th>{{ $t('timesheets.dateTime') }}</th>
                  <th>{{ $t('common.type') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="timesheet in relatedTimesheets" :key="timesheet.id">
                  <td>{{ formatDate(timesheet.timestamp) }}</td>
                  <td>
                    <v-chip
                      :color="timesheet.entry_type === 'ARRIVAL' ? 'success' : 'info'"
                      size="x-small"
                    >
                      {{ timesheet.entry_type === 'ARRIVAL' ? $t('timesheets.entryTypes.ARRIVAL') : $t('timesheets.entryTypes.DEPARTURE') }}
                    </v-chip>
                  </td>
                </tr>
              </tbody>
            </v-table>
          </div>
          <div v-else-if="!selectedAnomaly.schedule_details" class="text-center py-4">
            <p>{{ $t('dashboard.aucune_information_complmentaire_disponible_pour_cette_anomalie') }}</p>
          </div>
        </v-card-text>

        <v-divider></v-divider>
        <v-card-actions>
          <v-btn
            v-if="selectedAnomaly.status === 'RESOLVED'"
            color="error"
            variant="text"
            prepend-icon="mdi-delete"
            class="action-button"
            @click="deleteSelectedAnomaly"
          >
            {{ $t('common.delete') }}
          </v-btn>
          <v-spacer></v-spacer>
          <v-btn
            color="grey"
            variant="text"
            class="action-button"
            @click="showDetailsDialog = false"
          >
            {{ $t('common.close') }}
          </v-btn>
          <v-btn
            v-if="selectedAnomaly.status === 'PENDING'"
            color="success"
            variant="text"
            class="action-button"
            @click="resolveSelectedAnomaly"
          >
            {{ $t('dashboard.rsoudre') }}
          </v-btn>
          <v-btn
            v-if="selectedAnomaly.status === 'PENDING'"
            color="grey"
            variant="text"
            class="action-button"
            @click="ignoreSelectedAnomaly"
          >
            {{ $t('dashboard.ignorer') }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script>
import { useI18n } from 'vue-i18n'
import { ref, watch, computed } from 'vue'
import { timesheetsApi, sitesApi, usersApi } from '@/services/api'
import { useToast } from 'vue-toastification'
import { useSitesStore } from '@/stores/sites'
import { Title as PageTitle } from '@/components/typography'
import DashboardFilters from '@/components/dashboard/DashboardFilters.vue'

export default {
  name: 'AnomaliesView',
  components: {
    PageTitle,
    DashboardFilters
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
    const { t } = useI18n()
    const loading = ref(true)
    const scanning = ref(false)

    // Computed pour le site courant - priorité au siteId passé en prop
    const currentSiteId = computed(() => props.siteId || sitesStore.getCurrentSiteId)

    const error = ref(null)
    const searchingEmployees = ref(false)
    const employeeSearch = ref('')
    const employeeOptions = ref([])

    const headers = ref([
      { title: t('common.date'), align: 'start', key: 'formatted_date' },
      { title: t('common.employee'), align: 'start', key: 'employee_name' },
      { title: t('common.site'), align: 'start', key: 'site_name' },
      { title: t('common.type'), align: 'center', key: 'anomaly_type_display' },
      { title: t('anomalies.description'), align: 'start', key: 'translated_description', value: 'translated_description' },
      { title: t('common.actions'), align: 'center', key: 'actions', sortable: false }
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
      { text: 'Pointages consécutifs', value: 'CONSECUTIVE_SAME_TYPE' },
      { text: 'Planning non lié', value: 'UNLINKED_SCHEDULE' },
      { text: 'Autre', value: 'OTHER' }
    ])
    const statusOptions = ref([
      { text: 'En attente', value: 'PENDING' },
      { text: 'Résolu', value: 'RESOLVED' },
      { text: 'Ignoré', value: 'IGNORED' }
    ])

    const anomalies = ref([])

    const page = ref(1)
    const itemsPerPage = ref(10)

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
      if (type === 'Planning non lié') return 'blue'
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
        // Convertir l'ID de l'employé en nombre pour s'assurer qu'il est correctement traité
        params.employee = Number(filters.value.employee)
        // Ajouter des logs pour déboguer le filtrage par employé
        console.log('[Anomalies][Filter] Employé sélectionné:', filters.value.employee)
        console.log('[Anomalies][Filter] Employé converti:', params.employee)
        console.log('[Anomalies][Filter] Type de l\'employé après conversion:', typeof params.employee)
      }

      // Ajouter des logs pour déboguer
      console.log('[Anomalies][Filter] Valeurs des filtres:', filters.value)
      console.log('[Anomalies][Filter] Site sélectionné:', filters.value.site)
      console.log('[Anomalies][Filter] Type du site sélectionné:', typeof filters.value.site)
      console.log('[Anomalies][Filter] Site actif (currentSiteId):', currentSiteId.value)

      // Utiliser le site actif en priorité
      if (currentSiteId.value) {
        params.site = currentSiteId.value
        console.log('Utilisation du site actif:', params.site)
      } else if (filters.value.site) {
        params.site = filters.value.site
        console.log('Utilisation du site filtré:', params.site)
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

      console.log('Paramètres finaux pour l\'API:', params)
      return params
    }

    const applyFilters = async () => {
      loading.value = true
      error.value = null
      try {
        const params = buildQueryParams()
        console.log('[Anomalies][API] Requête API - paramètres:', params)

        // Afficher les données complètes de la requête
        console.log('[Anomalies][API] URL de la requête API:', `/timesheets/anomalies/?${new URLSearchParams(params).toString()}`)

        // Vérifier spécifiquement le paramètre employé
        if (params.employee) {
          console.log('[Anomalies][API] Filtrage par employé activé - ID:', params.employee, 'Type:', typeof params.employee)
        }

        const response = await timesheetsApi.getAnomalies(params)
        console.log('[Anomalies][API] Réponse API anomalies:', response.data)
        console.log('[Anomalies][API] En-têtes de la réponse:', response.headers)
        console.log('[Anomalies][API] URL de la requête exécutée:', response.request?.responseURL)

        if (response.data?.results) {
          // Pour chaque anomalie, afficher le site associé pour vérifier le filtrage
          console.log('Sites des anomalies retournées:')
          response.data.results.forEach(anomaly => {
            console.log(`Anomalie ID ${anomaly.id} - Site: ${anomaly.site} (${anomaly.site_name})`)
          })

          // Note: Pour afficher les dates réelles des événements dans la liste, il faudrait modifier l'API
          // pour inclure les détails des pointages associés dans la réponse initiale.
          // Actuellement, ces détails ne sont disponibles que lors de l'appel à getAnomalyDetails.
          anomalies.value = response.data.results.map(anomaly => {
            // Utiliser la date de l'anomalie pour la liste
            // Le champ 'date' contient la date de l'événement sans l'heure, donc on utilise created_at
            // qui contient la date et l'heure complètes

            // Ajouter des logs pour déboguer les dates
            console.log(`Anomalie ID ${anomaly.id} - Date: ${anomaly.date}, Created At: ${anomaly.created_at}`);
            console.log(`Anomalie ID ${anomaly.id} - Date formatée: ${formatDate(anomaly.created_at)}`);

            return {
              ...anomaly,
              formatted_date: formatDate(anomaly.created_at),
              // Utiliser la description traduite si disponible, sinon la description originale
              description: anomaly.translated_description || anomaly.description
            };
          })
          console.log('Anomalies formatées:', anomalies.value)
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
      console.log('[Anomalies][ResetFilters] Réinitialisation des filtres')
      filters.value = {
        employee: '',
        site: '',
        type: '',
        status: '',
        startDate: '',
        endDate: ''
      }
      // Réinitialiser également la recherche d'employés
      employeeSearch.value = ''
      employeeOptions.value = []
      console.log('[Anomalies][ResetFilters] Filtres réinitialisés:', filters.value)
      applyFilters()
    }

    const scanForAnomalies = async () => {
      try {
        scanning.value = true
        const params = buildQueryParams()
        const response = await timesheetsApi.scanAnomalies(params)

        // Afficher une notification de succès
        if (response.data) {
          let message = ''

          // Message pour les anomalies
          if (response.data.anomalies_created !== undefined) {
            const count = response.data.anomalies_created
            message = count > 0
              ? `${count} anomalie${count > 1 ? 's' : ''} détectée${count > 1 ? 's' : ''} et créée${count > 1 ? 's' : ''}.`
              : 'Aucune nouvelle anomalie détectée.'
          }

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
        console.log('[Anomalies][SearchEmployees] Recherche d\'employés avec la requête:', query)
        const response = await usersApi.searchUsers(query)
        console.log('[Anomalies][SearchEmployees] Réponse de la recherche:', response.data)
        console.log('[Anomalies][SearchEmployees] URL de la requête:', response.request?.responseURL)

        if (response.data?.results) {
          console.log('[Anomalies][SearchEmployees] Nombre de résultats:', response.data.results.length)

          // Vérifier si les résultats contiennent les données attendues
          response.data.results.forEach((user, index) => {
            console.log(`[Anomalies][SearchEmployees] Utilisateur ${index}:`, {
              id: user.id,
              first_name: user.first_name,
              last_name: user.last_name,
              username: user.username,
              email: user.email
            })
          })

          employeeOptions.value = response.data.results.map(user => {
            const option = {
              text: `${user.first_name} ${user.last_name}`,
              value: user.id
            }
            console.log('[Anomalies][SearchEmployees] Option créée:', option)
            return option
          })
          console.log('[Anomalies][SearchEmployees] Options finales:', employeeOptions.value)
        } else {
          console.warn('[Anomalies][SearchEmployees] Aucun résultat trouvé ou format de réponse inattendu')
        }
      } catch (error) {
        console.error('[Anomalies][SearchEmployees] Erreur lors de la recherche des employés:', error)
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

    // Variables pour le dialog de détails
    const showDetailsDialog = ref(false)
    const selectedAnomaly = ref(null)
    const relatedTimesheets = ref([])
    const loadingDetails = ref(false)

    // Fonction pour gérer le clic sur une ligne du tableau
    const handleRowClick = (event, { item }) => {
      console.log('handleRowClick appelé avec:', event, item)

      // Vérifier si le clic vient d'un élément interactif
      const target = event.target
      const clickedElement = target.closest('.v-btn, a, button, [data-no-row-click]')

      if (clickedElement || target.hasAttribute('data-no-row-click')) {
        return
      }

      if (item && item.id) {
        showAnomalyDetails(item)
      } else {
        console.error('Format de données inattendu pour le clic de ligne:', item)
      }
    }

    // Fonction pour afficher les détails d'une anomalie
    const showAnomalyDetails = async (item) => {
      console.log('showAnomalyDetails appelé avec:', item)

      if (!item || !item.id) {
        console.error('Impossible d\'afficher les détails: ID manquant', item)
        return
      }

      selectedAnomaly.value = item
      showDetailsDialog.value = true
      loadingDetails.value = true
      relatedTimesheets.value = []

      try {
        // Charger les détails de l'anomalie
        const anomalyResponse = await timesheetsApi.getAnomalyDetails(item.id)
        selectedAnomaly.value = anomalyResponse.data

        // Ajouter des logs pour déboguer les dates
        console.log('Détails de l\'anomalie:', selectedAnomaly.value);
        console.log(`Anomalie ID ${selectedAnomaly.value.id} - Date: ${selectedAnomaly.value.date}, Created At: ${selectedAnomaly.value.created_at}`);
        console.log(`Anomalie ID ${selectedAnomaly.value.id} - Date formatée (created_at): ${formatDate(selectedAnomaly.value.created_at)}`);

        // Vérifier si nous avons des pointages associés
        if (selectedAnomaly.value.timesheet_details) {
          console.log('Pointage associé:', selectedAnomaly.value.timesheet_details);
        }
        if (selectedAnomaly.value.related_timesheets_details && selectedAnomaly.value.related_timesheets_details.length > 0) {
          console.log('Pointages associés:', selectedAnomaly.value.related_timesheets_details);
        }

        // Mettre à jour la date formatée avec la date réelle de l'événement si disponible
        if (selectedAnomaly.value.timesheet_details?.timestamp) {
          console.log('Utilisation de la date du pointage associé:', selectedAnomaly.value.timesheet_details.timestamp)
          selectedAnomaly.value.formatted_date = formatDate(selectedAnomaly.value.timesheet_details.timestamp)
          console.log('Nouvelle date formatée:', selectedAnomaly.value.formatted_date);
        } else if (selectedAnomaly.value.related_timesheets_details && selectedAnomaly.value.related_timesheets_details.length > 0) {
          console.log('Utilisation de la date du premier pointage associé:', selectedAnomaly.value.related_timesheets_details[0].timestamp)
          selectedAnomaly.value.formatted_date = formatDate(selectedAnomaly.value.related_timesheets_details[0].timestamp)
          console.log('Nouvelle date formatée:', selectedAnomaly.value.formatted_date);
        } else {
          // Si aucun pointage associé, utiliser la date de l'anomalie
          console.log('Aucun pointage associé, utilisation de la date de l\'anomalie');
          selectedAnomaly.value.formatted_date = formatDate(selectedAnomaly.value.created_at);
        }

        // Si l'anomalie a des pointages associés dans related_timesheets_details
        if (selectedAnomaly.value.related_timesheets_details &&
            selectedAnomaly.value.related_timesheets_details.length > 0) {
          relatedTimesheets.value = selectedAnomaly.value.related_timesheets_details
        }
        // Sinon, si l'anomalie est liée à un pointage spécifique
        else if (selectedAnomaly.value.timesheet) {
          if (selectedAnomaly.value.timesheet_details) {
            relatedTimesheets.value = [selectedAnomaly.value.timesheet_details]
          } else {
            const timesheetResponse = await timesheetsApi.getTimesheetDetails(selectedAnomaly.value.timesheet)
            relatedTimesheets.value = [timesheetResponse.data]
          }
        } else {
          // Sinon, récupérer tous les pointages de l'employé pour cette date
          const params = {
            employee: selectedAnomaly.value.employee,
            site: selectedAnomaly.value.site,
            start_date: selectedAnomaly.value.date,
            end_date: selectedAnomaly.value.date
          }
          const timesheetsResponse = await timesheetsApi.getTimesheets(params)
          relatedTimesheets.value = timesheetsResponse.data.results || []
        }
      } catch (error) {
        console.error('Erreur lors du chargement des détails de l\'anomalie:', error)
        toast.error('Erreur lors du chargement des détails')
      } finally {
        loadingDetails.value = false
      }
    }

    // Fonctions pour résoudre, ignorer ou supprimer l'anomalie sélectionnée
    const resolveSelectedAnomaly = async () => {
      try {
        await resolveAnomaly(selectedAnomaly.value.id)
        selectedAnomaly.value.status = 'RESOLVED'
        selectedAnomaly.value.status_display = 'Résolu'
        toast.success('Anomalie résolue avec succès')
      } catch (error) {
        console.error('Erreur lors de la résolution de l\'anomalie:', error)
        toast.error('Erreur lors de la résolution de l\'anomalie')
      }
    }

    const ignoreSelectedAnomaly = async () => {
      try {
        await ignoreAnomaly(selectedAnomaly.value.id)
        selectedAnomaly.value.status = 'IGNORED'
        selectedAnomaly.value.status_display = 'Ignoré'
        toast.success('Anomalie ignorée avec succès')
      } catch (error) {
        console.error('Erreur lors de l\'ignorance de l\'anomalie:', error)
        toast.error('Erreur lors de l\'ignorance de l\'anomalie')
      }
    }

    const deleteSelectedAnomaly = async () => {
      try {
        await timesheetsApi.deleteAnomaly(selectedAnomaly.value.id)
        showDetailsDialog.value = false
        toast.success('Anomalie supprimée avec succès')
        // Rafraîchir la liste des anomalies
        await applyFilters()
      } catch (error) {
        console.error('Erreur lors de la suppression de l\'anomalie:', error)
        toast.error('Erreur lors de la suppression de l\'anomalie')
      }
    }

    // Ajout de la variable manquante
    const showDeleteDialog = ref(false)

    const formatDate = (dateString) => {
      if (!dateString) {
        return ''
      }

      try {
        // Analyser la date en respectant le fuseau horaire
        // Le format ISO inclut le fuseau horaire (ex: 2025-04-16T10:15:40.628856+02:00)
        const date = new Date(dateString)

        // Vérifier si la date est valide
        if (isNaN(date.getTime())) {
          console.error('Date invalide dans formatDate:', dateString)
          return dateString
        }

        // Utiliser les méthodes toLocaleString pour respecter le fuseau horaire
        // et éviter les problèmes de conversion UTC
        return date.toLocaleString('fr-FR', {
          day: '2-digit',
          month: '2-digit',
          year: 'numeric',
          hour: '2-digit',
          minute: '2-digit',
          hour12: false // Format 24h
        })
      } catch (error) {
        console.error('Error formatting date:', error)
        return dateString
      }
    }

    // Fonction pour formater les heures
    const formatTime = (timeString) => {
      if (!timeString) return ''

      try {
        // Si c'est déjà au format HH:MM, on le retourne tel quel
        if (typeof timeString === 'string' && timeString.includes(':')) {
          return timeString
        }

        // Si c'est un objet Date
        if (timeString instanceof Date) {
          const hours = timeString.getHours().toString().padStart(2, '0')
          const minutes = timeString.getMinutes().toString().padStart(2, '0')
          return `${hours}:${minutes}`
        }

        // Si c'est une chaîne ISO
        const date = new Date(timeString)
        if (!isNaN(date.getTime())) {
          const hours = date.getHours().toString().padStart(2, '0')
          const minutes = date.getMinutes().toString().padStart(2, '0')
          return `${hours}:${minutes}`
        }

        return timeString
      } catch (error) {
        console.error('Error formatting time:', error)
        return timeString
      }
    }

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
      currentSiteId,
      formatDate,
      formatTime,
      // Nouvelles variables et fonctions pour le dialog de détails
      showDetailsDialog,
      selectedAnomaly,
      relatedTimesheets,
      loadingDetails,
      handleRowClick,
      showAnomalyDetails,
      resolveSelectedAnomaly,
      ignoreSelectedAnomaly,
      deleteSelectedAnomaly,
      page,
      itemsPerPage,
      t
    }
  }
}
</script>

<style scoped>
/* Style des boutons dans le tableau */
:deep(.v-data-table .v-btn--icon) {
  background-color: transparent !important;
}

:deep(.v-data-table .v-btn--icon[color="primary"]) {
  color: #00346E !important;
}

:deep(.v-data-table .v-btn--icon[color="error"]) {
  color: #F78C48 !important;
}

:deep(.v-data-table .v-btn--icon[color="warning"]) {
  color: #FB8C00 !important;
}

:deep(.v-data-table .v-btn--icon[color="grey"]) {
  color: #999999 !important;
  opacity: 0.5 !important;
  cursor: default !important;
  pointer-events: none !important;
}

/* Assurer que les icônes dans les boutons sont visibles */
:deep(.v-data-table .v-btn--icon .v-icon) {
  opacity: 1 !important;
  color: inherit !important;
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

/* Correction des overlays et underlays */
:deep(.v-btn__overlay),
:deep(.v-btn__underlay) {
  opacity: 0 !important;
}

/* Styles pour le dialog de détails */
.form-dialog {
  border-radius: 8px;
  overflow: hidden;
}

.form-dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 1.5rem;
  background-color: #f8f9fa;
}

.form-dialog-title {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-dialog-title .text-h4 {
  font-size: 1.25rem;
  font-weight: 500;
  color: #00346E;
  margin: 0;
}

.close-button {
  margin-top: -0.5rem;
  margin-right: -0.5rem;
}

.v-card-text {
  padding: 1.5rem;
}

.v-card-actions {
  padding: 1rem 1.5rem;
}

.action-button {
  font-weight: 500;
  padding: 0.5rem 1rem;
}

:deep(.v-divider) {
  margin: 0;
}
</style>

