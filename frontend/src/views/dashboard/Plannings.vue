<template>
  <v-container fluid>
    <v-row>
      <v-col cols="12">
        <div class="d-flex align-center mb-4">
          <h1 class="text-h4 font-weight-bold">Plannings</h1>
          <v-spacer></v-spacer>
          <v-btn
            color="primary"
            prepend-icon="mdi-plus"
            @click="openDialog()"
          >
            Nouveau planning
          </v-btn>
        </div>

        <!-- Filtres -->
        <v-card class="mb-4">
          <v-card-title>Filtres</v-card-title>
          <v-card-text>
            <v-row>
              <v-col cols="12" md="4">
                <v-select
                  v-model="filters.site"
                  :items="sites"
                  item-title="name"
                  item-value="id"
                  label="Site"
                  variant="outlined"
                  prepend-inner-icon="mdi-map-marker"
                  clearable
                  @update:model-value="loadPlannings"
                ></v-select>
              </v-col>
              <v-col cols="12" md="4">
                <v-select
                  v-model="filters.type"
                  :items="planningTypes"
                  label="Type de planning"
                  variant="outlined"
                  prepend-inner-icon="mdi-calendar-clock"
                  clearable
                  @update:model-value="loadPlannings"
                ></v-select>
              </v-col>
              <v-col cols="12" md="4" class="d-flex align-center">
                <v-btn color="primary" @click="loadPlannings" class="mr-2">
                  Appliquer
                </v-btn>
                <v-btn color="error" variant="outlined" @click="resetFilters">
                  Réinitialiser
                </v-btn>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>

        <!-- Tableau des plannings -->
        <v-card>
          <v-data-table
            v-model:page="page"
            :headers="headers"
            :items="plannings"
            :loading="loading"
            :items-per-page="itemsPerPage"
            :items-length="totalItems"
            :no-data-text="'Aucun planning trouvé'"
            :loading-text="'Chargement des plannings...'"
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
            <!-- Type de planning -->
            <template v-slot:item.schedule_type="{ item }">
              <v-chip
                :color="item.schedule_type === 'FIXED' ? 'primary' : 'secondary'"
                size="small"
              >
                {{ item.schedule_type === 'FIXED' ? 'Fixe' : 'Fréquence' }}
              </v-chip>
            </template>

            <!-- Site -->
            <template v-slot:item.site_name="{ item }">
              {{ item.site_name }}
            </template>

            <!-- Actions -->
            <template v-slot:item.actions="{ item }">
              <v-btn
                icon
                variant="text"
                size="small"
                color="primary"
                @click="openDialog(item)"
              >
                <v-icon>mdi-pencil</v-icon>
              </v-btn>
              <v-btn
                icon
                variant="text"
                size="small"
                color="error"
                @click="confirmDelete(item)"
              >
                <v-icon>mdi-delete</v-icon>
              </v-btn>
            </template>
          </v-data-table>
        </v-card>
      </v-col>
    </v-row>

    <!-- Dialog pour création/édition -->
    <v-dialog v-model="dialog" max-width="1000px">
      <v-card>
        <v-card-title>
          <span class="text-h5">{{ editedItem.id ? 'Modifier' : 'Nouveau' }} planning</span>
        </v-card-title>

        <v-card-text>
          <v-container>
            <v-row>
              <v-col cols="12" sm="6">
                <v-select
                  v-model="editedItem.schedule_type"
                  :items="[
                    { title: 'Fixe', value: 'FIXED' },
                    { title: 'Fréquence', value: 'FREQUENCY' }
                  ]"
                  item-title="title"
                  item-value="value"
                  label="Type de planning"
                  required
                ></v-select>
              </v-col>
              <v-col cols="12" sm="6">
                <v-select
                  v-model="editedItem.site"
                  :items="sites"
                  item-title="name"
                  item-value="id"
                  label="Site"
                  required
                  @update:model-value="loadSiteEmployees"
                ></v-select>
              </v-col>

              <!-- Sélection de l'employé si plusieurs sur le site -->
              <v-col v-if="siteEmployees.length > 1" cols="12" sm="6">
                <v-select
                  v-model="editedItem.employee"
                  :items="siteEmployees"
                  item-title="employee_name"
                  item-value="id"
                  label="Employé"
                  required
                ></v-select>
              </v-col>
            </v-row>

            <!-- Planning type Fréquence -->
            <template v-if="editedItem.schedule_type === 'FREQUENCY'">
              <v-row v-for="day in weekDays" :key="day.value">
                <v-col cols="12" sm="4">
                  <v-checkbox
                    v-model="editedItem.details[day.value].enabled"
                    :label="day.text"
                  ></v-checkbox>
                </v-col>
                <v-col v-if="editedItem.details[day.value].enabled" cols="12" sm="4">
                  <v-text-field
                    v-model="editedItem.details[day.value].frequency_duration"
                    type="number"
                    label="Durée (minutes)"
                    min="0"
                    step="1"
                  ></v-text-field>
                </v-col>
              </v-row>
            </template>

            <!-- Planning type Fixe -->
            <template v-else>
              <v-row v-for="day in weekDays" :key="day.value">
                <v-col cols="12" sm="3">
                  <v-checkbox
                    v-model="editedItem.details[day.value].enabled"
                    :label="day.text"
                  ></v-checkbox>
                </v-col>
                <template v-if="editedItem.details[day.value].enabled">
                  <v-col cols="12" sm="3">
                    <v-select
                      v-model="editedItem.details[day.value].day_type"
                      :items="[
                        { text: 'Journée entière', value: 'FULL' },
                        { text: 'Matin', value: 'AM' },
                        { text: 'Après-midi', value: 'PM' }
                      ]"
                      item-title="text"
                      item-value="value"
                      label="Type de journée"
                    ></v-select>
                  </v-col>

                  <template v-if="editedItem.details[day.value].day_type === 'FULL' || editedItem.details[day.value].day_type === 'AM'">
                    <v-col cols="12" sm="3">
                      <v-text-field
                        v-model="editedItem.details[day.value].start_time_1"
                        type="time"
                        label="Début matin"
                      ></v-text-field>
                    </v-col>
                    <v-col cols="12" sm="3">
                      <v-text-field
                        v-model="editedItem.details[day.value].end_time_1"
                        type="time"
                        label="Fin matin"
                      ></v-text-field>
                    </v-col>
                  </template>

                  <template v-if="editedItem.details[day.value].day_type === 'FULL' || editedItem.details[day.value].day_type === 'PM'">
                    <v-col cols="12" sm="3">
                      <v-text-field
                        v-model="editedItem.details[day.value].start_time_2"
                        type="time"
                        label="Début après-midi"
                      ></v-text-field>
                    </v-col>
                    <v-col cols="12" sm="3">
                      <v-text-field
                        v-model="editedItem.details[day.value].end_time_2"
                        type="time"
                        label="Fin après-midi"
                      ></v-text-field>
                    </v-col>
                  </template>
                </template>
              </v-row>
            </template>
          </v-container>
        </v-card-text>

        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn
            color="primary"
            variant="text"
            @click="savePlanning"
          >
            Enregistrer
          </v-btn>
          <v-btn
            color="error"
            variant="text"
            @click="dialog = false"
          >
            Annuler
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Dialog de confirmation de suppression -->
    <v-dialog v-model="deleteDialog" max-width="500px">
      <v-card>
        <v-card-title class="text-h5">Supprimer ce planning ?</v-card-title>
        <v-card-text>
          Êtes-vous sûr de vouloir supprimer ce planning ? Cette action est irréversible.
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="primary" variant="text" @click="deleteDialog = false">Annuler</v-btn>
          <v-btn color="error" variant="text" @click="deletePlanning">Supprimer</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { planningsApi, sitesApi } from '@/services/api'
