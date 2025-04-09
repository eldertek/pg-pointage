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
        v-if="canCreateDelete"
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
      :items="filteredSchedules"
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
      @click:row="handleRowClick"
    >
      <!-- Site -->
      <template #item.site_name="{ item }">
        {{ item.site_name }}
      </template>

      <!-- Employés -->
      <template #item.employees="{ item }">
        <v-chip-group>
          <v-chip
            v-for="employee in item.assigned_employees"
            :key="employee.id"
            size="small"
            color="primary"
            variant="outlined"
          >
            {{ employee.employee_name }}
          </v-chip>
          <v-chip
            v-if="!item.assigned_employees?.length"
            size="small"
            color="grey"
            variant="outlined"
          >
            Aucun employé
          </v-chip>
        </v-chip-group>
      </template>

      <!-- Type de planning -->
      <template #item.schedule_type="{ item }">
        <v-chip
          :color="item.schedule_type === 'FIXED' ? 'primary' : 'secondary'"
          size="small"
        >
          {{ item.schedule_type === 'FIXED' ? 'Fixe' : 'Fréquence' }}
        </v-chip>
      </template>

      <!-- Actions -->
      <template #item.actions="{ item }">
        <v-btn
          icon
          variant="text"
          size="small"
          color="primary"
          :to="`/dashboard/plannings/${item.id}`"
          @click.stop
        >
          <v-icon>mdi-eye</v-icon>
        </v-btn>
        <v-btn
          v-if="canEdit"
          icon
          variant="text"
          size="small"
          color="primary"
          @click.stop="openDialog(item)"
        >
          <v-icon>mdi-pencil</v-icon>
        </v-btn>
        <v-btn
          v-if="canCreateDelete"
          icon
          variant="text"
          size="small"
          color="warning"
          @click.stop="toggleStatus(item)"
        >
          <v-icon>{{ item.is_active ? 'mdi-domain' : 'mdi-domain-off' }}</v-icon>
        </v-btn>
        <v-btn
          v-if="canCreateDelete"
          icon
          variant="text"
          size="small"
          color="error"
          @click.stop="confirmDelete(item)"
        >
          <v-icon>mdi-delete</v-icon>
        </v-btn>
      </template>
    </v-data-table>

    <!-- Formulaire -->
    <template #form>
      <DashboardForm ref="form" @submit="saveSchedule">
        <!-- Première ligne : Type de planning, Site, Employés -->
        <v-row class="mb-6">
          <v-col cols="12" sm="4">
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
              density="comfortable"
              variant="outlined"
            ></v-select>
          </v-col>
          <v-col cols="12" sm="4">
            <v-select
              v-if="editedItem"
              v-model="editedItem.site"
              :items="sites"
              item-title="name"
              item-value="id"
              label="Site"
              :rules="[v => !!v || 'Le site est requis']"
              required
              density="comfortable"
              variant="outlined"
              @update:model-value="loadEmployees"
            ></v-select>
          </v-col>
          <v-col cols="12" sm="4">
            <v-select
              v-if="editedItem && employees.length >= 0"
              v-model="editedItem.employees"
              :items="employees"
              item-title="employee_name"
              item-value="id"
              label="Employés"
              multiple
              chips
              closable-chips
              :disabled="!editedItem.site"
              :hint="!editedItem.site ? 'Veuillez d\'abord sélectionner un site' : undefined"
              :persistent-hint="!editedItem.site"
              density="comfortable"
              variant="outlined"
            >
              <template #chip="{ props: chipProps, item }">
                <v-chip
                  v-bind="chipProps"
                  :text="item.raw.employee_name"
                  color="primary"
                  variant="outlined"
                ></v-chip>
              </template>
              <template #no-data>
                <div class="pa-2 text-center">Aucun employé disponible pour ce site</div>
              </template>
            </v-select>
          </v-col>
        </v-row>

        <!-- Paramètres de tolérance -->
        <v-row v-if="editedItem" class="mb-6">
          <v-col cols="12">
            <v-card variant="outlined" class="pa-4">
              <v-card-title class="text-subtitle-1 mb-4">Paramètres de tolérance</v-card-title>
              
              <!-- Paramètres pour planning type fréquence -->
              <template v-if="editedItem.schedule_type === ScheduleTypeEnum.FREQUENCY">
                <v-row>
                  <v-col cols="12" sm="6">
                    <v-text-field
                      v-model="editedItem.frequency_tolerance_percentage"
                      type="number"
                      label="Marge de tolérance (%)"
                      min="0"
                      max="100"
                      step="1"
                      density="comfortable"
                      variant="outlined"
                      color="primary"
                      :rules="[
                        v => v >= 0 || 'La marge doit être positive',
                        v => v <= 100 || 'La marge ne peut pas dépasser 100%'
                      ]"
                      hide-details="auto"
                    >
                      <template #append-inner>
                        <span class="text-grey">%</span>
                      </template>
                    </v-text-field>
                  </v-col>
                </v-row>
              </template>
              
              <!-- Paramètres pour planning type fixe -->
              <template v-else>
                <v-row>
                  <v-col cols="12" sm="4">
                    <v-text-field
                      v-model="editedItem.late_arrival_margin"
                      type="number"
                      label="Marge de retard"
                      min="0"
                      step="1"
                      density="comfortable"
                      variant="outlined"
                      color="primary"
                      :rules="[v => v >= 0 || 'La marge doit être positive']"
                      hide-details="auto"
                    >
                      <template #append-inner>
                        <span class="text-grey">min</span>
                      </template>
                    </v-text-field>
                  </v-col>
                  <v-col cols="12" sm="4">
                    <v-text-field
                      v-model="editedItem.early_departure_margin"
                      type="number"
                      label="Marge de départ anticipé"
                      min="0"
                      step="1"
                      density="comfortable"
                      variant="outlined"
                      color="primary"
                      :rules="[v => v >= 0 || 'La marge doit être positive']"
                      hide-details="auto"
                    >
                      <template #append-inner>
                        <span class="text-grey">min</span>
                      </template>
                    </v-text-field>
                  </v-col>
                </v-row>
              </template>
            </v-card>
          </v-col>
        </v-row>

        <!-- Planning type Fréquence -->
        <template v-if="editedItem && editedItem.schedule_type === ScheduleTypeEnum.FREQUENCY">
          <v-row>
            <v-col cols="12">
              <v-card variant="outlined" class="pa-4">
                <v-card-title class="text-subtitle-1 mb-4">Sélectionnez les jours et définissez la durée de présence</v-card-title>
                <div v-for="(detail, index) in editedItem.details" :key="index" class="day-container mb-4">
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
                        <template #append-inner>
                          <span class="text-grey">min</span>
                        </template>
                      </v-text-field>
                    </div>
                  </div>
                </div>
                <v-alert
                  v-if="!editedItem.details.some(d => d.enabled)"
                  type="info"
                  variant="tonal"
                  class="mt-4"
                >
                  Veuillez sélectionner au moins un jour et définir sa durée de présence
                </v-alert>
              </v-card>
            </v-col>
          </v-row>
        </template>

        <!-- Planning type Fixe -->
        <template v-else-if="editedItem">
          <v-row>
            <v-col cols="12">
              <v-card variant="outlined" class="pa-4">
                <v-card-title class="text-subtitle-1 mb-4">Sélectionnez les jours et définissez les horaires</v-card-title>
                <div v-for="(detail, index) in editedItem.details" :key="index" class="day-container mb-4">
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
                              <template #activator="{ props: startTime1Props }">
                                <v-text-field
                                  v-model="detail.start_time_1"
                                  label="Début"
                                  v-bind="startTime1Props"
                                  density="comfortable"
                                  variant="outlined"
                                  color="primary"
                                  class="flex-grow-1"
                                  clearable
                                  :error-messages="getTimeError(detail)"
                                  type="time"
                                  @click:clear="detail.start_time_1 = undefined"
                                ></v-text-field>
                              </template>
                              <VTimePicker
                                v-model="detail.start_time_1"
                                format="24hr"
                                ok-text="OK"
                                cancel-text="Annuler"
                                hide-header
                                @click:save="detail.showStartTime1Menu = false"
                                @click:cancel="detail.showStartTime1Menu = false"
                              ></VTimePicker>
                            </v-menu>
                            <v-menu
                              v-model="detail.showEndTime1Menu"
                              :close-on-content-click="false"
                              location="bottom"
                            >
                              <template #activator="{ props: endTime1Props }">
                                <v-text-field
                                  v-model="detail.end_time_1"
                                  label="Fin"
                                  v-bind="endTime1Props"
                                  density="comfortable"
                                  variant="outlined"
                                  color="primary"
                                  class="flex-grow-1"
                                  clearable
                                  :error-messages="getTimeError(detail)"
                                  type="time"
                                  @click:clear="detail.end_time_1 = undefined"
                                ></v-text-field>
                              </template>
                              <VTimePicker
                                v-model="detail.end_time_1"
                                format="24hr"
                                ok-text="OK"
                                cancel-text="Annuler"
                                hide-header
                                @click:save="detail.showEndTime1Menu = false"
                                @click:cancel="detail.showEndTime1Menu = false"
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
                              <template #activator="{ props: startTime2Props }">
                                <v-text-field
                                  v-model="detail.start_time_2"
                                  label="Début"
                                  v-bind="startTime2Props"
                                  density="comfortable"
                                  variant="outlined"
                                  color="primary"
                                  class="flex-grow-1"
                                  clearable
                                  :error-messages="getTimeError(detail)"
                                  type="time"
                                  @click:clear="detail.start_time_2 = undefined"
                                ></v-text-field>
                              </template>
                              <VTimePicker
                                v-model="detail.start_time_2"
                                format="24hr"
                                ok-text="OK"
                                cancel-text="Annuler"
                                hide-header
                                @click:save="detail.showStartTime2Menu = false"
                                @click:cancel="detail.showStartTime2Menu = false"
                              ></VTimePicker>
                            </v-menu>
                            <v-menu
                              v-model="detail.showEndTime2Menu"
                              :close-on-content-click="false"
                              location="bottom"
                            >
                              <template #activator="{ props: endTime2Props }">
                                <v-text-field
                                  v-model="detail.end_time_2"
                                  label="Fin"
                                  v-bind="endTime2Props"
                                  density="comfortable"
                                  variant="outlined"
                                  color="primary"
                                  class="flex-grow-1"
                                  clearable
                                  :error-messages="getTimeError(detail)"
                                  type="time"
                                  @click:clear="detail.end_time_2 = undefined"
                                ></v-text-field>
                              </template>
                              <VTimePicker
                                v-model="detail.end_time_2"
                                format="24hr"
                                ok-text="OK"
                                cancel-text="Annuler"
                                hide-header
                                @click:save="detail.showEndTime2Menu = false"
                                @click:cancel="detail.showEndTime2Menu = false"
                              ></VTimePicker>
                            </v-menu>
                          </div>
                        </div>
                      </template>
                    </div>
                  </div>
                </div>
                <v-alert
                  v-if="!editedItem.details.some(d => d.enabled)"
                  type="info"
                  variant="tonal"
                  class="mt-4"
                >
                  Veuillez sélectionner au moins un jour et définir ses horaires
                </v-alert>
              </v-card>
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
import { useRouter } from 'vue-router'
import { sitesApi, schedulesApi, organizationsApi } from '@/services/api'
import type { Site } from '@/services/api'
import type { Schedule as BaseSchedule, Employee } from '@/types/api'
import { ScheduleTypeEnum, DayTypeEnum, DayOfWeekEnum, RoleEnum } from '@/types/api'
import { useAuthStore } from '@/stores/auth'
import DashboardView from '@/components/dashboard/DashboardView.vue'
import DashboardFilters from '@/components/dashboard/DashboardFilters.vue'
import DashboardForm from '@/components/dashboard/DashboardForm.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import { VTimePicker } from 'vuetify/labs/VTimePicker'
import { useConfirmDialog } from '@/utils/dialogs'
import type { DialogState } from '@/utils/dialogs'

