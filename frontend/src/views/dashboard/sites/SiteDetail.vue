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
                  <v-toolbar-title>{{ $t('dashboard.informations') }}</v-toolbar-title>
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
                              <!-- Adresse avec carte -->
                              <template v-if="field.type === 'address' && isAddressField(field)">
                                <AddressWithMap
                                  :address="item[field.address]"
                                  :postal-code="item[field.postalCode]"
                                  :city="item[field.city]"
                                  :country="item[field.country]"
                                />
                              </template>

                              <!-- Statut avec puce -->
                              <template v-else-if="field.type === 'status'">
                                <StatusChip
                                  :status="item[field.key]"
                                  :active-label="$t('dashboard.fieldactivelabel')"
                                  :inactive-label="$t('dashboard.fieldinactivelabel')"
                                />
                              </template>

                              <!-- Valeur par défaut -->
                              <template v-else>
                                {{ formatFieldValue(field, item[field.key]) }}
                              </template>
                            </v-list-item-subtitle>
                          </v-list-item>
                        </template>
                      </v-list>
                    </v-col>

                    <v-col cols="12" md="6">
                      <!-- QR Code -->
                      <v-card class="qr-code-card" variant="outlined">
                        <v-card-title class="d-flex align-center">
                          <v-icon icon="mdi-qrcode" class="mr-2"></v-icon>
                          {{ $t('sites.qrCode') }}
                        </v-card-title>
                        <v-card-text class="text-center">
                          <div v-if="item.qr_code" class="qr-code-container">
                            <v-img
                              :src="item.qr_code"
                              width="400"
                              height="400"
                              class="mx-auto mb-4"
                            ></v-img>
                            <div class="d-flex gap-2">
                              <v-btn
                                color="#00346E"
                                prepend-icon="mdi-download"
                                @click="downloadQRCode"
                              >
                                {{ $t('dashboard.tlcharger') }}
                              </v-btn>
                              <v-btn
                                color="#F78C48"
                                prepend-icon="mdi-refresh"
                                @click="generateQRCode"
                              >
                                {{ $t('dashboard.rgnrer') }}
                              </v-btn>
                            </div>
                          </div>
                          <v-progress-circular
                            v-else
                            indeterminate
                            color="primary"
                          ></v-progress-circular>
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
                :no-data-text="$t('dashboard.aucun_employ_trouv')"
                :detail-route="'/dashboard/admin/users/:id'"
                :edit-route="'/dashboard/admin/users/:id/edit'"
                @toggle-status="(item: TableItem) => handleToggleStatus('employees', item)"
                @delete="(item: TableItem) => handleDelete('employees', item)"
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
                    <v-tooltip activator="parent">{{ $t('common.viewDetails') }}</v-tooltip>
                  </v-btn>
                  <v-btn
                    v-if="canCreateDelete"
                    icon
                    variant="text"
                    size="small"
                    color="error"
                    @click.stop="unassignEmployeeFromSite(rowItem.id)"
                  >
                    <v-icon>mdi-account-remove</v-icon>
                    <v-tooltip activator="parent">{{ $t('common.removeFromSite') }}</v-tooltip>
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
              <v-card v-else>
                <v-toolbar flat>
                  <v-toolbar-title>{{ $t('plannings.title') }}</v-toolbar-title>
                  <v-spacer></v-spacer>
                </v-toolbar>
                <v-data-table
                  :headers="planningsHeaders"
                  :items="item.schedules || []"
                  :no-data-text="$t('dashboard.aucun_planning_trouv')"
                  class="elevation-1"
                  @click:row="(item: any) => router.push(`/dashboard/plannings/${item.id}`)"
                >
                  <!-- Site -->
                  <template #item.site_name="{ item: rowItem }">
                    {{ rowItem.site_name }}
                  </template>

                  <!-- Employés -->
                  <template #item.employees="{ item: rowItem }">
                    <v-chip-group>
                      <v-chip
                        v-for="employee in rowItem.assigned_employees"
                        :key="employee.id"
                        size="small"
                        color="primary"
                        variant="outlined"
                      >
                        {{ employee.employee_name }}
                      </v-chip>
                      <v-chip
                        v-if="!rowItem.assigned_employees?.length"
                        size="small"
                        color="grey"
                        variant="outlined"
                      >
                        {{ $t('plannings.noEmployees') }}
                      </v-chip>
                    </v-chip-group>
                  </template>

                  <!-- Type de planning -->
                  <template #item.schedule_type="{ item: rowItem }">
                    <v-chip
                      :color="rowItem.schedule_type === 'FIXED' ? 'primary' : 'secondary'"
                      size="small"
                    >
                      {{ rowItem.schedule_type === 'FIXED' ? $t('plannings.fixed') : $t('plannings.frequency') }}
                    </v-chip>
                  </template>

                  <!-- Actions -->
                  <template #item.actions="{ item: rowItem }">
                    <v-btn
                      icon
                      variant="text"
                      size="small"
                      color="primary"
                      @click.stop="viewPlanningDetails(rowItem)"
                    >
                      <v-icon>mdi-eye</v-icon>
                      <v-tooltip activator="parent">{{ $t('common.viewDetails') }}</v-tooltip>
                    </v-btn>
                    <v-btn
                      icon
                      variant="text"
                      size="small"
                      color="primary"
                      @click.stop="navigateToPlanning(rowItem)"
                    >
                      <v-icon>mdi-pencil</v-icon>
                      <v-tooltip activator="parent">{{ $t('common.edit') }}</v-tooltip>
                    </v-btn>
                    <v-btn
                      icon
                      variant="text"
                      size="small"
                      color="warning"
                      @click.stop="confirmTogglePlanningStatus(rowItem)"
                    >
                      <v-icon>{{ rowItem.is_active ? 'mdi-domain' : 'mdi-domain-off' }}</v-icon>
                      <v-tooltip activator="parent">{{ rowItem.is_active ? $t('common.deactivate') : $t('common.activate') }}</v-tooltip>
                    </v-btn>
                    <v-btn
                      icon
                      variant="text"
                      size="small"
                      color="error"
                      @click.stop="confirmDeletePlanning(rowItem)"
                    >
                      <v-icon>mdi-delete</v-icon>
                      <v-tooltip activator="parent">{{ $t('common.delete') }}</v-tooltip>
                    </v-btn>
                  </template>
                </v-data-table>
              </v-card>
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
                :no-data-text="$t('dashboard.aucun_pointage_trouv')"
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

                <template #item.actions="{ item: rowItem }">
                  <v-btn
                    icon
                    variant="text"
                    size="small"
                    color="primary"
                    @click.stop="downloadReport(rowItem.id)"
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
// @ts-nocheck
import { useI18n } from 'vue-i18n'
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Title } from '@/components/typography'
import { generateStyledQRCode } from '@/utils/qrcode'
import { format } from 'date-fns'
import { fr } from 'date-fns/locale'
import { sitesApi, planningsApi, schedulesApi } from '@/services/api'
import StatusChip from '@/components/common/StatusChip.vue'
import AddressWithMap from '@/components/common/AddressWithMap.vue'
import DataTable, { type TableItem } from '@/components/common/DataTable.vue'
import { useConfirmDialog } from '@/utils/dialogs'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import { useAuthStore } from '@/stores/auth'

