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
        :color="isOwnProfile ? 'grey' : 'primary'"
        prepend-icon="mdi-pencil"
        class="mr-2"
        :disabled="isOwnProfile"
        @click.stop="editItem"
      >
        Modifier
      </v-btn>
      <v-btn
        v-if="allowDelete"
        :color="isOwnProfile ? 'grey' : 'error'"
        prepend-icon="mdi-delete"
        :disabled="isOwnProfile"
        @click.stop="confirmDelete"
      >
        Supprimer
        <v-tooltip v-if="isOwnProfile" activator="parent">
          Vous ne pouvez pas supprimer votre propre compte
        </v-tooltip>
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
          <v-tab value="sites">Sites</v-tab>
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
                                  {{ item[field.key] === 'MANAGER' ? 'Manager' : 'Employé' }}
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
                        <v-card-title>Statistiques</v-card-title>
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
              <DataTable
                title="Sites"
                :headers="sitesHeaders"
                :items="sites"
                :no-data-text="'Aucun site trouvé'"
                :detail-route="'/dashboard/sites/:id'"
                :edit-route="'/dashboard/sites/:id/edit'"
                @toggle-status="(item: TableItem) => handleToggleStatus('sites', item)"
                @delete="(item: TableItem) => handleDelete('sites', item)"
                @row-click="(item: TableItem) => router.push(`/dashboard/sites/${item.id}`)"
              >
                <template #toolbar-actions>
                  <v-btn
                    color="primary"
                    prepend-icon="mdi-domain-plus"
                    @click="openAssignSitesDialog"
                  >
                    Assigner un site
                  </v-btn>
                </template>
                
                <template #item.is_active="{ item }">
                  <StatusChip :status="item.is_active" />
                </template>
                
                <template #item.created_at="{ item }">
                  {{ formatDate(item.created_at) }}
                </template>
                
                <template #item.actions="{ item }">
                  <v-btn
                    icon
                    variant="text"
                    size="small"
                    color="primary"
                    :to="`/dashboard/sites/${item.id}`"
                    @click.stop
                  >
                    <v-icon>mdi-eye</v-icon>
                    <v-tooltip activator="parent">Voir les détails</v-tooltip>
                  </v-btn>
                  <v-btn
                    icon
                    variant="text"
                    size="small"
                    color="error"
                    @click.stop="unassignSiteFromUser(item.id)"
                  >
                    <v-icon>mdi-domain-remove</v-icon>
                    <v-tooltip activator="parent">Retirer l'accès</v-tooltip>
                  </v-btn>
                </template>
              </DataTable>
            </v-window-item>

            <!-- Onglet Plannings -->
            <v-window-item value="plannings">
              <DataTable
                title="Plannings"
                :headers="planningsHeaders"
                :items="plannings"
                :no-data-text="'Aucun planning trouvé'"
              >
                <template #item.schedule_type="{ item }">
                  <v-chip
                    :color="item.schedule_type === 'FIXED' ? 'primary' : 'warning'"
                    size="small"
                  >
                    {{ item.schedule_type === 'FIXED' ? 'Fixe' : 'Fréquence' }}
                  </v-chip>
                </template>

                <template #item.site="{ item }">
                  {{ item.site_name }}
                </template>

                <template #item.details="{ item }">
                  <div v-for="detail in item.details" :key="detail.id" class="mb-1">
                    <strong>{{ getDayName(detail.day_of_week) }}:</strong>
                    <template v-if="item.schedule_type === 'FIXED'">
                      <template v-if="detail.day_type === 'FULL'">
                        {{ detail.start_time_1 }}-{{ detail.end_time_1 }} / {{ detail.start_time_2 }}-{{ detail.end_time_2 }}
                      </template>
                      <template v-else-if="detail.day_type === 'AM'">
                        {{ detail.start_time_1 }}-{{ detail.end_time_1 }}
                      </template>
                      <template v-else-if="detail.day_type === 'PM'">
                        {{ detail.start_time_2 }}-{{ detail.end_time_2 }}
                      </template>
                    </template>
                    <template v-else>
                      {{ detail.frequency_duration }}h
                    </template>
                  </div>
                </template>
              </DataTable>
            </v-window-item>

            <!-- Onglet Pointages -->
            <v-window-item value="pointages">
              <DataTable
                title="Pointages"
                :headers="pointagesHeaders"
                :items="pointages"
                :no-data-text="'Aucun pointage trouvé'"
              >
                <template #item.status="{ item }">
                  <v-chip
                    :color="getPointageStatusColor(item.status)"
                    size="small"
                  >
                    {{ getPointageStatusLabel(item.status) }}
                  </v-chip>
                </template>

                <template #item.created_at="{ item }">
                  {{ formatDate(item.created_at) }}
                </template>
              </DataTable>
            </v-window-item>

            <!-- Onglet Anomalies -->
            <v-window-item value="anomalies">
              <DataTable
                title="Anomalies"
                :headers="anomaliesHeaders"
                :items="anomalies"
                :no-data-text="'Aucune anomalie trouvée'"
              >
                <template #item.status="{ item }">
                  <v-chip
                    :color="getAnomalyStatusColor(item.status)"
                    size="small"
                  >
                    {{ getAnomalyStatusLabel(item.status) }}
                  </v-chip>
                </template>

                <template #item.created_at="{ item }">
                  {{ formatDate(item.created_at) }}
                </template>
              </DataTable>
            </v-window-item>

            <!-- Onglet Rapports -->
            <v-window-item value="reports">
              <DataTable
                title="Rapports"
                :headers="reportsHeaders"
                :items="reports"
                :no-data-text="'Aucun rapport trouvé'"
              >
                <template #item.created_at="{ item }">
                  {{ formatDate(item.created_at) }}
                </template>

                <template #item.actions="{ item }">
                  <v-btn
                    icon
                    variant="text"
                    size="small"
                    color="primary"
                    @click.stop="downloadReport(item.id)"
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
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Title } from '@/components/typography'
import { formatPhoneNumber } from '@/utils/formatters'
import { format } from 'date-fns'
import { fr } from 'date-fns/locale'
import { useAuthStore } from '@/stores/auth'
import { RoleEnum } from '@/types/api'
import { usersApi } from '@/services/api'
import StatusChip from '@/components/common/StatusChip.vue'
import DataTable, { type TableItem } from '@/components/common/DataTable.vue'

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