// Configuration de la locale pour Vuetify

const router = useRouter()
const { dialogState } = useConfirmDialog()

// Props
const props = defineProps({
  editId: {
    type: [String, Number],
    default: null
  }
})

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

// Interface pour les employés assignés dans la réponse de l'API
interface ApiAssignedEmployee {
  id: number;
  employee: number;
  employee_name: string;
  schedule: number;
  site: number;
}

// Interface pour la réponse de l'API des plannings
interface ApiSchedule extends BaseSchedule {
  site_name: string;
  assigned_employees: ApiAssignedEmployee[];
  assigned_employee_ids: number[];
}

// Interface pour les employés assignés dans notre composant
interface AssignedEmployee {
  id: number;
  employee: number;
  employee_name: string;
  schedule: number;
  site: number;
}

// Interface étendue pour les plannings avec les propriétés supplémentaires
interface ExtendedSchedule extends Omit<BaseSchedule, 'details'> {
  enabled?: boolean;
  employees?: Array<{ id: number }>;
  site: number;
  details: ExtendedScheduleDetail[];
  assigned_employees?: AssignedEmployee[];
  assigned_employee_ids?: number[];
  // Champs pour les plannings de type fréquence
  frequency_tolerance_percentage?: number;
  // Champs pour les plannings de type fixe
  late_arrival_margin?: number;
  early_departure_margin?: number;
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
  // Champs pour les plannings de type fréquence
  frequency_tolerance_percentage?: number;
  // Champs pour les plannings de type fixe
  late_arrival_margin?: number;
  early_departure_margin?: number;
}

