<template>
  <v-container fluid>
    <!-- En-tête avec titre et actions -->
    <div class="d-flex align-center mb-4">
      <v-btn
        v-if="showBackButton"
        icon="mdi-arrow-left"
        variant="text"
        :to="backRoute"
        class="mr-4"
      ></v-btn>
      <Title :level="1" class="font-weight-bold">{{ title }}</Title>
      <v-spacer></v-spacer>
      <v-btn
        v-if="canEdit"
        color="primary"
        prepend-icon="mdi-pencil"
        class="mr-2"
        @click.stop="editItem"
      >
        {{ $t('common.edit') }}
      </v-btn>
      <v-btn
        v-if="canCreateDelete"
        color="error"
        prepend-icon="mdi-delete"
        @click.stop="confirmDelete"
      >
        {{ $t('common.delete') }}
      </v-btn>
    </div>

    <!-- Loader -->
    <v-row v-if="loading">
      <v-col cols="12" class="text-center">
        <v-progress-circular indeterminate color="primary"></v-progress-circular>
      </v-col>
    </v-row>

    <template v-else>
      <v-card>
        <v-tabs v-model="activeTab" color="#00346E">
          <v-tab value="details">{{ $t('dashboard.informations') }}</v-tab>
          <v-tab value="employees">{{ $t('reports.reportTypes.EMPLOYEE') }}</v-tab>
        </v-tabs>

        <v-card-text>
          <v-window v-model="activeTab" :reverse="reverse">
            <!-- Onglet Informations -->
            <v-window-item value="details">
              <v-card class="elevation-1">
                <v-toolbar flat>
                  <v-toolbar-title>Informations</v-toolbar-title>
                  <v-spacer></v-spacer>
                </v-toolbar>
                <v-card-text>
                  <v-row>
                    <v-col cols="12" md="6">
                      <v-list>
                        <template v-for="(field) in displayFields" :key="field.key || index">
                          <v-list-item>
                            <template #prepend>
                              <v-icon>{{ field.icon }}</v-icon>
                            </template>
                            <v-list-item-title>{{ field.label }}</v-list-item-title>
                            <v-list-item-subtitle>
                              <template v-if="field.type === 'status'">
                                <StatusChip
                                  :status="item[field.key]"
                                  :active-:label="$t('dashboard.fieldactivelabel')"
                                  :inactive-:label="$t('dashboard.fieldinactivelabel')"
                                />
                              </template>
                              <template v-else-if="field.type === 'schedule_type'">
                                <v-chip
                                  :color="item[field.key] === 'FIXED' ? 'primary' : 'secondary'"
                                  size="small"
                                >
                                  {{ item[field.key] === 'FIXED' ? t('plannings.planningTypes.FIXED') : t('plannings.planningTypes.FREQUENCY') }}
                                </v-chip>
                              </template>
                              <template v-else>
                                {{ formatFieldValue(field, item[field.key]) }}
                              </template>
                            </v-list-item-subtitle>
                          </v-list-item>
                        </template>
                      </v-list>
                    </v-col>

                    <v-col cols="12" md="6">
                      <v-card class="mb-4">
                        <v-card-title>{{ $t('dashboard.statistics') }}</v-card-title>
                        <v-card-text>
                          <v-row>
                            <v-col cols="12" class="text-center">
                              <div class="text-h4">{{ statistics.total_employees }}</div>
                              <div class="text-subtitle-1">{{ $t('plannings.assignedEmployees') }}</div>
                            </v-col>
                          </v-row>
                        </v-card-text>
                      </v-card>
                    </v-col>
                  </v-row>
                </v-card-text>
              </v-card>
            </v-window-item>

            <!-- Onglet Employés -->
            <v-window-item value="employees">
              <v-row v-if="loadingTabs.employees">
                <v-col cols="12" class="text-center">
                  <v-progress-circular indeterminate color="primary"></v-progress-circular>
                </v-col>
              </v-row>
              <DataTable
                v-else
                :title="$t('reports.reportTypes.EMPLOYEE')"
                :headers="employeesHeaders"
                :items="employees"
                :no-data-:text="$t('dashboard.aucun_employ_trouv')"
                :detail-route="'/dashboard/admin/users/:id'"
                :edit-route="'/dashboard/admin/users/:id/edit'"
                @toggle-status="(item: TableItem) => handleToggleStatus(item)"
                @delete="(item: TableItem) => handleDelete(item)"
                @row-click="(item: TableItem) => router.push(`/dashboard/admin/users/${item.employee}`)"
              >
                <template #item.actions="{ item: rowItem }">
                  <v-btn
                    v-if="canEdit"
                    icon
                    variant="text"
                    size="small"
                    color="primary"
                    :to="`/dashboard/admin/users/${rowItem.employee}`"
                    @click.stop
                  >
                    <v-icon>mdi-eye</v-icon>
                    <v-tooltip activator="parent">{{ $t("common.viewDetails") }}</v-tooltip>
                  </v-btn>
                  <v-btn
                    v-if="canCreateDelete"
                    icon
                    variant="text"
                    size="small"
                    color="warning"
                    @click.stop="toggleUserStatus(rowItem)"
                  >
                    <v-icon>{{ rowItem.is_active ? 'mdi-account-off' : 'mdi-account-check' }}</v-icon>
                    <v-tooltip activator="parent">{{ rowItem.is_active ? 'Désactiver' : 'Activer' }} l'utilisateur</v-tooltip>
                  </v-btn>
                  <v-btn
                    v-if="canCreateDelete"
                    icon
                    variant="text"
                    size="small"
                    color="error"
                    @click.stop="confirmDeleteUser(rowItem)"
                  >
                    <v-icon>mdi-delete</v-icon>
                    <v-tooltip activator="parent">{{ $t("users.deleteUser") }}</v-tooltip>
                  </v-btn>
                </template>
              </DataTable>
            </v-window-item>
          </v-window>
        </v-card-text>
      </v-card>
    </template>
    <ConfirmDialog />

    <!-- Snackbar pour les notifications -->
    <v-snackbar
      v-model="snackbar.show"
      :color="snackbar.color"
      :timeout="3000"
      location="top"
    >
      {{ snackbar.text }}
      <template #actions>
        <v-btn variant="text" icon="mdi-close" @click="snackbar.show = false"></v-btn>
      </template>
    </v-snackbar>
  </v-container>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Title } from '@/components/typography'
