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
        :color="isOwnProfile ? 'grey' : 'primary'"
        prepend-icon="mdi-pencil"
        class="mr-2"
        :disabled="isOwnProfile"
        @click.stop="editItem"
      >
        {{ $t('common.edit') }}
        <v-tooltip v-if="isOwnProfile" activator="parent">
          {{ $t('common.cannotEditOwnAccount') }}
        </v-tooltip>
      </v-btn>
      <v-btn
        v-if="canCreateDelete && !isOwnProfile"
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
          <v-tab value="sites">{{ $t('sites.title') }}</v-tab>
          <v-tab value="plannings">{{ $t('plannings.title') }}</v-tab>
          <v-tab value="pointages">{{ $t('timesheets.title') }}</v-tab>
          <v-tab value="anomalies">{{ $t('anomalies.title') }}</v-tab>
          <v-tab value="reports">{{ $t('reports.title') }}</v-tab>
        </v-tabs>

        <v-card-text>
          <v-window v-model="activeTab" :reverse="reverse">
            <!-- Onglet Informations -->
            <v-window-item value="details">
              <v-card class="elevation-1">
                <v-toolbar flat>
                  <v-toolbar-title>{{ $t("dashboard.informations") }}</v-toolbar-title>
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
                                  :active-label="field.activeLabel"
                                  :inactive-label="field.inactiveLabel"
                                />
                              </template>
                              <template v-else-if="field.type === 'role'">
                                <v-chip
                                  :color="item[field.key] === 'MANAGER' ? 'primary' : 'success'"
                                  size="small"
                                >
                                  {{ item[field.key] === 'MANAGER' ? $t('users.roles.MANAGER') : $t('users.roles.EMPLOYEE') }}
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
                            <template v-for="(stat) in statistics" :key="stat.label">
                              <v-col :cols="12 / statistics.length" class="text-center">
                                <div class="text-h4">{{ stat.value }}</div>
                                <div class="text-subtitle-1">{{ stat.label }}</div>
                              </v-col>
                            </template>
                          </v-row>
                        </v-card-text>
                      </v-card>
                    </v-col>
                  </v-row>
                </v-card-text>
              </v-card>
            </v-window-item>

            <!-- Autres onglets à intégrer au besoin... -->
            <!-- Onglet Sites -->
            <v-window-item value="sites">
              <v-row v-if="loadingTabs.sites">
                <v-col cols="12" class="text-center">
                  <v-progress-circular indeterminate color="primary"></v-progress-circular>
                </v-col>
              </v-row>
              <DataTable
                v-else
                :title="$t('sites.title')"
                :headers="sitesHeaders"
                :items="sites"
                :no-data-text="$t('dashboard.noSitesFound', 'Aucun site trouvé')"
                :detail-route="'/dashboard/sites/:id'"
                :edit-route="'/dashboard/sites/:id/edit'"
                @toggle-status="handleToggleStatus"
                @delete="handleDelete"
                @row-click="(item: TableItem) => router.push(`/dashboard/sites/${item.id}`)"
              >

                <template #item.address="{ item: rowItem }">
                  <AddressWithMap
                    :address="rowItem.address"
                    :postal-code="rowItem.postal_code"
                    :city="rowItem.city"
                    :country="rowItem.country"
                  />
                </template>

                <template #item.created_at="{ item: rowItem }">
                  {{ formatDate(rowItem.created_at) }}
                </template>

                <template #item.actions="{ item: rowItem }">
                  <v-btn
                    v-if="canEdit"
                    icon
                    variant="text"
                    size="small"
                    color="primary"
                    :to="`/dashboard/sites/${rowItem.id}`"
                    @click.stop
                  >
                    <v-icon>mdi-eye</v-icon>
                    <v-tooltip activator="parent">{{ $t('common.viewDetails') }}</v-tooltip>
                  </v-btn>
                  <v-btn
                    v-if="canCreateDelete && !isManager"
                    icon
                    variant="text"
                    size="small"
                    color="error"
                    @click.stop="confirmDelete(rowItem)"
                  >
                    <v-icon>mdi-delete</v-icon>
                    <v-tooltip activator="parent">{{ $t('sites.deleteSite') }}</v-tooltip>
                  </v-btn>
                </template>
              </DataTable>
            </v-window-item>

            <!-- Onglet Plannings -->
            <v-window-item value="plannings">
              <v-row v-if="loadingTabs.plannings">
                <v-col cols="12" class="text-center">
                  <v-progress-circular indeterminate color="primary"></v-progress-circular>
                </v-col>
              </v-row>
              <DataTable
                v-else
                :title="$t('plannings.title')"
                :headers="planningsHeaders"
                :items="plannings"
                :no-data-text="$t('dashboard.noSchedulesFound', 'Aucun planning trouvé')"
                :detail-route="'/dashboard/plannings/:id'"
                :edit-route="'/dashboard/plannings/:id/edit'"
                :is-manager="isManager"
                @toggle-status="confirmTogglePlanningStatus"
                @delete="confirmDeletePlanning"
                @row-click="(item: TableItem) => router.push(`/dashboard/plannings/${item.id}`)"
              >
                <template #item.site_name="{ item: rowItem }">
                  {{ rowItem.site_name }}
                </template>
                <template #item.employees="{ item: rowItem }">
                  <span v-for="(e, i) in rowItem.assigned_employees" :key="e.id">
                    {{ e.employee_name }}<span v-if="i < rowItem.assigned_employees.length - 1">, </span>
                  </span>
                </template>
                <template #item.schedule_type="{ item: rowItem }">
                  {{ rowItem.schedule_type }}
                </template>
              </DataTable>
            </v-window-item>

            <!-- Onglet Pointages -->
            <v-window-item value="pointages">
              <v-row v-if="loadingTabs.pointages">
                <v-col cols="12" class="text-center">
                  <v-progress-circular indeterminate color="primary"></v-progress-circular>
                </v-col>
              </v-row>
              <DataTable
                v-else
                :title="$t('timesheets.title')"
                :headers="pointagesHeaders"
                :items="pointages"
                :no-data-text="$t('dashboard.noTimesheetsFound', 'Aucun pointage trouvé')"
              >
                <template #item.entry_type="{ item: rowItem }">
                  {{ $t(`timesheets.entryTypes.${rowItem.entry_type}`) }}
                </template>
                <template #item.timestamp="{ item: rowItem }">
                  {{ format(new Date(rowItem.timestamp), 'dd/MM/yyyy HH:mm:ss', { locale: fr }) }}
                </template>
              </DataTable>
            </v-window-item>

            <!-- Onglet Anomalies -->
            <v-window-item value="anomalies">
              <v-row v-if="loadingTabs.anomalies">
                <v-col cols="12" class="text-center">
                  <v-progress-circular indeterminate color="primary"></v-progress-circular>
                </v-col>
              </v-row>
              <DataTable
                v-else
                :title="$t('anomalies.title')"
                :headers="anomaliesHeaders"
                :items="anomalies"
                :no-data-text="$t('dashboard.noAnomaliesFound', 'Aucune anomalie trouvée')"
              >
                <template #item.status="{ item: rowItem }">
                  <v-chip
                    :color="getAnomalyStatusColor(rowItem.status)"
                    size="small"
                  >
                    {{ getAnomalyStatusLabel(rowItem.status) }}
                  </v-chip>
                </template>

                <template #item.created_at="{ item: rowItem }">
                  {{ formatDate(rowItem.created_at) }}
                </template>
              </DataTable>
            </v-window-item>

            <!-- Onglet Rapports -->
            <v-window-item value="reports">
              <v-row v-if="loadingTabs.reports">
                <v-col cols="12" class="text-center">
                  <v-progress-circular indeterminate color="primary"></v-progress-circular>
                </v-col>
              </v-row>
              <DataTable
                v-else
                :title="$t('reports.title')"
                :headers="reportsHeaders"
                :items="reports"
                :no-data-text="$t('dashboard.noReportsFound', 'Aucun rapport trouvé')"
              >
                <template #item.created_at="{ item: rowItem }">
                  {{ formatDate(rowItem.created_at) }}
                </template>

                <template #item.actions="{}">
                  <v-btn
                    icon
                    variant="text"
                    size="small"
                    color="primary"
                    @click.stop="downloadReport"
                  >
                    <v-icon>mdi-download</v-icon>
                    <v-tooltip activator="parent">{{ $t('common.downloadReport') }}</v-tooltip>
                  </v-btn>
                </template>
              </DataTable>
            </v-window-item>
          </v-window>
        </v-card-text>
      </v-card>
    </template>

    <!-- Boîte de dialogue de confirmation -->
    <ConfirmDialog />
  </v-container>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Title } from '@/components/typography'
