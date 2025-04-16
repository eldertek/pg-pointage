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
          <v-tab value="sites">{{ $t('sites.title') }}</v-tab>
          <v-tab value="employees">{{ $t('reports.reportTypes.EMPLOYEE') }}</v-tab>
          <v-tab value="reports">{{ $t('reports.title') }}</v-tab>
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
                              <template v-if="field.type === 'address' && isAddressField(field)">
                                <AddressWithMap
                                  :address="item[field.address]"
                                  :postal-code="item[field.postalCode]"
                                  :city="item[field.city]"
                                  :country="item[field.country]"
                                />
                              </template>
                              <template v-else-if="field.type === 'status'">
                                <StatusChip
                                  :status="item[field.key]"
                                  :active-:label="$t('dashboard.fieldactivelabel')"
                                  :inactive-:label="$t('dashboard.fieldinactivelabel')"
                                />
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
                      <v-card v-if="item.logo" class="mb-4">
                        <v-card-title>{{ $t('organizations.logo') }}</v-card-title>
                        <v-card-text class="text-center">
                          <v-img
                            :src="item.logo"
                            :alt="item.name"
                            max-width="200"
                            class="mx-auto"
                          ></v-img>
                        </v-card-text>
                      </v-card>
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

            <!-- Onglet Sites -->
            <v-window-item value="sites">
              <DataTable
                :title="$t('sites.title')"
                :headers="sitesHeaders"
                :items="sites"
                :no-data-:text="$t('dashboard.aucun_site_trouv')"
                :detail-route="'/dashboard/sites/:id'"
                :edit-route="'/dashboard/sites/:id/edit'"
                @toggle-status="(item: TableItem) => handleToggleStatus('sites', item)"
                @delete="(item: TableItem) => handleDelete('sites', item)"
                @row-click="(item: TableItem) => router.push(`/dashboard/sites/${item.id}`)"
              >
                
                <template #item.is_active="{ item: rowItem }">
                  <StatusChip :status="rowItem.is_active" />
                </template>
                
                <template #item.created_at="{ item: rowItem }">
                  {{ formatDate(rowItem.created_at) }}
                </template>
              </DataTable>
            </v-window-item>

            <!-- Onglet Employés -->
            <v-window-item value="employees">
              <DataTable
                :title="$t('reports.reportTypes.EMPLOYEE')"
                :headers="employeesHeaders"
                :items="employees"
                :no-data-:text="$t('dashboard.aucun_employ_trouv')"
                :detail-route="'/dashboard/admin/users/:id'"
                :edit-route="'/dashboard/admin/users/:id/edit'"
                @toggle-status="(item: TableItem) => handleToggleStatus('employees', item)"
                @delete="(item: TableItem) => handleDelete('employees', item)"
                @row-click="(item: TableItem) => router.push(`/dashboard/admin/users/${item.id}`)"
              >
                <template #item.email="{ item: rowItem }">
                  {{ rowItem.first_name }} {{ rowItem.last_name }}
                </template>
                
                <template #item.phone_number="{ item: rowItem }">
                  <v-tooltip location="top" :text="$t('dashboard.cliquer_pour_appeler')">
                    <template #activator="{ props }">
                      <a 
                        v-bind="props"
                        :href="`tel:${rowItem.phone_number}`"
                        class="text-decoration-none"
                        @click.stop
                      >
                        {{ formatPhoneNumber(rowItem.phone_number) }}
                      </a>
                    </template>
                  </v-tooltip>
                </template>
                
                <template #item.role="{ item: rowItem }">
                  {{ getRoleTranslation(rowItem.role) }}
                </template>
              </DataTable>
            </v-window-item>

            <!-- Onglet Rapports -->
            <v-window-item value="reports">
              <DataTable
                :title="$t('reports.title')"
                :headers="reportsHeaders"
                :items="reports"
                :no-data-:text="$t('dashboard.aucun_rapport_trouv')"
              >
                <template #item.created_at="{ item: rowItem }">
                  {{ formatDate(rowItem.created_at) }}
                </template>
                <template #item.report_type_display="{ item: rowItem }">
                  {{ rowItem.report_type_display }}
                </template>
                <template #item.report_format_display="{ item: rowItem }">
                  {{ rowItem.report_format_display }}
                </template>
                <template #item.period="{ item: rowItem }">
                  {{ rowItem.period }}
                </template>
                <template #item.created_by_name="{ item: rowItem }">
                  {{ rowItem.created_by_name }}
                </template>
              </DataTable>
            </v-window-item>
          </v-window>
        </v-card-text>
      </v-card>
    </template>
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
import { organizationsApi } from '@/services/api'
import StatusChip from '@/components/common/StatusChip.vue'
import AddressWithMap from '@/components/common/AddressWithMap.vue'
import DataTable, { type TableItem } from '@/components/common/DataTable.vue'
import { sitesApi } from '@/services/api'
import { employeesService } from '@/services/employees'

