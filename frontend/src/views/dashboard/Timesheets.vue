<template>
  <div>
    <div class="d-flex justify-space-between align-center mb-4">
      <Title :level="1">Pointages</Title>
    </div>

    <v-card v-if="!isDetailView" class="mb-4">
      <v-card-title>Filtres</v-card-title>
      <v-card-text>
        <DashboardFilters @reset="resetFilters">
          <v-col cols="12" :md="currentSiteId ? 4 : 3">
            <v-text-field
              v-model="filters.employee"
              label="Employé"
              variant="outlined"
              prepend-inner-icon="mdi-account-search"
              clearable
              @update:model-value="applyFilters"
            ></v-text-field>
          </v-col>

          <v-col v-if="!currentSiteId" cols="12" :md="currentSiteId ? 4 : 3">
            <v-select
              v-model="filters.site"
              label="Site"
              :items="siteOptions"
              variant="outlined"
              prepend-inner-icon="mdi-map-marker"
              clearable
              @update:model-value="applyFilters"
            ></v-select>
          </v-col>

          <v-col cols="12" :md="currentSiteId ? 4 : 3">
            <v-select
              v-model="filters.entryType"
              label="Type de pointage"
              :items="entryTypeOptions"
              variant="outlined"
              prepend-inner-icon="mdi-clock-time-four"
              clearable
              @update:model-value="applyFilters"
            ></v-select>
          </v-col>

          <v-col cols="12" :md="currentSiteId ? 4 : 3">
            <v-select
              v-model="filters.status"
              label="Statut"
              :items="statusOptions"
              variant="outlined"
              prepend-inner-icon="mdi-alert-circle"
              clearable
              @update:model-value="applyFilters"
            ></v-select>
          </v-col>

          <v-col cols="12" md="4">
            <v-text-field
              v-model="filters.startDate"
              label="Du"
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
              label="Au"
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
        :headers="headers"
        :items="timesheets"
        :loading="loading"
        :items-per-page="itemsPerPage"
        :page="currentPage"
        :total-items="totalItems"
        :no-data-text="'Aucun pointage trouvé'"
        :loading-text="'Chargement des pointages...'"
        :items-per-page-text="'Lignes par page'"
        :page-text="'{0}-{1} sur {2}'"
        :items-per-page-options="[
          { title: '5', value: 5 },
          { title: '10', value: 10 },
          { title: '15', value: 15 },
          { title: 'Tout', value: -1 }
        ]"
        class="elevation-1"
        @update:options="handleTableUpdate"
        @click:row="(_: any, { item }: any) => showDetails(item)"
      >
        <template #item.entry_type="{ item }">
          <v-chip
            :color="item.entry_type === EntryTypeEnum.ARRIVAL ? 'success' : 'info'"
            size="small"
          >
            {{ getEntryTypeLabel(item.entry_type) }}
          </v-chip>
        </template>
        <template #item.status="{ item }">
          <v-chip
            :color="getStatusColor(item)"
            size="small"
          >
            {{ getStatusLabel(item) }}
          </v-chip>
        </template>
        <template #item.actions="{ item }">
          <v-btn
            v-if="canEditTimesheet"
            icon="mdi-pencil"
            size="small"
            color="primary"
            variant="text"
            class="mr-2"
            @click.stop="editTimesheet(item)"
          >
            <v-tooltip activator="parent" location="top">Modifier</v-tooltip>
          </v-btn>
          <v-btn
            v-if="canEditTimesheet"
            icon="mdi-delete"
            size="small"
            color="error"
            variant="text"
            @click.stop="confirmDelete(item)"
          >
            <v-tooltip activator="parent" location="top">Supprimer</v-tooltip>
          </v-btn>
        </template>
      </v-data-table>
    </v-card>

    <!-- Dialog de détails -->
    <v-dialog v-model="detailDialog" max-width="800">
      <v-card v-if="selectedTimesheet">
        <v-card-title class="text-h5 pb-2">
          Détails du pointage
          <v-spacer></v-spacer>
          <v-btn icon="mdi-close" variant="text" @click="detailDialog = false"></v-btn>
        </v-card-title>

        <v-divider></v-divider>

        <v-card-text class="pt-4">
          <v-row>
            <v-col cols="12" :md="selectedTimesheet.latitude && selectedTimesheet.longitude ? 6 : 12">
              <v-list>
                <v-list-item>
                  <template #prepend>
                    <v-icon color="primary">mdi-account</v-icon>
                  </template>
                  <v-list-item-title class="text-subtitle-2 mb-1">Employé</v-list-item-title>
                  <v-list-item-subtitle>{{ selectedTimesheet.employee }}</v-list-item-subtitle>
                </v-list-item>

                <v-list-item>
                  <template #prepend>
                    <v-icon color="primary">mdi-map-marker</v-icon>
                  </template>
                  <v-list-item-title class="text-subtitle-2 mb-1">Site</v-list-item-title>
                  <v-list-item-subtitle>{{ selectedTimesheet.site }}</v-list-item-subtitle>
                </v-list-item>

                <v-list-item>
                  <template #prepend>
                    <v-icon color="primary">mdi-clock-outline</v-icon>
                  </template>
                  <v-list-item-title class="text-subtitle-2 mb-1">Date et heure</v-list-item-title>
                  <v-list-item-subtitle>{{ selectedTimesheet.date }} à {{ selectedTimesheet.time }}</v-list-item-subtitle>
                </v-list-item>

                <v-list-item>
                  <template #prepend>
                    <v-icon color="primary">mdi-gesture-tap-button</v-icon>
                  </template>
                  <v-list-item-title class="text-subtitle-2 mb-1">Type</v-list-item-title>
                  <v-list-item-subtitle>
                    <v-chip
                      :color="selectedTimesheet.entry_type === EntryTypeEnum.ARRIVAL ? 'success' : 'info'"
                      size="small"
                    >
                      {{ getEntryTypeLabel(selectedTimesheet.entry_type) }}
                    </v-chip>
                  </v-list-item-subtitle>
                </v-list-item>

                <v-list-item v-if="selectedTimesheet.is_late || selectedTimesheet.is_early_departure">
                  <template #prepend>
                    <v-icon :color="selectedTimesheet.is_late ? 'warning' : 'error'">mdi-alert-circle</v-icon>
                  </template>
                  <v-list-item-title class="text-subtitle-2 mb-1">Statut</v-list-item-title>
                  <v-list-item-subtitle>
                    <v-chip
                      :color="getStatusColor(selectedTimesheet)"
                      size="small"
                    >
                      {{ getStatusLabel(selectedTimesheet) }}
                    </v-chip>
                  </v-list-item-subtitle>
                </v-list-item>

                <v-list-item v-if="selectedTimesheet.schedule_details">
                  <template #prepend>
                    <v-icon color="primary">mdi-calendar-clock</v-icon>
                  </template>
                  <v-list-item-title class="text-subtitle-2 mb-1">Planning associé</v-list-item-title>
                  <v-list-item-subtitle>
                    <div>{{ selectedTimesheet.schedule_details.name }}</div>
                    <div class="text-caption">
                      Type: {{ selectedTimesheet.schedule_details.schedule_type_display }}
                      <template v-if="selectedTimesheet.schedule_details.schedule_type === 'FIXED'">
                        <div v-if="selectedTimesheet.schedule_details.start_time_1 && selectedTimesheet.schedule_details.end_time_1">
                          Matin: {{ formatTime(selectedTimesheet.schedule_details.start_time_1) }} - {{ formatTime(selectedTimesheet.schedule_details.end_time_1) }}
                        </div>
                        <div v-if="selectedTimesheet.schedule_details.start_time_2 && selectedTimesheet.schedule_details.end_time_2">
                          Après-midi: {{ formatTime(selectedTimesheet.schedule_details.start_time_2) }} - {{ formatTime(selectedTimesheet.schedule_details.end_time_2) }}
                        </div>
                      </template>
                      <template v-else-if="selectedTimesheet.schedule_details.schedule_type === 'FREQUENCY'">
                        <div>
                          Fréquence: {{ selectedTimesheet.schedule_details.frequency_duration }} minutes
                          (Tolérance: {{ selectedTimesheet.schedule_details.tolerance_percentage }}%)
                        </div>
                      </template>
                    </div>
                  </v-list-item-subtitle>
                </v-list-item>

                <v-list-item v-if="selectedTimesheet.correction_note">
                  <template #prepend>
                    <v-icon color="primary">mdi-note-text</v-icon>
                  </template>
                  <v-list-item-title class="text-subtitle-2 mb-1">Note de correction</v-list-item-title>
                  <v-list-item-subtitle>{{ selectedTimesheet.correction_note }}</v-list-item-subtitle>
                </v-list-item>
              </v-list>
            </v-col>

            <v-col v-if="selectedTimesheet.latitude && selectedTimesheet.longitude" cols="12" md="6">
              <div id="mapContainer" style="height: 300px; width: 100%; border-radius: 4px; position: relative; z-index: 1;"></div>
            </v-col>
          </v-row>
        </v-card-text>

        <v-card-actions v-if="canEditTimesheet">
          <v-spacer></v-spacer>
          <v-btn
            color="primary"
            variant="text"
            prepend-icon="mdi-pencil"
            @click="editTimesheet(selectedTimesheet)"
          >
            Modifier
          </v-btn>
          <v-btn
            color="error"
            variant="text"
            prepend-icon="mdi-delete"
            @click="confirmDelete(selectedTimesheet)"
          >
            Supprimer
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Dialog d'édition -->
    <v-dialog v-model="editDialog" max-width="500" persistent>
      <v-card v-if="editingTimesheet">
        <v-card-title>
          Modifier le pointage
          <v-spacer></v-spacer>
          <v-btn icon="mdi-close" variant="text" @click="editDialog = false"></v-btn>
        </v-card-title>

        <v-card-text>
          <v-form ref="editForm">
            <v-text-field
              v-model="editingTimesheet.timestamp"
              label="Date et heure"
              type="datetime-local"
              variant="outlined"
            ></v-text-field>

            <v-select
              v-model="editingTimesheet.entry_type"
              :items="entryTypeOptions"
              label="Type de pointage"
              variant="outlined"
            ></v-select>

            <v-textarea
              v-model="editingTimesheet.correction_note"
              label="Note de correction"
              variant="outlined"
              rows="3"
            ></v-textarea>
          </v-form>
        </v-card-text>

        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="error" variant="text" @click="editDialog = false">Annuler</v-btn>
          <v-btn color="primary" @click="saveTimesheet">Enregistrer</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Dialog de confirmation de suppression -->
    <v-dialog v-model="deleteDialog" max-width="400" persistent>
      <v-card>
        <v-card-title>Confirmer la suppression</v-card-title>
        <v-card-text>
          Êtes-vous sûr de vouloir supprimer ce pointage ? Cette action est irréversible.
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="error" variant="text" @click="deleteDialog = false">Annuler</v-btn>
          <v-btn color="primary" @click="deleteTimesheet">Supprimer</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
  <ConfirmDialog />
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { sitesApi, timesheetsApi } from '@/services/api'
import { format } from 'date-fns'
import { fr } from 'date-fns/locale'
import { useAuthStore } from '@/stores/auth'
import { useSitesStore } from '@/stores/sites'
import 'leaflet/dist/leaflet.css'
import L from 'leaflet'
import type { ExtendedTimesheet, Filters, SiteOption, EditingTimesheet } from '@/types/sites'
import { EntryTypeEnum } from '@/types/api'
import type { TableOptions } from '@/types/sites'
import { Title } from '@/components/typography'
import DashboardFilters from '@/components/dashboard/DashboardFilters.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'