const authStore = useAuthStore()

// Computed properties pour les permissions
const canCreateDelete = computed(() => {
  const role = authStore.user?.role
  return role === RoleEnum.SUPER_ADMIN || role === RoleEnum.ADMIN
})

const canEdit = computed(() => {
  const role = authStore.user?.role
  return role === RoleEnum.SUPER_ADMIN || role === RoleEnum.ADMIN || role === RoleEnum.MANAGER
})

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
  { title: 'Employés', key: 'employees' },
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

// Filtrer les plannings selon les permissions
const filteredSchedules = computed(() => {
  const user = authStore.user
  if (!user) return []
  
  console.log('[Plannings][Filter] User:', {
    id: user.id,
    role: user.role,
    organizations: user.organizations
  })
  
  console.log('[Plannings][Filter] Plannings avant filtrage:', schedules.value)
  
  // Filtrer d'abord par permissions
  let filtered = schedules.value.filter(schedule => {
    // Super Admin voit tout
    if (user.role === RoleEnum.SUPER_ADMIN) return true
    
    // Admin et Manager voient les plannings de leurs organisations
    if (user.role === RoleEnum.ADMIN || user.role === RoleEnum.MANAGER) {
      // Convertir les IDs en nombres pour la comparaison
      const userOrgIds = user.organizations?.map(org => Number(org)) ?? []
      
      // Trouver le site associé au planning
      const site = sites.value.find(s => s.id === schedule.site)
      if (!site) return false
      
      const siteOrgId = Number(site.organization)
      const hasAccess = userOrgIds.includes(siteOrgId)
      
      console.log('[Plannings][Filter] Vérification accès pour le planning:', {
        scheduleId: schedule.id,
        siteId: schedule.site,
        siteOrg: siteOrgId,
        userOrgs: userOrgIds,
        hasAccess
      })
      return hasAccess
    }
    
    // Employé voit les plannings des sites auxquels il est rattaché
    if (user.role === RoleEnum.EMPLOYEE) {
      return user.sites?.some(s => s.id === schedule.site) ?? false
    }
    
    return false
  })
  
  // Filtrage supplémentaire côté client
  // Filtrer par site
  if (filters.value.site) {
    const siteId = Number(filters.value.site)
    filtered = filtered.filter(schedule => schedule.site === siteId)
  }
  
  // Filtrer par type de planning
  if (filters.value.type) {
    filtered = filtered.filter(schedule => schedule.schedule_type === filters.value.type)
  }
  
  console.log('[Plannings][Filter] Plannings après filtrage:', filtered)
  return filtered
})

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
    console.log('[Plannings][LoadSchedules] Filtres actuels:', {
      site: filters.value.site,
      type: filters.value.type,
      page: page.value,
      page_size: itemsPerPage.value
    })

    // Préparer les paramètres de requête
    const params: any = {
      page: page.value,
      page_size: itemsPerPage.value
    }

    // Ajouter le filtre site si présent
    if (filters.value.site) {
      const siteId = Number(filters.value.site)
      if (!isNaN(siteId)) {
        params.site = siteId
      }
    }

    // Ajouter le filtre type si présent
    if (filters.value.type) {
      // Le type est déjà dans le bon format (FIXED ou FREQUENCY)
      params.schedule_type = filters.value.type
    }

    console.log('[Plannings][LoadSchedules] Paramètres de requête:', params)

    const response = await schedulesApi.getAllSchedules(params)
    console.log('[Plannings][LoadSchedules] Réponse brute:', JSON.stringify(response.data, null, 2))

    schedules.value = (response.data.results as ApiSchedule[] || []).map(schedule => {
      console.log(`[Plannings][LoadSchedules] Traitement du planning ${schedule.id}:`, JSON.stringify({
        assignedEmployees: schedule.assigned_employees,
        isActive: schedule.is_active,
        scheduleType: schedule.schedule_type
      }, null, 2))
      
      return {
        ...schedule,
        schedule_type: schedule.schedule_type as ScheduleTypeEnum,
        name: schedule.site_name,
        min_daily_hours: 0,
        min_weekly_hours: 0,
        allow_early_arrival: false,
        allow_late_departure: false,
        early_arrival_limit: 0,
        late_departure_limit: 0,
        assigned_employees: schedule.assigned_employees || [],
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
      }
    })

    totalItems.value = response.data.count
  } catch (error) {
    console.error('[Plannings][Error] Erreur lors du chargement des plannings:', error)
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
    
    const numericSiteId = typeof siteId === 'string' ? Number(siteId) : siteId
    console.log('[Plannings][LoadEmployees] SiteId converti:', numericSiteId)
    
    if (!isValidSiteId(numericSiteId)) {
      console.log('[Plannings][LoadEmployees] SiteId invalide')
      employees.value = []
      return
    }

    // Récupérer d'abord le site pour avoir l'ID de l'organisation
    const siteResponse = await sitesApi.getSite(numericSiteId)
    const organizationId = siteResponse.data.organization

    // Récupérer les employés de l'organisation
    const response = await organizationsApi.getOrganizationEmployees(organizationId, { role: 'EMPLOYEE' })
    employees.value = response.data.results.map((employee: any) => ({
      id: employee.id,
      first_name: employee.first_name,
      last_name: employee.last_name,
      email: employee.email,
      organization: employee.organization,
      employee_name: `${employee.first_name} ${employee.last_name}`
    }))

    console.log('[Plannings][LoadEmployees] Employés chargés:', JSON.stringify(employees.value, null, 2))
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
  console.log('[Plannings][OpenDialog] Item reçu:', item)
  
  editedItem.value = item ? {
    id: item.id,
    site: item.site,
    employees: item.assigned_employee_ids || [],
    details: daysOfWeek.map(day => {
      // Rechercher un détail existant pour ce jour
      const existingDetail = item.details?.find(detail => detail.day_of_week === day.value)
      
      if (existingDetail) {
        console.log(`[Plannings][OpenDialog] Détail existant trouvé pour le jour ${day.label}:`, existingDetail)
        return {
          ...existingDetail,
          enabled: true,
          showStartTime1Menu: false,
          showEndTime1Menu: false,
          showStartTime2Menu: false,
          showEndTime2Menu: false
        }
      } else {
        console.log(`[Plannings][OpenDialog] Création d'un nouveau détail pour le jour ${day.label}`)
        return {
          day_of_week: day.value,
          enabled: false,
          day_type: DayTypeEnum.FULL,
          frequency_duration: item.schedule_type === ScheduleTypeEnum.FREQUENCY ? 0 : undefined,
          start_time_1: item.schedule_type === ScheduleTypeEnum.FIXED ? '09:00' : undefined,
          end_time_1: item.schedule_type === ScheduleTypeEnum.FIXED ? '12:00' : undefined,
          start_time_2: item.schedule_type === ScheduleTypeEnum.FIXED ? '14:00' : undefined,
          end_time_2: item.schedule_type === ScheduleTypeEnum.FIXED ? '17:00' : undefined,
          showStartTime1Menu: false,
          showEndTime1Menu: false,
          showStartTime2Menu: false,
          showEndTime2Menu: false
        }
      }
    }),
    is_active: item.is_active,
    schedule_type: item.schedule_type,
    enabled: true,
    // Initialisation des marges de tolérance
    frequency_tolerance_percentage: item.frequency_tolerance_percentage ?? 10,
    late_arrival_margin: item.late_arrival_margin ?? 0,
    early_departure_margin: item.early_departure_margin ?? 0
  } : {
    site: undefined,
    employees: [],
    details: daysOfWeek.map(day => ({
      day_of_week: day.value,
      enabled: false,
      day_type: DayTypeEnum.FULL,
      start_time_1: '09:00',
      end_time_1: '12:00',
      start_time_2: '14:00',
      end_time_2: '17:00',
      showStartTime1Menu: false,
      showEndTime1Menu: false,
      showStartTime2Menu: false,
      showEndTime2Menu: false
    })),
    schedule_type: ScheduleTypeEnum.FIXED,
    enabled: true,
    is_active: true,
    // Initialisation des marges par défaut
    frequency_tolerance_percentage: undefined,
    late_arrival_margin: 0,
    early_departure_margin: 0
  }

  console.log('[Plannings][OpenDialog] Item préparé:', editedItem.value)

  const currentItem = editedItem.value
  // Si un site est sélectionné, charger les employés
  if (currentItem?.site) {
    loadEmployees(currentItem.site).then(() => {
      // Après le chargement des employés, vérifier que les employés sélectionnés sont toujours disponibles
      if (currentItem.employees?.length) {
        console.log('[Plannings][OpenDialog] Employés sélectionnés:', currentItem.employees)
        console.log('[Plannings][OpenDialog] Employés disponibles:', employees.value)
      }
    })
  }

  if (dashboardView.value) {
    dashboardView.value.showForm = true
  }
}

