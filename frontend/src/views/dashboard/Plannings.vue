<template>
  <DashboardView
    ref="dashboardView"
    title="Plannings"
    :form-title="editedItem?.id ? 'Modifier' : 'Nouveau' + ' planning'"
    :saving="saving"
    @save="saveSchedule"
  >
    <!-- Actions -->
    <template #actions>
      <v-btn
        color="primary"
        prepend-icon="mdi-plus"
        @click="openDialog()"
      >
        Nouveau planning
      </v-btn>
    </template>

    <!-- Filtres -->
    <template #filters>
      <DashboardFilters @reset="resetFilters">
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
            @update:model-value="loadSchedules"
          ></v-select>
        </v-col>
        <v-col cols="12" md="4">
          <v-select
            v-model="filters.type"
            :items="scheduleTypes"
            label="Type de planning"
            variant="outlined"
            prepend-inner-icon="mdi-calendar-clock"
            clearable
            @update:model-value="loadSchedules"
          ></v-select>
        </v-col>
      </DashboardFilters>
    </template>

    <!-- Tableau -->
    <v-data-table
      v-model:page="page"
      :headers="headers"
      :items="schedules"
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

    <!-- Formulaire -->
    <template #form>
      <DashboardForm ref="form" @submit="saveSchedule">
        <v-col cols="12" sm="6">
          <v-select
            v-if="editedItem"
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
            v-if="editedItem"
            v-model="editedItem.site"
            :items="sites"
            item-title="name"
            item-value="id"
            label="Site"
            required
            @update:model-value="loadEmployees"
          ></v-select>
        </v-col>

        <!-- Sélection de l'employé si plusieurs sur le site -->
        <v-col v-if="editedItem && employees.length >= 0" cols="12" sm="6">
          <v-select
            v-model="editedItem.employees"
            :items="employees"
            item-title="employee_name"
            item-value="id"
            label="Employés"
            multiple
            chips
            closable-chips
            required
          >
            <template v-slot:chip="{ props, item }">
              <v-chip
                v-bind="props"
                :text="item.raw.employee_name"
                color="primary"
                variant="outlined"
              ></v-chip>
            </template>
            <template v-slot:prepend-inner>
              <v-icon color="primary">mdi-account-multiple</v-icon>
            </template>
            <template v-slot:no-data>
              <div class="pa-2 text-center">Aucun employé disponible pour ce site</div>
            </template>
          </v-select>
        </v-col>

        <!-- Planning type Fréquence -->
        <template v-if="editedItem && editedItem.schedule_type === ScheduleTypeEnum.FREQUENCY">
          <v-row>
            <v-col cols="12">
              <div v-for="(detail, index) in editedItem.details" :key="index" class="day-container mb-6">
                <v-checkbox
                  v-model="detail.enabled"
                  :label="daysOfWeek.find(d => d.value === detail.day_of_week)?.label || ''"
                  class="mb-2 day-checkbox"
                  color="primary"
                  hide-details
                ></v-checkbox>

                <div v-if="detail.enabled" class="day-content pl-8">
                  <div class="time-section">
                    <div class="text-subtitle-2 mb-3">Durée de présence</div>
                    <v-text-field
                      v-model="detail.frequency_duration"
                      type="number"
                      label="Durée (minutes)"
                      min="0"
                      step="1"
                      density="comfortable"
                      variant="outlined"
                      color="primary"
                      class="flex-grow-1"
                      hide-details
                    >
                      <template v-slot:append-inner>
                        <span class="text-grey">min</span>
                      </template>
                    </v-text-field>
                  </div>
                </div>
              </div>
            </v-col>
          </v-row>
        </template>

        <!-- Planning type Fixe -->
        <template v-else-if="editedItem">
          <v-row>
            <v-col cols="12">
              <div v-for="(detail, index) in editedItem.details" :key="index" class="day-container mb-6">
                <v-checkbox
                  v-model="detail.enabled"
                  :label="daysOfWeek.find(d => d.value === detail.day_of_week)?.label || ''"
                  class="mb-2 day-checkbox"
                  color="primary"
                  hide-details
                ></v-checkbox>

                <div v-if="detail.enabled" class="day-content pl-8">
                  <v-select
                    v-model="detail.day_type"
                    :items="[
                      { text: 'Journée entière', value: DayTypeEnum.FULL },
                      { text: 'Matin uniquement', value: DayTypeEnum.AM },
                      { text: 'Après-midi uniquement', value: DayTypeEnum.PM }
                    ]"
                    item-title="text"
                    item-value="value"
                    label="Type de journée"
                    class="mb-4"
                    density="comfortable"
                    variant="outlined"
                    color="primary"
                  ></v-select>

                  <div class="d-flex gap-4">
                    <template v-if="detail.day_type === DayTypeEnum.FULL || detail.day_type === DayTypeEnum.AM">
                      <div class="time-section flex-grow-1">
                        <div class="text-subtitle-2 mb-3">Horaires du matin</div>
                        <div class="d-flex gap-4">
                          <v-menu
                            v-model="detail.showStartTime1Menu"
                            :close-on-content-click="false"
                            location="bottom"
                          >
                            <template v-slot:activator="{ props }">
                              <v-text-field
                                v-model="detail.start_time_1"
                                label="Début"
                                v-bind="props"
                                density="comfortable"
                                variant="outlined"
                                color="primary"
                                class="flex-grow-1"
                                @click:clear="detail.start_time_1 = undefined"
                                clearable
                                :error-messages="getTimeError(detail)"
                                type="time"
                              ></v-text-field>
                            </template>
                            <VTimePicker
                              v-model="detail.start_time_1"
                              format="24hr"
                              @click:save="detail.showStartTime1Menu = false"
                              @click:cancel="detail.showStartTime1Menu = false"
                              ok-text="OK"
                              cancel-text="Annuler"
                              hide-header
                            ></VTimePicker>
                          </v-menu>
                          <v-menu
                            v-model="detail.showEndTime1Menu"
                            :close-on-content-click="false"
                            location="bottom"
                          >
                            <template v-slot:activator="{ props }">
                              <v-text-field
                                v-model="detail.end_time_1"
                                label="Fin"
                                v-bind="props"
                                density="comfortable"
                                variant="outlined"
                                color="primary"
                                class="flex-grow-1"
                                @click:clear="detail.end_time_1 = undefined"
                                clearable
                                :error-messages="getTimeError(detail)"
                                type="time"
                              ></v-text-field>
                            </template>
                            <VTimePicker
                              v-model="detail.end_time_1"
                              format="24hr"
                              @click:save="detail.showEndTime1Menu = false"
                              @click:cancel="detail.showEndTime1Menu = false"
                              ok-text="OK"
                              cancel-text="Annuler"
                              hide-header
                            ></VTimePicker>
                          </v-menu>
                        </div>
                      </div>
                    </template>

                    <template v-if="detail.day_type === DayTypeEnum.FULL || detail.day_type === DayTypeEnum.PM">
                      <div class="time-section flex-grow-1">
                        <div class="text-subtitle-2 mb-3">Horaires de l'après-midi</div>
                        <div class="d-flex gap-4">
                          <v-menu
                            v-model="detail.showStartTime2Menu"
                            :close-on-content-click="false"
                            location="bottom"
                          >
                            <template v-slot:activator="{ props }">
                              <v-text-field
                                v-model="detail.start_time_2"
                                label="Début"
                                v-bind="props"
                                density="comfortable"
                                variant="outlined"
                                color="primary"
                                class="flex-grow-1"
                                @click:clear="detail.start_time_2 = undefined"
                                clearable
                                :error-messages="getTimeError(detail)"
                                type="time"
                              ></v-text-field>
                            </template>
                            <VTimePicker
                              v-model="detail.start_time_2"
                              format="24hr"
                              @click:save="detail.showStartTime2Menu = false"
                              @click:cancel="detail.showStartTime2Menu = false"
                              ok-text="OK"
                              cancel-text="Annuler"
                              hide-header
                            ></VTimePicker>
                          </v-menu>
                          <v-menu
                            v-model="detail.showEndTime2Menu"
                            :close-on-content-click="false"
                            location="bottom"
                          >
                            <template v-slot:activator="{ props }">
                              <v-text-field
                                v-model="detail.end_time_2"
                                label="Fin"
                                v-bind="props"
                                density="comfortable"
                                variant="outlined"
                                color="primary"
                                class="flex-grow-1"
                                @click:clear="detail.end_time_2 = undefined"
                                clearable
                                :error-messages="getTimeError(detail)"
                                type="time"
                              ></v-text-field>
                            </template>
                            <VTimePicker
                              v-model="detail.end_time_2"
                              format="24hr"
                              @click:save="detail.showEndTime2Menu = false"
                              @click:cancel="detail.showEndTime2Menu = false"
                              ok-text="OK"
                              cancel-text="Annuler"
                              hide-header
                            ></VTimePicker>
                          </v-menu>
                        </div>
                      </div>
                    </template>
                  </div>
                </div>
              </div>
            </v-col>
          </v-row>
        </template>
      </DashboardForm>
    </template>
  </DashboardView>
  <ConfirmDialog />
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { useRoute } from 'vue-router'
import { sitesApi, schedulesApi } from '@/services/api'
import type { Site, Employee } from '@/services/api'
import type { Schedule as BaseSchedule, ScheduleDetail as BaseScheduleDetail } from '@/types/api'
import { ScheduleTypeEnum, DayTypeEnum, DayOfWeekEnum, RoleEnum } from '@/types/api'
import { useAuthStore } from '@/stores/auth'
import DashboardView from '@/components/dashboard/DashboardView.vue'
import DashboardFilters from '@/components/dashboard/DashboardFilters.vue'
import DashboardForm from '@/components/dashboard/DashboardForm.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import { VTimePicker } from 'vuetify/labs/VTimePicker'
import { fr } from 'vuetify/locale'