import { formatPhoneNumber } from '@/utils/formatters'
import { format } from 'date-fns'
import { fr } from 'date-fns/locale'
import { useAuthStore } from '@/stores/auth'
import {
  usersApi,
  timesheetsApi,
  sitesApi,
  schedulesApi } from '@/services/api'
import StatusChip from '@/components/common/StatusChip.vue'
import DataTable, { type TableItem } from '@/components/common/DataTable.vue'
import AddressWithMap from '@/components/common/AddressWithMap.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import { useConfirmDialog } from '@/utils/dialogs'
import type { DialogState } from '@/utils/dialogs'
import { useDetailTableHeaders } from '@/composables/useDetailTableHeaders'

// Type definitions
interface Field {
  key: string;
  label: string;
  icon: string;
  type?: 'status' | 'role' | 'default' | 'date';
  activeLabel?: string;
  inactiveLabel?: string;
  format?: 'phone' | 'date' | 'role' | 'scan_preference';
  dateFormat?: string;
  suffix?: string;
}

interface User {
  id: number;
  role: string;
  first_name: string;
  last_name: string;
  organization?: any;
  [key: string]: any;
}

interface Planning {
  id: number;
  site_name: string;
  assigned_employees: Array<{ id: number; employee_name: string }>;
  schedule_type: string;
  is_active: boolean;
}

