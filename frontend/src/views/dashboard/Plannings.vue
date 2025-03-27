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
            <template v-if="editedItem.schedule_type === ScheduleTypeEnum.FREQUENCY">
              <v-row v-for="(detail, index) in editedItem.details" :key="index">
                <v-col cols="12" sm="4">
                  <v-checkbox
                    v-model="detail.enabled"
                    :label="weekDays.find(d => d.value === detail.day_of_week)?.text || ''"
                  ></v-checkbox>
                </v-col>
                <v-col v-if="detail.enabled" cols="12" sm="4">
                  <v-text-field
                    v-model="detail.frequency_duration"
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
              <v-row v-for="(detail, index) in editedItem.details" :key="index">
                <v-col cols="12" sm="3">
                  <v-checkbox
                    v-model="detail.enabled"
                    :label="weekDays.find(d => d.value === detail.day_of_week)?.text || ''"
                  ></v-checkbox>
                </v-col>
                <template v-if="detail.enabled">
                  <v-col cols="12" sm="3">
                    <v-select
                      v-model="detail.day_type"
                      :items="[
                        { text: 'Journée entière', value: DayTypeEnum.FULL },
                        { text: 'Matin', value: DayTypeEnum.AM },
                        { text: 'Après-midi', value: DayTypeEnum.PM }
                      ]"
                      item-title="text"
                      item-value="value"
                      label="Type de journée"
                    ></v-select>
                  </v-col>

                  <template v-if="detail.day_type === DayTypeEnum.FULL || detail.day_type === DayTypeEnum.AM">
                    <v-col cols="12" sm="3">
                      <v-text-field
                        v-model="detail.start_time_1"
                        type="time"
                        label="Début matin"
                      ></v-text-field>
                    </v-col>
                    <v-col cols="12" sm="3">
                      <v-text-field
                        v-model="detail.end_time_1"
                        type="time"
                        label="Fin matin"
                      ></v-text-field>
                    </v-col>
                  </template>

                  <template v-if="detail.day_type === DayTypeEnum.FULL || detail.day_type === DayTypeEnum.PM">
                    <v-col cols="12" sm="3">
                      <v-text-field
                        v-model="detail.start_time_2"
                        type="time"
                        label="Début après-midi"
                      ></v-text-field>
                    </v-col>
                    <v-col cols="12" sm="3">
                      <v-text-field
                        v-model="detail.end_time_2"
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
import { useRoute } from 'vue-router'
import { sitesApi, schedulesApi } from '@/services/api'
import type { Site, Employee } from '@/services/api'
import type { Schedule as BaseSchedule, ScheduleDetail as BaseScheduleDetail } from '@/types/api'
import { ScheduleTypeEnum, DayTypeEnum, DayOfWeekEnum } from '@/types/api'
import type { ExtendedSchedule } from '@/types/sites'

// Type avec les propriétés additionnelles pour l'édition
interface ScheduleDetailEdit extends Partial<BaseScheduleDetail> {
  id?: number;
  day_type?: DayTypeEnum;
  frequency_duration?: number;
  enabled?: boolean; // Pour la UI seulement
  day_name?: string; // Required property from BaseScheduleDetail
}

// Type de base pour Schedule avec les propriétés supplémentaires
interface EditingSchedule {
  id: number;
  schedule_type: ScheduleTypeEnum;
  site: number;
  employee?: number;
  details: ScheduleDetailEdit[];
  assigned_employees: Array<{ employee: number }>;
}

// Type pour les données à envoyer à l'API
interface ScheduleAPIRequest {
  schedule_type: ScheduleTypeEnum;
  site?: number;
  details: Array<Partial<ScheduleDetailEdit>>;
  assigned_employees: Array<{ employee: number }>;
}

// Types pour les paramètres de l'API
interface ScheduleParams {
  page: number;
  page_size: number;
  site?: number;
  schedule_type?: string;
}

// État
const loading = ref(false)
const dialog = ref(false)
const deleteDialog = ref(false)
const page = ref(1)
const itemsPerPage = ref(10)
const totalItems = ref(0)
const plannings = ref<ExtendedSchedule[]>([])
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
  { title: 'Site', key: 'site_name', align: 'start' as const },
  { title: 'Type', key: 'schedule_type' },
  { title: 'Actions', key: 'actions', sortable: false }
]

// Structure initiale pour les détails du planning
const defaultDetails = (): ScheduleDetailEdit[] => {
  return weekDays.map(day => ({
    id: 0,
    day_of_week: day.value,
    day_type: DayTypeEnum.FULL,
    frequency_duration: 0,
    start_time_1: '',
    end_time_1: '',
    start_time_2: '',
    end_time_2: '',
    enabled: false,
    day_name: weekDays.find(d => d.value === day.value)?.text || ''
  }));
}

const editedItem = ref<EditingSchedule>({
  id: 0,
  schedule_type: ScheduleTypeEnum.FIXED,
  site: 0,
  details: defaultDetails(),
  assigned_employees: []
});

const itemToDelete = ref<ExtendedSchedule | null>(null)