import type { Schedule, Site, Employee, ScheduleDetail } from '@/services/api'

// Type pour les détails du planning en édition
interface ScheduleDetailEdit {
  day_of_week: number;
  day_type: 'FULL' | 'AM' | 'PM';
  frequency_duration: number;
  start_time_1: string;
  end_time_1: string;
  start_time_2: string;
  end_time_2: string;
  enabled: boolean;
}

// Type étendu pour ScheduleDetail qui inclut toutes les propriétés possibles
interface ExtendedScheduleDetail extends ScheduleDetail {
  day_type?: 'FULL' | 'AM' | 'PM';
  frequency_duration?: number;
}

// Type de base pour Schedule avec les propriétés supplémentaires
interface BaseSchedule extends Omit<Schedule, 'site'> {
  site?: { id: number };
  tolerance_margin?: number;
}

// Type pour le planning en édition
interface EditingSchedule {
  id: number;
  schedule_type: 'FIXED' | 'FREQUENCY';
  site?: number;
  employee?: number;
  details: {
    [key: number]: ScheduleDetailEdit;
  };
  assigned_employees: Array<{ employee: number }>;
}

// Type pour les détails à envoyer à l'API
interface ScheduleDetailAPI {
  day_of_week: number;
  frequency_duration?: number;
  start_time_1?: string;
  end_time_1?: string;
  start_time_2?: string;
  end_time_2?: string;
  day_type?: 'FULL' | 'AM' | 'PM';
}