// Props
const showBackButton = ref(true)

// State variables
const router = useRouter()
const route = useRoute()
const loading = ref(true)
const loadingTabs = ref({
  sites: false,
  plannings: false,
  pointages: false,
  anomalies: false,
  reports: false
})
const item = ref<any>({})
const statistics = ref<Array<{ label: string; value: number }>>([])
const auth = useAuthStore()
const activeTab = ref('details')
const previousTab = ref('details')
const reverse = ref(false)
const { dialogState, showConfirmDialog } = useConfirmDialog()

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

// Données pour les tableaux
const sites = ref<any[]>([])
const plannings = ref<any[]>([])
const pointages = ref<any[]>([])
const anomalies = ref<any[]>([])
const reports = ref<any[]>([])

const { t } = useI18n()

// Insert shared headers hook
const { sitesHeaders, planningsHeaders, pointagesHeaders, anomaliesHeaders, reportsHeaders } = useDetailTableHeaders()

const tabOrder = ['details', 'sites', 'plannings', 'pointages', 'anomalies', 'reports']

watch(activeTab, (newTab, oldTab) => {
  if (!oldTab || !newTab) return

  const oldIndex = tabOrder.indexOf(oldTab)
  const newIndex = tabOrder.indexOf(newTab)

  reverse.value = newIndex < oldIndex
  previousTab.value = oldTab
})