const props = defineProps<{
  isDetailView?: boolean
  siteId?: number | null
}>()

const auth = useAuthStore()
const sitesStore = useSitesStore()
const loading = ref(true)

// Computed pour le site courant - priorité au siteId passé en prop
const currentSiteId = computed(() => props.siteId || sitesStore.getCurrentSiteId)

const headers = ref([
  { title: 'Date', align: 'start' as const, key: 'date' },
  { title: 'Heure', align: 'start' as const, key: 'time' },
  { title: 'Employé', align: 'start' as const, key: 'employee' },
  { title: 'Site', align: 'start' as const, key: 'site' },
  { title: 'Type', align: 'center' as const, key: 'entry_type' },
  { title: 'Statut', align: 'center' as const, key: 'status' },
  { title: 'Actions', align: 'center' as const, key: 'actions', sortable: false }
])

const filters = ref<Filters>({
  employee: '',
  site: null,
  entryType: '',
  status: '',
  startDate: '',
  endDate: ''
})

const siteOptions = ref<SiteOption[]>([])
const entryTypeOptions = ref([
  { title: 'Arrivée', value: EntryTypeEnum.ARRIVAL },
  { title: 'Départ', value: EntryTypeEnum.DEPARTURE }
])
const statusOptions = ref([
  { title: 'Normal', value: 'NORMAL' },
  { title: 'Retard', value: 'LATE' },
  { title: 'Départ anticipé', value: 'EARLY_DEPARTURE' }
])