// Types
interface Field {
  key: string;
  label: string;
  icon: string;
  type?: 'address' | 'status' | 'default' | 'date';
  activeLabel?: string;
  inactiveLabel?: string;
  format?: 'phone' | 'date';
  dateFormat?: string;
}

interface AddressField extends Field {
  type: 'address';
  address: string;
  postalCode: string;
  city: string;
  country: string;
}

type DisplayField = Field | AddressField;

// Props
const showBackButton = ref(true)
const allowDelete = ref(true)

// State variables
const router = useRouter()
const route = useRoute()
const loading = ref(true)
const loadingTabs = ref({
  sites: false,
  employees: false,
  pointages: false,
  anomalies: false,
  reports: false
})
const showDeleteDialog = ref(false)
const item = ref<any>({})
const statistics = ref<Array<{ label: string; value: number }>>([])
const activeTab = ref('details')
const previousTab = ref('details')
const reverse = ref(false)

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
const tabOrder = ['details', 'sites', 'employees', 'pointages', 'anomalies', 'reports']

watch(activeTab, (newTab, oldTab) => {
  if (!oldTab || !newTab) return
  
  const oldIndex = tabOrder.indexOf(oldTab)
  const newIndex = tabOrder.indexOf(newTab)
  
  reverse.value = newIndex < oldIndex
  previousTab.value = oldTab

  // Charger les données du nouvel onglet s'il n'est pas 'details'
  if (newTab !== 'details') {
    loadTabData(newTab)
  }
})

// Computed properties
const itemId = computed(() => Number(route.params.id))

const title = computed(() => "Détails de l'organisation")

const backRoute = computed(() => '/dashboard/admin/access')

const displayFields = computed((): DisplayField[] => {
  return [
    { key: 'name', label: 'Nom', icon: 'mdi-domain' },
    { key: 'org_id', label: 'ID Organisation', icon: 'mdi-identifier' },
    {
      type: 'address',
      label: 'Adresse',
      icon: 'mdi-map-marker',
      address: 'address',
      postalCode: 'postal_code',
      city: 'city',
      country: 'country',
      key: 'address'
    },
    { key: 'phone', label: 'Téléphone', icon: 'mdi-phone', format: 'phone' },
    { key: 'contact_email', label: 'Email de contact', icon: 'mdi-email-outline' },
    { key: 'siret', label: 'SIRET', icon: 'mdi-card-account-details' },
    { key: 'notes', label: 'Notes', icon: 'mdi-note-text' },
    { key: 'created_at', label: 'Date de création', icon: 'mdi-calendar-plus', format: 'date', dateFormat: 'dd/MM/yyyy HH:mm' },
    { key: 'updated_at', label: 'Dernière modification', icon: 'mdi-calendar-clock', format: 'date', dateFormat: 'dd/MM/yyyy HH:mm' },
    { 
      key: 'is_active',
      label: 'Statut',
      icon: 'mdi-check-circle',
      type: 'status',
      activeLabel: 'Active',
      inactiveLabel: 'Inactive'
    }
  ]
})

// Type guard pour vérifier si un champ est de type adresse
const isAddressField = (field: DisplayField): field is AddressField => {
  return field.type === 'address'
}

// Données pour les tableaux
const sites = ref<any[]>([])
const employees = ref<any[]>([])
const pointages = ref<any[]>([])
const anomalies = ref<any[]>([])
const reports = ref<any[]>([])

// En-têtes des tableaux
const sitesHeaders = [
  { title: 'Nom', key: 'name' },
  { title: 'Adresse', key: 'address' },
  { title: 'Manager', key: 'manager_name' },
  { title: 'Actions', key: 'actions', sortable: false }
]