// Méthodes
const loadPlannings = async () => {
  loading.value = true;
  try {
    const params: ScheduleParams = {
      page: page.value,
      page_size: itemsPerPage.value
    };
    
    // Ajouter les filtres optionnels seulement s'ils sont définis
    if (filters.value.site) {
      params.site = filters.value.site;
    }
    if (filters.value.type) {
      params.schedule_type = filters.value.type;
    }
    
    const response = await schedulesApi.getAllSchedules(params);
    plannings.value = response.data.results ? 
      (response.data.results.map(schedule => ({
        ...schedule,
        name: schedule.site_name,
        min_daily_hours: 0,
        min_weekly_hours: 0,
        allow_early_arrival: false,
        allow_late_departure: false,
        early_arrival_limit: 30,
        late_departure_limit: 30,
        break_duration: 60,
        min_break_start: '09:00',
        max_break_end: '17:00',
        frequency_hours: 0,
        frequency_type: 'DAILY',
        frequency_count: 1,
        time_window: 8,
        assigned_employees_count: 0
      })) as unknown as ExtendedSchedule[]) :
      [];
    totalItems.value = response.data.count;
  } catch (error) {
    console.error('Erreur lors du chargement des plannings:', error);
  } finally {
    loading.value = false;
  }
};

const loadSites = async () => {
  try {
    const response = await sitesApi.getAllSites()
    sites.value = response.data.results
  } catch (error) {
    console.error('Erreur lors du chargement des sites:', error)
  }
}

const openDialog = (item?: ExtendedSchedule) => {
  if (item) {
    // Mode édition
    const details: ScheduleDetailEdit[] = defaultDetails();
    
    // Convertir les détails en objet indexé par jour
    if (item.details) {
      item.details.forEach((detail: BaseScheduleDetail) => {
        const idx = details.findIndex(d => d.day_of_week === detail.day_of_week);
        if (idx >= 0) {
          details[idx] = {
            ...detail,
            day_type: detail.day_type || DayTypeEnum.FULL,
            frequency_duration: (detail as any).frequency_duration || 0,
            enabled: true
          };
        }
      });
    }

    // Récupérer l'ID du site correctement
    const siteId = typeof item.site === 'object' && item.site && 'id' in item.site
      ? (item.site as { id: number }).id
      : item.site;

    editedItem.value = {
      id: item.id,
      schedule_type: item.schedule_type || ScheduleTypeEnum.FIXED,
      site: siteId || 0,
      employee: item.assigned_employees_count ? 
        (Array.isArray(item.assigned_employees_count) && item.assigned_employees_count.length > 0 ? 
          item.assigned_employees_count[0].id : 
          typeof item.assigned_employees_count === 'number' ? item.assigned_employees_count : undefined) : 
        undefined,
      details,
      assigned_employees: item.assigned_employees_count ? 
        (Array.isArray(item.assigned_employees_count) ? 
          item.assigned_employees_count.map(emp => ({ employee: emp.id })) : 
          typeof item.assigned_employees_count === 'number' ? 
            [{ employee: item.assigned_employees_count }] : 
            []) : 
        []
    };

    // Charger les employés du site si un site est sélectionné
    if (siteId) {
      loadSiteEmployees();
    }
  } else {
    // Mode création
    editedItem.value = {
      id: 0,
      schedule_type: ScheduleTypeEnum.FIXED,
      site: 0,
      details: defaultDetails(),
      assigned_employees: []
    };
  }
  dialog.value = true
}

const savePlanning = async () => {
  try {
    // Convertir les détails en tableau
    const details = editedItem.value.details
      .filter(detail => detail.enabled)
      .map(detail => {
        const baseDetail: any = {
          day_of_week: detail.day_of_week,
          day_type: detail.day_type,
        };

        if (editedItem.value.schedule_type === ScheduleTypeEnum.FREQUENCY) {
          return {
            ...baseDetail,
            frequency_duration: detail.frequency_duration
          };
        } else {
          // Gestion des horaires en fonction du type de journée
          const timeFields: { [key: string]: string | undefined } = {};

          if (detail.day_type === DayTypeEnum.FULL || detail.day_type === DayTypeEnum.AM) {
            timeFields.start_time_1 = detail.start_time_1 || undefined;
            timeFields.end_time_1 = detail.end_time_1 || undefined;
          }

          if (detail.day_type === DayTypeEnum.FULL || detail.day_type === DayTypeEnum.PM) {
            timeFields.start_time_2 = detail.start_time_2 || undefined;
            timeFields.end_time_2 = detail.end_time_2 || undefined;
          }

          return {
            ...baseDetail,
            ...timeFields
          };
        }
      });

    const planningData: ScheduleAPIRequest = {
      schedule_type: editedItem.value.schedule_type,
      site: editedItem.value.site,
      details,
      assigned_employees: editedItem.value.employee 
        ? [{ employee: editedItem.value.employee }] 
        : []
    };

    if (editedItem.value.id) {
      await schedulesApi.updateSchedule(editedItem.value.id, planningData as any);
    } else {
      await schedulesApi.createSchedule(planningData as any);
    }
    dialog.value = false;
    loadPlannings();
  } catch (error) {
    console.error('Erreur lors de la sauvegarde du planning:', error);
  }
};

const deletePlanning = async () => {
  if (!itemToDelete.value?.id) return

  try {
    await schedulesApi.deleteSchedule(itemToDelete.value.id)
    deleteDialog.value = false
    loadPlannings()
  } catch (error) {
    console.error('Erreur lors de la suppression du planning:', error)
  }
}

const confirmDelete = (item: ExtendedSchedule) => {
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