import { format } from 'date-fns'
import { fr } from 'date-fns/locale'
import { schedulesApi, timesheetsApi, sitesApi, usersApi } from '@/services/api'
import StatusChip from '@/components/common/StatusChip.vue'
import DataTable, { type TableItem } from '@/components/common/DataTable.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import { useConfirmDialog } from '@/utils/dialogs'
import type { DialogState } from '@/utils/dialogs'
import { useAuthStore } from '@/stores/auth'

// Initialize i18n
const { t } = useI18n()

// Types
interface Field {
  key: string;
  label: string;
  icon: string;
  type?: 'status' | 'schedule_type' | 'default' | 'date';
  activeLabel?: string;
  inactiveLabel?: string;
  format?: 'date';
  dateFormat?: string;
}

// Props
const showBackButton = ref(true)

// State variables
const router = useRouter()
const route = useRoute()
const loading = ref(true)
const loadingTabs = ref({
  employees: false,
  pointages: false,
  anomalies: false,
  reports: false
})
const item = ref<any>({})
const statistics = ref<{ total_employees: number }>({
  total_employees: 0
})
const activeTab = ref('details')
const previousTab = ref('details')
const reverse = ref(false)
const { dialogState } = useConfirmDialog()
const auth = useAuthStore()

// Fonction de garde de type pour vérifier qu'un siteId est valide
function isValidSiteId(siteId: number | string | undefined): siteId is number {
  if (typeof siteId === 'string') {
    const numericSiteId = Number(siteId)
    return !isNaN(numericSiteId) && numericSiteId > 0
  }
  return typeof siteId === 'number' && siteId > 0
}

// Snackbar pour les notifications
const snackbar = ref({
  show: false,
  text: '',
  color: 'success'
})