const employeesHeaders = [
  { 
    title: 'Email', 
    key: 'email',
    align: 'start',
    sortable: true
  },
  { 
    title: 'Téléphone', 
    key: 'phone_number',
    align: 'start',
    sortable: true
  },
  { 
    title: 'Rôle', 
    key: 'role',
    align: 'start',
    sortable: true
  },
  { 
    title: 'Actions', 
    key: 'actions', 
    sortable: false,
    align: 'end'
  }
]

const reportsHeaders = [
  { title: 'Site', key: 'site_name' },
  { title: 'Type', key: 'report_type_display' },
  { title: 'Format', key: 'report_format_display' },
  { title: 'Période', key: 'period' },
  { title: 'Créé par', key: 'created_by_name' },
  { title: 'Actions', key: 'actions', sortable: false }
]

// Méthodes
const loadData = async () => {
  loading.value = true
  try {
    const orgResponse = await organizationsApi.getOrganization(itemId.value)
    item.value = orgResponse.data
    
    const orgStats = await organizationsApi.getOrganizationStatistics(itemId.value)
    statistics.value = [
      { label: 'Sites', value: orgStats.data.total_sites || 0 },
      { label: 'Employés', value: orgStats.data.total_employees || 0 },
      { label: 'Sites actifs', value: orgStats.data.active_sites || 0 }
    ]
  } catch (error) {
    console.error('[OrganizationDetail][LoadData] Erreur lors du chargement des données:', error)
    showError('Erreur lors du chargement des données de l\'organisation')
  } finally {
    loading.value = false
  }
}

const formatFieldValue = (field: Field, value: any) => {
  if (!value) return ''
  if (field.format === 'phone') return formatPhoneNumber(value)
  if (field.format === 'date') {
    try {
      const date = new Date(value)
      return format(date, field.dateFormat || 'dd/MM/yyyy', { locale: fr })
    } catch (error) {
      console.error('[OrganizationDetail][FormatDate] Erreur lors du formatage de la date:', error)
      return value
    }
  }
  return value
}

const editItem = () => {
  router.push(`/dashboard/organizations/${itemId.value}/edit`).catch(error => {
    console.error('[OrganizationDetail][Edit] Erreur lors de la redirection:', error)
  })
}

const confirmDelete = () => {
  showDeleteDialog.value = true
}

const formatDate = (date: string) => {
  return format(new Date(date), 'dd/MM/yyyy HH:mm', { locale: fr })
}

const handleToggleStatus = async (type: string, item: TableItem) => {
  try {
    if (type === 'sites') {
      await sitesApi.updateSite(item.id, {
        is_active: !item.is_active
      })
    } else if (type === 'employees') {
      await employeesService.toggleEmployeeStatus(item.id, !item.is_active)
    }
    await loadData()
    showSuccess(`Statut mis à jour avec succès`)
  } catch (error) {
    console.error('[OrganizationDetail][HandleToggleStatus] Erreur lors de la mise à jour du statut:', error)
    showError(`Erreur lors de la mise à jour du statut`)
  }
}

const handleDelete = async (type: string, item: TableItem) => {
  try {
    if (type === 'sites') {
      await sitesApi.deleteSite(item.id)
    } else if (type === 'employees') {
      await employeesService.deleteEmployee(item.id)
    }
    await loadData()
    showSuccess(`Élément supprimé avec succès`)
  } catch (error) {
    console.error('[OrganizationDetail][HandleDelete] Erreur lors de la suppression:', error)
    showError(`Erreur lors de la suppression`)
  }
}

// Méthodes de chargement des données pour chaque onglet
const loadSites = async () => {
  console.log('[OrganizationDetail][LoadSites] Chargement des sites...')
  loadingTabs.value.sites = true
  try {
    const response = await organizationsApi.getOrganizationSites(itemId.value)
    sites.value = response.data.results
  } catch (error) {
    console.error('[OrganizationDetail][LoadSites] Erreur lors du chargement des sites:', error)
    showError('Erreur lors du chargement des sites')
  } finally {
    loadingTabs.value.sites = false
  }
}