// Configuration de la locale pour Vuetify
const locale = {
  ...fr,
  timePicker: {
    ...fr.timePicker,
    select: 'Sélectionner l\'heure'
  }
}

const route = useRoute()

// Interface étendue pour les détails de planning
interface ExtendedScheduleDetail {
  id?: number;
  day_of_week: number;
  frequency_duration?: number;
  start_time_1?: string;
  end_time_1?: string;
  start_time_2?: string;
  end_time_2?: string;
  day_type?: 'FULL' | 'AM' | 'PM';
  enabled?: boolean;
  showStartTime1Menu?: boolean;
  showEndTime1Menu?: boolean;
  showStartTime2Menu?: boolean;
  showEndTime2Menu?: boolean;
}

// Interface étendue pour les plannings avec les propriétés supplémentaires
interface ExtendedSchedule extends Omit<BaseSchedule, 'details'> {
  enabled?: boolean;
  employees?: Array<{ id: number }>;
  site: number;
  details: ExtendedScheduleDetail[];
}

// Interface pour le formulaire de planning
interface ScheduleFormData {
  id?: number;
  site: number | undefined;
  employees: number[];
  details: ExtendedScheduleDetail[];
  is_active?: boolean;
  schedule_type?: ScheduleTypeEnum;
  enabled?: boolean;
}