// Props
const showBackButton = ref(true)
const allowDelete = ref(true)

// State variables
const router = useRouter()
const route = useRoute()
const loading = ref(true)
const deleting = ref(false)
const showDeleteDialog = ref(false)
const item = ref<any>({})
const statistics = ref<Array<{ label: string; value: number }>>([])
const auth = useAuthStore()
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

// Données pour les tableaux
const sites = ref<any[]>([])
const plannings = ref<any[]>([])
const pointages = ref<any[]>([])
const anomalies = ref<any[]>([])
const reports = ref<any[]>([])

// En-têtes des tableaux
const sitesHeaders = [
  { title: 'Nom', key: 'name' },
  { title: 'Adresse', key: 'address' },
  { title: 'Organisation', key: 'organization_name' },
  { title: 'Statut', key: 'is_active' },
  { title: 'Date d\'ajout', key: 'created_at' },
  { title: 'Actions', key: 'actions', sortable: false }
]

const planningsHeaders = [
  { title: 'Type', key: 'schedule_type' },
  { title: 'Site', key: 'site' },
  { title: 'Détails', key: 'details' },
  { title: 'Statut', key: 'is_active' }
]

const pointagesHeaders = [
  { title: 'Site', key: 'site_name' },
  { title: 'Type', key: 'type' },
  { title: 'Date/Heure', key: 'created_at' },
  { title: 'Statut', key: 'status' }
]

const anomaliesHeaders = [
  { title: 'Site', key: 'site_name' },
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
  'SUPER_ADMIN': 'Super Administrateur',
  'ADMIN': 'Administrateur',
  'MANAGER': 'Manager',
  'EMPLOYEE': 'Employé'
}