// Type pour les données à envoyer à l'API
interface ScheduleAPI {
  schedule_type: 'FIXED' | 'FREQUENCY';
  site?: { id: number };
  details: ScheduleDetailAPI[];
  assigned_employees: Array<{ employee: number }>;
}

// Type pour le planning avec site
interface ScheduleWithSite {
  id: number;
  schedule_type: 'FIXED' | 'FREQUENCY';
  site?: { id: number };
  site_name?: string;
  details?: ScheduleDetail[];
  assigned_employees?: Array<{ employee: number }>;
}

// État
const loading = ref(false)
const dialog = ref(false)
const deleteDialog = ref(false)
const page = ref(1)
const itemsPerPage = ref(10)
const totalItems = ref(0)
const plannings = ref<Schedule[]>([])
const sites = ref<Site[]>([])
const siteEmployees = ref<Employee[]>([])

const filters = ref({
  site: undefined as number | undefined,
  type: undefined as string | undefined,
})

const planningTypes = [
  { title: 'Fixe', value: 'FIXED' },
  { title: 'Fréquence', value: 'FREQUENCY' },
]

const weekDays = [
  { text: 'Lundi', value: 0 },
  { text: 'Mardi', value: 1 },
  { text: 'Mercredi', value: 2 },
  { text: 'Jeudi', value: 3 },
  { text: 'Vendredi', value: 4 },
  { text: 'Samedi', value: 5 },
  { text: 'Dimanche', value: 6 }
]

const headers = [
  { title: 'Site', key: 'site_name', align: 'start' },
  { title: 'Type', key: 'schedule_type' },
  { title: 'Actions', key: 'actions', sortable: false }
]

// Structure initiale pour les détails du planning
const defaultDetails = () => {
  const details: { [key: number]: ScheduleDetailEdit } = {}
  weekDays.forEach(day => {
    details[day.value] = {
      day_of_week: day.value,
      day_type: 'FULL',
      frequency_duration: 0,
      start_time_1: '',
      end_time_1: '',
      start_time_2: '',
      end_time_2: '',
      enabled: false
    }
  })
  return details
}

const editedItem = ref<EditingSchedule>({
  id: 0,
  schedule_type: 'FIXED',
  site: undefined,
  employee: undefined,
  details: defaultDetails(),
  assigned_employees: []
})

const itemToDelete = ref<Schedule | null>(null)

// Charger les employés d'un site
const loadSiteEmployees = async () => {
  if (!editedItem.value.site) return
  try {
    const response = await sitesApi.getSiteEmployees(editedItem.value.site)
    siteEmployees.value = response.data.results
    
    // Si un seul employé, le sélectionner automatiquement
    if (siteEmployees.value.length === 1) {
      editedItem.value.employee = siteEmployees.value[0].id
    }
  } catch (error) {
    console.error('Erreur lors du chargement des employés:', error)
  }
}

// Méthodes
const loadPlannings = async () => {
  loading.value = true
  try {
    const response = await planningsApi.getAllPlannings(page.value, itemsPerPage.value)
    plannings.value = response.data.results.map(planning => ({
      ...planning,
      site_name: planning.site_name || ''  // S'assurer que site_name existe
    }))
    totalItems.value = response.data.count
  } catch (error) {
    console.error('Erreur lors du chargement des plannings:', error)
  } finally {
    loading.value = false
  }
}

const loadSites = async () => {
  try {
    const response = await sitesApi.getAllSites()
    sites.value = response.data.results
  } catch (error) {
    console.error('Erreur lors du chargement des sites:', error)
  }
}