const saveSchedule = async () => {
  if (!form.value?.validate()) return

  // Vérifier que le site est sélectionné
  if (!editedItem.value?.site) {
    alert('Veuillez sélectionner un site avant de sauvegarder')
    return
  }

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
      enabled: currentItem.enabled,
      // Ajout des paramètres de tolérance selon le type de planning
      ...(currentItem.schedule_type === ScheduleTypeEnum.FREQUENCY ? {
        frequency_tolerance_percentage: currentItem.frequency_tolerance_percentage
      } : {
        late_arrival_margin: currentItem.late_arrival_margin,
        early_departure_margin: currentItem.early_departure_margin
      })
    }

    console.log('[Plannings][Save] Données à sauvegarder:', scheduleData)

    let savedSchedule
    try {
      if (currentItem.id) {
        console.log('[Plannings][Save] Mise à jour du planning:', {
          siteId: currentItem.site,
          scheduleId: currentItem.id,
          data: scheduleData
        })
        savedSchedule = await schedulesApi.updateSchedule(currentItem.site, currentItem.id, scheduleData)
      } else {
        console.log('[Plannings][Save] Création d\'un nouveau planning:', {
          data: scheduleData
        })
        savedSchedule = await schedulesApi.createSchedule(scheduleData)
      }

      // Gérer l'assignation des employés si le planning a été sauvegardé avec succès
      if (savedSchedule?.data?.id && currentItem.employees?.length >= 0) {
        console.log('[Plannings][Save] Assignation des employés:', {
          siteId: currentItem.site,
          scheduleId: savedSchedule.data.id,
          employees: currentItem.employees
        })
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
      console.error('[Plannings][Save] Erreur lors de la sauvegarde:', error)
      throw error
    }
  } catch (error) {
    console.error('[Plannings][Error] Erreur lors de la sauvegarde:', error)
  } finally {
    saving.value = false
  }
}