const showSuccess = (text: string) => {
  snackbar.value = {
    show: true,
    text,
    color: 'success'
  }
}

const showError = (text: string) => {
  snackbar.value = {
    show: true,
    text,
    color: 'error'
  }
}

// Computed pour les permissions
const canEdit = computed(() => {
  const role = auth.user?.role
  return role === 'SUPER_ADMIN' || role === 'ADMIN' || role === 'MANAGER'
})

const canCreateDelete = computed(() => {
  const role = auth.user?.role
  return role === 'SUPER_ADMIN' || role === 'ADMIN'
})

// Données pour les tableaux
const employees = ref<any[]>([])
const pointages = ref<any[]>([])
const anomalies = ref<any[]>([])
const reports = ref<any[]>([])

// En-têtes des tableaux
const employeesHeaders = [
  { title: t('common.name'), key: 'employee_name' },
  { title: t('common.actions'), key: 'actions', sortable: false }
]

// Configuration des onglets
const tabOrder = ['details', 'employees', 'pointages', 'anomalies', 'reports']

watch(activeTab, (newTab, oldTab) => {
  if (!oldTab || !newTab) return

  const oldIndex = tabOrder.indexOf(oldTab)
  const newIndex = tabOrder.indexOf(newTab)

  reverse.value = newIndex < oldIndex
  previousTab.value = oldTab
})

// Computed properties
const itemId = computed(() => Number(route.params.id))

const title = computed(() => t('plannings.planningDetails'))

const backRoute = computed(() => '/dashboard/plannings')

const displayFields = computed((): Field[] => {
  return [
    { key: 'site_name', label: t('sites.title'), icon: 'mdi-map-marker' },
    {
      key: 'schedule_type',
      label: t('plannings.type'),
      icon: 'mdi-calendar-clock',
      type: 'schedule_type'
    },
    { key: 'created_at', label: t('reports.creationDate'), icon: 'mdi-calendar-plus', format: 'date', dateFormat: 'dd/MM/yyyy HH:mm' },
    { key: 'updated_at', label: t('reports.lastModified'), icon: 'mdi-calendar-clock', format: 'date', dateFormat: 'dd/MM/yyyy HH:mm' },
    {
      key: 'is_active',
      label: t('common.status'),
      icon: 'mdi-check-circle',
      type: 'status',
      activeLabel: t('sites.active'),
      inactiveLabel: t('sites.inactive')
    }
  ]
})

// Méthodes
const loadData = async () => {
  loading.value = true
  try {
    const response = await schedulesApi.getSchedule(itemId.value)
    item.value = response.data

    const stats = await schedulesApi.getScheduleStatistics(itemId.value)
    statistics.value = {
      total_employees: stats.data.total_employees || 0
    }
  } catch (error) {
    console.error('[PlanningDetail][LoadData] Erreur lors du chargement des données:', error)
  } finally {
    loading.value = false
  }
}

const formatFieldValue = (field: Field, value: any) => {
  if (!value) return ''
  if (field.format === 'date') {
    try {
      const date = new Date(value)
      return format(date, field.dateFormat || 'dd/MM/yyyy', { locale: fr })
    } catch (error) {
      console.error('[PlanningDetail][FormatDate] Erreur lors du formatage de la date:', error)
      return value
    }
  }
  return value
}

const editItem = () => {
  router.push(`/dashboard/plannings/${itemId.value}/edit`).catch(error => {
    console.error('[PlanningDetail][Edit] Erreur lors de la redirection:', error)
  })
}

const confirmDelete = () => {
  const state = dialogState.value as DialogState
  state.show = true
  state.title = t('common.deleteConfirmation')
  state.message = t('plannings.deleteConfirmation')
  state.confirmText = t('common.delete')
  state.cancelText = t('common.cancel')
  state.confirmColor = 'error'
  state.loading = false
  state.onConfirm = async () => {
    state.loading = true
    try {
      await schedulesApi.deleteSchedule(itemId.value)
      router.push('/dashboard/plannings')
    } finally {
      state.show = false
      state.loading = false
    }
  }
}