const authStore = useAuthStore()
const isSuperAdmin = computed(() => authStore.user?.role === RoleEnum.SUPER_ADMIN)

// État
const loading = ref(false)
const saving = ref(false)
const page = ref(1)
const itemsPerPage = ref(10)
const totalItems = ref(0)
const editedItem = ref<ScheduleFormData | null>(null)
const form = ref()
const dashboardView = ref()

// Filtres
const filters = ref({
  search: '',
  site: undefined as string | number | undefined,
  type: undefined as string | undefined
})

// Données
const schedules = ref<ExtendedSchedule[]>([])
const sites = ref<Site[]>([])
const employees = ref<Employee[]>([])

// En-têtes des tableaux
const headers = [
  { title: 'Site', key: 'site_name' },
  { title: 'Employé', key: 'employee_name' },
  { title: 'Type', key: 'schedule_type' },
  { title: 'Actions', key: 'actions', sortable: false }
]

// Jours de la semaine
const daysOfWeek = [
  { label: 'Lundi', value: DayOfWeekEnum._0 },
  { label: 'Mardi', value: DayOfWeekEnum._1 },
  { label: 'Mercredi', value: DayOfWeekEnum._2 },
  { label: 'Jeudi', value: DayOfWeekEnum._3 },
  { label: 'Vendredi', value: DayOfWeekEnum._4 },
  { label: 'Samedi', value: DayOfWeekEnum._5 },
  { label: 'Dimanche', value: DayOfWeekEnum._6 }
]