const confirmDelete = (item: ExtendedSchedule) => {
  const state = dialogState.value as DialogState
  state.show = true
  state.title = 'Confirmation de suppression'
  state.message = 'Êtes-vous sûr de vouloir supprimer ce planning ?'
  state.confirmText = 'Supprimer'
  state.cancelText = 'Annuler'
  state.confirmColor = 'error'
  state.loading = false
  state.onConfirm = async () => {
    state.loading = true
    await deleteSchedule(item)
    state.show = false
    state.loading = false
  }
}

const deleteSchedule = async (item: ExtendedSchedule) => {
  try {
    console.log('[Plannings][Delete] Suppression du planning:', item.id)
    await schedulesApi.deleteSchedule(item.id)
    console.log('[Plannings][Delete] Planning supprimé avec succès')
    await loadSchedules()
  } catch (error) {
    console.error('[Plannings][Error] Erreur lors de la suppression:', error)
  }
}

const toggleStatus = async (item: ExtendedSchedule) => {
  console.log('[Plannings][ToggleStatus] Début de la mise à jour du statut pour le planning:', JSON.stringify({
    id: item.id,
    currentStatus: item.is_active,
    assignedEmployees: item.assigned_employees
  }, null, 2))
  
  const state = dialogState.value as DialogState
  state.show = true
  state.title = 'Confirmation'
  state.message = `Êtes-vous sûr de vouloir ${item.is_active ? 'désactiver' : 'activer'} ce planning ?`
  state.confirmText = item.is_active ? 'Désactiver' : 'Activer'
  state.cancelText = 'Annuler'
  state.confirmColor = 'warning'
  state.loading = false
  state.onConfirm = async () => {
    state.loading = true
    try {
      console.log('[Plannings][ToggleStatus] Envoi de la requête de mise à jour:', JSON.stringify({
        id: item.id,
        newStatus: !item.is_active
      }, null, 2))
      
      await schedulesApi.updateSchedule(item.site, item.id, {
        is_active: !item.is_active
      })
      
      console.log('[Plannings][ToggleStatus] Rechargement des plannings')
      await loadSchedules()
    } catch (error) {
      console.error('[Plannings][Error] Erreur lors du changement de statut:', error)
    } finally {
      state.show = false
      state.loading = false
    }
  }
}

