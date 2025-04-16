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
v-model="filters.employee" label="Employé" variant="outlined"
              prepend-inner-icon="mdi-account-search" clearable @update:model-value="applyFilters"></v-text-field>
          </v-col>

          <v-col v-if="!currentSiteId" cols="12" :md="currentSiteId ? 4 : 3">
            <v-select
v-model="filters.site" label="Site" :items="siteOptions" variant="outlined"
              prepend-inner-icon="mdi-map-marker" clearable @update:model-value="applyFilters"></v-select>
          </v-col>

          <v-col cols="12" :md="currentSiteId ? 4 : 3">
            <v-select
v-model="filters.entryType" label="Type de pointage" :items="entryTypeOptions" variant="outlined"
              prepend-inner-icon="mdi-clock-time-four" clearable @update:model-value="applyFilters"></v-select>
          </v-col>

          <v-col cols="12" :md="currentSiteId ? 4 : 3">
            <v-select
v-model="filters.status" label="Statut" :items="statusOptions" variant="outlined"
              prepend-inner-icon="mdi-alert-circle" clearable @update:model-value="applyFilters"></v-select>
          </v-col>

          <v-col cols="12" md="4">
            <v-text-field
v-model="filters.startDate" label="Du" type="date" variant="outlined"
              prepend-inner-icon="mdi-calendar" clearable @update:model-value="applyFilters"></v-text-field>
          </v-col>

          <v-col cols="12" md="4">
            <v-text-field
v-model="filters.endDate" label="Au" type="date" variant="outlined"
              prepend-inner-icon="mdi-calendar" clearable @update:model-value="applyFilters"></v-text-field>
          </v-col>
        </DashboardFilters>
      </v-card-text>
    </v-card>

    <v-card>
      <v-data-table
v-model:page="page" :headers="headers" :items="timesheets" :loading="loading"
        :items-per-page="itemsPerPage"
        :items-length="timesheets.length"
        :no-data-text="'Aucun pointage trouvé'" :loading-text="'Chargement des pointages...'"
        class="elevation-1"
        :items-per-page-options="[
          { title: '5', value: 5 },
          { title: '10', value: 10 },
          { title: '15', value: 15 },
          { title: 'Tout', value: -1 }
        ]"
        :page-text="'{0}-{1} sur {2}'"
        :items-per-page-text="'Lignes par page'"
        @click:row="handleRowClick">
        <template #item.entry_type="{ item }">
          <v-chip :color="item.entry_type === EntryTypeEnum.ARRIVAL ? 'success' : 'info'" size="small">
            {{ getEntryTypeLabel(item.entry_type) }}
          </v-chip>
        </template>
        <template #item.status="{ item }">
          <v-chip :color="getStatusColor(item)" size="small">
            {{ getStatusLabel(item) }}
          </v-chip>
        </template>
        <template #item.actions="{ item }">
          <v-btn
            icon="mdi-eye"
            size="small"
            color="primary"
            variant="text"
            @click.stop="showDetails(item)"
          >
            <v-icon>mdi-eye</v-icon>
            <v-tooltip activator="parent">Voir les détails</v-tooltip>
          </v-btn>
          <v-btn
            v-if="canEditTimesheet"
            icon="mdi-pencil"
            size="small"
            color="primary"
            variant="text"
            @click.stop="editTimesheet(item)"
          >
            <v-icon>mdi-pencil</v-icon>
            <v-tooltip activator="parent">Modifier</v-tooltip>
          </v-btn>
          <v-btn
            v-if="canEditTimesheet"
            icon="mdi-delete"
            size="small"
            color="error"
            variant="text"
            @click.stop="confirmDelete(item)"
          >
            <v-icon>mdi-delete</v-icon>
            <v-tooltip activator="parent">Supprimer</v-tooltip>
          </v-btn>
        </template>
      </v-data-table>
    </v-card>

    <!-- Dialog de détails -->
    <v-dialog v-model="detailDialog" max-width="800">
      <v-card v-if="selectedTimesheet" class="form-dialog">
        <div class="form-dialog-header">
          <div class="form-dialog-title">
            <span class="text-h4">Détails du pointage</span>
            <span class="text-subtitle">Informations complètes du pointage</span>
          </div>
          <v-btn
            icon
            variant="text"
            size="small"
            color="grey"
            class="close-button"
            @click="detailDialog = false"
          >
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </div>

        <v-divider></v-divider>

        <v-card-text class="pt-6">
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
                  <v-list-item-subtitle>{{ selectedTimesheet.date }} à {{ selectedTimesheet.time
                    }}</v-list-item-subtitle>
                </v-list-item>

                <v-list-item>
                  <template #prepend>
                    <v-icon color="primary">mdi-gesture-tap-button</v-icon>
                  </template>
                  <v-list-item-title class="text-subtitle-2 mb-1">Type</v-list-item-title>
                  <v-list-item-subtitle>
                    <v-chip