const timesheets = ref<ExtendedTimesheet[]>([])
const currentPage = ref(1)
const itemsPerPage = ref(10)
const totalItems = ref(0)

const detailDialog = ref(false)
const editDialog = ref(false)
const deleteDialog = ref(false)
const selectedTimesheet = ref<ExtendedTimesheet | null>(null)
const editingTimesheet = ref<EditingTimesheet | null>(null)
const timesheetToDelete = ref<ExtendedTimesheet | null>(null)
let map: L.Map | null = null

const canEditTimesheet = computed(() => {
  return auth.user?.role === 'SUPER_ADMIN' || auth.user?.role === 'MANAGER'
})

const getStatusColor = (timesheet: ExtendedTimesheet): string => {
  if (timesheet.is_late) return 'warning'
  if (timesheet.is_early_departure) return 'error'
  return 'success'
}

const getStatusLabel = (timesheet: ExtendedTimesheet): string => {
  if (timesheet.is_late) return `Retard (${timesheet.late_minutes} min)`
  if (timesheet.is_early_departure) return `Départ anticipé (${timesheet.early_departure_minutes} min)`
  return 'Normal'
}

const getEntryTypeLabel = (type: EntryTypeEnum): string => {
  return type === EntryTypeEnum.ARRIVAL ? 'Arrivée' : 'Départ'
}