// Types de planning
const scheduleTypes = [
  { title: 'Fixe', value: ScheduleTypeEnum.FIXED },
  { title: 'Fréquence', value: ScheduleTypeEnum.FREQUENCY }
]

// Fonction de garde de type pour vérifier qu'un siteId est valide
function isValidSiteId(siteId: number | string | undefined): siteId is number {
  if (typeof siteId === 'string') {
    const numericSiteId = Number(siteId)
    return !isNaN(numericSiteId) && numericSiteId > 0
  }
  return typeof siteId === 'number' && siteId > 0
}

// Méthodes
const loadSchedules = async () => {
  loading.value = true
  try {
    const response = await schedulesApi.getAllSchedules({
      page: page.value,
      page_size: itemsPerPage.value,
      site: filters.value.site ? Number(filters.value.site) : undefined,
      schedule_type: filters.value.type
    })
    schedules.value = (response.data.results || []).map(schedule => ({
      ...schedule,
      schedule_type: schedule.schedule_type as ScheduleTypeEnum,
      name: schedule.site_name,
      min_daily_hours: 0,
      min_weekly_hours: 0,
      allow_early_arrival: false,
      allow_late_departure: false,
      early_arrival_limit: 0,
      late_departure_limit: 0,
      details: schedule.details?.map(detail => ({
        id: detail.id || 0,
        day_of_week: detail.day_of_week,
        frequency_duration: detail.frequency_duration || undefined,
        start_time_1: detail.start_time_1 || undefined,
        end_time_1: detail.end_time_1 || undefined,
        start_time_2: detail.start_time_2 || undefined,
        end_time_2: detail.end_time_2 || undefined,
        day_type: detail.day_type,
        enabled: true,
        showStartTime1Menu: false,
        showEndTime1Menu: false,
        showStartTime2Menu: false,
        showEndTime2Menu: false
      })) || []
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
    sites.value = response.data.results || []
  } catch (error) {
    console.error('Erreur lors du chargement des sites:', error)
  }
}

const loadEmployees = async (siteId: number | string | undefined) => {
  try {
    console.log('[Plannings][LoadEmployees] Début du chargement des employés pour le site:', siteId)
    
    // Convertir siteId en nombre si c'est une chaîne
    const numericSiteId = typeof siteId === 'string' ? Number(siteId) : siteId
    console.log('[Plannings][LoadEmployees] SiteId converti:', numericSiteId)
    
    // Vérifier que siteId est un nombre valide
    if (!isValidSiteId(numericSiteId)) {
      console.log('[Plannings][LoadEmployees] SiteId invalide')
      return
    }

    // Si on crée un nouveau planning (pas d'ID), on utilise getSiteEmployees
    // Sinon, on utilise getScheduleEmployees
    const response = editedItem.value?.id 
      ? await schedulesApi.getScheduleEmployees(numericSiteId, editedItem.value.id)
      : await sitesApi.getSiteEmployees(numericSiteId);
    
    employees.value = response.data.results || []
    console.log('[Plannings][LoadEmployees] Employés chargés:', employees.value.length)
  } catch (error) {
    console.error('[Plannings][Error] Erreur lors du chargement des employés:', error)
    employees.value = []
  }
}

const resetFilters = () => {
  filters.value = {
    search: '',
    site: undefined,
    type: undefined
  }
  loadSchedules()
}

const openDialog = (item?: ExtendedSchedule) => {
  editedItem.value = item ? {
    id: item.id,
    site: item.site,
    employees: item.employees?.map(e => e.id) || [],
    details: item.details.map(detail => ({
      ...detail,
      showStartTime1Menu: false,
      showEndTime1Menu: false,
      showStartTime2Menu: false,
      showEndTime2Menu: false
    })),
    is_active: item.is_active,
    schedule_type: item.schedule_type,
    enabled: item.enabled
  } : {
    site: undefined,
    employees: [],
    details: daysOfWeek.map(day => ({
      day_of_week: day.value,
      enabled: false,
      day_type: DayTypeEnum.FULL,
      showStartTime1Menu: false,
      showEndTime1Menu: false,
      showStartTime2Menu: false,
      showEndTime2Menu: false
    })),
    schedule_type: ScheduleTypeEnum.FIXED,
    enabled: true,
    is_active: true
  }

  const currentItem = editedItem.value
  // Si un site est sélectionné, charger les employés
  if (currentItem?.site) {
    loadEmployees(currentItem.site)
  }

  if (dashboardView.value) {
    dashboardView.value.showForm = true
  }
}

const saveSchedule = async () => {
  if (!form.value?.validate()) return

  // Vérifier les horaires
  if (!editedItem.value) return

  const invalidDetails = editedItem.value.details.filter(detail => {
    if (!detail.enabled) return false
    if (editedItem.value?.schedule_type === ScheduleTypeEnum.FIXED) {
      return getTimeError(detail) !== null
    }
    return false
  })
  
  if (invalidDetails.length > 0) {
    alert('Veuillez corriger les horaires invalides avant de sauvegarder')
    return
  }

  saving.value = true
  try {
    const currentItem = editedItem.value
    if (!currentItem) return
    if (!currentItem.site) return

    // Préparer les données du planning
    const scheduleData = {
      site: currentItem.site,
      schedule_type: currentItem.schedule_type,
      details: currentItem.details
        .filter(detail => detail.enabled)
        .map(detail => ({
          id: detail.id || undefined,
          day_of_week: detail.day_of_week,
          frequency_duration: currentItem.schedule_type === ScheduleTypeEnum.FREQUENCY ? detail.frequency_duration : undefined,
          start_time_1: currentItem.schedule_type === ScheduleTypeEnum.FIXED ? detail.start_time_1 : undefined,
          end_time_1: currentItem.schedule_type === ScheduleTypeEnum.FIXED ? detail.end_time_1 : undefined,
          start_time_2: currentItem.schedule_type === ScheduleTypeEnum.FIXED ? detail.start_time_2 : undefined,
          end_time_2: currentItem.schedule_type === ScheduleTypeEnum.FIXED ? detail.end_time_2 : undefined,
          day_type: currentItem.schedule_type === ScheduleTypeEnum.FIXED ? detail.day_type : undefined,
          schedule_type: currentItem.schedule_type
        })),
      is_active: currentItem.is_active,
      enabled: currentItem.enabled
    }

    let savedSchedule
    if (currentItem.id) {
      savedSchedule = await schedulesApi.updateSchedule(currentItem.id, scheduleData)
    } else {
      savedSchedule = await schedulesApi.createSchedule(scheduleData)
    }

    // Gérer l'assignation des employés
    if (savedSchedule?.data?.id && currentItem.employees?.length > 0) {
      await schedulesApi.assignMultipleEmployees(
        currentItem.site,
        savedSchedule.data.id,
        currentItem.employees
      )
    }
    
    await loadSchedules()
    if (dashboardView.value) {
      dashboardView.value.showForm = false
    }
  } catch (error) {
    console.error('[Plannings][Error] Erreur lors de la sauvegarde:', error)
  } finally {
    saving.value = false
  }
}

const confirmDelete = (item: ExtendedSchedule) => {
  if (window.confirm('Êtes-vous sûr de vouloir supprimer ce planning ?')) {
    deleteSchedule(item)
  }
}

const deleteSchedule = async (item: ExtendedSchedule) => {
  try {
    const scheduleData = {
      is_active: false,
      enabled: false
    }
    await schedulesApi.updateSchedule(item.id, scheduleData)
    await loadSchedules()
  } catch (error) {
    console.error('Erreur lors de la suppression:', error)
  }
}

const validateTimeRange = (startTime: string, endTime: string): boolean => {
  if (!startTime || !endTime) return true
  return startTime < endTime
}

const validateDaySequence = (morningStart: string | undefined, morningEnd: string | undefined, afternoonStart: string | undefined, afternoonEnd: string | undefined): boolean => {
  if (!morningEnd || !afternoonStart) return true
  return morningEnd < afternoonStart
}

const getTimeError = (detail: ExtendedScheduleDetail): string | null => {
  // Validation des horaires du matin
  if ((detail.day_type === DayTypeEnum.FULL || detail.day_type === DayTypeEnum.AM) && detail.start_time_1 && detail.end_time_1) {
    if (!validateTimeRange(detail.start_time_1, detail.end_time_1)) {
      return "L'heure de fin du matin doit être après l'heure de début"
    }
  }
  
  // Validation des horaires de l'après-midi
  if ((detail.day_type === DayTypeEnum.FULL || detail.day_type === DayTypeEnum.PM) && detail.start_time_2 && detail.end_time_2) {
    if (!validateTimeRange(detail.start_time_2, detail.end_time_2)) {
      return "L'heure de fin de l'après-midi doit être après l'heure de début"
    }
  }
  
  // Pour une journée complète, vérifier que les horaires de l'après-midi sont après ceux du matin
  if (detail.day_type === DayTypeEnum.FULL && detail.end_time_1 && detail.start_time_2) {
    if (!validateDaySequence(detail.start_time_1, detail.end_time_1, detail.start_time_2, detail.end_time_2)) {
      return "Les horaires de l'après-midi doivent être après ceux du matin"
    }
  }
  
  return null
}

// Initialisation
onMounted(async () => {
  await Promise.all([
    loadSchedules(),
    loadSites()
  ])
})

// Observateurs
watch(() => filters.value.site, (newValue) => {
  const numericValue = typeof newValue === 'string' ? Number(newValue) : newValue
  if (isValidSiteId(numericValue)) {
    loadEmployees(numericValue)
  }
})

watch(() => page.value, () => {
  loadSchedules()
})

watch(() => itemsPerPage.value, () => {
  loadSchedules()
})
</script>

<style scoped>
.day-container {
  border-left: 3px solid transparent;
  padding-left: 16px;
  transition: all 0.3s ease;
}

.day-container:hover {
  border-left-color: #00346E;
}

.day-checkbox :deep(.v-label) {
  font-size: 1.1rem;
  font-weight: 500;
}

.day-content {
  background-color: #f8f9fa;
  border-radius: 8px;
  padding: 16px;
}

.time-section {
  background-color: white;
  border-radius: 6px;
  padding: 16px;
  min-width: 0; /* Pour éviter le débordement des champs flex */
}

.time-section + .time-section {
  margin-left: 16px;
}

.text-subtitle-2 {
  color: rgba(0, 0, 0, 0.6);
  font-weight: 500;
  font-size: 0.95rem;
}

:deep(.v-checkbox) {
  margin-top: 0;
}

:deep(.v-input__details) {
  padding-inline-start: 0;
}

/* Style des boutons dans le tableau */
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

/* Assurer que les icônes dans les boutons sont visibles */
:deep(.v-data-table .v-btn--icon .v-icon) {
  opacity: 1 !important;
  color: inherit !important;
}

:deep(.v-field__input) {
  cursor: pointer;
}

:deep(.v-field__append-inner) {
  cursor: pointer;
}

:deep(.time-field) {
  cursor: pointer;
}

:deep(.time-field .v-field__input),
:deep(.time-field .v-field__append-inner),
:deep(.time-field .v-field__prepend-inner),
:deep(.time-field .v-field__field) {
  cursor: pointer;
}

:deep(.time-field input[type="time"]) {
  cursor: pointer;
}

:deep(.time-field *) {
  pointer-events: none;
}

:deep(.time-field input) {
  pointer-events: auto;
}
</style> 