// Configuration des rôles
const roleLabels: Record<string, string> = {
  'SUPER_ADMIN': t('users.roles.SUPER_ADMIN'),
  'ADMIN': t('users.roles.ADMIN'),
  'MANAGER': t('users.roles.MANAGER'),
  'EMPLOYEE': t('users.roles.EMPLOYEE')
}

const scanPreferenceLabels: Record<string, string> = {
  'BOTH': t('profile.scanPreferences.BOTH'),
  'QR_ONLY': t('profile.scanPreferences.QR_ONLY'),
  'NFC_ONLY': t('profile.scanPreferences.NFC_ONLY')
}

// Computed properties
const itemId = computed(() => Number(route.params.id))

const title = computed(() => t("users.userDetails", "Détails de l'utilisateur"))

const backRoute = computed(() => '/dashboard/admin/users')

// Computed pour vérifier si c'est le profil de l'utilisateur connecté
const isOwnProfile = computed(() => {
  return (auth.user as User)?.id === itemId.value
})

const isManager = computed(() => {
  return auth.user?.role === 'MANAGER'
})

const canManageStatus = computed(() => {
  return !isManager.value && (auth.user?.role === 'SUPER_ADMIN' || auth.user?.role === 'ADMIN')
})

const canEdit = computed(() => {
  const role = auth.user?.role
  return role === 'SUPER_ADMIN' || role === 'ADMIN' || role === 'MANAGER'
})

const canCreateDelete = computed(() => {
  const role = auth.user?.role
  return role === 'SUPER_ADMIN' || role === 'ADMIN'
})

const displayFields = computed((): Field[] => {
  const fields: Field[] = [
    { key: 'employee_id', label: t('common.id'), icon: 'mdi-card-account-details', type: 'default' },
    { key: 'first_name', label: t('common.firstName'), icon: 'mdi-account', type: 'default' },
    { key: 'last_name', label: t('common.lastName'), icon: 'mdi-account-box', type: 'default' },
    { key: 'email', label: t('common.email'), icon: 'mdi-email', type: 'default' },
    { key: 'phone_number', label: t('common.phone'), icon: 'mdi-phone', type: 'default', format: 'phone' },
    { key: 'role', label: t('common.role'), icon: 'mdi-badge-account', type: 'default', format: 'role' }
  ]

  return [
    ...fields,
    { key: 'scan_preference', label: t('profile.scanPreference'), icon: 'mdi-qrcode-scan', type: 'default', format: 'scan_preference' },
    { key: 'simplified_mobile_view', label: t('profile.simplifiedView'), icon: 'mdi-cellphone',
      type: 'status',
      activeLabel: t('common.activate'),
      inactiveLabel: t('common.deactivate')
    },
    { key: 'date_joined', label: t('users.dateJoined'), icon: 'mdi-calendar', type: 'default', format: 'date', dateFormat: 'dd/MM/yyyy HH:mm' },
    {
      key: 'is_active',
      label: t('common.status'),
      icon: 'mdi-check-circle',
      type: 'status',
      activeLabel: t('users.active'),
      inactiveLabel: t('users.inactive')
    }
  ]
})

// Méthodes
const loadData = async () => {
  loading.value = true
  try {
    const response = await usersApi.getUser(itemId.value);
    item.value = response.data;
    const stats = await usersApi.getUserStatistics(itemId.value);
    statistics.value = [
      { label: t('dashboard.totalHours', 'Heures totales'), value: stats.data.total_hours || 0 },
      { label: t('anomalies.title'), value: stats.data.anomalies || 0 }
    ];

    // Charger les données de l'onglet actif
    await loadTabData(activeTab.value);
  } catch (error) {
    console.error('[UserDetail][LoadData] Erreur lors du chargement des données:', error)
  } finally {
    loading.value = false
  }
}