// Types
interface Field {
  key: string;
  label: string;
  icon: string;
  type?: 'address' | 'status' | 'default';
  activeLabel?: string;
  inactiveLabel?: string;
  suffix?: string;
}

interface AddressField extends Field {
  type: 'address';
  address: string;
  postalCode: string;
  city: string;
  country: string;
}

type DisplayField = Field | AddressField;

// Extended Site with additional properties needed for UI
interface ExtendedSite {
  id: number;
  name: string;
  nfc_id: string;
  address: string;
  postal_code: string;
  city: string;
  country: string;
  is_active: boolean;
  qr_code?: string;
  download_qr_code?: string;
  manager_name: string;
  organization_name: string;
  [key: string]: any; // Pour les autres propriétés dynamiques
}

// Props
const showBackButton = ref(true)

// State variables
const router = useRouter()
const route = useRoute()
const loading = ref(true)
const loadingTabs = ref({
  employees: false,
  plannings: false,
  pointages: false,
  anomalies: false,
  reports: false
})
const showDeleteDialog = ref(false)
const item = ref<ExtendedSite>({} as ExtendedSite)
const statistics = ref<Array<{ label: string; value: number }>>([])
const activeTab = ref('details')
const previousTab = ref('details')
const reverse = ref(false)
const { showConfirmDialog } = useConfirmDialog()