// Méthodes de chargement des données pour chaque onglet
const loadEmployees = async (siteId: number | string | undefined) => {
  try {
    console.log('[Plannings][LoadEmployees] Début du chargement des employés pour le site:', siteId)

    const numericSiteId = typeof siteId === 'string' ? Number(siteId) : siteId
    console.log('[Plannings][LoadEmployees] SiteId converti:', numericSiteId)

    if (!isValidSiteId(numericSiteId)) {
      console.log('[Plannings][LoadEmployees] SiteId invalide')
      return
    }

    const response = await sitesApi.getSiteEmployees(numericSiteId, { role: 'EMPLOYEE' })
    employees.value = response.data.results.map((siteEmployee: any) => {
      // Utiliser directement employee_name qui est fourni par le backend
      return {
        id: siteEmployee.id,
        employee: siteEmployee.employee, // ID de l'employé
        employee_name: siteEmployee.employee_name, // Nom complet de l'employé
        email: '', // Le backend ne fournit pas l'email dans cette réponse
        organization: siteEmployee.employee_organization,
        is_active: siteEmployee.is_active
      }
    })

    console.log('[Plannings][LoadEmployees] Employés chargés:', JSON.stringify(employees.value, null, 2))
  } catch (error) {
    console.error('[Plannings][Error] Erreur lors du chargement des employés:', error)
    employees.value = []
  }
}

const loadPointages = async () => {
  loadingTabs.value.pointages = true
  try {
    const response = await timesheetsApi.getTimesheets({
      schedule: itemId.value,
      page: 1,
      page_size: 10
    })
    pointages.value = response.data.results
  } catch (error) {
    console.error('[PlanningDetail][LoadPointages] Erreur lors du chargement des pointages:', error)
  } finally {
    loadingTabs.value.pointages = false
  }
}

const loadAnomalies = async () => {
  loadingTabs.value.anomalies = true
  try {
    const response = await timesheetsApi.getAnomalies({
      schedule: itemId.value,
      page: 1,
      page_size: 10
    })
    anomalies.value = response.data.results
  } catch (error) {
    console.error('[PlanningDetail][LoadAnomalies] Erreur lors du chargement des anomalies:', error)
  } finally {
    loadingTabs.value.anomalies = false
  }
}

const loadReports = async () => {
  loadingTabs.value.reports = true
  try {
    // Temporairement, on retourne un tableau vide en attendant l'implémentation de l'API
    reports.value = []
  } catch (_error) {
    console.error('[PlanningDetail][LoadReports] Erreur lors du chargement des rapports:', _error)
  } finally {
    loadingTabs.value.reports = false
  }
}

const loadTabData = async (tab: string) => {
  switch (tab) {
    case 'employees':
      if (item.value?.site) {
        await loadEmployees(item.value.site)
      }
      break
    case 'pointages':
      await loadPointages()
      break
    case 'anomalies':
      await loadAnomalies()
      break
    case 'reports':
      await loadReports()
      break
  }
}

const toggleUserStatus = async (user: any) => {
  try {
    // La fonction toggleUserStatus nécessite l'ID de l'utilisateur et le nouveau statut (inverse du statut actuel)
    await usersApi.toggleUserStatus(user.employee, !user.is_active)

    // Recharger les données des employés après la modification
    if (item.value?.site) {
      await loadEmployees(item.value.site)
    }

    // Afficher un message de succès
    showSuccess(user.is_active ? t('profile.userDeactivated') : t('profile.userActivated'))
  } catch (error) {
    console.error('[PlanningDetail][ToggleUserStatus] Erreur lors de la modification du statut de l\'utilisateur:', error)
    showError(user.is_active ? t('profile.userDeactivationError') : t('profile.userActivationError'))
  }
}