// Méthodes de chargement des données pour chaque onglet
const loadSites = async () => {
  loadingTabs.value.sites = true;
  try {
    const response = await usersApi.getUserSites(itemId.value, {
      page: 1,
      page_size: 10
    });
    console.log('[UserDetail][LoadSites] Réponse complète:', response);
    // Vérifier si la réponse contient des résultats ou si c'est un tableau direct
    if (response.data && Array.isArray(response.data)) {
      sites.value = response.data;
    } else if (response.data && response.data.results) {
      sites.value = response.data.results;
    } else {
      console.error('[UserDetail][LoadSites] Format de réponse inattendu:', response.data);
      sites.value = [];
    }
  } catch (error) {
    console.error('[UserDetail][LoadSites] Erreur lors du chargement des sites:', error);
    showError(t('profile.loadError') + ' ' + t('sites.title'));
    sites.value = [];
  } finally {
    loadingTabs.value.sites = false;
  }
};

const loadPlannings = async () => {
  loadingTabs.value.plannings = true;
  try {
    const response = await usersApi.getUserSchedules(itemId.value, {
      page: 1,
      page_size: 10
    });
    console.log('[UserDetail][LoadPlannings] Réponse complète:', response);
    // Vérifier si la réponse contient des résultats ou si c'est un tableau direct
    if (response.data && Array.isArray(response.data)) {
      plannings.value = response.data;
    } else if (response.data && response.data.results) {
      plannings.value = response.data.results;
    } else {
      console.error('[UserDetail][LoadPlannings] Format de réponse inattendu:', response.data);
      plannings.value = [];
    }
  } catch (error) {
    console.error('[UserDetail][LoadPlannings] Erreur lors du chargement des plannings:', error);
    showError(t('profile.loadError') + ' ' + t('plannings.title'));
    plannings.value = [];
  } finally {
    loadingTabs.value.plannings = false;
  }
};

const loadPointages = async () => {
  loadingTabs.value.pointages = true;
  try {
    const response = await timesheetsApi.getTimesheets({
      employee: itemId.value,
      page: 1,
      page_size: 10
    });
    console.log('[UserDetail][LoadPointages] Réponse complète:', response);
    // Vérifier si la réponse contient des résultats ou si c'est un tableau direct
    if (response.data && Array.isArray(response.data)) {
      pointages.value = response.data;
    } else if (response.data && response.data.results) {
      pointages.value = response.data.results;
    } else {
      console.error('[UserDetail][LoadPointages] Format de réponse inattendu:', response.data);
      pointages.value = [];
    }
  } catch (error) {
    console.error('[UserDetail][LoadPointages] Erreur lors du chargement des pointages:', error);
    showError(t('profile.loadError') + ' ' + t('timesheets.title'));
    pointages.value = [];
  } finally {
    loadingTabs.value.pointages = false;
  }
};

const loadAnomalies = async () => {
  loadingTabs.value.anomalies = true;
  try {
    const response = await timesheetsApi.getAnomalies({
      employee: itemId.value,
      page: 1,
      page_size: 10
    });
    console.log('[UserDetail][LoadAnomalies] Réponse complète:', response);
    // Vérifier si la réponse contient des résultats ou si c'est un tableau direct
    if (response.data && Array.isArray(response.data)) {
      anomalies.value = response.data;
    } else if (response.data && response.data.results) {
      anomalies.value = response.data.results;
    } else {
      console.error('[UserDetail][LoadAnomalies] Format de réponse inattendu:', response.data);
      anomalies.value = [];
    }
  } catch (error) {
    console.error('[UserDetail][LoadAnomalies] Erreur lors du chargement des anomalies:', error);
    showError(t('profile.loadError') + ' ' + t('anomalies.title'));
    anomalies.value = [];
  } finally {
    loadingTabs.value.anomalies = false;
  }
};