const formatTime = (timeString: string): string => {
  try {
    // Format: "HH:MM:SS"
    const parts = timeString.split(':')
    return `${parts[0]}:${parts[1]}`
  } catch (error) {
    console.error('Erreur lors du formatage de l\'heure:', error)
    return timeString
  }
}

const formatTimesheet = (timesheet: ExtendedTimesheet): ExtendedTimesheet => {
  try {
    if (!timesheet.timestamp) {
      return {
        ...timesheet,
        date: 'Date invalide',
        time: '--:--'
      }
    }

    const timestamp = new Date(timesheet.timestamp)
    if (isNaN(timestamp.getTime())) {
      console.error('Date invalide dans formatTimesheet:', timesheet.timestamp)
      return {
        ...timesheet,
        date: 'Date invalide',
        time: '--:--'
      }
    }

    return {
      ...timesheet,
      date: format(timestamp, 'dd/MM/yyyy', { locale: fr }),
      time: format(timestamp, 'HH:mm', { locale: fr }),
      employee: timesheet.employee_name || 'Employé inconnu',
      site: timesheet.site_name || 'Site inconnu'
    }
  } catch (error) {
    console.error('Erreur lors du formatage du pointage:', error)
    return {
      ...timesheet,
      date: 'Erreur',
      time: '--:--',
      employee: 'Erreur',
      site: 'Erreur'
    }
  }
}

const fetchTimesheets = async (options: Partial<TableOptions> = {}) => {
  try {
    loading.value = true
    const params = {
      employee_name: filters.value.employee || undefined,
      site: currentSiteId.value || filters.value.site || undefined,
      entry_type: filters.value.entryType || undefined,
      start_date: filters.value.startDate || undefined,
      end_date: filters.value.endDate || undefined,
      page: options.page || currentPage.value,
      page_size: options.itemsPerPage || itemsPerPage.value,
      expand: 'employee,site'
    }

    const response = await timesheetsApi.getTimesheets(params)
    const results = response.data.results || []

    // Format timesheets for display
    timesheets.value = results.map((timesheet: ExtendedTimesheet) => formatTimesheet(timesheet))

    totalItems.value = response.data.count || 0

    // Update pagination state
    currentPage.value = options.page || currentPage.value
    itemsPerPage.value = options.itemsPerPage || itemsPerPage.value
  } catch (error) {
    console.error('Erreur lors du chargement des pointages:', error)
    timesheets.value = []
    totalItems.value = 0
  } finally {
    loading.value = false
  }
}

const handleTableUpdate = (options: TableOptions): void => {
  const { page, itemsPerPage: newItemsPerPage } = options
  fetchTimesheets({
    page: page,
    itemsPerPage: newItemsPerPage
  })
}

const applyFilters = () => {
  currentPage.value = 1 // Reset to first page when applying filters
  fetchTimesheets()
}

const resetFilters = () => {
  filters.value = {
    employee: '',
    site: null,
    entryType: '',
    status: '',
    startDate: '',
    endDate: ''
  }
  currentPage.value = 1 // Reset to first page when resetting filters
  fetchTimesheets()
}