const scanPreferenceLabels: Record<string, string> = {
  'BOTH': 'QR Code et NFC',
  'QR_CODE': 'QR Code uniquement',
  'NFC': 'NFC uniquement'
}

// Computed properties
const itemId = computed(() => Number(route.params.id))

const title = computed(() => "Détails de l'utilisateur")

const backRoute = computed(() => '/dashboard/admin/users')

// Computed pour vérifier si c'est le profil de l'utilisateur connecté
const isOwnProfile = computed(() => {
  return (auth.user as User)?.id === itemId.value
})

const displayFields = computed((): Field[] => {
  const fields: Field[] = [
    { key: 'first_name', label: 'Prénom', icon: 'mdi-account', type: 'default' },
    { key: 'last_name', label: 'Nom', icon: 'mdi-account-box', type: 'default' },
    { key: 'email', label: 'Email', icon: 'mdi-email', type: 'default' },
    { key: 'phone_number', label: 'Téléphone', icon: 'mdi-phone', type: 'default', format: 'phone' },
    { key: 'role', label: 'Rôle', icon: 'mdi-badge-account', type: 'default', format: 'role' }
  ]

  // Ajouter employee_id seulement s'il existe et n'est pas vide
  if (item.value?.employee_id) {
    fields.push({ key: 'employee_id', label: 'ID Employé', icon: 'mdi-card-account-details', type: 'default' })
  }

  return [
    ...fields,
    { key: 'scan_preference', label: 'Préférence de scan', icon: 'mdi-qrcode-scan', type: 'default', format: 'scan_preference' },
    { key: 'simplified_mobile_view', label: 'Vue mobile simplifiée', icon: 'mdi-cellphone',
      type: 'status',
      activeLabel: 'Activée',
      inactiveLabel: 'Désactivée'
    },
    { key: 'date_joined', label: 'Date d\'inscription', icon: 'mdi-calendar', type: 'default', format: 'date', dateFormat: 'dd/MM/yyyy HH:mm' },
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

// Méthodes
const loadData = async () => {
  loading.value = true
  try {
    const response = await usersApi.getUser(itemId.value);
    item.value = response.data;
    const stats = await usersApi.getUserStatistics(itemId.value);
    statistics.value = [
      { label: 'Heures totales', value: stats.data.total_hours || 0 },
      { label: 'Anomalies', value: stats.data.anomalies || 0 }
    ];
  } catch (error) {
    console.error('[UserDetail][LoadData] Erreur lors du chargement des données:', error)
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
  
  router.push(`/dashboard/admin/users/${itemId.value}/edit`).catch(error => {
    console.error('[UserDetail][Edit] Erreur lors de la redirection:', error)
  })
}

const confirmDelete = () => {
  if (isOwnProfile.value) {
    return
  }
  showDeleteDialog.value = true
}

const deleteItem = async () => {
  deleting.value = true
  try {
    await usersApi.deleteUser(itemId.value)
    await router.push('/dashboard/admin/users')
  } catch (error) {
    console.error('[UserDetail][Delete] Erreur lors de la suppression:', error)
  } finally {
    deleting.value = false
    showDeleteDialog.value = false
  }
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
    // Implémentation à faire
    showSuccess(`Statut mis à jour avec succès`)
  } catch (error) {
    showError(`Erreur lors de la mise à jour du statut`)
  }
}

const handleDelete = async (type: string, item: TableItem) => {
  try {
    // Implémentation à faire
    showSuccess(`Élément supprimé avec succès`)
  } catch (error) {
    showError(`Erreur lors de la suppression`)
  }
}

const openAssignSitesDialog = () => {
  // Implémentation à faire
}

const unassignSiteFromUser = async (siteId: number) => {
  try {
    // Implémentation à faire
    showSuccess(`Site retiré avec succès`)
  } catch (error) {
    showError(`Erreur lors du retrait du site`)
  }
}

const downloadReport = async (reportId: number) => {
  try {
    // Implémentation à faire
    showSuccess(`Rapport téléchargé avec succès`)
  } catch (error) {
    showError(`Erreur lors du téléchargement du rapport`)
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
</style> 