const loadReports = async () => {
  loadingTabs.value.reports = true;
  try {
    const response = await usersApi.getUserReports(itemId.value, {
      page: 1,
      page_size: 10
    });
    console.log('[UserDetail][LoadReports] Réponse complète:', response);
    // Vérifier si la réponse contient des résultats ou si c'est un tableau direct
    if (response.data && Array.isArray(response.data)) {
      reports.value = response.data;
    } else if (response.data && response.data.results) {
      reports.value = response.data.results;
    } else {
      console.error('[UserDetail][LoadReports] Format de réponse inattendu:', response.data);
      reports.value = [];
    }
  } catch (error) {
    console.error('[UserDetail][LoadReports] Erreur lors du chargement des rapports:', error);
    showError(t('profile.loadError') + ' ' + t('reports.title'));
    reports.value = [];
  } finally {
    loadingTabs.value.reports = false;
  }
};

// Fonction pour charger les données en fonction de l'onglet actif
const loadTabData = async (tab: string) => {
  switch (tab) {
    case 'sites':
      await loadSites();
      break;
    case 'plannings':
      await loadPlannings();
      break;
    case 'pointages':
      await loadPointages();
      break;
    case 'anomalies':
      await loadAnomalies();
      break;
    case 'reports':
      await loadReports();
      break;
  }
};

// Watch pour le changement d'onglet
watch(activeTab, async (newTab) => {
  if (newTab !== 'details') {
    await loadTabData(newTab);
  }
});

const formatFieldValue = (field: Field, value: any) => {
  if (!value) return ''
  if (field.format === 'phone') return formatPhoneNumber(value)
  if (field.format === 'date') {
    try {
      const date = new Date(value)
      return format(date, field.dateFormat || 'dd/MM/yyyy', { locale: fr })
    } catch (error) {
      console.error('[UserDetail][FormatDate] Erreur lors du formatage de la date:', error)
      return value
    }
  }
  if (field.format === 'role') return roleLabels[value] || value
  if (field.format === 'scan_preference') return scanPreferenceLabels[value] || value
  if (field.suffix) return `${value}${field.suffix}`
  return value
}

const editItem = () => {
  if (isOwnProfile.value) {
    return
  }

  // Ajouter des logs pour déboguer
  console.log('[UserDetail][Edit] Redirection vers la page d\'édition avec les données:', JSON.stringify(item.value))

  router.push(`/dashboard/admin/users/${itemId.value}/edit`).catch(error => {
    console.error('[UserDetail][Edit] Erreur lors de la redirection:', error)
  })
}

// Méthodes de confirmation
const confirmDelete = (site: any) => {
  showConfirmDialog({
    title: t('sites.deleteSite'),
    message: t('sites.deleteConfirmation'),
    confirmText: t('common.delete'),
    confirmColor: 'error',
    onConfirm: () => handleDelete(site)
  })
}

const confirmTogglePlanningStatus = (planning: any) => {
  const state = dialogState.value as DialogState
  state.show = true
  state.title = planning.is_active ? t('common.deactivate') : t('common.activate')
  state.message = planning.is_active ? t('sites.deactivateConfirmation') : t('sites.activateConfirmation')
  state.confirmText = planning.is_active ? t('common.deactivate') : t('common.activate')
  state.cancelText = t('common.cancel')
  state.confirmColor = planning.is_active ? 'warning' : 'success'
  state.loading = false
  state.onConfirm = async () => {
    state.loading = true
    try {
      await togglePlanningStatus(planning)
    } finally {
      state.show = false
      state.loading = false
    }
  }
}

const formatDate = (date: string) => {
  return format(new Date(date), 'dd/MM/yyyy HH:mm', { locale: fr })
}

const getPointageStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    'PENDING': 'warning',
    'VALIDATED': 'success',
    'REJECTED': 'error'
  }
  return colors[status] || 'grey'
}

const getPointageStatusLabel = (status: string) => {
  const labels: Record<string, string> = {
    'PENDING': t('timesheets.statuses.PENDING'),
    'VALIDATED': t('timesheets.statuses.VALIDATED'),
    'REJECTED': t('timesheets.statuses.REJECTED')
  }
  return labels[status] || status
}

const getAnomalyStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    'PENDING': 'warning',
    'RESOLVED': 'success',
    'REJECTED': 'error'
  }
  return colors[status] || 'grey'
}

const getAnomalyStatusLabel = (status: string) => {
  const labels: Record<string, string> = {
    'PENDING': t('anomalies.anomalyStatuses.PENDING'),
    'RESOLVED': t('anomalies.anomalyStatuses.RESOLVED'),
    'REJECTED': t('anomalies.anomalyStatuses.IGNORED')
  }
  return labels[status] || status
}

const handleToggleStatus = async (site: any) => {
  try {
    await sitesApi.updateSite(site.id, { is_active: !site.is_active })
    // Mettre à jour le site dans la liste
    const index = sites.value.findIndex((s: any) => s.id === site.id)
    if (index !== -1) {
      sites.value[index].is_active = !site.is_active
    }
    showSuccess(site.is_active ? t('profile.statusUpdated') : t('profile.statusUpdated'))
  } catch (error) {
    console.error('[UserDetail][HandleToggleStatus] Erreur lors de la mise à jour du statut:', error)
    showError(t('profile.statusUpdateError'))
  }
}

const handleDelete = async (site: any) => {
  try {
    await sitesApi.deleteSite(site.id)
    // Retirer le site de la liste
    sites.value = sites.value.filter((s: any) => s.id !== site.id)
    showSuccess(t('profile.siteDeleted'))
  } catch (error) {
    console.error('[UserDetail][HandleDelete] Erreur lors de la suppression:', error)
    showError(t('profile.deleteError') + ' ' + t('sites.title'))
  }
}

const downloadReport = async () => {
  try {
    // Implémentation à faire
    showSuccess(t('profile.downloadStarted'))
  } catch (error) {
    console.error('[UserDetail][DownloadReport] Erreur lors du téléchargement du rapport:', error)
    showError(t('profile.downloadError'))
  }
}

// Méthodes pour l'onglet plannings
const navigateToPlanning = (planning: any) => {
  router.push({
    name: 'PlanningEdit',
    params: { id: planning.id }
  })
}

const viewPlanningDetails = (planning: any) => {
  router.push({
    name: 'Plannings',
    query: { view: planning.id }
  })
}

const togglePlanningStatus = async (planning: any) => {
  try {
    await schedulesApi.updateSchedule(planning.site, planning.id, {
      is_active: !planning.is_active
    })

    // Mettre à jour le planning dans la liste locale
    const index = plannings.value.findIndex((p: any) => p.id === planning.id)
    if (index !== -1) {
      plannings.value[index].is_active = !planning.is_active
    }

    showSuccess(t('profile.statusUpdated'))
  } catch (error) {
    console.error('[UserDetail][TogglePlanningStatus] Erreur lors du changement de statut:', error)
    showError(t('profile.statusUpdateError'))
  }
}

const confirmDeletePlanning = (planning: any) => {
  const state = dialogState.value as DialogState
  state.show = true
  state.title = t('plannings.deletePlanning')
  state.message = t('plannings.deletePlanningConfirmation')
  state.confirmText = t('common.delete')
  state.cancelText = t('common.cancel')
  state.confirmColor = 'error'
  state.loading = false
  state.onConfirm = async () => {
    state.loading = true
    try {
      await deletePlanning(planning)
    } finally {
      state.show = false
      state.loading = false
    }
  }
}

const deletePlanning = async (planning: any) => {
  try {
    await schedulesApi.deleteSchedule(planning.id)

    // Retirer le planning de la liste
    plannings.value = plannings.value.filter((p: any) => p.id !== planning.id)

    showSuccess(t('profile.planningDeleted'))
  } catch (error) {
    console.error('[UserDetail][DeletePlanning] Erreur lors de la suppression:', error)
    showError(t('profile.deleteError') + ' ' + t('plannings.title'))
  }
}

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