// Données pour les tableaux
const employees = ref<any[]>([])
const pointages = ref<any[]>([])
const anomalies = ref<any[]>([])
const reports = ref<any[]>([])

const { t } = useI18n()
const authStore = useAuthStore()

// En-têtes des tableaux
const employeesHeaders = [
  { title: t('common.name'), key: 'employee_name' },
  { title: t('common.actions'), key: 'actions', sortable: false }
]

const planningsHeaders = [
  { title: t('common.site'), key: 'site_name', align: 'start' as const },
  { title: t('common.employee'), key: 'employees', align: 'start' as const },
  { title: t('common.type'), key: 'schedule_type', align: 'start' as const },
  { title: t('common.actions'), key: 'actions', sortable: false, align: 'end' as const }
]

const pointagesHeaders = [
  { title: t('common.site'), key: 'site_name' },
  { title: t('timesheets.entryType'), key: 'entry_type' },
  { title: t('timesheets.dateTime', 'Date/Heure'), key: 'timestamp' }
]

const anomaliesHeaders = [
  { title: t('common.employee'), key: 'employee_name' },
  { title: t('common.type'), key: 'type' },
  { title: t('timesheets.dateTime', 'Date/Heure'), key: 'created_at' },
  { title: t('common.status'), key: 'status' }
]

const reportsHeaders = [
  { title: t('common.name'), key: 'name' },
  { title: t('common.type'), key: 'type' },
  { title: t('reports.creationDate', 'Date de création'), key: 'created_at' },
  { title: t('common.actions'), key: 'actions', sortable: false }
]

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

// Configuration des onglets
const tabOrder = ['details', 'employees', 'plannings', 'pointages', 'anomalies', 'reports']

watch(activeTab, (newTab, oldTab) => {
  if (!oldTab || !newTab) return

  const oldIndex = tabOrder.indexOf(oldTab)
  const newIndex = tabOrder.indexOf(newTab)

  reverse.value = newIndex < oldIndex
  previousTab.value = oldTab
})

// Computed properties
const itemId = computed(() => Number(route.params.id))

const title = computed(() => t('sites.siteDetails'))

const backRoute = computed(() => '/dashboard/sites')

// Computed properties for permissions
const canEdit = computed(() => {
  const role = authStore.user?.role
  return role === 'SUPER_ADMIN' || role === 'ADMIN' || role === 'MANAGER'
})

const canCreateDelete = computed(() => {
  const role = authStore.user?.role
  return role === 'SUPER_ADMIN' || role === 'ADMIN'
})

const displayFields = computed((): DisplayField[] => {
  return [
    { key: 'name', label: t('common.name'), icon: 'mdi-domain' },
    {
      type: 'address',
      label: t('common.address'),
      icon: 'mdi-map-marker',
      address: 'address',
      postalCode: 'postal_code',
      city: 'city',
      country: 'country',
      key: 'address'
    },
    { key: 'nfc_id', label: t('common.id'), icon: 'mdi-nfc' },
    { key: 'organization_name', label: t('common.organization'), icon: 'mdi-domain' },
    { key: 'manager_name', label: t('common.manager'), icon: 'mdi-account-tie' },
    { key: 'late_margin', label: t('sites.lateMarginMinutes'), icon: 'mdi-clock-alert', suffix: ' minutes' },
    {
      key: 'is_active',
      label: t('common.status'),
      icon: 'mdi-check-circle',
      type: 'status',
      activeLabel: t('sites.statusActive'),
      inactiveLabel: t('sites.statusInactive')
    }
  ]
})

