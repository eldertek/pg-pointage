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
        color="primary"
        prepend-icon="mdi-pencil"
        class="mr-2"
        @click.stop="editItem"
      >
        Modifier
      </v-btn>
      <v-btn
        v-if="allowDelete"
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
          <v-tab value="sites">Sites</v-tab>
          <v-tab value="employees">Employés</v-tab>
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
                                  :active-label="field.activeLabel"
                                  :inactive-label="field.inactiveLabel"
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
                        <v-card-title>Logo</v-card-title>
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
                    :to="`/dashboard/sites/create?organization=${itemId}`"
                  >
                    Ajouter un site
                  </v-btn>
                </template>
                
                <template #item.is_active="{ item }">
                  <StatusChip :status="item.is_active" />
                </template>
                
                <template #item.created_at="{ item }">
                  {{ formatDate(item.created_at) }}
                </template>
              </DataTable>
            </v-window-item>

            <!-- Onglet Employés -->
            <v-window-item value="employees">
              <DataTable
                title="Employés"
                :headers="employeesHeaders"
                :items="employees"
                :no-data-text="'Aucun employé trouvé'"
                :detail-route="'/dashboard/admin/users/:id'"
                :edit-route="'/dashboard/admin/users/:id/edit'"
                @toggle-status="(item: TableItem) => handleToggleStatus('employees', item)"
                @delete="(item: TableItem) => handleDelete('employees', item)"
                @row-click="(item: TableItem) => router.push(`/dashboard/admin/users/${item.id}`)"
              >
                <template #toolbar-actions>
                  <v-btn
                    color="primary"
                    prepend-icon="mdi-account-plus"
                    :to="`/dashboard/admin/users/create?organization=${itemId}`"
                  >
                    Ajouter un employé
                  </v-btn>
                </template>
                
                <template #item.is_active="{ item }">
                  <StatusChip :status="item.is_active" />
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
import { organizationsApi } from '@/services/api'
import StatusChip from '@/components/common/StatusChip.vue'
import AddressWithMap from '@/components/common/AddressWithMap.vue'
import DataTable, { type TableItem } from '@/components/common/DataTable.vue'

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
const deleting = ref(false)
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
const tabOrder = ['details', 'sites', 'employees', 'reports']

watch(activeTab, (newTab, oldTab) => {
  if (!oldTab || !newTab) return
  
  const oldIndex = tabOrder.indexOf(oldTab)
  const newIndex = tabOrder.indexOf(newTab)
  
  reverse.value = newIndex < oldIndex
  previousTab.value = oldTab
})

// Computed properties
const itemId = computed(() => Number(route.params.id))

const title = computed(() => "Détails de l'organisation")

const backRoute = computed(() => '/dashboard/organizations')

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
const reports = ref<any[]>([])

// En-têtes des tableaux
const sitesHeaders = [
  { title: 'Nom', key: 'name' },
  { title: 'Adresse', key: 'address' },
  { title: 'Manager', key: 'manager_name' },
  { title: 'Statut', key: 'is_active' },
  { title: 'Date d\'ajout', key: 'created_at' },
  { title: 'Actions', key: 'actions', sortable: false }
]

const employeesHeaders = [
  { title: 'Nom', key: 'last_name' },
  { title: 'Prénom', key: 'first_name' },
  { title: 'Email', key: 'email' },
  { title: 'Rôle', key: 'role' },
  { title: 'Statut', key: 'is_active' },
  { title: 'Date d\'ajout', key: 'created_at' },
  { title: 'Actions', key: 'actions', sortable: false }
]

const reportsHeaders = [
  { title: 'Nom', key: 'name' },
  { title: 'Type', key: 'type' },
  { title: 'Date de création', key: 'created_at' },
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

const deleteItem = async () => {
  deleting.value = true
  try {
    await organizationsApi.deleteOrganization(itemId.value)
    await router.push('/dashboard/organizations')
  } catch (error) {
    console.error('[OrganizationDetail][Delete] Erreur lors de la suppression:', error)
    showError('Erreur lors de la suppression de l\'organisation')
  } finally {
    deleting.value = false
    showDeleteDialog.value = false
  }
}

const formatDate = (date: string) => {
  return format(new Date(date), 'dd/MM/yyyy HH:mm', { locale: fr })
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