const openDialog = (item?: ScheduleWithSite) => {
  if (item) {
    // Mode édition
    const details: { [key: number]: ScheduleDetailEdit } = defaultDetails()
    
    // Convertir les détails en objet indexé par jour
    if (item.details) {
      item.details.forEach((detail: ScheduleDetail) => {
        const extendedDetail = detail as ExtendedScheduleDetail
        details[detail.day_of_week] = {
          day_of_week: detail.day_of_week,
          day_type: extendedDetail.day_type || 'FULL',
          frequency_duration: extendedDetail.frequency_duration || 0,
          start_time_1: detail.start_time_1 || '',
          end_time_1: detail.end_time_1 || '',
          start_time_2: detail.start_time_2 || '',
          end_time_2: detail.end_time_2 || '',
          enabled: true
        }
      })
    }

    // Récupérer l'ID du site correctement
    const siteId = typeof item.site === 'object' ? item.site?.id : item.site

    editedItem.value = {
      id: item.id,
      schedule_type: item.schedule_type,
      site: siteId,
      employee: item.assigned_employees?.[0]?.employee,
      details,
      assigned_employees: item.assigned_employees || []
    }

    // Charger les employés du site si un site est sélectionné
    if (siteId) {
      loadSiteEmployees()
    }
  } else {
    // Mode création
    editedItem.value = {
      id: 0,
      schedule_type: 'FIXED',
      site: undefined,
      employee: undefined,
      details: defaultDetails(),
      assigned_employees: []
    }
  }
  dialog.value = true
}

const savePlanning = async () => {
  try {
    // Convertir les détails en tableau
    const details = Object.values(editedItem.value.details)
      .filter(detail => detail.enabled)
      .map(detail => {
        const baseDetail = {
          day_of_week: detail.day_of_week,
          day_type: detail.day_type,
          schedule_type: editedItem.value.schedule_type
        }

        if (editedItem.value.schedule_type === 'FREQUENCY') {
          return {
            ...baseDetail,
            frequency_duration: detail.frequency_duration
          }
        } else {
          // Gestion des horaires en fonction du type de journée
          const timeFields = {
            start_time_1: null,
            end_time_1: null,
            start_time_2: null,
            end_time_2: null
          }

          if (detail.day_type === 'FULL' || detail.day_type === 'AM') {
            timeFields.start_time_1 = detail.start_time_1 || null
            timeFields.end_time_1 = detail.end_time_1 || null
          }

          if (detail.day_type === 'FULL' || detail.day_type === 'PM') {
            timeFields.start_time_2 = detail.start_time_2 || null
            timeFields.end_time_2 = detail.end_time_2 || null
          }

          return {
            ...baseDetail,
            ...timeFields
          }
        }
      })

    const planningData = {
      schedule_type: editedItem.value.schedule_type,
      site: editedItem.value.site ? { id: editedItem.value.site } : undefined,
      details: details,
      assigned_employees: editedItem.value.employee 
        ? [{ employee: editedItem.value.employee }] 
        : []
    }

    if (editedItem.value.id) {
      await planningsApi.updatePlanning(editedItem.value.id, planningData)
    } else {
      await planningsApi.createPlanning(planningData)
    }
    dialog.value = false
    loadPlannings()
  } catch (error) {
    console.error('Erreur lors de la sauvegarde du planning:', error)
  }
}

const deletePlanning = async () => {
  if (!itemToDelete.value?.id) return

  try {
    await planningsApi.deletePlanning(itemToDelete.value.id)
    deleteDialog.value = false
    loadPlannings()
  } catch (error) {
    console.error('Erreur lors de la suppression du planning:', error)
  }
}

const confirmDelete = (item: Schedule) => {
  itemToDelete.value = item
  deleteDialog.value = true
}

const resetFilters = () => {
  filters.value = {
    site: undefined,
    type: undefined
  }
  loadPlannings()
}

// Lifecycle hooks
onMounted(() => {
  loadPlannings()
  loadSites()
})
</script>

<style scoped>
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

/* Style des boutons icônes colorés dans le tableau */
:deep(.v-data-table .v-btn--icon[color="primary"]) {
  background-color: transparent !important;
  color: #00346E !important;
  opacity: 1 !important;
}

:deep(.v-data-table .v-btn--icon[color="error"]) {
  background-color: transparent !important;
  color: #F78C48 !important;
  opacity: 1 !important;
}

:deep(.v-data-table .v-btn--icon[color="success"]) {
  background-color: transparent !important;
  color: #00346E !important;
  opacity: 1 !important;
}

:deep(.v-data-table .v-btn--icon[color="warning"]) {
  background-color: transparent !important;
  color: #F78C48 !important;
  opacity: 1 !important;
}

/* Correction des overlays et underlays */
:deep(.v-btn__overlay),
:deep(.v-btn__underlay) {
  opacity: 0 !important;
}

/* Assurer que les icônes dans les boutons sont visibles */
:deep(.v-data-table .v-btn--icon .v-icon) {
  opacity: 1 !important;
  color: inherit !important;
}
</style> 