// Type guard pour vérifier si un champ est de type adresse
const isAddressField = (field: DisplayField): field is AddressField => {
  return field.type === 'address'
}

// Méthodes
const loadData = async () => {
  try {
    loading.value = true

    // Charger les détails du site et les statistiques en parallèle
    const [siteResponse, siteStats] = await Promise.all([
      sitesApi.getSite(itemId.value),
      sitesApi.getSiteStatistics(itemId.value)
    ])

    // Mettre à jour les données du site
    item.value = {
      ...siteResponse.data,
      manager_name: siteResponse.data.manager_name || '',
      organization_name: siteResponse.data.organization_name || ''
    } as ExtendedSite

    // Mettre à jour les statistiques
    statistics.value = [
      { label: 'Employés', value: siteStats.data.total_employees || 0 },
      { label: 'Heures totales', value: siteStats.data.total_hours || 0 },
      { label: 'Anomalies', value: siteStats.data.anomalies || 0 }
    ]

    // Générer le QR code
    await generateQRCode()
  } catch (error) {
    console.error('[SiteDetail][LoadData] Erreur lors du chargement des données:', error)
    showError('Erreur lors du chargement des données du site')
  } finally {
    loading.value = false
  }
}

const generateQRCode = async () => {
  if (!item.value) {
    showError(t('profile.cannotGenerateQr'))
    return
  }

  try {
    const previewQRCode = await generateStyledQRCode(item.value, {
      width: 500,
      height: 500,
      qrSize: 500,
      showFrame: false
    })

    const downloadQRCode = await generateStyledQRCode(item.value, {
      width: 500,
      height: 700,
      qrSize: 400,
      showFrame: true,
      radius: 20
    })

    item.value.qr_code = previewQRCode
    item.value.download_qr_code = downloadQRCode
  } catch (error) {
    console.error('[SiteDetail][GenerateQRCode] Erreur lors de la génération du QR code:', error)
    showError('Erreur lors de la génération du QR code')
  }
}

const downloadQRCode = async () => {
  if (!item.value?.qr_code) {
    showError(t('profile.qrNotAvailable'))
    return
  }

  try {
    const link = document.createElement('a')
    link.href = item.value.download_qr_code || item.value.qr_code
    const fileName = `qr-code-${item.value.name.toLowerCase().replace(/\s+/g, '-')}.png`
    link.download = fileName

    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    showSuccess(t('profile.qrDownloadStarted'))
  } catch (error) {
    console.error('[SiteDetail][DownloadQRCode] Erreur lors du téléchargement du QR code:', error)
    showError(t('profile.downloadError'))
  }
}

const formatFieldValue = (field: Field, value: any) => {
  if (!value) return ''
  if (field.suffix) return `${value}${field.suffix}`
  return value
}

const editItem = () => {
  router.push(`/dashboard/sites/${itemId.value}/edit`).catch(error => {
    console.error('[SiteDetail][Edit] Erreur lors de la redirection:', error)
  })
}

const confirmDelete = () => {
  showDeleteDialog.value = true
}