:color="selectedTimesheet.entry_type === EntryTypeEnum.ARRIVAL ? 'success' : 'info'"
                      size="small">
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
                    <v-chip :color="getStatusColor(selectedTimesheet)" size="small">
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
                        <div
                          v-if="selectedTimesheet.schedule_details.start_time_1 && selectedTimesheet.schedule_details.end_time_1">
                          Matin: {{ formatTime(selectedTimesheet.schedule_details.start_time_1) }} - {{
                            formatTime(selectedTimesheet.schedule_details.end_time_1) }}
                        </div>
                        <div
                          v-if="selectedTimesheet.schedule_details.start_time_2 && selectedTimesheet.schedule_details.end_time_2">
                          Après-midi: {{ formatTime(selectedTimesheet.schedule_details.start_time_2) }} - {{
                            formatTime(selectedTimesheet.schedule_details.end_time_2) }}
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
              <div
id="mapContainer"
                style="height: 300px; width: 100%; border-radius: 4px; position: relative; z-index: 1;"></div>
            </v-col>
          </v-row>
        </v-card-text>

        <v-divider v-if="canEditTimesheet"></v-divider>

        <v-card-actions v-if="canEditTimesheet">
          <v-spacer></v-spacer>
          <v-btn 
            color="primary" 
            variant="text" 
            prepend-icon="mdi-pencil"
            class="action-button"
            @click="editTimesheet(selectedTimesheet)"
          >
            Modifier
          </v-btn>
          <v-btn 
            color="error" 
            variant="text" 
            prepend-icon="mdi-delete"
            class="action-button"
            @click="confirmDelete(selectedTimesheet)"
          >
            Supprimer
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Dialog d'édition -->
    <v-dialog v-model="editDialog" max-width="800" persistent>
      <v-card v-if="editingTimesheet" class="form-dialog">
        <div class="form-dialog-header">
          <div class="form-dialog-title">
            <span class="text-h4">Modifier le pointage</span>
            <span class="text-subtitle">Modifiez les informations du pointage</span>
          </div>
          <v-btn
            icon
            variant="text"
            size="small"
            color="grey"
            class="close-button"
            @click="editDialog = false"
          >
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </div>
        <v-divider></v-divider>
        <v-card-text>
          <v-container>
            <DashboardForm id="editForm" ref="editForm" :errors="formErrors" @submit="saveTimesheet">
              <v-row>
                <v-col cols="12" sm="6">
                  <v-text-field
                    v-model="editingTimesheet.timestamp"
                    label="Date et heure"
                    type="datetime-local"
                    variant="outlined"
                    required
                    :error-messages="getFieldErrors('timestamp')"
                  ></v-text-field>
                </v-col>
                
                <v-col cols="12" sm="6">
                  <v-select
                    v-model="editingTimesheet.entry_type"
                    :items="entryTypeOptions"
                    label="Type de pointage"
                    variant="outlined"
                    required
                    :error-messages="getFieldErrors('entry_type')"
                  ></v-select>
                </v-col>
                
                <v-col cols="12">
                  <v-divider class="my-4"></v-divider>
                  <v-card-title class="text-subtitle-1 font-weight-medium">
                    Note de correction
                    <v-chip
                      color="grey"
                      size="small"
                      class="ml-2"
                    >
                      Optionnel
                    </v-chip>
                  </v-card-title>
                  <v-card-text class="text-caption text-grey">
                    Vous pouvez ajouter une note pour expliquer la raison de cette modification.
                  </v-card-text>
                </v-col>
                
                <v-col cols="12">
                  <v-textarea
                    v-model="editingTimesheet.correction_note"
                    label="Note de correction"
                    variant="outlined"
                    rows="3"
                    hint="Laissez vide si aucune correction n'est nécessaire"
                    persistent-hint
                    :error-messages="getFieldErrors('correction_note')"
                  ></v-textarea>
                </v-col>
              </v-row>
            </DashboardForm>
          </v-container>
        </v-card-text>
        <v-divider></v-divider>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn 
            color="grey" 
            variant="text" 
            class="action-button"
            @click="editDialog = false"
          >
            Annuler
          </v-btn>
          <v-btn 
            color="primary" 
            variant="text" 
            :loading="loading"
            class="action-button"
            type="submit" 
            form="editForm" 
            @click="saveTimesheet"
          >
            Enregistrer
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Dialog de confirmation de suppression -->
    <v-dialog v-model="deleteDialog" max-width="500" persistent>
      <v-card class="form-dialog">
        <div class="form-dialog-header">
          <div class="form-dialog-title">
            <span class="text-h4">Confirmer la suppression</span>
            <span class="text-subtitle">Cette action est irréversible</span>
          </div>
          <v-btn
            icon
            variant="text"
            size="small"
            color="grey"
            class="close-button"
            @click="deleteDialog = false"
          >
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </div>
        <v-divider></v-divider>
        <v-card-text class="pa-6">
          <v-alert
            type="warning"
            variant="tonal"
            border="start"
            class="mb-4"
          >
            <div class="d-flex align-center">
              <v-icon icon="mdi-alert-circle" class="mr-2"></v-icon>
              <span class="font-weight-medium">Êtes-vous sûr de vouloir supprimer ce pointage ?</span>
            </div>
            <div class="mt-2">
              Cette action est définitive et ne pourra pas être annulée.
            </div>
          </v-alert>
        </v-card-text>
        <v-divider></v-divider>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn 
            color="grey" 
            variant="text" 
            class="action-button"
            @click="deleteDialog = false"
          >
            Annuler
          </v-btn>
          <v-btn 
            color="error" 
            variant="text" 
            :loading="loading"
            class="action-button"
            @click="deleteTimesheet"
          >
            Supprimer
          </v-btn>
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
import type { Filters, SiteOption, EditingTimesheet } from '@/types/sites'
import { EntryTypeEnum } from '@/types/api'
import { Title } from '@/components/typography'
import DashboardFilters from '@/components/dashboard/DashboardFilters.vue'
import DashboardForm from '@/components/dashboard/DashboardForm.vue'
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
  { title: 'Actions', align: 'center' as const, key: 'actions', sortable: false, width: '120px' }
])