const validateTimeRange = (startTime: string, endTime: string): boolean => {
  if (!startTime || !endTime) return true
  return startTime < endTime
}

const validateDaySequence = (morningStart: string | undefined, morningEnd: string | undefined, afternoonStart: string | undefined): boolean => {
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
    if (!validateDaySequence(detail.start_time_1, detail.end_time_1, detail.start_time_2)) {
      return "Les horaires de l'après-midi doivent être après ceux du matin"
    }
  }
  
  return null
}

const handleRowClick = (event: Event, { item }: { item: ExtendedSchedule }) => {
  // Vérifier si le clic vient d'un élément interactif
  const target = event.target as HTMLElement
  const clickedElement = target.closest('.v-btn, a, button, [data-no-row-click]')
  
  if (clickedElement || target.hasAttribute('data-no-row-click')) {
    return
  }

  console.log('[Plannings][Navigation] Redirection vers les détails du planning:', item.id)
  router.push(`/dashboard/plannings/${item.id}`)
}

// Initialisation
onMounted(async () => {
  await Promise.all([
    loadSchedules(),
    loadSites()
  ])

  // Si on a un editId, charger directement le planning depuis la liste
  if (props.editId) {
    console.log('[Plannings][Mount] EditId trouvé:', props.editId)
    const scheduleToEdit = schedules.value.find(s => s.id === Number(props.editId))
    if (scheduleToEdit) {
      console.log('[Plannings][Mount] Planning trouvé dans la liste:', scheduleToEdit)
      openDialog(scheduleToEdit)
    } else {
      console.log('[Plannings][Mount] Planning non trouvé dans la liste, chargement direct...')
      try {
        // Utiliser le site_id si disponible dans le planning trouvé
        const response = await schedulesApi.getSchedule(Number(props.editId))
        const extendedSchedule = {
          ...response.data,
          schedule_type: response.data.schedule_type as ScheduleTypeEnum,
          assigned_employees: response.data.assigned_employees?.map((emp: any) => ({
            ...emp,
            schedule: response.data.id,
            site: response.data.site
          })) || []
        }
        console.log('[Plannings][Mount] Planning chargé:', extendedSchedule)
        openDialog(extendedSchedule)
      } catch (error) {
        console.error('[Plannings][Error] Erreur lors du chargement du planning:', error)
      }
    }
  }
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
  margin-top: 8px;
}

.time-section {
  background-color: white;
  border-radius: 6px;
  padding: 16px;
  min-width: 0; /* Pour éviter le débordement des champs flex */
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
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

:deep(.v-card-title) {
  font-size: 1.1rem !important;
  font-weight: 500 !important;
  color: rgba(0, 0, 0, 0.87) !important;
}

:deep(.v-alert) {
  font-size: 0.95rem;
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
}

/* Style pour le bouton désactivé */
:deep(.disabled-button) {
  opacity: 0.5 !important;
  color: #999 !important;
  cursor: not-allowed !important;
}

:deep(.disabled-button .v-icon) {
  color: #999 !important;
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

/* Style pour le tableau avec pointeur */
:deep(.v-data-table tbody tr) {
  cursor: pointer;
}
</style> 