const showDetails = (item: ExtendedTimesheet): void => {
  try {
    if (!item.timestamp) {
      console.error('Timestamp manquant')
      return
    }

    const timestamp = new Date(item.timestamp)
    console.log('Timestamp original:', item.timestamp)
    console.log('Timestamp parsé:', timestamp)

    if (isNaN(timestamp.getTime())) {
      console.error('Date invalide:', item.timestamp)
      return
    }

    selectedTimesheet.value = {
      ...item,
      date: format(timestamp, 'dd/MM/yyyy', { locale: fr }),
      time: format(timestamp, 'HH:mm', { locale: fr })
    }

    detailDialog.value = true

    if (selectedTimesheet.value?.latitude && selectedTimesheet.value?.longitude) {
      setTimeout(() => {
        try {
          if (map) {
            map.remove()
            map = null
          }

          const mapDiv = document.getElementById('mapContainer')

          if (mapDiv) {
            mapDiv.style.height = '300px'
            mapDiv.style.width = '100%'

            map = L.map('mapContainer').setView(
              [selectedTimesheet.value!.latitude!, selectedTimesheet.value!.longitude!],
              15
            )

            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
              attribution: '© OpenStreetMap contributors'
            }).addTo(map)

            L.marker([selectedTimesheet.value!.latitude!, selectedTimesheet.value!.longitude!]).addTo(map)

            setTimeout(() => {
              map?.invalidateSize()
            }, 100)
          }
        } catch (error) {
          console.error('Erreur lors de l\'initialisation de la carte:', error)
        }
      }, 250)
    }
  } catch (error) {
    console.error('Erreur lors de l\'affichage des détails:', error)
  }
}

const editTimesheet = (item: ExtendedTimesheet): void => {
  try {
    if (!item.timestamp) {
      console.error('Timestamp manquant pour l\'édition')
      return
    }

    const timestamp = new Date(item.timestamp)
    if (isNaN(timestamp.getTime())) {
      console.error('Date invalide pour l\'édition:', item.timestamp)
      return
    }

    editingTimesheet.value = {
      id: item.id,
      timestamp: format(timestamp, "yyyy-MM-dd'T'HH:mm", { locale: fr }),
      entry_type: item.entry_type,
      correction_note: item.correction_note || ''
    }
    editDialog.value = true
  } catch (error) {
    console.error('Erreur lors de l\'initialisation de l\'édition:', error)
  }
}

const saveTimesheet = async () => {
  try {
    if (!editingTimesheet.value) return;
    loading.value = true
    await timesheetsApi.updateTimesheet(editingTimesheet.value.id, {
      timestamp: editingTimesheet.value.timestamp,
      entry_type: editingTimesheet.value.entry_type,
      correction_note: editingTimesheet.value.correction_note
    })
    editDialog.value = false
    await fetchTimesheets()
  } catch (error) {
    console.error('Erreur lors de la mise à jour du pointage:', error)
  } finally {
    loading.value = false
  }
}

const confirmDelete = (item: ExtendedTimesheet): void => {
  timesheetToDelete.value = item
  deleteDialog.value = true
}

const deleteTimesheet = async () => {
  try {
    if (!timesheetToDelete.value) return;
    loading.value = true
    await timesheetsApi.deleteTimesheet(timesheetToDelete.value.id)
    deleteDialog.value = false
    await fetchTimesheets()
  } catch (error) {
    console.error('Erreur lors de la suppression du pointage:', error)
  } finally {
    loading.value = false
  }
}

// Update the watch handler to handle the computed ref value correctly
watch(() => currentSiteId.value, (newSiteId: number | null) => {
  filters.value.site = newSiteId
  currentPage.value = 1
  fetchTimesheets()
})

// Ajout de la fonction pour charger les sites
const loadSites = async () => {
  try {
    const response = await sitesApi.getAllSites()
    siteOptions.value = response.data.results.map(site => ({
      title: site.name,
      value: site.id
    }))
  } catch (error) {
    console.error('Erreur lors du chargement des sites:', error)
    siteOptions.value = []
  }
}

onMounted(() => {
  if (currentSiteId.value) {
    filters.value.site = currentSiteId.value
  }
  loadSites() // Chargement des sites
  fetchTimesheets()
})
</script>

<style scoped>
.leaflet-container {
  z-index: 1 !important;
  border-radius: 4px;
}

.v-dialog {
  z-index: 1000 !important;
}

.v-list-item {
  min-height: 64px;
}

.v-list-item-subtitle {
  margin-top: 4px;
}

#mapContainer {
  position: relative !important;
  z-index: 1 !important;
}

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