const formatDate = (date: string) => {
  return format(new Date(date), 'dd/MM/yyyy HH:mm', { locale: fr })
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

const handleToggleStatus = async (type: string, item: TableItem) => {
  try {
    if (type === 'employees') {
      await sitesApi.updateSite(item.id, {
        ...item,
        is_active: !item.is_active
      })
    } else if (type === 'schedules') {
      await sitesApi.updateSchedule(itemId.value, item.id, {
        ...item,
        is_active: !item.is_active
      })
    }
    await loadTabData(activeTab.value)
    showSuccess(t('profile.statusUpdated'))
  } catch (error) {
    console.error('[SiteDetail][HandleToggleStatus] Erreur lors de la mise à jour du statut:', error)
    showError(t('profile.statusUpdateError'))
  }
}

const handleDelete = async (type: string, item: TableItem) => {
  try {
    if (type === 'employees') {
      await sitesApi.unassignEmployee(itemId.value, item.id)
    } else if (type === 'schedules') {
      await sitesApi.deleteSchedule(itemId.value, item.id)
    }
    await loadTabData(activeTab.value)
    showSuccess(t('profile.planningDeleted'))
  } catch (error) {
    console.error('[SiteDetail][HandleDelete] Erreur lors de la suppression:', error)
    showError(t('profile.deleteError'))
  }
}

const unassignEmployeeFromSite = async (employeeId: number) => {
  try {
    await sitesApi.unassignEmployee(itemId.value, employeeId)
    await loadEmployees()
    showSuccess(t('plannings.employeeRemoved'))
  } catch (error) {
    console.error('[SiteDetail][UnassignEmployeeFromSite] Erreur lors du retrait de l\'employé:', error)
    showError(t('profile.deleteError'))
  }
}

const downloadReport = async (reportId: number) => {
  try {
    const response = await sitesApi.downloadReport(itemId.value, reportId)
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `rapport-${reportId}.pdf`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    showSuccess(t('profile.downloadStarted'))
  } catch (error) {
    showError(t('profile.downloadError'))
    console.error('[SiteDetail][DownloadReport] Erreur lors du téléchargement du rapport:', error)
  }
}

// Méthodes de chargement des données pour chaque onglet
const loadEmployees = async () => {
  loadingTabs.value.employees = true;
  try {
    console.log('[SiteDetail][LoadEmployees] Chargement des employés pour le site:', itemId.value);
    const response = await sitesApi.getSiteEmployees(itemId.value);
    console.log('[SiteDetail][LoadEmployees] Réponse reçue:', response.data);
    employees.value = response.data.results;
  } catch (error) {
    console.error('[SiteDetail][LoadEmployees] Erreur lors du chargement des employés:', error);
    showError('Erreur lors du chargement des employés');
  } finally {
    loadingTabs.value.employees = false;
  }
};

const loadPointages = async () => {
  loadingTabs.value.pointages = true;
  try {
    const response = await sitesApi.getSitePointages(itemId.value);
    pointages.value = response.data.results;
  } catch (error) {
    console.error('[SiteDetail][LoadPointages] Erreur lors du chargement des pointages:', error);
    showError('Erreur lors du chargement des pointages');
  } finally {
    loadingTabs.value.pointages = false;
  }
};

const loadAnomalies = async () => {
  loadingTabs.value.anomalies = true;
  try {
    const response = await sitesApi.getSiteAnomalies(itemId.value);
    anomalies.value = response.data.results;
  } catch (error) {
    console.error('[SiteDetail][LoadAnomalies] Erreur lors du chargement des anomalies:', error);
    showError('Erreur lors du chargement des anomalies');
  } finally {
    loadingTabs.value.anomalies = false;
  }
};

const loadReports = async () => {
  loadingTabs.value.reports = true;
  try {
    const response = await sitesApi.getSiteReports(itemId.value);
    reports.value = response.data.results;
  } catch (error) {
    console.error('[SiteDetail][LoadReports] Erreur lors du chargement des rapports:', error);
    showError('Erreur lors du chargement des rapports');
  } finally {
    loadingTabs.value.reports = false;
  }
};

const loadPlannings = async () => {
  loadingTabs.value.plannings = true;
  try {
    console.log('[SiteDetail][LoadPlannings] Chargement des plannings pour le site:', itemId.value);
    const response = await planningsApi.getSitePlannings(itemId.value);
    console.log('[SiteDetail][LoadPlannings] Réponse reçue:', response.data);
    item.value.schedules = response.data.results;
  } catch (error) {
    console.error('[SiteDetail][LoadPlannings] Erreur lors du chargement des plannings:', error);
    showError('Erreur lors du chargement des plannings');
  } finally {
    loadingTabs.value.plannings = false;
  }
};

// Fonction pour charger les données en fonction de l'onglet actif
const loadTabData = async (tab: string) => {
  switch (tab) {
    case 'employees':
      await loadEmployees();
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

const confirmTogglePlanningStatus = (planning: any) => {
  showConfirmDialog({
    title: planning.is_active ? t('common.deactivate') + ' ' + t('plannings.title').toLowerCase() : t('common.activate') + ' ' + t('plannings.title').toLowerCase(),
    message: t('plannings.deletePlanningConfirmation'),
    confirmText: planning.is_active ? t('common.deactivate') : t('common.activate'),
    cancelText: t('common.cancel'),
    confirmColor: planning.is_active ? 'warning' : 'success',
    onConfirm: async () => {
      await togglePlanningStatus(planning)
    }
  })
}

const togglePlanningStatus = async (planning: any) => {
  try {
    // Utiliser l'ID du planning directement sans l'ID du site
    // Cela utilise l'endpoint /sites/schedules/{id}/ au lieu de /sites/{siteId}/schedules/{scheduleId}/
    await schedulesApi.updateSchedule(0, planning.id, {
      is_active: !planning.is_active
    })

    // Mettre à jour le planning dans la liste locale
    const index = item.value.schedules.findIndex((p: any) => p.id === planning.id)
    if (index !== -1) {
      item.value.schedules[index].is_active = !planning.is_active
    }

    showSuccess(t('profile.statusUpdated'))
  } catch (error) {
    console.error('[SiteDetail][TogglePlanningStatus] Erreur lors du changement de statut:', error)
    showError(t('profile.statusUpdateError'))
  }
}

const confirmDeletePlanning = (planning: any) => {
  showConfirmDialog({
    title: t('plannings.deletePlanning'),
    message: t('plannings.deletePlanningConfirmation'),
    confirmText: t('common.delete'),
    cancelText: t('common.cancel'),
    confirmColor: 'error',
    onConfirm: async () => {
      await deletePlanning(planning)
    }
  })
}

const deletePlanning = async (planning: any) => {
  try {
    await schedulesApi.deleteSchedule(planning.id)

    // Retirer le planning de la liste
    item.value.schedules = item.value.schedules.filter((p: any) => p.id !== planning.id)

    showSuccess(t('profile.planningDeleted'))
  } catch (error) {
    console.error('[SiteDetail][DeletePlanning] Erreur lors de la suppression:', error)
    showError(t('profile.deleteError'))
  }
}
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

/* Style du QR code */
.qr-code-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 1rem;
}

:deep(.v-img.mx-auto) {
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: 8px;
  padding: 8px;
  background-color: white;
}

.gap-2 {
  gap: 8px;
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

/* Style des tooltips */
:deep(.v-tooltip) {
  z-index: 100;
}

/* Style des lignes du tableau */
:deep(.v-data-table .v-data-table__tr) {
  cursor: pointer;
}

:deep(.v-data-table .v-data-table__tr:hover) {
  background-color: rgba(0, 52, 110, 0.04) !important;
}

/* Style des cellules du tableau */
:deep(.v-data-table .v-data-table__td) {
  padding: 12px 16px;
}

/* Style des en-têtes du tableau */
:deep(.v-data-table .v-data-table-header) {
  background-color: #f5f5f5;
}

:deep(.v-data-table .v-data-table-header th) {
  font-weight: 500;
  color: rgba(0, 0, 0, 0.87);
  padding: 12px 16px;
}

/* Style du message "Aucun employé trouvé" */
:deep(.v-data-table .v-data-table__empty-wrapper) {
  padding: 24px;
  text-align: center;
  color: rgba(0, 0, 0, 0.6);
}
</style>