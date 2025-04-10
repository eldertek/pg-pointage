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
        Modifier
      </v-btn>
      <v-btn
        v-if="canCreateDelete"
        color="error"
        prepend-icon="mdi-delete"
        @click.stop="confirmDelete"
      >
        Supprimer
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
          <v-tab value="details">Informations</v-tab>
          <v-tab value="employees">Employés</v-tab>
          <v-tab value="plannings">Plannings</v-tab>
          <v-tab value="pointages">Pointages</v-tab>
          <v-tab value="anomalies">Anomalies</v-tab>
          <v-tab value="reports">Rapports</v-tab>
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
                                  :active-label="field.activeLabel"
                                  :inactive-label="field.inactiveLabel"
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
                          QR Code du site
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
                                Télécharger
                              </v-btn>
                              <v-btn
                                color="#F78C48"
                                prepend-icon="mdi-refresh"
                                @click="generateQRCode"
                              >
                                Régénérer
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
                title="Employés"
                :headers="employeesHeaders"
                :items="employees"
                :no-data-text="'Aucun employé trouvé'"
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
                    <v-tooltip activator="parent">Voir les détails</v-tooltip>
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
                    <v-tooltip activator="parent">Retirer du site</v-tooltip>
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
                  <v-toolbar-title>Plannings</v-toolbar-title>
                  <v-spacer></v-spacer>
                </v-toolbar>
                <v-data-table
                  :headers="planningsHeaders"
                  :items="item.schedules || []"
                  :no-data-text="'Aucun planning trouvé'"
                  class="elevation-1"
                  @click:row="(item) => router.push(`/dashboard/plannings/${item.id}`)"
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
                      @click.stop="viewPlanningDetails(item)"
                    >
                      <v-icon>mdi-eye</v-icon>
                      <v-tooltip activator="parent">Voir les détails</v-tooltip>
                    </v-btn>
                    <v-btn
                      icon
                      variant="text"
                      size="small"
                      color="primary"
                      @click.stop="navigateToPlanning(item)"
                    >
                      <v-icon>mdi-pencil</v-icon>
                      <v-tooltip activator="parent">Modifier</v-tooltip>
                    </v-btn>
                    <v-btn
                      icon
                      variant="text"
                      size="small"
                      color="warning"
                      @click.stop="confirmTogglePlanningStatus(item)"
                    >
                      <v-icon>{{ item.is_active ? 'mdi-domain' : 'mdi-domain-off' }}</v-icon>
                      <v-tooltip activator="parent">{{ item.is_active ? 'Désactiver' : 'Activer' }}</v-tooltip>
                    </v-btn>
                    <v-btn
                      icon
                      variant="text"
                      size="small"
                      color="error"
                      @click.stop="confirmDeletePlanning(item)"
                    >
                      <v-icon>mdi-delete</v-icon>
                      <v-tooltip activator="parent">Supprimer</v-tooltip>
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
                title="Pointages"
                :headers="pointagesHeaders"
                :items="pointages"
                :no-data-text="'Aucun pointage trouvé'"
              >
                <template #item.status="{ item: rowItem }">
                  <v-chip
                    :color="getPointageStatusColor(rowItem.status)"
                    size="small"
                  >
                    {{ getPointageStatusLabel(rowItem.status) }}
                  </v-chip>
                </template>

                <template #item.created_at="{ item: rowItem }">
                  {{ formatDate(rowItem.created_at) }}
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
                title="Anomalies"
                :headers="anomaliesHeaders"
                :items="anomalies"
                :no-data-text="'Aucune anomalie trouvée'"
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
                title="Rapports"
                :headers="reportsHeaders"
                :items="reports"
                :no-data-text="'Aucun rapport trouvé'"
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
                    <v-tooltip activator="parent">Télécharger le rapport</v-tooltip>
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
import type { DialogState } from '@/utils/dialogs'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'

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
const allowDelete = ref(true)

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
const { dialogState, showConfirmDialog } = useConfirmDialog()

// Données pour les tableaux
const employees = ref<any[]>([])
const pointages = ref<any[]>([])
const anomalies = ref<any[]>([])
const reports = ref<any[]>([])

// En-têtes des tableaux
const employeesHeaders = [
  { title: 'Nom', key: 'employee_name' },
  { title: 'Actions', key: 'actions', sortable: false }
]

const planningsHeaders = [
  { title: 'Site', key: 'site_name', align: 'start' },
  { title: 'Employés', key: 'employees', align: 'start' },
  { title: 'Type', key: 'schedule_type', align: 'start' },
  { title: 'Actions', key: 'actions', sortable: false, align: 'end' }
]

const pointagesHeaders = [
  { title: 'Employé', key: 'employee_name' },
  { title: 'Type', key: 'type' },
  { title: 'Date/Heure', key: 'created_at' },
  { title: 'Statut', key: 'status' }
]

const anomaliesHeaders = [
  { title: 'Employé', key: 'employee_name' },
  { title: 'Type', key: 'type' },
  { title: 'Date/Heure', key: 'created_at' },
  { title: 'Statut', key: 'status' }
]