const loadEmployees = async () => {
  console.log('[OrganizationDetail][LoadEmployees] Début du chargement des employés...')
  loadingTabs.value.employees = true
  try {
    const response = await organizationsApi.getOrganizationUsers(itemId.value)
    employees.value = response.data.results
    console.log('[OrganizationDetail][LoadEmployees] Appel API pour l\'organisation', itemId.value)
    console.log('[OrganizationDetail][LoadEmployees] Données reçues:', response.data)
    console.log('[OrganizationDetail][LoadEmployees] Nombre d\'employés chargés:', employees.value.length)
    
    // Ajout des logs détaillés pour chaque employé
    employees.value.forEach((employee, index) => {
      console.log(`[OrganizationDetail][LoadEmployees] Détails de l'employé ${index + 1}:`)
      console.log('- ID:', employee.id)
      console.log('- Nom complet:', `${employee.first_name} ${employee.last_name}`)
      console.log('- Email:', employee.email)
      console.log('- Rôle:', employee.role)
      console.log('- Téléphone:', employee.phone_number)
      console.log('- Statut:', employee.is_active ? 'Actif' : 'Inactif')
      console.log('- Organisations:', employee.organizations_names)
      console.log('----------------------------------------')
    })
  } catch (error) {
    console.error('[OrganizationDetail][LoadEmployees] Erreur lors du chargement des employés:', error)
    showError('Erreur lors du chargement des employés')
  } finally {
    loadingTabs.value.employees = false
  }
}

const loadPointages = async () => {
  console.log('[OrganizationDetail][LoadPointages] Chargement des pointages...')
  loadingTabs.value.pointages = true
  try {
    const response = await organizationsApi.getOrganizationTimesheets(itemId.value, {
      page: 1,
      page_size: 10
    })
    pointages.value = response.data.results
  } catch (error) {
    console.error('[OrganizationDetail][LoadPointages] Erreur lors du chargement des pointages:', error)
    showError('Erreur lors du chargement des pointages')
  } finally {
    loadingTabs.value.pointages = false
  }
}

const loadAnomalies = async () => {
  console.log('[OrganizationDetail][LoadAnomalies] Chargement des anomalies...')
  loadingTabs.value.anomalies = true
  try {
    const response = await organizationsApi.getOrganizationAnomalies(itemId.value, {
      page: 1,
      page_size: 10
    })
    anomalies.value = response.data.results
  } catch (error) {
    console.error('[OrganizationDetail][LoadAnomalies] Erreur lors du chargement des anomalies:', error)
    showError('Erreur lors du chargement des anomalies')
  } finally {
    loadingTabs.value.anomalies = false
  }
}

const loadReports = async () => {
  console.log('[OrganizationDetail][LoadReports] Chargement des rapports...')
  loadingTabs.value.reports = true
  try {
    const response = await organizationsApi.getOrganizationReports(itemId.value, {
      page: 1,
      page_size: 10
    })
    reports.value = response.data.results
  } catch (error) {
    console.error('[OrganizationDetail][LoadReports] Erreur lors du chargement des rapports:', error)
    showError('Erreur lors du chargement des rapports')
  } finally {
    loadingTabs.value.reports = false
  }
}

// Fonction pour charger les données en fonction de l'onglet actif
const loadTabData = async (tab: string) => {
  console.log('[OrganizationDetail][LoadTabData] Chargement des données pour l\'onglet:', tab)
  switch (tab) {
    case 'sites':
      await loadSites()
      break
    case 'employees':
      await loadEmployees()
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

// Lifecycle hooks
onMounted(async () => {
  await loadData()
  // Charger les données de l'onglet initial si ce n'est pas 'details'
  if (activeTab.value !== 'details') {
    await loadTabData(activeTab.value)
  }
})

// Watch for route changes
watch(
  () => route.params.id,
  async (newId, oldId) => {
    if (newId !== oldId) {
      await loadData()
      // Recharger les données de l'onglet actif si ce n'est pas 'details'
      if (activeTab.value !== 'details') {
        await loadTabData(activeTab.value)
      }
    }
  }
)

// Ajouter cette fonction dans la section script
const getRoleTranslation = (role: string) => {
  const roleTranslations: { [key: string]: string } = {
    'SUPER_ADMIN': 'Super administrateur',
    'ADMIN': 'Administrateur',
    'MANAGER': 'Manager',
    'EMPLOYEE': 'Employé'
  }
  return roleTranslations[role] || role
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