const confirmDeleteUser = (user: any) => {
  const state = dialogState.value as DialogState
  state.show = true
  state.title = t('common.deleteConfirmation')
  state.message = t('users.deleteUserConfirmation').replace('cet utilisateur', user.employee_name)
  state.confirmText = t('common.delete')
  state.cancelText = t('common.cancel')
  state.confirmColor = 'error'
  state.loading = false
  state.onConfirm = async () => {
    state.loading = true
    try {
      await usersApi.deleteUser(user.employee)

      // Recharger les données des employés après la suppression
      if (item.value?.site) {
        await loadEmployees(item.value.site)
      }

      showSuccess('Utilisateur supprimé avec succès')
    } catch (error) {
      console.error('[PlanningDetail][DeleteUser] Erreur lors de la suppression de l\'utilisateur:', error)
      showError('Erreur lors de la suppression de l\'utilisateur')
    } finally {
      state.show = false
      state.loading = false
    }
  }
}

const handleToggleStatus = async (item: TableItem) => {
  try {
    // Déterminer si nous sommes dans l'onglet des employés
    if (activeTab.value === 'employees') {
      // Si oui, utiliser toggleUserStatus
      await toggleUserStatus(item)
    } else {
      // Sinon, mettre à jour le planning comme avant
      await schedulesApi.updateSchedule(itemId.value, item.id, {
        is_active: !item.is_active
      })
      showSuccess('Statut du planning mis à jour avec succès')
    }
  } catch (error) {
    console.error('[PlanningDetail][ToggleStatus] Erreur lors de la mise à jour du statut:', error)
    showError('Erreur lors de la mise à jour du statut')
  }
}

const handleDelete = async (item: TableItem) => {
  try {
    // Déterminer si nous sommes dans l'onglet des employés
    if (activeTab.value === 'employees') {
      // Si oui, utiliser confirmDeleteUser
      confirmDeleteUser(item)
    } else {
      // Sinon, supprimer le planning comme avant
      await schedulesApi.deleteSchedule(item.id)
      showSuccess('Planning supprimé avec succès')
      router.push({ name: 'plannings' })
    }
  } catch (error) {
    console.error('[PlanningDetail][Delete] Erreur lors de la suppression:', error)
    showError('Erreur lors de la suppression')
  }
}

// Watch pour le changement d'onglet
watch(activeTab, async (newTab) => {
  if (newTab !== 'details') {
    await loadTabData(newTab)
  }
})

// Lifecycle hooks
onMounted(async () => {
  await loadData()
})

// Watch for route changes
watch(
  () => route.params.id,
  async (newId, oldId) => {
    if (newId !== oldId) {
      await loadData()
    }
  }
)
</script>

<style scoped>
.white-space-pre-wrap {
  white-space: pre-wrap;
}

/* Style des icônes dans la liste */
:deep(.v-list-item) {
  padding: 12px 16px;
}

:deep(.v-list-item .v-icon) {
  color: #00346E !important;
  margin-right: 12px;
  font-size: 20px;
}

:deep(.v-list-item-title) {
  font-size: 0.875rem;
  font-weight: 500;
  color: rgba(0, 0, 0, 0.87);
  margin-bottom: 4px;
}

:deep(.v-list-item-subtitle) {
  font-size: 1rem;
  color: rgba(0, 0, 0, 0.87);
  font-weight: 400;
}

/* Style du bouton retour */
:deep(.v-btn.mr-4) {
  color: #00346E !important;
  border: 1px solid #00346E !important;
  margin-right: 16px !important;
  transition: all 0.3s ease;
}

:deep(.v-btn.mr-4 .v-icon) {
  color: #00346E !important;
  opacity: 1 !important;
}

:deep(.v-btn.mr-4:hover) {
  background-color: #00346E !important;
  color: white !important;
}

:deep(.v-btn.mr-4:hover .v-icon) {
  color: white !important;
}

/* Style des onglets */
:deep(.v-tabs) {
  border-bottom: 1px solid rgba(0, 0, 0, 0.12);
}

:deep(.v-tab) {
  text-transform: none !important;
  font-weight: 500 !important;
  letter-spacing: normal !important;
}

:deep(.v-tab--selected) {
  color: #00346E !important;
}

:deep(.v-tab:hover) {
  color: #00346E !important;
  opacity: 0.8;
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
</style>