console.log('Headers du tableau:', headers.value)

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

const timesheets = ref<any[]>([])

const detailDialog = ref(false)
const editDialog = ref(false)
const deleteDialog = ref(false)
const selectedTimesheet = ref<any | null>(null)
const editingTimesheet = ref<EditingTimesheet | null>(null)
const timesheetToDelete = ref<any | null>(null)
const formErrors = ref<Record<string, string[]>>({})
let map: L.Map | null = null

const canEditTimesheet = computed(() => {
  return auth.user?.role === 'SUPER_ADMIN' || auth.user?.role === 'MANAGER'
})

const getStatusColor = (timesheet: any): string => {
  if (timesheet.is_late) return 'warning'
  if (timesheet.is_early_departure) return 'error'
  return 'success'
}

const getStatusLabel = (timesheet: any): string => {
  if (timesheet.is_late) return `Retard (${timesheet.late_minutes} min)`
  if (timesheet.is_early_departure) return `Départ anticipé (${timesheet.early_departure_minutes} min)`
  return 'Normal'
}

const getEntryTypeLabel = (type: EntryTypeEnum): string => {
  return type === EntryTypeEnum.ARRIVAL ? 'Arrivée' : 'Départ'
}

// Fonction pour récupérer les messages d'erreur d'un champ spécifique
const getFieldErrors = (field: string): string[] => {
  if (!formErrors.value) return []
  return formErrors.value[field] || []
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

const formatTimesheet = (timesheet: any): any => {
  try {
    console.log('Formatage du pointage:', timesheet)
    if (!timesheet.timestamp) {
      console.warn('Timestamp manquant dans le pointage:', timesheet)
      return {
        ...timesheet,
        date: 'Date invalide',
        time: '--:--',
        // Conserver l'original pour le débogage
        original_timestamp: timesheet.timestamp
      }
    }

    const timestamp = new Date(timesheet.timestamp)
    if (isNaN(timestamp.getTime())) {
      console.error('Date invalide dans formatTimesheet:', timesheet.timestamp)
      return {
        ...timesheet,
        date: 'Date invalide',
        time: '--:--',
        // Conserver l'original pour le débogage
        original_timestamp: timesheet.timestamp
      }
    }

    const formatted = {
      ...timesheet,
      date: format(timestamp, 'dd/MM/yyyy', { locale: fr }),
      time: format(timestamp, 'HH:mm', { locale: fr }),
      employee: timesheet.employee_name || 'Employé inconnu',
      site: timesheet.site_name || 'Site inconnu',
      // Conserver l'original pour le débogage
      original_timestamp: timesheet.timestamp
    }
    console.log('Pointage formaté:', formatted)
    return formatted
  } catch (error) {
    console.error('Erreur lors du formatage du pointage:', error)
    return {
      ...timesheet,
      date: 'Erreur',
      time: '--:--',
      employee: 'Erreur',
      site: 'Erreur',
      original_timestamp: timesheet?.timestamp
    }
  }
}

const fetchTimesheets = async () => {
  try {
    loading.value = true
    const params = {
      employee_name: filters.value.employee || undefined,
      site: currentSiteId.value || filters.value.site || undefined,
      entry_type: filters.value.entryType || undefined,
      start_date: filters.value.startDate || undefined,
      end_date: filters.value.endDate || undefined,
      expand: 'employee,site'
    }

    console.log('Paramètres de la requête:', params)
    const response = await timesheetsApi.getTimesheets(params)
    console.log('Réponse API complète:', response)
    console.log('Données reçues:', response.data)

    const results = Array.isArray(response.data) ? response.data : (response.data.results || []);
    console.log('Nombre de résultats:', results.length)

    // Format timesheets for display
    const formattedTimesheets = results.map((timesheet: any) => formatTimesheet(timesheet))
    console.log('Pointages formatés:', formattedTimesheets)
    timesheets.value = formattedTimesheets
    console.log('Variable timesheets après affectation:', timesheets.value)
  } catch (error) {
    console.error('Erreur lors du chargement des pointages:', error)
    timesheets.value = []
  } finally {
    loading.value = false
  }
}

const applyFilters = () => {
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
  fetchTimesheets()
}

const showDetails = (item: any): void => {
  try {
    console.log('showDetails appelé avec:', item)

    // Vérifier si l'item est complet
    if (!item) {
      console.error('Item manquant')
      return
    }

    // Si l'item n'a pas de timestamp mais a déjà date et time (formaté précédemment)
    if (!item.timestamp && item.date && item.time) {
      console.log('Utilisation des champs date et time déjà formatés')
      selectedTimesheet.value = { ...item }
      detailDialog.value = true
      return
    }

    // Vérification du timestamp
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

const editTimesheet = (item: any): void => {
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

    // Réinitialiser les erreurs
    formErrors.value = {}

    loading.value = true
    await timesheetsApi.updateTimesheet(editingTimesheet.value.id, {
      timestamp: editingTimesheet.value.timestamp,
      entry_type: editingTimesheet.value.entry_type,
      correction_note: editingTimesheet.value.correction_note
    })
    editDialog.value = false
    await fetchTimesheets()
  } catch (error: any) {
    console.error('Erreur lors de la mise à jour du pointage:', error)

    // Traitement des erreurs de validation
    if (error.response?.data) {
      const processedErrors: Record<string, string[]> = {}

      // Traitement spécial pour le format d'erreur spécifique montré dans la capture d'écran
      if (error.response.data.detail && typeof error.response.data.detail === 'string') {
        try {
          // Essayer de parser le message JSON dans le champ detail
          const detailObj = JSON.parse(error.response.data.detail.replace(/'/g, '"'))

          // Si c'est un objet avec entry_type, utiliser directement
          if (detailObj.entry_type) {
            processedErrors.entry_type = Array.isArray(detailObj.entry_type)
              ? detailObj.entry_type
              : [detailObj.entry_type]
          } else {
            // Sinon, garder le message complet
            processedErrors.detail = [error.response.data.detail]
          }
        } catch (_) {
          // Si le parsing échoue, utiliser le message tel quel
          processedErrors.detail = [error.response.data.detail]
        }
      } else {
        // Traitement standard pour les autres formats d'erreur
        Object.entries(error.response.data).forEach(([field, messages]) => {
          // Gérer les erreurs imbriquées comme "detail.entry_type"
          if (field === 'detail' && typeof messages === 'object' && !Array.isArray(messages)) {
            // Parcourir les sous-champs dans detail
            Object.entries(messages as Record<string, any>).forEach(([subField, subMessages]) => {
              if (Array.isArray(subMessages)) {
                processedErrors[subField] = subMessages
              } else {
                processedErrors[subField] = [subMessages as string]
              }
            })
          } else if (Array.isArray(messages)) {
            processedErrors[field] = messages
          } else {
            processedErrors[field] = [messages as string]
          }
        })
      }

      formErrors.value = processedErrors
      console.log('Erreurs de formulaire:', formErrors.value)
    }
  } finally {
    loading.value = false
  }
}

const confirmDelete = (item: any): void => {
  timesheetToDelete.value = item
  deleteDialog.value = true
}

const handleRowClick = (item: any): void => {
  showDetails(item)
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

const page = ref(1)
const itemsPerPage = ref(10)

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

/* Styles pour le formulaire d'édition */
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
  font-size: 1.5rem;
  font-weight: 600;
  line-height: 1.2;
  color: #00346E;
  margin: 0;
}

.form-dialog-title .text-subtitle {
  font-size: 0.9rem;
  font-weight: 400;
  line-height: 1.4;
  color: #666;
}

.close-button {
  margin-top: -0.5rem;
  margin-right: -0.5rem;
}

.action-button {
  font-size: 0.9rem;
  font-weight: 500;
  padding: 0.5rem 1rem;
}

/* Styles pour l'en-tête du formulaire */
:deep(.form-header) {
  padding-bottom: 16px;
  margin-bottom: 16px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.12);
}

:deep(.form-header h2) {
  color: #00346E;
  margin-bottom: 4px;
}

:deep(.form-header p) {
  margin-top: 0;
  color: rgba(0, 0, 0, 0.6);
}

/* Styles pour les messages d'erreur */
:deep(.form-errors) {
  margin-bottom: 16px;
}

:deep(.v-alert.v-alert--density-default.v-alert--variant-tonal) {
  border-left: 4px solid #F78C48;
}

:deep(.v-alert strong) {
  color: #00346E;
  font-weight: 600;
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
  visibility: visible !important;
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

/* Styles supplémentaires pour assurer la visibilité des boutons d'action */
:deep(.v-data-table tbody tr td:last-child) {
  position: relative !important;
  z-index: 10 !important;
}

:deep(.v-data-table tbody tr td:last-child .v-btn) {
  opacity: 1 !important;
  visibility: visible !important;
  display: inline-flex !important;
  z-index: 10 !important;
}

/* Empêcher que d'autres éléments couvrent les boutons */
:deep(.v-data-table) {
  overflow: visible !important;
}

/* Styles spécifiques pour les boutons d'action */
.action-button {
  opacity: 1 !important;
  visibility: visible !important;
  z-index: 10 !important;
  position: relative !important;
  display: inline-flex !important;
}

/* Forcer la visibilité des icônes dans les boutons */
:deep(.v-btn .v-icon) {
  opacity: 1 !important;
  visibility: visible !important;
  color: currentColor !important;
}

/* Surcharge des styles de Vuetify qui pourraient causer des problèmes */
:deep(.v-data-table .v-data-table__td) {
  position: relative !important;
  z-index: 1 !important;
}

:deep(.v-data-table .v-data-table__td--action) {
  z-index: 10 !important;
  padding: 0 8px !important;
  white-space: nowrap !important;
  display: flex !important;
  justify-content: center !important;
  align-items: center !important;
}

/* Style pour le tableau avec pointeur */
:deep(.v-data-table tbody tr) {
  cursor: pointer;
}
</style>