const reportsHeaders = [
  { title: 'Nom', key: 'name' },
  { title: 'Type', key: 'type' },
  { title: 'Date de création', key: 'created_at' },
  { title: 'Actions', key: 'actions', sortable: false }
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

const title = computed(() => 'Détails du site')

const backRoute = computed(() => '/dashboard/sites')

const displayFields = computed((): DisplayField[] => {
  return [
    { key: 'name', label: 'Nom', icon: 'mdi-domain' },
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
    { key: 'nfc_id', label: 'ID', icon: 'mdi-nfc' },
    { key: 'organization_name', label: 'Organisation', icon: 'mdi-domain' },
    { key: 'manager_name', label: 'Manager', icon: 'mdi-account-tie' },
    { key: 'late_margin', label: 'Marge de retard', icon: 'mdi-clock-alert', suffix: ' minutes' },
    {
      key: 'is_active',
      label: 'Statut',
      icon: 'mdi-check-circle',
      type: 'status',
      activeLabel: 'Actif',
      inactiveLabel: 'Inactif'
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
    showError('Impossible de générer le QR code : site non défini')
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
    showError('QR code non disponible pour le téléchargement')
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
    showSuccess('Téléchargement du QR code initié')
  } catch (error) {
    console.error('[SiteDetail][DownloadQRCode] Erreur lors du téléchargement du QR code:', error)
    showError('Erreur lors du téléchargement du QR code')
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

const getDayName = (dayNumber: number) => {
  const days = ['Dimanche', 'Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi']
  return days[dayNumber]
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
    'PENDING': 'En attente',
    'VALIDATED': 'Validé',
    'REJECTED': 'Rejeté'
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
    'PENDING': 'En attente',
    'RESOLVED': 'Résolu',
    'REJECTED': 'Rejeté'
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
    showSuccess(`Statut mis à jour avec succès`)
  } catch (error) {
    console.error('[SiteDetail][HandleToggleStatus] Erreur lors de la mise à jour du statut:', error)
    showError(`Erreur lors de la mise à jour du statut`)
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
    showSuccess(`Élément supprimé avec succès`)
  } catch (error) {
    console.error('[SiteDetail][HandleDelete] Erreur lors de la suppression:', error)
    showError(`Erreur lors de la suppression`)
  }
}

const unassignEmployeeFromSite = async (employeeId: number) => {
  try {
    await sitesApi.unassignEmployee(itemId.value, employeeId)
    await loadEmployees()
    showSuccess(`Employé retiré du site avec succès`)
  } catch (error) {
    console.error('[SiteDetail][UnassignEmployeeFromSite] Erreur lors du retrait de l\'employé:', error)
    showError(`Erreur lors du retrait de l'employé`)
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
    showSuccess(`Rapport téléchargé avec succès`)
  } catch (error) {
    showError(`Erreur lors du téléchargement du rapport`)
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

const openDialog = (item: any) => {
  router.push(`/dashboard/sites/${itemId.value}/schedules/${item.id}/edit`)
}

const toggleStatus = async (item: any) => {
  try {
    await planningsApi.updatePlanning(item.id, {
      ...item,
      is_active: !item.is_active
    })
    await loadPlannings()
    showSuccess(`Statut du planning mis à jour avec succès`)
  } catch (error) {
    console.error('[SiteDetail][ToggleStatus] Erreur lors de la mise à jour du statut:', error)
    showError(`Erreur lors de la mise à jour du statut`)
  }
}

const confirmDeleteSchedule = async (item: any) => {
  try {
    await planningsApi.deletePlanning(item.id)
    await loadPlannings()
    showSuccess(`Planning supprimé avec succès`)
  } catch (error) {
    console.error('[SiteDetail][Delete] Erreur lors de la suppression:', error)
    showError(`Erreur lors de la suppression`)
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

const confirmTogglePlanningStatus = (planning: any) => {
  showConfirmDialog({
    title: planning.is_active ? 'Désactiver le planning' : 'Activer le planning',
    message: `Êtes-vous sûr de vouloir ${planning.is_active ? 'désactiver' : 'activer'} ce planning ?`,
    confirmText: planning.is_active ? 'Désactiver' : 'Activer',
    cancelText: 'Annuler',
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

    showSuccess(`Planning ${planning.is_active ? 'désactivé' : 'activé'} avec succès`)
  } catch (error) {
    console.error('[SiteDetail][TogglePlanningStatus] Erreur lors du changement de statut:', error)
    showError(`Erreur lors du ${planning.is_active ? 'désactivation' : 'activation'} du planning`)
  }
}

const confirmDeletePlanning = (planning: any) => {
  showConfirmDialog({
    title: 'Supprimer le planning',
    message: 'Êtes-vous sûr de vouloir supprimer ce planning ? Cette action est irréversible.',
    confirmText: 'Supprimer',
    cancelText: 'Annuler',
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

    showSuccess('Planning supprimé avec succès')
  } catch (error) {
    console.error('[SiteDetail][DeletePlanning] Erreur lors de la suppression:', error)
    showError('Erreur lors de la suppression du planning')
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